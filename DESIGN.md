# Veil-FHE — Design & Engineering Document

> **This is the canonical reference for building Veil-FHE.** It is the single
> source of truth for ideology, architecture, technical decisions, the build
> roadmap, and implementation detail. The user-facing documentation under
> `docs/` is derived from this; when they disagree, *this* document wins.
>
> **Status:** Pre-implementation, architecture finalized
> **License:** MIT
> **Scope:** Solo build, ~3 months
> **Last updated:** 2026-06-04

---

## Table of contents

1. [What Veil-FHE is](#1-what-veil-fhe-is)
2. [Ideology and honest positioning](#2-ideology-and-honest-positioning)
3. [Threat model](#3-threat-model)
4. [Locked design decisions](#4-locked-design-decisions)
5. [System architecture](#5-system-architecture)
6. [The compilation pipeline, stage by stage](#6-the-compilation-pipeline-stage-by-stage)
7. [Operator mapping](#7-operator-mapping)
8. [Critical implementation detail](#8-critical-implementation-detail)
9. [Public API specification](#9-public-api-specification)
10. [Repository layout](#10-repository-layout)
11. [Build system](#11-build-system)
12. [Testing strategy](#12-testing-strategy)
13. [Benchmarking methodology](#13-benchmarking-methodology)
14. [The roadmap](#14-the-roadmap)
15. [Resolved questions (decision log)](#15-resolved-questions-decision-log)
16. [Glossary](#16-glossary)
17. [References](#17-references)

---

## 1. What Veil-FHE is

Veil-FHE is a privacy-preserving machine-learning inference library. It compiles
a standard `torch.nn.Module` into an encrypted inference graph so that a server
can run a forward pass on data it cannot read.

The trust flow is: the **client** holds the secret key, encrypts an input, and
sends only ciphertext to the **server**. The server runs `forward()` using
homomorphic operations and never possesses the secret key, so it never sees the
plaintext input or the plaintext output. The server returns an encrypted result
the client decrypts locally.

The target developer experience is a three-line change from ordinary PyTorch
inference:

```python
import veil

fhe_model = veil.compile(model, input_shape=(1, 784), calibration_data=X_sample)

# Client side (holds the secret key)
enc_input, ctx = fhe_model.encrypt(x)        # x: torch.Tensor

# Server side (no secret key)
enc_output = fhe_model.forward(enc_input)

# Client side
output = fhe_model.decrypt(enc_output, ctx)  # -> torch.Tensor
```

The cryptography is CKKS (approximate arithmetic over real numbers) provided by
the OpenFHE C++ library, exposed to Python through a thin pybind11 extension.

---

## 2. Ideology and honest positioning

**Veil-FHE is a research and learning artifact, not a product, and it does not
claim to invent anything.** This framing is deliberate and load-bearing; every
piece of public-facing copy must respect it.

### 2.1 What this project is honestly trying to be

The goal is to build, end to end and from first principles, the full pipeline
that turns a trained neural network into something that runs under homomorphic
encryption: ONNX ingestion, graph rewriting, polynomial approximation of
activations, CKKS level-budget planning, encrypted linear algebra, and a clean
Python API. The value is in *understanding the whole stack deeply enough to have
built it*, and in producing something a reader can study, run, and benchmark.

### 2.2 Prior art that already exists (acknowledge it, do not pretend otherwise)

This problem is well-trodden. The following projects already do versions of what
Veil-FHE does, and the documentation must link to them rather than imply a
green field:

- **Zama Concrete ML** — compiles models to FHE using the TFHE scheme with a
  quantization pipeline. The most mature thing in this space. Veil-FHE borrows
  *API-design taste* from it (the "compile a model object" ergonomic) and
  nothing else.
- **OpenFHE's own `openfhe-python`** — the official pybind11 wrapper exposing the
  raw CKKS/BGV/BFV/TFHE primitives. Veil-FHE sits a layer above this: it is a
  *compiler*, not a primitives binding. (We write our own minimal binding rather
  than depending on `openfhe-python` so the C++/Python boundary stays small and
  fully under our control — see §4.4.)
- **Academic encrypted-inference work** — packing- and depth-aware CNN inference,
  encrypted transformer inference, and similar. These are the state of the art
  and are far beyond this project's scope. Cite them; do not compete with them.

The honest one-line positioning is: *"An educational, from-scratch FHE inference
compiler built on CKKS/OpenFHE, exploring the tradeoffs of approximate-arithmetic
homomorphic encryption for neural-network inference."* The differentiator versus
Concrete ML is the **scheme** (CKKS native floats, no quantization pipeline), not
a novel technique.

### 2.3 Intellectual honesty rules (non-negotiable)

These bind both human and agent contributors:

- **Never claim novelty.** No "first," "novel," "breakthrough." It is a
  reimplementation that explores known ideas.
- **Never hide the performance reality.** FHE inference is orders of magnitude
  slower than plaintext (expect milliseconds → seconds, sometimes minutes for
  deep networks with bootstrapping). Every performance claim must be backed by a
  reproducible benchmark in `benchmarks/`. The README states the slowdown up
  front.
- **Never overstate accuracy.** CKKS is approximate and polynomial activation
  approximations add error. Report measured error, do not hand-wave it.
- **Never imply security guarantees we have not earned.** The code is not
  audited. It must carry the "do not use to protect real secrets" notice
  (`SECURITY.md`). Correct *use* of a library does not make an *implementation*
  secure.
- **When a pre-existing solution covers something, say so** rather than
  retrofitting a justification for reinventing it.

### 2.4 "Research now, maybe production later"

The architecture is allowed to make choices that keep a future hardening path
open (clean module boundaries, a serializable compiled-model artifact, a real
benchmark harness), but it must **not** spend current effort on
production-only concerns (HA, multi-tenant key services, side-channel hardening).
Where a decision trades present simplicity against future production needs,
prefer present simplicity and leave a note in the decision log.

---

## 3. Threat model

Stating this precisely is part of being honest about what the library does.

### 3.1 The standard model Veil-FHE targets

- **Client** is trusted and holds the CKKS secret key. It performs key
  generation, encryption, and decryption locally.
- **Server** is *semi-honest* (honest-but-curious): it runs the protocol
  correctly but may try to learn the input from what it sees. The server
  receives ciphertexts plus the public evaluation keys (rotation and
  relinearization keys) needed to compute, but never the secret key.
- **Model weights are plaintext on the server.** This is the primary, simplest
  use case: the server owns/knows the model; the client's *input and output* are
  what stay private. (See §15, decision 7.) The both-blind variant where weights
  are also encrypted is explicitly out of scope for v1.

### 3.2 What Veil-FHE protects

The confidentiality of the client's input tensor and the inference output,
against a semi-honest server, under the security level of the chosen CKKS
parameter set (targeting 128-bit security via OpenFHE's parameter selection).

### 3.3 What Veil-FHE does NOT protect against, and must say so

- **Malicious (actively dishonest) servers.** There is no integrity proof that
  the server ran the correct computation. CKKS provides confidentiality, not
  verifiable computation.
- **Model privacy.** The model architecture and weights are not hidden from the
  server in v1.
- **Metadata leakage.** Input *shape*, model *topology*, and timing are visible.
- **Implementation-level attacks.** No constant-time guarantees, no side-channel
  hardening, no audited key management.
- **CKKS-specific subtlety:** the IND-CPA-D class of attacks against approximate
  FHE means that *returning decrypted CKKS results to an adversary who chose the
  ciphertexts* can leak secret-key information. Veil-FHE's model (client decrypts
  locally, server never sees plaintext output) avoids the classic exposure, but
  the threat-model doc must mention this and warn against building protocols that
  hand decrypted CKKS output back to an untrusted party.

---

## 4. Locked design decisions

These have been evaluated and should not be reopened without strong cause. Each
states the decision, the reason, and what was rejected.

### 4.1 FHE scheme: CKKS

CKKS operates over approximate real numbers natively, so weights stay as floats
and there is **no quantization pipeline**. It supports SIMD batching (one
ciphertext packs thousands of slots), which is what makes encrypted linear
layers tractable. Its approximate decryption is acceptable for inference (not for
training).

*Rejected:* BFV/BGV need a full PTQ/QAT quantization pipeline before FHE
compilation, reproducing Concrete ML's complexity for no gain here. TFHE is built
for Boolean/LUT circuits, a fundamentally different programming model.

### 4.2 FHE library: OpenFHE (≥ 1.5.1)

Actively maintained, strong CKKS support including **approximate bootstrapping**
(needed for networks deeper than ~5 multiplicative levels), good rotation support
(needed for the diagonal linear-layer encoding), and a `FLEXIBLEAUTO` rescaling
mode that handles post-multiply rescaling automatically. Pin to a released tag,
not `main`.

*Rejected:* Microsoft SEAL is mature but development has slowed and its
bootstrapping story is weaker.

### 4.3 Model IR: ONNX internally, PyTorch frontend externally

Users pass an `nn.Module` to `veil.compile()`. Internally, `compile()` calls
`torch.onnx.export` with hardened settings and operates on the ONNX graph; users
never touch ONNX.

Why ONNX rather than `torch.fx` internally:

- A finite, versioned op set (~170 ops in opset 17) versus PyTorch's hundreds of
  variant ops needing normalization.
- A structurally static graph with explicit shape annotations on every edge —
  required for FHE parameter planning.
- A stable, opset-versioned API surface versus the shifting
  TorchScript → fx → torch.export landscape.
- A correctness property for free: a model that fails ONNX export because of
  dynamic control flow *cannot be FHE-compiled anyway*, so export failure is a
  useful early gate.

**Target opset: 17, and only 17 for v1** (see §15, decision 9).

### 4.4 Python bindings: pybind11, with our own minimal surface

OpenFHE is C++. pybind11 gives proper RAII and exception propagation across the
boundary and is what the official `openfhe-python` uses, so the patterns are
proven. We write our **own** thin binding (`src/backend.cpp`) exposing only the
handful of primitives Veil-FHE needs, rather than depending on `openfhe-python`,
because a small surface we control is easier to reason about, test, and keep
honest about lifetimes/keys. Do not use ctypes. Do not add a Rust shim.

### 4.5 OpenFHE acquisition: CMake FetchContent (with a system fallback)

`FetchContent` pinned to an OpenFHE release tag builds OpenFHE from source as
part of our build, so contributors and CI need no separate install step. Because
OpenFHE is large and slow to compile, the build also supports linking a
preinstalled OpenFHE via `find_package` for fast local iteration, selected by a
CMake option (`VEIL_USE_SYSTEM_OPENFHE`). Build caching (ccache) is mandatory in
CI. See §11.

### 4.6 Dependency management (uv) and packaging (scikit-build-core)

**uv** manages the environment, dependencies, and lockfile (`uv.lock`, committed).
**scikit-build-core** is the build backend that ships the CMake + pybind11
extension as wheels. These are complementary: uv orchestrates, scikit-build-core
builds. `pyproject.toml` is the single configuration root — runtime deps under
`[project]`, dev tooling under `[dependency-groups]` (PEP 735). Do not reintroduce
bare `pip`/`requirements.txt` or hand-edit the lockfile.

### 4.7 Platforms and Python

Linux x86_64, macOS (arm64 + x86_64), and Windows x86_64 are all supported
(OpenFHE supports all three). Python **3.12+**. Windows is the slowest and most
fragile to build; CI treats it as a first-class but separately-cached job, and
the docs note it may need Visual Studio build tools.

### 4.8 Acceleration

Intel **HEXL** (AVX-512 acceleration for CKKS on x86) is an **optional**,
**off-by-default** build flag (`VEIL_WITH_HEXL`), documented but not required.
**GPU acceleration is out of scope for v1.**

### 4.9 Language conventions

C++17 (OpenFHE's floor). Python tooling: ruff (lint + format) and mypy
(strict). C++ tooling: clang-format and clang-tidy. Strict TDD, Conventional
Commits, MkDocs Material docs.

---

## 5. System architecture

```
User: torch.nn.Module
          │
          ▼
┌──────────────────────────┐
│   Python Frontend        │  veil.compile(), FHEModel
│   (veil/api.py,          │  Owns the public API and orchestration.
│    veil/model.py)        │
└───────────┬──────────────┘
            │  torch.onnx.export (internal, hardened)
            ▼
┌──────────────────────────┐
│   ONNX Ingestor          │  Parse protobuf, run onnxsim, validate op
│   (veil/ingest.py)       │  coverage, extract weights + topology as a DAG.
└───────────┬──────────────┘
            │
            ▼
┌──────────────────────────┐
│   Graph Transformer      │  Fold BatchNorm, rewrite activations to
│   (veil/transform.py)    │  polynomial approximations, run the level-budget
│                          │  analysis, choose CKKS parameters, plan
│                          │  bootstrap insertion.
└───────────┬──────────────┘
            │
            ▼
┌──────────────────────────┐
│   FHE Operator Library   │  Encrypted matmul (diagonal method),
│   (veil/ops/*.py)        │  polynomial activation eval, conv via im2col,
│                          │  pooling, elementwise. Pure orchestration over
│                          │  the backend primitives.
└───────────┬──────────────┘
            │
            ▼
┌──────────────────────────┐
│   C++ FHE Backend        │  OpenFHE CKKS: context + keygen, encrypt,
│   (src/backend.cpp)      │  decrypt, EvalAdd/Mult/Rotate, Chebyshev eval,
│                          │  bootstrap. Thin, lifetime-correct pybind11.
└───────────┬──────────────┘
            │  pybind11
            ▼
┌──────────────────────────┐
│   veil_backend (.so/.pyd)│  Python-importable extension module.
└──────────────────────────┘
```

The strict layering rule: **Python never speaks OpenFHE C++ types directly; it
speaks only the `veil_backend` primitive API.** All cryptographic operations live
behind the backend boundary. The Python side is a compiler and an orchestrator.

---

## 6. The compilation pipeline, stage by stage

`veil.compile(model, input_shape, calibration_data, profile)` runs this pipeline.
Each stage is a pure function from one well-typed representation to the next so it
can be unit-tested in isolation.

### Stage A — Export (`veil/api.py`)
PyTorch `nn.Module` → ONNX `ModelProto`. Uses the hardened export settings in
§8.4. Any export failure is surfaced as a `veil.errors.ExportError` with the
underlying torch message, plus a hint that dynamic control flow is unsupported.

### Stage B — Ingest (`veil/ingest.py`)
ONNX `ModelProto` → internal graph DAG (`veil.ir.Graph`). Runs `onnxsim` first to
fold constants and canonicalize. Validates every op against the supported set
(§7); the **first** unsupported op raises `veil.errors.UnsupportedOpError`
listing the op, its name, and the recommended alternative. Extracts weight and
bias tensors as numpy arrays keyed by edge name; records shapes on every edge.

### Stage C — Transform (`veil/transform.py`)
Internal graph → lowered graph annotated with FHE plans. In order:
1. **BatchNorm folding** — fuse each `BatchNormalization` into the preceding
   `Gemm`/`Conv` at plaintext time (adjust weights/bias; never a runtime FHE op).
2. **Activation rewriting** — replace each `Relu`/`Sigmoid`/`Gelu`/… node with a
   polynomial-approximation node carrying its Chebyshev coefficients, degree, and
   approximation interval (the interval comes from calibration, Stage D's output
   feeds back here — see ordering note below).
3. **Level-budget analysis** — walk every path, sum multiplicative-level
   consumption, and either confirm the chosen `Profile` supports the depth or
   plan bootstrap insertions / raise `LevelBudgetError` (§8.1).
4. **Parameter selection** — derive the OpenFHE CKKS parameters from the budget
   analysis (§8.2).

> **Ordering note:** calibration (Stage D) must run *before* activation rewriting
> can pin its intervals, but *after* ingestion produces the graph. In
> implementation, calibration runs on the plaintext torch model up front (it
> needs the real module, not the ONNX graph), and its per-layer ranges are passed
> into the transform stage. Keep calibration a separate module (`veil/calibration.py`)
> invoked by `compile()` between Stage A inputs and Stage C.

### Stage D — Calibrate (`veil/calibration.py`)
Plaintext torch model + representative batch → per-activation input ranges. Runs
the batch through the plaintext model with forward hooks, records min/max (and
optionally robust percentiles) at each activation site, and returns the intervals
used to fit polynomial approximations. Without this, a ReLU approximated over
`[-5, 5]` behaves nothing like one over `[-50, 50]`.

### Stage E — Lower to operators (`veil/ops/*`, `veil/model.py`)
Lowered graph → an executable `FHEModel`: an ordered list of operator closures
over the `veil_backend` primitives, plus the crypto context spec and the slot
layout metadata. This is what `forward()` walks.

### Stage F — Key generation & artifact (`veil/model.py`)
`FHEModel` builds the OpenFHE crypto context, generates the key set (secret,
public, relinearization, rotation keys for the rotation indices the graph needs,
and bootstrap keys if planned), and is ready to `encrypt`/`forward`/`decrypt`.
`save()`/`load()` serialize the compiled graph + crypto params; eval keys are
saved separately by default (§15, decision 5).

---

## 7. Operator mapping

### 7.1 Supported ops (must implement)

| ONNX op | FHE implementation | Notes |
|---|---|---|
| `Gemm` / `MatMul` | Diagonal encoding + rotations (Halevi–Shoup) | Baby-step/giant-step for O(√n) rotations. OpenFHE `EvalLinearTransform` / `EvalLinearWSum` family wraps the primitive. 1 multiplicative level. |
| `Conv` | im2col → encrypted matmul | Reshape so convolution becomes a matrix multiply, then reuse the linear-layer op. Document the slot-packing cost. |
| `Relu` | Chebyshev poly approx, degree 7–15 | Coefficients fit offline with a minimax/Chebyshev routine over the calibrated interval. Evaluate with Paterson–Stockmeyer to minimize level use. Most expensive and least accurate activation; discourage it. |
| `Sigmoid` | Chebyshev poly approx | Same machinery; degree ~7 is usually enough. |
| `Gelu` | Low-degree (≈3) poly approx | Approximates well at low degree; the recommended activation. |
| `BatchNormalization` | Folded into preceding Gemm/Conv | Plaintext fusion at transform time. Never a runtime FHE op. |
| `Add` | Ciphertext–ciphertext add | Cheap, no level consumption. Handles residual connections. |
| `Mul` (by plaintext) | Ciphertext–plaintext mult | 1 level. Mult by *ciphertext* costs a relinearization. |
| `Reshape` / `Flatten` | Slot-layout metadata change | No FHE op; remap indices. |
| `AveragePool` / `GlobalAveragePool` | Rotate-and-add over the window | Sum across the spatial window using rotations, then scale. |

### 7.2 Unsupported ops (reject at compile time with a clear error)

- `MaxPool` — max over encrypted values is not feasible without an expensive
  approximation; suggest `AveragePool`.
- `Loop`, `If` — data-dependent control flow cannot run on ciphertexts.
- `TopK`, `ArgMax`, `ArgMin` — comparison operators.
- Anything requiring division by a ciphertext.

Rejection happens in Stage B, names the op and the node, and points to the
nearest supported alternative.

### 7.3 Activations to recommend to users (document prominently)

In rough order of FHE-friendliness:
- **`x²` (square)** — native, 1 level, ideal where it is acceptable.
- **GELU** — low-degree approximation, low error. **Recommended default.**
- **SiLU/Swish** — approximable but needs higher degree.
- **ReLU** — approximable but the most expensive and least accurate; document
  this explicitly so users are not surprised.

---

## 8. Critical implementation detail

### 8.1 Level-budget management

In CKKS, every multiplication — including each squaring inside a polynomial
activation evaluation — consumes one multiplicative *level*. Approximate
per-layer consumption:

- Linear/Conv layer: **1 level** (one ciphertext–plaintext multiply).
- Polynomial activation of degree `d` via Paterson–Stockmeyer:
  **≈ ⌈log₂(d)⌉ + 1 levels** (e.g. degree-7 ≈ 3–4 levels, degree-15 ≈ 4–5).

A 5-layer MLP with degree-7 ReLU approximations can easily need ~20 levels. The
transformer (Stage C) must:

1. Traverse the graph and sum level consumption along every path.
2. Check the chosen `Profile`'s multiplicative depth covers the max path.
3. If not, and bootstrapping is enabled, plan a bootstrap at the point the budget
   would be exhausted (bootstrapping refreshes the noise/level budget but costs
   ~seconds per call).
4. If the depth is exceeded and bootstrapping is **not** enabled, raise
   `LevelBudgetError` **at compile time, never at runtime** (decision 4).

Bootstrap auto-insertion is **opt-in** (`allow_bootstrap=True` or `"auto"`).
Default is the conservative hard error, so deep networks fail loudly instead of
silently running orders of magnitude slower.

### 8.2 CKKS parameter selection — presets, not raw knobs

Expose presets; derive raw parameters from the budget analysis.

```python
class Profile(Enum):
    FAST     # ring dim 8192,  ~5 levels,  128-bit security
    BALANCED # ring dim 16384, ~10 levels, 128-bit security
    DEEP     # ring dim 32768, ~20 levels, 128-bit security, slow
```

Underlying OpenFHE configuration (set via `CCParams<CryptoContextCKKSRNS>`):
- `SetMultiplicativeDepth(...)` — from the level-budget analysis.
- `SetScalingModSize(50)` — 50-bit scaling: good precision/noise tradeoff.
- `SetFirstModSize(60)` — 60-bit first modulus.
- `SetBatchSize(...)` — match the input vector / packing length.
- `SetScalingTechnique(FLEXIBLEAUTO)` — **always**. Never `FIXEDMANUAL`; do not
  implement manual rescaling.
- `SetSecurityLevel(HEStd_128_classic)` — 128-bit target; let OpenFHE pick ring
  dimension consistent with depth + security where possible, and validate it
  matches the profile.

The `Profile` is a *ceiling and a default*; if the analyzed depth exceeds the
profile, that is exactly the `LevelBudgetError` case.

### 8.3 The calibration pass

Before generating parameters, run a plaintext calibration pass (Stage D):

```python
fhe_model = veil.compile(
    model,
    input_shape=(1, 784),
    calibration_data=X_sample,   # small, representative batch
    profile=veil.Profile.BALANCED,
)
```

It forwards a representative batch through the **plaintext** model, records
activation ranges per layer, and uses them to set each polynomial
approximation's domain. Calibration data is required whenever the model has any
non-square activation; `compile()` raises a clear error if it is missing and
needed.

### 8.4 ONNX export hardening

The internal export must be fully static:

```python
torch.onnx.export(
    model,
    dummy_input,
    buffer,
    opset_version=17,
    do_constant_folding=True,
    input_names=["input"],
    output_names=["output"],
    dynamic_axes=None,        # force a fully static graph
    export_params=True,
)
```

After export, run `onnxsim` to fold constants and canonicalize before ingestion;
this removes many degenerate node patterns the compiler would otherwise handle.

### 8.5 Out-of-range inputs at inference time

Polynomial approximations diverge sharply outside their fitted interval (Runge
phenomenon), so an input outside the calibration range can produce a silently
wrong result — the worst possible failure for a privacy tool, because the client
cannot tell. Policy (decision 8): **warn + clamp by default**, with a strict mode
that errors.
- At calibration: warn if the recorded range looks suspiciously narrow.
- At encryption/inference: clamp inputs to the calibrated domain and emit a
  warning, unless `strict=True`, in which case raise `OutOfDomainError`.

### 8.6 Key management

Eval keys (rotation + relinearization, and bootstrap keys when used) can be
hundreds of MB and are tied to the crypto context, not the model logic. Default
(decision 5): `FHEModel.save(path)` persists the compiled graph + crypto
parameters; eval keys are saved separately via an explicit call, with an opt-in
`bundle=True` for convenience.

### 8.7 Batching

v1 is single-sample (decision 6), but the slot-layout metadata is designed so
that packing N samples into the SIMD slots of one ciphertext can be added later
without an API break. Do not hard-code "one input vector" assumptions into the
operator closures; route everything through the slot-layout object.

---

## 9. Public API specification

```python
import veil
from veil import Profile

# --- Compilation (anywhere; needs the plaintext model) ---
fhe_model: veil.FHEModel = veil.compile(
    model: torch.nn.Module,
    input_shape: tuple[int, ...],
    *,
    calibration_data: torch.Tensor | None = None,
    profile: Profile = Profile.BALANCED,
    allow_bootstrap: bool | str = False,   # False | True | "auto"
    strict: bool = False,                  # out-of-domain behavior
)

# --- Client: holds the secret key ---
enc_input: veil.EncryptedTensor
ctx: veil.ClientContext
enc_input, ctx = fhe_model.encrypt(x: torch.Tensor)

# --- Server: no secret key ---
enc_output: veil.EncryptedTensor = fhe_model.forward(enc_input)

# --- Client ---
output: torch.Tensor = fhe_model.decrypt(enc_output, ctx)

# --- Persistence ---
fhe_model.save(path)                       # graph + crypto params
fhe_model.save_eval_keys(path)             # large; explicit
fhe_model.save(path, bundle=True)          # everything, opt-in
FHEModel.load(path)
```

Type sketch:
- `EncryptedTensor` wraps one or more backend ciphertext handles plus the slot
  layout; it is opaque and carries no secret material.
- `ClientContext` holds the secret key and the metadata needed to decrypt; it
  **never** crosses to the server in any example or doc.
- `FHEModel` is the compiled, executable artifact. `forward()` requires only
  public eval keys.

Errors (in `veil/errors.py`): `ExportError`, `UnsupportedOpError`,
`LevelBudgetError`, `OutOfDomainError`, `CalibrationError`, `BackendError`.

---

## 10. Repository layout

```
veil-fhe/
├── DESIGN.md                  # this document (source of truth)
├── AGENTS.md                  # directives for AI coding agents
├── README.md
├── LICENSE                    # MIT
├── SECURITY.md                # "not audited" notice + reporting
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── CHANGELOG.md               # Keep a Changelog format
├── pyproject.toml             # uv + scikit-build-core; ruff/mypy/pytest config
├── uv.lock                    # pinned dependency resolution (committed)
├── .python-version            # pins Python 3.12 for uv
├── CMakeLists.txt             # builds veil_backend via FetchContent(OpenFHE)
├── cmake/
│   └── FindOrFetchOpenFHE.cmake
├── .pre-commit-config.yaml
├── .clang-format
├── .clang-tidy
├── .gitignore
├── mkdocs.yml
├── src/
│   └── backend.cpp            # pybind11 bindings over OpenFHE CKKS
├── veil/
│   ├── __init__.py            # public API surface
│   ├── api.py                 # compile() entry point + export
│   ├── model.py               # FHEModel, keygen, save/load, forward()
│   ├── ingest.py              # ONNX parse + onnxsim + op validation
│   ├── transform.py           # BN fold, activation rewrite, budget, params
│   ├── calibration.py         # plaintext range calibration
│   ├── params.py              # CKKS Profile presets + derivation
│   ├── ir.py                  # internal graph/edge/op dataclasses
│   ├── errors.py              # exception hierarchy
│   └── ops/
│       ├── __init__.py
│       ├── linear.py          # diagonal-method encrypted matmul
│       ├── conv.py            # im2col + matmul
│       ├── activation.py      # Chebyshev fit + Paterson–Stockmeyer eval
│       └── elementwise.py     # add, mul, reshape, pooling
├── tests/
│   ├── test_backend.py        # round-trip encryption accuracy
│   ├── test_ingest.py         # ONNX parsing + op rejection
│   ├── test_transform.py      # BN fold, budget analysis
│   ├── test_ops.py            # each FHE op vs plaintext, error-bounded
│   ├── test_models.py         # end-to-end on tiny models
│   └── fixtures/              # tiny ONNX models + reference outputs
├── benchmarks/
│   ├── README.md
│   └── run_benchmarks.py
├── docs/                      # MkDocs Material (user-facing)
│   ├── index.md
│   ├── getting-started.md
│   ├── architecture.md
│   ├── supported-ops.md
│   ├── threat-model.md
│   ├── benchmarks.md
│   └── faq.md
└── .github/
    ├── workflows/{ci.yml, docs.yml, wheels.yml}
    ├── ISSUE_TEMPLATE/{bug_report.md, feature_request.md}
    └── PULL_REQUEST_TEMPLATE.md
```

---

## 11. Build system

### 11.1 CMake + OpenFHE via FetchContent

`CMakeLists.txt` builds the `veil_backend` pybind11 module. OpenFHE is acquired
through `cmake/FindOrFetchOpenFHE.cmake`:

- If `VEIL_USE_SYSTEM_OPENFHE=ON`, use `find_package(OpenFHE REQUIRED)` (fast
  local iteration against a preinstalled OpenFHE).
- Otherwise, `FetchContent_Declare(OpenFHE GIT_REPOSITORY ... GIT_TAG v1.5.1)`
  and `FetchContent_MakeAvailable`, then link the exported OpenFHE targets
  (`OPENFHEcore`, `OPENFHEpke`, `OPENFHEbinfhe` as needed).
- `VEIL_WITH_HEXL=OFF` by default; when `ON`, pass the corresponding OpenFHE HEXL
  flag through.

Pin OpenFHE to a **released tag**, never `main`. Bump deliberately via a PR that
re-runs the full benchmark suite (parameter behavior can shift between releases).

### 11.2 Dependency management (uv) and packaging (scikit-build-core)

**uv** manages the environment and dependencies; resolutions are pinned in a
committed `uv.lock`. uv does **not** replace the build backend — the native
extension is still built by **scikit-build-core** driving CMake.
`pyproject.toml` uses `build-backend = "scikit_build_core.build"` and declares
runtime deps under `[project]`, dev tooling under `[dependency-groups]` (PEP 735;
the `dev` group syncs by default).

- `uv sync` creates the venv, builds `veil_backend` (hermetic OpenFHE via
  FetchContent), and installs the `dev` group. `uv run <cmd>` executes inside it.
- Fast local iteration links a preinstalled OpenFHE:
  `CMAKE_ARGS="-DVEIL_USE_SYSTEM_OPENFHE=ON" uv sync` (scikit-build-core honors
  `CMAKE_ARGS`), or an explicit `uv pip install -e . -C cmake.define.VEIL_USE_SYSTEM_OPENFHE=ON`.
- Editable installs don't auto-rebuild the C++ on source change; re-sync after
  touching `src/`.
- Wheels are produced in CI via `cibuildwheel` using the `build[uv]` frontend.
- Add deps with `uv add` / `uv add --group dev`; never hand-edit `uv.lock`.

### 11.3 Build caching

ccache in CI for all platforms. The FetchContent OpenFHE build is cached on the
pinned tag so it is built once per tag per platform, not per push.

---

## 12. Testing strategy

**Strict TDD.** No production code without a failing test that motivates it. The
crypto correctness story is the whole point, so the tests are not optional
scaffolding — they are the spec.

Layers:
1. **Backend round-trip** (`test_backend.py`) — encrypt → decrypt a vector, assert
   reconstruction within a CKKS-appropriate tolerance. Encrypt → op → decrypt for
   add/mult/rotate against numpy.
2. **Operator equivalence** (`test_ops.py`) — every FHE operator vs its plaintext
   PyTorch/numpy equivalent, with **quantified error bounds**, not exact equality.
   CKKS is approximate; tests assert `max_abs_error < tol` where `tol` is justified
   in a comment and per-op.
3. **Compiler-stage units** (`test_ingest.py`, `test_transform.py`) — op rejection
   raises the right error; BatchNorm folding is numerically equivalent to the
   unfused graph in plaintext; budget analysis counts levels correctly; depth
   overflow raises `LevelBudgetError`.
4. **End-to-end** (`test_models.py`) — tiny models (a 2-layer MLP on a few MNIST
   digits, a 1-conv-layer net) compiled and run through the full encrypt → forward
   → decrypt cycle, asserting the FHE output matches the plaintext output within a
   documented accuracy budget.

Error tolerances are first-class: every approximate assertion documents *why* its
tolerance is what it is. A test that passes only because the tolerance is loose is
a bug.

CI runs the Python suite on all platforms; the thin GoogleTest C++ unit suite runs
where it builds cheaply (Linux at minimum).

---

## 13. Benchmarking methodology

Performance is the headline limitation, so benchmarking is a deliverable, not an
afterthought. `benchmarks/run_benchmarks.py` produces a reproducible report.

Measure and report, per model and per `Profile`:
- **Latency** — compile time, keygen time, encrypt time, `forward()` time,
  decrypt time, separated. `forward()` is the headline number.
- **Throughput** — inferences/second (single-sample in v1).
- **Accuracy degradation** — top-1 agreement and max/mean absolute error of FHE
  output vs plaintext output on a held-out set, broken down by activation choice
  and polynomial degree.
- **Level/bootstrap profile** — levels consumed, whether bootstrapping fired, and
  its cost.
- **Artifact sizes** — compiled model, eval keys, ciphertext.

Reference models: a small MNIST MLP and a small MNIST CNN, with GELU vs ReLU
variants to show the activation cost difference. Where a fair comparison exists,
note Concrete ML numbers from their published benchmarks (cited, not re-run,
unless re-run under identical hardware).

Every number in the README or docs must trace to a committed benchmark run on
stated hardware. No vibes.

---

## 14. The roadmap

A solo, ~3-month (≈13-week) build. Phases are ordered so each produces something
runnable and testable; do not start a phase before the previous phase's exit
criteria are green. Week numbers are a guide, not a contract.

### Phase 0 — Repository & build bootstrap (Week 1)
Stand up the repo exactly as in §10: CI skeleton, pre-commit, pyproject, an empty
`veil_backend` that compiles and imports, OpenFHE wired via FetchContent on at
least Linux. Conventional Commits and branch protection on.
**Exit:** `uv sync` builds; `import veil_backend` works; CI green on
Linux; docs site builds and deploys.

### Phase 1 — FHE primitives (Weeks 2–3)
Implement `src/backend.cpp`: bind `CryptoContext`, key generation,
`encrypt(vector)`, `decrypt(ciphertext)`, `eval_add`, `eval_mult` (with
relinearization), `eval_rotate`, and Chebyshev-series evaluation. Validate
round-trip accuracy against plaintext.
**Exit:** `test_backend.py` green; round-trip and each primitive within tolerance;
extension builds on all three platforms in CI (Windows allowed to lag by days).

### Phase 2 — FHE operator library (Weeks 4–6)
Encrypted matrix–vector multiply (Halevi–Shoup diagonal method, baby-step/
giant-step rotations); polynomial activation evaluation (Chebyshev fit offline,
Paterson–Stockmeyer eval); `Conv` via im2col; pooling and elementwise ops. Each
operator tested in isolation against its plaintext equivalent with quantified
error bounds.
**Exit:** `test_ops.py` green for every op in §7.1 with documented tolerances.

### Phase 3 — ONNX ingestor (Weeks 6–7)
Parse ONNX with the `onnx` library, run `onnxsim`, validate op coverage (reject
unsupported ops with clear errors), extract weights/biases/topology into the
internal IR (`veil/ir.py`).
**Exit:** `test_ingest.py` green; supported tiny models ingest; each unsupported
op raises the right error pointing to an alternative.

### Phase 4 — Graph transformer (Weeks 8–9)
BatchNorm folding; activation rewriting to polynomial nodes (intervals from
calibration); level-budget analysis; bootstrap-insertion planning; CKKS parameter
derivation; `LevelBudgetError` on overflow when bootstrap is disabled.
**Exit:** `test_transform.py` green; folded graphs numerically match unfused in
plaintext; budget math verified; depth overflow errors at compile time.

### Phase 5 — Python API, calibration & persistence (Weeks 10–11)
Wire `veil.compile()` end to end; implement `calibration.py`; `FHEModel.encrypt/
forward/decrypt`; out-of-domain warn/clamp/strict; `save/load` and separate
`save_eval_keys`.
**Exit:** `test_models.py` green; the 3-line API in §1 works end to end on the
MNIST MLP within the documented accuracy budget.

### Phase 6 — Benchmarking & hardening (Weeks 12–13)
Build `benchmarks/run_benchmarks.py`; produce the first real benchmark report on
stated hardware; tighten docs to match measured reality; close the honesty loop
(README numbers all trace to committed runs). Polish error messages and the
getting-started guide. Tag `v0.1.0`.
**Exit:** reproducible benchmark report committed; docs accurate; `v0.1.0` tagged;
README slowdown/accuracy claims all sourced.

### Explicitly deferred (post-v1)
Batched SIMD inference; encrypted weights (both-blind); GPU; more opsets;
transformer-scale models; CKKS↔TFHE scheme switching for non-smooth functions.

---

## 15. Resolved questions (decision log)

| # | Question | Decision |
|---|---|---|
| 1 | Relationship to other projects | **Standalone.** No cross-references to any sibling project. |
| 2 | Novelty framing | **Honest educational reimplementation** exploring CKKS tradeoffs. No novelty claims. |
| 3 | Maturity posture | **Research now**, production path kept open but not invested in. |
| 4 | Bootstrap threshold | **Conservative:** `LevelBudgetError` at compile time unless `allow_bootstrap` is `True`/`"auto"`. |
| 5 | Key management | **Separate by default;** explicit `save_eval_keys`; opt-in `bundle=True`. |
| 6 | Batching | **Single-sample v1;** slot layout designed to allow batching later without API break. |
| 7 | Weight encryption | **Plaintext weights on server** (server knows model, not input). |
| 8 | Out-of-range inputs | **Warn + clamp** by default; `strict=True` raises `OutOfDomainError`. |
| 9 | Opset | **Pin opset 17 only** for v1. |
| 10 | OpenFHE acquisition | **FetchContent** pinned to a release tag; `find_package` fallback via `VEIL_USE_SYSTEM_OPENFHE`. |
| 11 | Packaging & deps | **uv** for env/deps (committed `uv.lock`); **scikit-build-core** as the build backend. |
| 12 | Platforms / Python | **Linux, macOS, Windows; Python 3.12+.** |
| 13 | Acceleration | **HEXL optional/off by default; GPU out of scope.** |
| 14 | C++ std / tests | **C++17;** test through Python (pytest) + thin GoogleTest. |
| 15 | Conventions | **MIT;** monorepo, MkDocs Material, strict TDD, Conventional Commits, ruff+mypy, clang-format+clang-tidy. |
| 16 | CI | **Generated up front** with build caching. |
| 17 | Timeline | **Solo, ~3 months.** |
| 18 | Benchmarking | **In scope** from the start; numbers must be reproducible. |

---

## 16. Glossary

- **CKKS** — Cheon–Kim–Kim–Song, an FHE scheme for approximate arithmetic over
  real/complex numbers with SIMD packing.
- **Level / multiplicative depth** — how many sequential multiplications a
  ciphertext can undergo before its noise budget is exhausted.
- **Bootstrapping** — a (costly) operation that refreshes the noise budget,
  enabling deeper computation.
- **Relinearization** — the key-switching step after a ciphertext×ciphertext
  multiply that returns the result to a normal-size ciphertext.
- **Rotation** — cyclically shifting the SIMD slots of a ciphertext; the building
  block of the diagonal matmul method.
- **Diagonal (Halevi–Shoup) method** — encodes a matrix by its diagonals so that
  matrix–vector multiply becomes rotations + plaintext multiplies + adds.
- **Paterson–Stockmeyer** — an algorithm to evaluate a degree-`d` polynomial with
  ≈√d multiplications, minimizing level consumption.
- **im2col** — rearranging convolution patches into columns so convolution becomes
  a single matrix multiply.
- **Calibration** — a plaintext pass that records activation ranges to fit
  polynomial approximation intervals.

---

## 17. References

- OpenFHE — https://github.com/openfheorg/openfhe-development ; docs at
  https://openfhe-development.readthedocs.io
- OpenFHE Python wrapper (pybind11 patterns) —
  https://github.com/openfheorg/openfhe-python
- Halevi & Shoup, "Algorithms in HElib" (2014) — diagonal matrix encoding.
- Paterson & Stockmeyer (1973) — efficient polynomial evaluation.
- Cheon et al. — CKKS and CKKS bootstrapping.
- Zama Concrete ML (TFHE-based reference for API design) —
  https://github.com/zama-ai/concrete-ml
- ONNX operator spec — https://onnx.ai/onnx/operators/
- uv — https://docs.astral.sh/uv
- scikit-build-core — https://scikit-build-core.readthedocs.io
- pybind11 — https://pybind11.readthedocs.io

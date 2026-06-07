<h1 align="center">Veil-FHE</h1>

<p align="center">
  <em>Run neural-network inference on data a server can't read.</em><br>
  A from-scratch, educational FHE inference compiler built on CKKS / OpenFHE.
</p>

<p align="center">
  <a href="#status"><img alt="status" src="https://img.shields.io/badge/status-pre--alpha-orange"></a>
  <a href="LICENSE"><img alt="license" src="https://img.shields.io/badge/license-MIT-blue"></a>
  <img alt="python" src="https://img.shields.io/badge/python-3.12%2B-blue">
  <img alt="backend" src="https://img.shields.io/badge/FHE-OpenFHE%20CKKS-6f42c1">
</p>

---

> [!WARNING]
> **Veil-FHE is a research and learning project. It is not audited and must not
> be used to protect real secrets.** It explores the tradeoffs of approximate
> homomorphic encryption (CKKS) for ML inference; it does not claim to invent
> anything, and it does not provide production security guarantees. See
> [`SECURITY.md`](SECURITY.md).

> [!IMPORTANT]
> **FHE inference is orders of magnitude slower than plaintext** — expect
> milliseconds to seconds per inference, sometimes more for deep networks that
> require bootstrapping. This is inherent to the technique, not a bug. All
> performance and accuracy claims trace to reproducible runs under
> [`benchmarks/`](benchmarks/).

## What it does

Veil-FHE compiles a standard `torch.nn.Module` into an encrypted inference graph.
The client holds the secret key, encrypts an input, and sends only ciphertext to
a server. The server runs the forward pass without ever holding the key — it
never sees the plaintext input or output — and returns an encrypted result the
client decrypts locally.

```python
import veil

fhe_model = veil.compile(model, input_shape=(1, 784), calibration_data=X_sample)

# Client (holds the secret key)
enc_input, ctx = fhe_model.encrypt(x)        # x: torch.Tensor

# Server (no secret key)
enc_output = fhe_model.forward(enc_input)

# Client
output = fhe_model.decrypt(enc_output, ctx)  # -> torch.Tensor
```

The cryptography is **CKKS** (approximate arithmetic over real numbers) from
**OpenFHE**, exposed to Python through a thin **pybind11** extension. Because CKKS
is native floating point, there is **no quantization pipeline** — weights stay as
floats.

## How it works (one paragraph)

`compile()` exports your model to ONNX internally, validates op coverage, folds
BatchNorm into adjacent layers, rewrites activations into polynomial
approximations fitted over ranges measured by a plaintext calibration pass,
analyzes the CKKS multiplicative-level budget, selects encryption parameters, and
lowers everything onto encrypted linear-algebra primitives (diagonal-method
matmul, im2col convolution, Paterson–Stockmeyer polynomial evaluation). Full
detail is in [`DESIGN.md`](DESIGN.md).

## Status

Pre-alpha, under active solo development. The roadmap and current phase live in
[`DESIGN.md` §14](DESIGN.md#14-the-roadmap). v1 targets small MLPs and CNNs
(think MNIST-scale), single-sample inference, with plaintext model weights on the
server.

## Install

> Requires [uv](https://docs.astral.sh/uv/), a C++17 toolchain, and CMake. OpenFHE
> is built automatically via CMake FetchContent, or you can point at a system
> install for faster iteration.

```bash
# Hermetic build (builds OpenFHE from source; slow the first time)
uv sync                       # creates .venv, builds veil_backend, installs the dev group
uv run pytest                 # run the suite inside the managed environment

# Faster local build against a preinstalled OpenFHE
CMAKE_ARGS="-DVEIL_USE_SYSTEM_OPENFHE=ON" uv sync
```

Dependencies are managed with uv and pinned in `uv.lock`; the build itself is
still driven by scikit-build-core + CMake (uv does not replace the build backend).

See [`docs/getting-started.md`](docs/getting-started.md) for platform notes
(Linux, macOS, Windows are all supported; Windows is the slowest to build).

## Supported models (v1)

Feed-forward networks using FHE-friendly activations. Recommended activation:
**GELU** (low-degree, low error). `Conv`, `Gemm`/`MatMul`, `Add`, `AveragePool`,
BatchNorm (folded), and reshape/flatten are supported. `MaxPool`, dynamic control
flow (`If`/`Loop`), and comparison ops (`ArgMax`, `TopK`, …) are rejected at
compile time with a clear error. Full table: [`docs/supported-ops.md`](docs/supported-ops.md).

## Documentation

- [`DESIGN.md`](DESIGN.md) — the full design, architecture, and roadmap.
- [`ROADMAP.md`](ROADMAP.md) — phase-by-phase build checklist to work through.
- [`docs/`](docs/) — user guide, threat model, supported ops, benchmarks
  (rendered with MkDocs Material).
- [`SECURITY.md`](SECURITY.md) — threat model summary and the "not audited" notice.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). The project uses uv for dependency
management, strict TDD, Conventional Commits, ruff + mypy (Python), and
clang-format + clang-tidy (C++). If you use an AI coding agent, point it at
[`AGENTS.md`](AGENTS.md).

## License

[MIT](LICENSE).

## Acknowledgements & prior art

Veil-FHE stands on a large body of existing work and does not pretend to be first.
[OpenFHE](https://github.com/openfheorg/openfhe-development) provides the
cryptography; its [`openfhe-python`](https://github.com/openfheorg/openfhe-python)
wrapper informed the binding patterns. [Zama Concrete
ML](https://github.com/zama-ai/concrete-ml) (a TFHE-based system) inspired the
"compile a model object" API ergonomic. The encrypted-inference research
literature is far ahead of this project and worth reading.

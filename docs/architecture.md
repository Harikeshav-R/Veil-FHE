# Architecture

Veil-FHE is a compiler. `veil.compile()` runs a staged pipeline; each stage is a
pure transform that can be tested in isolation.

```
torch.nn.Module
   → ONNX export (hardened, static, opset 17)
   → ingest (onnxsim + op-coverage validation → internal IR)
   → calibrate (plaintext activation ranges)
   → transform (BatchNorm fold, activation→polynomial, level-budget, CKKS params)
   → lower (encrypted-op closures + slot layout)
   → keygen → FHEModel
```

**Layering rule:** the Python package speaks only the `veil_backend` primitive
API. All cryptography lives behind the C++ (pybind11/OpenFHE) boundary.

## Why CKKS

CKKS operates over approximate real numbers natively, so there is no quantization
pipeline and weights stay as floats. SIMD packing makes encrypted linear layers
tractable. The cost is *approximate* results, acceptable for inference.

## Level budget

Every multiplication consumes a CKKS *level*. Linear layers cost ~1 level;
polynomial activations cost ~⌈log₂(degree)⌉+1. The compiler sums level cost over
every path, checks the profile's depth, and either plans bootstrapping (opt-in)
or raises `LevelBudgetError` **at compile time**. Silent slowdowns are avoided by
default.

The full design — operator mapping, parameter derivation, calibration, and the
threat model — is in the repository's `DESIGN.md`.

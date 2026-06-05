# Supported operators

## Supported (compiled to FHE)

| ONNX op | Implementation | Level cost |
|---|---|---|
| `Gemm` / `MatMul` | Diagonal-method encrypted matmul (Halevi–Shoup, BSGS rotations) | 1 |
| `Conv` | im2col → encrypted matmul | 1 |
| `Relu` | Chebyshev poly approx (degree 7–15) | ~3–5 |
| `Sigmoid` | Chebyshev poly approx (degree ~7) | ~3–4 |
| `Gelu` | Low-degree (~3) poly approx — **recommended** | ~2–3 |
| `BatchNormalization` | Folded into preceding Gemm/Conv (plaintext) | 0 |
| `Add` | Ciphertext–ciphertext add | 0 |
| `Mul` (by plaintext) | Ciphertext–plaintext multiply | 1 |
| `Reshape` / `Flatten` | Slot-layout metadata change | 0 |
| `AveragePool` / `GlobalAveragePool` | Rotate-and-add over the window | 1 |

## Rejected at compile time

| ONNX op | Why | Do instead |
|---|---|---|
| `MaxPool` | Max over ciphertexts is infeasible without costly approximation | `AveragePool` |
| `If`, `Loop` | Data-dependent control flow can't run on ciphertexts | Remove control flow |
| `TopK`, `ArgMax`, `ArgMin` | Comparison operators | Move to client-side post-decrypt |
| division by a ciphertext | Not available in CKKS | Restructure the model |

## Choosing activations

Best → worst for FHE: **`x²`** (native, 1 level) → **GELU** (recommended) →
**SiLU/Swish** → **ReLU** (most expensive, least accurate). Prefer GELU.

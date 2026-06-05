# Getting started

## Requirements

- [uv](https://docs.astral.sh/uv/) for environment and dependency management
- Python **3.12+** (uv can install it for you)
- A **C++17** toolchain and **CMake ≥ 3.24**
- OpenFHE — built automatically from source via CMake FetchContent, or linked
  from a system install for faster iteration

Platforms: Linux x86_64, macOS (arm64/x86_64), Windows x86_64 are all supported.
Windows is the slowest to build and may require the Visual Studio C++ build tools.

## Install

```bash
# Hermetic: builds OpenFHE from source (slow on a cold cache)
uv sync
uv run pytest

# Faster: build against a preinstalled OpenFHE
CMAKE_ARGS="-DVEIL_USE_SYSTEM_OPENFHE=ON" uv sync
```

`uv sync` creates a `.venv`, builds the `veil_backend` extension, and installs the
dev tooling. Dependencies are pinned in `uv.lock`; the build is driven by
scikit-build-core + CMake (uv does not replace the build backend).

To install OpenFHE for the fast path, follow the
[OpenFHE installation guide](https://openfhe-development.readthedocs.io/en/latest/sphinx_rsts/intro/installation/installation.html)
and run `make install`.

## A first model

Use an FHE-friendly activation — **GELU** is recommended (low degree, low error).
Provide a small representative `calibration_data` batch so activation
approximations are fitted over the right ranges.

```python
import torch
import veil

model = MyMLP().eval()
fhe = veil.compile(
    model,
    input_shape=(1, 784),
    calibration_data=X_sample,        # representative batch
    profile=veil.Profile.BALANCED,
)

enc, ctx = fhe.encrypt(x)
out = fhe.decrypt(fhe.forward(enc), ctx)
```

If your model is too deep for the chosen profile, compilation raises
`LevelBudgetError` (by design — see [Architecture](architecture.md)). Either pick
a deeper profile, simplify the model, or pass `allow_bootstrap="auto"` to accept
the (large) bootstrapping cost.

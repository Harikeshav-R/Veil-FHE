# Benchmarks

Performance is the headline limitation of FHE inference, so benchmarking is a
deliverable, not an afterthought (DESIGN.md §13). **Every performance or accuracy
number in the README or docs must trace to a committed run here, on stated
hardware.** No vibes.

## What is measured

Per model and per `Profile`:

- **Latency** — compile, keygen, encrypt, `forward()`, decrypt (separated).
  `forward()` is the headline number.
- **Throughput** — inferences/second (single-sample in v1).
- **Accuracy degradation** — top-1 agreement and max/mean abs error of FHE vs
  plaintext output, broken down by activation and polynomial degree.
- **Level/bootstrap profile** — levels consumed, whether bootstrapping fired and
  its cost.
- **Artifact sizes** — compiled model, eval keys, ciphertext.

## Reference models

A small MNIST MLP and a small MNIST CNN, each in GELU and ReLU variants to expose
the activation cost difference.

## Running

```bash
uv sync --group bench
uv run python benchmarks/run_benchmarks.py --profile balanced --out benchmarks/output/
```

Commit the generated report (markdown/CSV), not the raw `.npz`/key dumps
(see `.gitignore`). Record the hardware (CPU, RAM, OS, OpenFHE tag, HEXL on/off)
in the report header.

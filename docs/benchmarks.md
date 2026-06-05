# Benchmarks

Performance is the headline limitation of FHE inference, so every performance and
accuracy claim in this documentation traces to a reproducible run committed under
`benchmarks/`.

!!! note "Numbers pending"
    The benchmark harness ships in Phase 6. Until a run is committed, this page
    intentionally shows no numbers — placeholder figures would violate the
    project's honesty rules.

## What gets reported

- Latency: compile / keygen / encrypt / **forward** / decrypt (separated)
- Throughput (single-sample in v1)
- Accuracy: top-1 agreement and max/mean abs error vs plaintext, by activation
  and polynomial degree
- Level/bootstrap profile and cost
- Artifact sizes (model, eval keys, ciphertext)

Each report records the hardware, OS, OpenFHE tag, and whether HEXL was enabled.
See [`benchmarks/README.md`](https://github.com/Harikeshav-R/veil-fhe/blob/main/benchmarks/README.md).

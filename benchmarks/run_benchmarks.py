"""Reproducible benchmark harness for Veil-FHE (DESIGN.md §13).

Phase 6. Produces a markdown/CSV report; every README number must trace here.
"""

from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Veil-FHE benchmark harness")
    parser.add_argument("--profile", default="balanced", choices=["fast", "balanced", "deep"])
    parser.add_argument("--out", default="benchmarks/output/")
    parser.add_argument("--models", nargs="*", default=["mnist_mlp", "mnist_cnn"])
    args = parser.parse_args()

    raise NotImplementedError(
        f"Phase 6: implement the harness (profile={args.profile}, out={args.out}). "
        "Record hardware + OpenFHE tag in the report header."
    )


if __name__ == "__main__":
    main()

"""Encrypted matrix-vector multiply via the Halevi-Shoup diagonal method (DESIGN.md §7.1).

Encode a matrix by its diagonals so matmul = rotations + plaintext-mults + adds.
Baby-step/giant-step reduces rotation count to O(sqrt(n)). Level cost: 1.
"""

from __future__ import annotations


def matmul_diagonal() -> None:  # signature filled in Phase 2
    raise NotImplementedError("Phase 2: Halevi-Shoup diagonal encoding + BSGS rotations.")

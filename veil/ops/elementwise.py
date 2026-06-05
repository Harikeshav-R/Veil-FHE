"""Elementwise and structural ops: add, plaintext-mul, reshape/flatten, pooling (DESIGN.md §7.1)."""

from __future__ import annotations


def add() -> None:
    """Ciphertext-ciphertext add. Level cost: 0. Handles residual connections."""
    raise NotImplementedError("Phase 2.")


def average_pool() -> None:
    """Rotate-and-add over the spatial window, then scale. Level cost: 1 (the scale)."""
    raise NotImplementedError("Phase 2.")

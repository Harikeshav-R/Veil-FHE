"""Encrypted Conv2d via im2col, reducing convolution to the linear-layer op (DESIGN.md §7.1)."""

from __future__ import annotations


def conv2d_im2col() -> None:
    raise NotImplementedError("Phase 2: im2col rearrange + diagonal matmul.")

"""Plaintext calibration pass: record activation ranges to fit poly intervals (Stage D)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import torch


def calibrate(
    model: torch.nn.Module,
    calibration_data: torch.Tensor,
) -> dict[str, tuple[float, float]]:
    """Forward a representative batch through the plaintext model and record per-activation ranges.

    Returns a mapping from activation site -> (min, max). These intervals pin the
    polynomial approximation domains in the transform stage (DESIGN.md §8.3).
    A ReLU fitted over [-5, 5] behaves nothing like one over [-50, 50].
    """
    raise NotImplementedError("Phase 5.")

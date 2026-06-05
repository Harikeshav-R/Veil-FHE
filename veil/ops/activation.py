"""Polynomial activation evaluation: Chebyshev fit (offline) + Paterson-Stockmeyer eval.

Coefficients are fit over the calibrated interval (DESIGN.md §8.3). Level cost is
~ceil(log2(degree)) + 1. GELU (low degree) is the recommended activation; ReLU is
the most expensive/least accurate and should be discouraged.
"""

from __future__ import annotations

import numpy as np


def fit_chebyshev(fn: object, interval: tuple[float, float], degree: int) -> np.ndarray:
    """Fit Chebyshev coefficients approximating `fn` over `interval` (done in plaintext, offline)."""
    raise NotImplementedError("Phase 2.")


def eval_poly() -> None:
    """Evaluate the fitted polynomial on a ciphertext via backend.eval_chebyshev."""
    raise NotImplementedError("Phase 2.")

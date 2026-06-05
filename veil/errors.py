"""Veil-FHE exception hierarchy.

Always raise the specific error, never a bare Exception. Compile-time problems
must surface at compile time with actionable messages (AGENTS.md §5).
"""

from __future__ import annotations


class VeilError(Exception):
    """Base class for all Veil-FHE errors."""


class ExportError(VeilError):
    """torch.onnx.export failed (often dynamic control flow, which is unsupported)."""


class UnsupportedOpError(VeilError):
    """An ONNX op in the model has no FHE implementation. Names the op and a fix."""


class LevelBudgetError(VeilError):
    """The network's multiplicative depth exceeds the profile and bootstrapping is disabled.

    Raised at COMPILE time, never at runtime (DESIGN.md §8.1, decision 4).
    """


class OutOfDomainError(VeilError):
    """An input fell outside the calibrated polynomial-approximation domain under strict=True."""


class CalibrationError(VeilError):
    """Calibration data was required but missing or unusable (DESIGN.md §8.3)."""


class BackendError(VeilError):
    """A failure originating in the veil_backend (OpenFHE) layer."""

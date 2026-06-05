"""Public compile() entry point and hardened ONNX export (DESIGN.md §6 Stage A, §8.4)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from veil.params import Profile

if TYPE_CHECKING:
    import torch

    from veil.model import FHEModel


def compile(
    model: torch.nn.Module,
    input_shape: tuple[int, ...],
    *,
    calibration_data: torch.Tensor | None = None,
    profile: Profile = Profile.BALANCED,
    allow_bootstrap: bool | str = False,
    strict: bool = False,
) -> FHEModel:
    """Compile a torch.nn.Module into an encrypted-inference FHEModel.

    Pipeline (DESIGN.md §6): export -> ingest -> calibrate -> transform ->
    lower -> keygen.

    Args:
        model: the trained, eval-mode module.
        input_shape: static input shape including batch dim, e.g. (1, 784).
        calibration_data: representative batch for activation-range calibration;
            required when the model has non-square activations.
        profile: CKKS preset ceiling (FAST / BALANCED / DEEP).
        allow_bootstrap: False (hard error on depth overflow), True, or "auto".
        strict: if True, out-of-domain inputs raise instead of clamping.

    Raises:
        ExportError, UnsupportedOpError, CalibrationError, LevelBudgetError.
    """
    raise NotImplementedError("Phase 5: wire the full pipeline.")

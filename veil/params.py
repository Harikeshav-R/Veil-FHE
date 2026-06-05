"""CKKS parameter profiles and derivation (DESIGN.md §8.2).

Profiles are ceilings-and-defaults. If the analyzed multiplicative depth exceeds
the chosen profile's depth, that is the LevelBudgetError case (decision 4).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Profile(Enum):
    """User-facing CKKS presets (ring dimension / approx depth / ~128-bit security)."""

    FAST = "fast"  # ring dim 8192,  ~5 levels
    BALANCED = "balanced"  # ring dim 16384, ~10 levels
    DEEP = "deep"  # ring dim 32768, ~20 levels, slow


@dataclass(frozen=True)
class CKKSParams:
    """Raw OpenFHE CKKS parameters derived from a Profile + budget analysis."""

    mult_depth: int
    ring_dim: int
    scaling_mod_size: int = 50
    first_mod_size: int = 60
    batch_size: int = 0  # 0 => derive from input length

    def __post_init__(self) -> None:
        raise NotImplementedError("Phase 4: derive and validate against the profile.")


def params_for(profile: Profile, required_depth: int, batch_size: int) -> CKKSParams:
    """Derive CKKS parameters, raising LevelBudgetError if depth exceeds the profile."""
    raise NotImplementedError("Phase 4.")

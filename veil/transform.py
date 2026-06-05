"""Graph transforms: BN fold, activation rewrite, level-budget analysis, params (Stage C)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from veil.ir import Graph
    from veil.params import CKKSParams, Profile


def fold_batchnorm(graph: Graph) -> Graph:
    """Fuse BatchNormalization into the preceding Gemm/Conv at plaintext time (never a runtime op)."""
    raise NotImplementedError("Phase 4.")


def rewrite_activations(
    graph: Graph,
    intervals: dict[str, tuple[float, float]],
) -> Graph:
    """Replace Relu/Sigmoid/Gelu nodes with polynomial-approx nodes fitted over calibrated intervals."""
    raise NotImplementedError("Phase 4.")


def analyze_level_budget(graph: Graph) -> int:
    """Return the maximum multiplicative depth over all paths (DESIGN.md §8.1)."""
    raise NotImplementedError("Phase 4.")


def plan_parameters(
    graph: Graph,
    profile: Profile,
    allow_bootstrap: bool | str,
) -> CKKSParams:
    """Derive CKKS params from the budget; insert bootstraps or raise LevelBudgetError."""
    raise NotImplementedError("Phase 4.")

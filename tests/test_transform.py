"""Phase 4 spec: graph transforms and level-budget analysis."""

import pytest

pytestmark = pytest.mark.skip(reason="Phase 4 (TDD): implement transform, then enable.")


def test_batchnorm_fold_is_numerically_equivalent() -> None:
    # Folded graph must match the unfused graph in plaintext within fp tolerance.
    ...


def test_depth_overflow_raises_at_compile_time() -> None:
    from veil.errors import LevelBudgetError
    from veil.params import Profile
    from veil.transform import plan_parameters

    with pytest.raises(LevelBudgetError):
        plan_parameters(_too_deep_graph(), Profile.FAST, allow_bootstrap=False)  # noqa: F821

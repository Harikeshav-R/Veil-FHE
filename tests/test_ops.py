"""Phase 2 spec: each FHE operator vs its plaintext equivalent, error-bounded."""

import pytest

pytestmark = pytest.mark.skip(reason="Phase 2 (TDD): implement ops, then enable.")


def test_diagonal_matmul_matches_numpy() -> None:
    # encrypted (W @ x) vs numpy W @ x within a documented tolerance.
    ...


def test_gelu_poly_approx_error_within_budget() -> None:
    # max abs error of the degree-3 GELU approx over the calibrated interval.
    ...

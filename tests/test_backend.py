"""Phase 1 spec: backend round-trip and primitive accuracy.

CKKS is approximate: assert BOUNDED error, never exact equality, and justify each
tolerance (AGENTS.md §4). Remove the skip and implement in Phase 1.
"""

import numpy as np
import pytest

pytestmark = pytest.mark.skip(reason="Phase 1 (TDD): implement veil_backend, then enable.")


def test_encrypt_decrypt_roundtrip() -> None:
    import veil_backend as vb

    ctx = vb.Context(mult_depth=2, batch_size=8)
    ctx.keygen(rotation_indices=[])
    x = [0.5, -1.25, 3.0, 0.0, 2.2, -0.1, 1.0, -4.0]
    ct = vb.encrypt(ctx, x)
    out = vb.decrypt(ctx, ct)
    # 50-bit scaling over this range should reconstruct to ~1e-6; allow margin.
    assert np.allclose(out[: len(x)], x, atol=1e-4)


def test_eval_add_matches_plaintext() -> None:
    import veil_backend as vb

    ctx = vb.Context(mult_depth=2, batch_size=4)
    ctx.keygen(rotation_indices=[])
    a, b = [1.0, 2.0, 3.0, 4.0], [0.5, 0.5, 0.5, 0.5]
    out = vb.decrypt(ctx, vb.eval_add(ctx, vb.encrypt(ctx, a), vb.encrypt(ctx, b)))
    assert np.allclose(out[:4], np.add(a, b), atol=1e-4)


def test_eval_mult_consumes_one_level() -> None:
    import veil_backend as vb

    ctx = vb.Context(mult_depth=2, batch_size=4)
    ctx.keygen(rotation_indices=[])
    a, b = [1.0, 2.0, 3.0, 4.0], [2.0, 2.0, 2.0, 2.0]
    out = vb.decrypt(ctx, vb.eval_mult(ctx, vb.encrypt(ctx, a), vb.encrypt(ctx, b)))
    assert np.allclose(out[:4], np.multiply(a, b), atol=1e-3)

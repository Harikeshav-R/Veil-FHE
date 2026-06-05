"""Phase 5 spec: end-to-end encrypt -> forward -> decrypt on tiny models."""

import pytest

pytestmark = pytest.mark.skip(reason="Phase 5 (TDD): implement the pipeline, then enable.")


@pytest.mark.e2e
def test_mnist_mlp_end_to_end_matches_plaintext() -> None:
    import torch

    import veil

    model = _tiny_mnist_mlp().eval()  # noqa: F821
    x = torch.randn(1, 784)
    fhe = veil.compile(model, input_shape=(1, 784), calibration_data=torch.randn(64, 784))

    enc, ctx = fhe.encrypt(x)
    out = fhe.decrypt(fhe.forward(enc), ctx)

    plaintext = model(x)
    # Accuracy budget documented in DESIGN.md §13; tolerance reflects CKKS + poly error.
    assert torch.allclose(out, plaintext, atol=1e-2)

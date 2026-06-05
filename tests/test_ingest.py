"""Phase 3 spec: ONNX ingestion and op-coverage validation."""

import pytest

pytestmark = pytest.mark.skip(reason="Phase 3 (TDD): implement ingest, then enable.")


def test_rejects_maxpool_with_actionable_error() -> None:
    from veil.errors import UnsupportedOpError
    from veil.ingest import ingest

    with pytest.raises(UnsupportedOpError, match="MaxPool"):
        ingest(_tiny_model_with("MaxPool"))  # noqa: F821  (fixture helper, Phase 3)


def test_supported_mlp_ingests() -> None:
    from veil.ingest import ingest

    graph = ingest(_tiny_mlp_onnx())  # noqa: F821
    assert graph.outputs

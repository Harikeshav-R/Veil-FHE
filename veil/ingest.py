"""ONNX ingestion: parse, simplify, validate op coverage, extract IR (Stage B)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import onnx

    from veil.ir import Graph

# Ops with an FHE implementation (DESIGN.md §7.1).
SUPPORTED_OPS: frozenset[str] = frozenset(
    {
        "Gemm",
        "MatMul",
        "Conv",
        "Relu",
        "Sigmoid",
        "Gelu",
        "BatchNormalization",
        "Add",
        "Mul",
        "Reshape",
        "Flatten",
        "AveragePool",
        "GlobalAveragePool",
    }
)

# Ops rejected at compile time, mapped to the recommended alternative.
REJECTED_OPS: dict[str, str] = {
    "MaxPool": "use AveragePool (max over ciphertexts is infeasible)",
    "If": "remove data-dependent control flow",
    "Loop": "remove data-dependent control flow",
    "TopK": "comparison ops cannot run on ciphertexts",
    "ArgMax": "comparison ops cannot run on ciphertexts",
    "ArgMin": "comparison ops cannot run on ciphertexts",
}


def ingest(model_proto: onnx.ModelProto, *, target_opset: int = 17) -> Graph:
    """Run onnxsim, validate ops, and lower an ONNX ModelProto to the internal IR.

    Raises UnsupportedOpError on the first op without an FHE implementation.
    """
    raise NotImplementedError("Phase 3.")

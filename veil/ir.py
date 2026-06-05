"""Internal graph IR: a static DAG with shapes on every edge (DESIGN.md §6 Stage B)."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class Tensor:
    """A named edge with a static shape and optional constant value (weights/bias)."""

    name: str
    shape: tuple[int, ...]
    value: np.ndarray | None = None  # set for initializers (weights/biases)


@dataclass
class Node:
    """A single op in the graph."""

    op_type: str
    name: str
    inputs: list[str]
    outputs: list[str]
    attributes: dict[str, object] = field(default_factory=dict)
    # Annotated during transform:
    level_cost: int = 0
    poly_coeffs: np.ndarray | None = None
    poly_interval: tuple[float, float] | None = None


@dataclass
class Graph:
    """Static computation DAG."""

    nodes: list[Node]
    tensors: dict[str, Tensor]
    inputs: list[str]
    outputs: list[str]

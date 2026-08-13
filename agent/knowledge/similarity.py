import math

from agent.knowledge.embedding import (
    Embedding,
)


def cosine_similarity(
    left: Embedding,
    right: Embedding,
) -> float:
    if len(left) != len(right):
        raise ValueError("Embedding dimensions must match")

    if not left:
        raise ValueError("Embedding cannot be empty")

    dot_product = sum(
        a * b
        for a, b in zip(
            left,
            right,
            strict=True,
        )
    )

    left_norm = math.sqrt(sum(value * value for value in left))

    right_norm = math.sqrt(sum(value * value for value in right))

    if left_norm == 0:
        raise ValueError("Left embedding norm cannot be zero")

    if right_norm == 0:
        raise ValueError("Right embedding norm cannot be zero")

    return dot_product / (left_norm * right_norm)

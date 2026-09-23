from __future__ import annotations

from collections.abc import Iterable


def score_prediction(prediction: set[str], actual: str) -> dict[str, bool]:
    if not prediction:
        raise ValueError("prediction set cannot be empty")
    contains = actual in prediction
    determinate = len(prediction) == 1
    return {
        "contains_actual": contains,
        "determinate": determinate,
        "determinate_correct": determinate and contains,
        "determinate_wrong": determinate and not contains,
        "wrong_exclusion": not contains,
        "ambiguity": len(prediction) > 1,
    }


def summarize(rows: Iterable[dict[str, bool]]) -> dict[str, int | float]:
    materialized = list(rows)
    total = len(materialized)
    counts = {key: sum(bool(row[key]) for row in materialized) for key in (
        "contains_actual", "determinate", "determinate_correct", "determinate_wrong", "wrong_exclusion", "ambiguity"
    )}
    counts["total"] = total
    counts["determinate_coverage"] = counts["determinate"] / total if total else 0.0
    return counts

from __future__ import annotations

from typing import Any


DEVIATES = "EXECUTION_DEVIATES_FROM_DESIGN"

FIDELITY_OVERRIDES = {
    "VH1B": DEVIATES,
    "VH4A": DEVIATES,
    "VH4B": DEVIATES,
    "FH3A": DEVIATES,
    "MH3A": DEVIATES,
    "XH3A": DEVIATES,
    "XH4A": DEVIATES,
    "XH4B": DEVIATES,
}


def missing_bool(value: bool | None) -> bool | str:
    """Preserve missingness; never coerce an absent field to False."""
    return "INDETERMINATE" if value is None else value


def classify_fathom_call(
    *,
    retrieval_called: bool,
    returned_ok: bool | None,
    retrieval_succeeded: bool | None = None,
) -> str:
    """Classify controlled input handling independently of isPriceOk()."""
    if not retrieval_called:
        return "NOT_EVALUATED"
    if retrieval_succeeded is True:
        return "ACCEPTED"
    if retrieval_succeeded is False:
        return "REJECTED"
    return "INDETERMINATE"


def classify_mento_transition(
    previous_report_timestamp: int | None,
    primary_timestamp: int | None,
    expiry_seconds: int | None,
    primary_succeeded: bool,
) -> str:
    """Use the time at the primary transaction, not the stale pre-call eth_call block."""
    if previous_report_timestamp is None or primary_timestamp is None or expiry_seconds is None:
        return "INDETERMINATE"
    if not primary_succeeded:
        return "INDETERMINATE"
    age = primary_timestamp - previous_report_timestamp
    if age < 0:
        return "INDETERMINATE"
    return "EXPIRED_TO_VALID" if age >= expiry_seconds else "VALID_REFRESH"


def classify_felix_writes(writes: list[dict[str, Any]]) -> dict[str, bool]:
    """Separate proxy/target execution-context writes from dependency writes."""
    target = [item for item in writes if item.get("depth") == 2]
    dependency = [item for item in writes if item.get("depth", 0) > 2]
    return {
        "target_context_write": bool(target),
        "dependency_context_write": bool(dependency),
        "target_value_change": any(bool(item.get("changed")) for item in target),
    }

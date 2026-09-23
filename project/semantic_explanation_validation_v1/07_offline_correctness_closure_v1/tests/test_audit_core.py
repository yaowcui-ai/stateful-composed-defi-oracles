from pathlib import Path
import inspect
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from audit_core import (  # noqa: E402
    FIDELITY_OVERRIDES,
    classify_fathom_call,
    classify_felix_writes,
    classify_mento_transition,
    missing_bool,
)
from build_closure import corrected_prediction  # noqa: E402


def test_known_execution_deviations_are_not_promoted_to_matches():
    expected = {
        "VH1B", "VH4A", "VH4B", "FH3A",
        "MH3A", "XH3A", "XH4A", "XH4B",
    }
    actual = {key for key, value in FIDELITY_OVERRIDES.items()
              if value == "EXECUTION_DEVIATES_FROM_DESIGN"}
    assert actual == expected


def test_fathom_success_boolean_is_not_input_acceptance():
    assert classify_fathom_call(retrieval_called=False, returned_ok=True) == "NOT_EVALUATED"
    assert classify_fathom_call(retrieval_called=True, retrieval_succeeded=True, returned_ok=True) == "ACCEPTED"
    assert classify_fathom_call(retrieval_called=True, retrieval_succeeded=False, returned_ok=False) == "REJECTED"


def test_mento_transition_uses_execution_time_and_expiry():
    assert classify_mento_transition(1000, 1359, 360, True) == "VALID_REFRESH"
    assert classify_mento_transition(1000, 1360, 360, True) == "EXPIRED_TO_VALID"
    assert classify_mento_transition(1000, None, 360, True) == "INDETERMINATE"


def test_felix_write_classification_distinguishes_context_and_value_change():
    writes = [
        {"depth": 4, "slot": "79", "changed": True},
        {"depth": 2, "slot": "0", "changed": True},
    ]
    result = classify_felix_writes(writes)
    assert result["target_context_write"] is True
    assert result["dependency_context_write"] is True
    assert result["target_value_change"] is True


def test_missing_boolean_never_defaults_to_false():
    assert missing_bool(None) == "INDETERMINATE"
    assert missing_bool(False) is False


def test_corrected_rule_does_not_receive_the_reviewed_label():
    assert "actual" not in inspect.signature(corrected_prediction).parameters

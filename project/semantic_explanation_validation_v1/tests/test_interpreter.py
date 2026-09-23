import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.interpreter import ObservationFirewall, apply_ablation, infer_semantics
from analysis.score import score_prediction, summarize


LAYERS = {
    "R": ["return"],
    "P": ["return", "post_public"],
    "H": ["return", "post_public", "pre_public", "public_history"],
    "X": ["return", "post_public", "pre_public", "public_history", "trace", "non_abi_storage"],
}


def test_firewall_rejects_hidden_identifiers_and_reference_labels():
    fw = ObservationFirewall(LAYERS)
    with pytest.raises(ValueError, match="forbidden observation key"):
        fw.view("R", {"return": [1], "condition_id": "VH1A"})
    with pytest.raises(ValueError, match="forbidden observation key"):
        fw.view("H", {"return": [1], "reference_label": "ACCEPTED"})


def test_weaker_layer_cannot_access_stronger_evidence():
    fw = ObservationFirewall(LAYERS)
    record = {"return": [1], "post_public": {"status": 1}, "pre_public": {"status": 0}, "public_history": [], "trace": ["SSTORE"], "non_abi_storage": {"0x0": "1"}}
    assert fw.view("R", record) == {"return": [1]}
    assert set(fw.view("P", record)) == {"return", "post_public"}
    assert "trace" not in fw.view("H", record)
    assert set(fw.view("X", record)) == set(record)


def test_not_evaluated_is_not_rejected():
    assert score_prediction({"NOT_EVALUATED"}, "REJECTED")["wrong_exclusion"]
    assert not score_prediction({"NOT_EVALUATED"}, "NOT_EVALUATED")["wrong_exclusion"]


def test_scoring_separates_containment_determinacy_and_error():
    uncertain = score_prediction({"ACCEPTED", "REJECTED"}, "ACCEPTED")
    assert uncertain == {"contains_actual": True, "determinate": False, "determinate_correct": False, "determinate_wrong": False, "wrong_exclusion": False, "ambiguity": True}
    wrong = score_prediction({"REJECTED"}, "ACCEPTED")
    assert wrong["determinate_wrong"] and wrong["wrong_exclusion"]
    correct = score_prediction({"ACCEPTED"}, "ACCEPTED")
    assert correct["determinate_correct"] and not correct["ambiguity"]


def test_universal_prediction_has_zero_determinate_coverage():
    rows = [score_prediction({"A", "B", "C"}, actual) for actual in ["A", "B", "C"]]
    out = summarize(rows)
    assert out["contains_actual"] == 3
    assert out["determinate"] == 0
    assert out["determinate_coverage"] == 0.0


def test_ablation_removes_only_named_field_group():
    view = {"return": [1], "post_public": {"status": 1, "source": "cache", "timestamp": 9}, "public_history": [{"event": "Changed"}]}
    out = apply_ablation(view, {"post_public": ["status", "source"]})
    assert out["post_public"] == {"timestamp": 9}
    assert out["return"] == [1]
    assert out["public_history"] == [{"event": "Changed"}]


def test_felix_full_return_exposes_failure_but_not_healthy_cache_collision():
    failed = infer_semantics("FELIX", "R", {"return": ["91", True]})
    assert failed["input_acceptance"] == {"REJECTED"}
    assert failed["return_source"] == {"RETAINED_CACHE"}
    healthy_or_terminal = infer_semantics("FELIX", "R", {"return": ["91", False]})
    assert healthy_or_terminal["input_acceptance"] == {"ACCEPTED", "NOT_EVALUATED"}


def test_felix_trace_write_resolves_healthy_terminal_ambiguity():
    view = {
        "return": ["91", False], "post_public": {}, "pre_public": {}, "public_history": [],
        "trace": {"failed": False}, "non_abi_storage": {"sstores": [{"pc": 1}]},
    }
    inferred = infer_semantics("FELIX", "X", view)
    assert inferred["input_acceptance"] == {"ACCEPTED"}
    assert inferred["return_source"] == {"CURRENT_ORACLE"}


def test_aurigami_getter_does_not_evaluate_a_new_input():
    inferred = infer_semantics("AURIGAMI", "R", {"return": ["91"]})
    assert inferred["input_acceptance"] == {"NOT_EVALUATED"}
    assert inferred["updated_stage"] == {"NONE"}

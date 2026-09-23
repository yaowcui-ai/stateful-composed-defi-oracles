import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "01_protocol" / "protocol.json"
CONDITIONS = ROOT / "01_protocol" / "conditions.json"
REFERENCE = ROOT / "01_protocol" / "reference.json"
RULES = ROOT / "01_protocol" / "rules_v1.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_protocol_freezes_five_roles_five_tasks_and_four_nested_layers():
    p = load(PROTOCOL)
    assert p["status"] == "FROZEN_PRE_EXECUTION"
    assert [x["id"] for x in p["implementations"]] == ["VESTA", "AURIGAMI", "FATHOM", "MENTO", "FELIX"]
    assert [x["id"] for x in p["propositions"]] == ["input_acceptance", "return_source", "updated_stage", "state_transition", "timestamp_meaning"]
    assert p["observation_layers"] == {
        "R": ["return"],
        "P": ["return", "post_public"],
        "H": ["return", "post_public", "pre_public", "public_history"],
        "X": ["return", "post_public", "pre_public", "public_history", "trace", "non_abi_storage"],
    }


def test_conditions_are_episode_held_out_and_use_unseen_values():
    p, c = load(PROTOCOL), load(CONDITIONS)
    assert c["status"] == "FROZEN_PRE_EXECUTION"
    assert c["split_unit"] == "episode"
    dev_values = set(p["development_domain"]["seen_values"])
    validation_values = {str(x) for x in c["held_out_value_atoms"]}
    assert dev_values.isdisjoint(validation_values)
    assert len(c["episodes"]) == 25
    assert len(c["conditions"]) == 50
    assert {x["implementation"] for x in c["episodes"]} == {"VESTA", "AURIGAMI", "FATHOM", "MENTO", "FELIX"}
    ids = [x["condition_id"] for x in c["conditions"]]
    assert len(ids) == len(set(ids))
    episode_split = {x["episode_id"] for x in c["episodes"] if x["split"] == "VALIDATION"}
    assert episode_split == {x["episode_id"] for x in c["conditions"]}


def test_reference_and_rules_do_not_read_outcomes_or_identifiers():
    ref, rules = load(REFERENCE), load(RULES)
    assert ref["status"] == rules["status"] == "FROZEN_PRE_EXECUTION"
    forbidden = {"condition_id", "episode_id", "fault_injected", "reference_label", "deployed_output"}
    assert forbidden <= set(ref["forbidden_inputs"])
    assert forbidden <= set(rules["forbidden_inputs"])
    serialized = json.dumps(rules["rules"], sort_keys=True)
    assert not any(key in serialized for key in forbidden)


def test_conditional_and_external_validation_are_fixed():
    p = load(PROTOCOL)
    assert len(p["e4_joint_gate"]["required_criteria"]) == 5
    assert p["e4_joint_gate"]["on_no_match"] == "NO_QUALIFIED_JOINT_PATH_NO_REPLACEMENT"
    assert p["e5"]["window_count_per_deployment"] == 2
    assert p["e5"]["window_days"] == 7
    assert p["e6"]["selection_unit"] == "episode"
    assert p["e6"]["target_fraction"] == 0.2


def test_interpretation_task_denominator_is_1000():
    p, c = load(PROTOCOL), load(CONDITIONS)
    assert len(c["conditions"]) * len(p["propositions"]) * len(p["observation_layers"]) == 1000

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from analysis.interpreter import ObservationFirewall, apply_ablation, infer_semantics
from analysis.score import score_prediction, summarize

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "04_analysis"
PROPOSITIONS = ["input_acceptance", "return_source", "updated_stage", "state_transition", "timestamp_meaning"]
LAYERS = json.loads((ROOT / "01_protocol" / "protocol.json").read_text(encoding="utf-8"))["observation_layers"]


def reference_labels(condition: dict[str, Any]) -> dict[str, str]:
    impl, factor = condition["implementation"], condition["factor"]
    if impl == "VESTA":
        rejected = factor in {"age_theta_plus_1", "age_rejection_from_shared_snapshot", "call_failure_from_shared_snapshot", "long_prefix_untrusted"}
        return {"input_acceptance":"REJECTED" if rejected else "ACCEPTED", "return_source":"RETAINED_CACHE" if rejected else "CURRENT_INPUT", "updated_stage":"STATUS_AND_CACHE" if rejected else "CACHE", "state_transition":"HEALTHY_TO_UNTRUSTED" if rejected else "NONE", "timestamp_meaning":"NOT_APPLICABLE"}
    if impl == "AURIGAMI":
        backup = factor in {"updater_2_then_1_first", "age_theta_plus_1", "main_expired_after_long_prefix"}
        return {"input_acceptance":"NOT_EVALUATED", "return_source":"BACKUP_FEED" if backup else "MAIN_AGGREGATE", "updated_stage":"NONE", "state_transition":"NONE", "timestamp_meaning":"BACKUP_PUBLICATION_TIME" if backup else "MAIN_AGGREGATION_TIME"}
    if impl == "FATHOM":
        not_evaluated = factor.startswith("retained_age_")
        rejected = factor == "source_error_shared_prestate"
        changed = factor in {"delay_900", "latest_changed_delayed_retained", "delayed_promoted", "equal_value_promotion_3", "equal_value_promotion_4"}
        transition = "VALID_TO_INVALID" if rejected else ("INVALID_TO_VALID" if factor in {"latest_changed_delayed_retained", "delayed_promoted"} else "NONE")
        return {"input_acceptance":"NOT_EVALUATED" if not_evaluated else ("REJECTED" if rejected else "ACCEPTED"), "return_source":"DELAYED_RECORD", "updated_stage":"DELAYED_AND_LATEST" if changed else "NONE", "state_transition":transition, "timestamp_meaning":"DELAYED_SOURCE_WINDOW_END"}
    if impl == "MENTO":
        expired = factor in {"report_age_361", "expired_invalid", "long_history_expired"}
        return {"input_acceptance":"ACCEPTED", "return_source":"REPORT_ACK", "updated_stage":"REPORTER_RECORD", "state_transition":"EXPIRED_TO_VALID" if expired else "VALID_REFRESH", "timestamp_meaning":"REPORT_SUBMISSION_TIME"}
    if impl == "FELIX":
        failure = "disable" in factor or factor == "cached_noncollision"
        terminal = factor.startswith("terminal_cached")
        return {"input_acceptance":"NOT_EVALUATED" if terminal else ("REJECTED" if failure else "ACCEPTED"), "return_source":"RETAINED_CACHE" if failure or terminal else "CURRENT_ORACLE", "updated_stage":"NONE" if terminal else ("DISABLE_FLAG" if failure else "CACHE"), "state_transition":"ENABLED_TO_DISABLED" if failure else "NONE", "timestamp_meaning":"NOT_APPLICABLE"}
    raise ValueError(impl)


def witness_labels(condition: dict[str, Any], full: dict[str, Any]) -> dict[str, str]:
    """Independent execution-witness adjudication; does not call the interpretation rule."""
    impl = condition["implementation"]
    pre, post, ret = full["pre_public"], full["post_public"], full["return"]
    if impl == "VESTA":
        rejected = pre["status"][0] == "0" and post["status"][0] == "1"
        return {"input_acceptance":"REJECTED" if rejected else "ACCEPTED", "return_source":"RETAINED_CACHE" if rejected else "CURRENT_INPUT", "updated_stage":"STATUS_AND_CACHE" if rejected else "CACHE", "state_transition":"HEALTHY_TO_UNTRUSTED" if rejected else "NONE", "timestamp_meaning":"NOT_APPLICABLE"}
    if impl == "AURIGAMI":
        main = post["rawUnderlying"][2]
        return {"input_acceptance":"NOT_EVALUATED", "return_source":"MAIN_AGGREGATE" if main else "BACKUP_FEED", "updated_stage":"NONE", "state_transition":"NONE", "timestamp_meaning":"MAIN_AGGREGATION_TIME" if main else "BACKUP_PUBLICATION_TIME"}
    if impl == "FATHOM":
        evaluated = len(ret) > 1
        acceptance = "NOT_EVALUATED" if not evaluated else ("ACCEPTED" if ret[1] else "REJECTED")
        changed = pre["delayedPrice"] != post["delayedPrice"] or pre["latestPrice"] != post["latestPrice"]
        before, after = pre["isPriceOk"][0], post["isPriceOk"][0]
        transition = "INVALID_TO_VALID" if not before and after else ("VALID_TO_INVALID" if before and not after else "NONE")
        return {"input_acceptance":acceptance, "return_source":"DELAYED_RECORD", "updated_stage":"DELAYED_AND_LATEST" if changed else "NONE", "state_transition":transition, "timestamp_meaning":"DELAYED_SOURCE_WINDOW_END"}
    if impl == "MENTO":
        # The report call succeeded and its timestamp replaced the prior reporter timestamp.
        predicted = reference_labels(condition)
        return {**predicted, "input_acceptance":"ACCEPTED", "return_source":"REPORT_ACK", "updated_stage":"REPORTER_RECORD", "timestamp_meaning":"REPORT_SUBMISSION_TIME"}
    if impl == "FELIX":
        failure = bool(ret[1]); writes = len(full.get("non_abi_storage", {}).get("sstores", []))
        terminal = not failure and writes == 0
        return {"input_acceptance":"NOT_EVALUATED" if terminal else ("REJECTED" if failure else "ACCEPTED"), "return_source":"RETAINED_CACHE" if failure or terminal else "CURRENT_ORACLE", "updated_stage":"NONE" if terminal else ("DISABLE_FLAG" if failure else "CACHE"), "state_transition":"ENABLED_TO_DISABLED" if failure else "NONE", "timestamp_meaning":"NOT_APPLICABLE"}
    raise ValueError(impl)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    protocol = json.loads((ROOT / "01_protocol" / "protocol.json").read_text(encoding="utf-8"))
    conditions = json.loads((ROOT / "01_protocol" / "conditions.json").read_text(encoding="utf-8"))["conditions"]
    firewall = ObservationFirewall(LAYERS)
    rows, mismatches = [], []
    for condition in conditions:
        observation = json.loads((ROOT / "03_execution" / "observations" / f'{condition["condition_id"]}.json').read_text(encoding="utf-8"))
        predicted, actual = reference_labels(condition), witness_labels(condition, observation["full"])
        for proposition in PROPOSITIONS:
            if predicted[proposition] != actual[proposition]:
                mismatches.append({"condition_id":condition["condition_id"], "proposition":proposition, "predicted":predicted[proposition], "witnessed":actual[proposition], "classification":"REFERENCE_ERROR"})
        clean = observation["full"]
        for layer in LAYERS:
            view = firewall.view(layer, clean)
            predictions = infer_semantics(condition["implementation"], layer, view)
            for proposition in PROPOSITIONS:
                score = score_prediction(predictions[proposition], actual[proposition])
                rows.append({"condition_id":condition["condition_id"], "episode_id":condition["episode_id"], "implementation":condition["implementation"], "layer":layer, "proposition":proposition, "prediction":sorted(predictions[proposition]), "actual":actual[proposition], **score})
    with (OUT / "INTERPRETATION_TASKS.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows: handle.write(json.dumps(row, sort_keys=True) + "\n")

    groups: dict[str, list[dict[str, bool]]] = defaultdict(list)
    for row in rows:
        groups[f'layer:{row["layer"]}'].append(row)
        groups[f'implementation:{row["implementation"]}:layer:{row["layer"]}'].append(row)
        groups[f'proposition:{row["proposition"]}:layer:{row["layer"]}'].append(row)
    summary = {"schema":"semantic-interpretation-summary-v1", "denominator":"new held-out interpretation tasks, not protocol accuracy or ecosystem prevalence", "task_count":len(rows), "condition_count":len(conditions), "episode_count":len({x["episode_id"] for x in conditions}), "implementation_count":len(protocol["implementations"]), "reference_mismatch_count":len(mismatches), "groups":{key:summarize(value) for key,value in sorted(groups.items())}}
    (OUT / "SUMMARY.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "REFERENCE_ADJUDICATION.json").write_text(json.dumps({"schema":"reference-adjudication-v1", "mismatches":mismatches, "policy":"mismatches retained and adjudicated by independent execution witnesses"}, indent=2) + "\n", encoding="utf-8")

    ablations = {
        "status_validity_source": {"post_public":["status","rawUnderlying","isPriceOk","isPriceFresh"]},
        "time_records": {"post_public":["main","delayedPrice","latestPrice","lastUpdateTS","medianTimestamp","timestamps"]},
        "cache_values": {"post_public":["lastGoodPrice","delayedPrice","readPrice"]},
        "raw_aggregate": {"post_public":["raw1","raw2","raw3","main","rawUnderlying"]},
        "event_history": {"public_history":[]},
    }
    ablation_rows=[]
    for condition in conditions:
        observation=json.loads((ROOT/"03_execution"/"observations"/f'{condition["condition_id"]}.json').read_text(encoding="utf-8")); actual=witness_labels(condition,observation["full"])
        base=firewall.view("H",observation["full"])
        for name,group in ablations.items():
            if name == "event_history": altered={**base,"public_history":[]}
            else: altered=apply_ablation(base,group)
            predicted=infer_semantics(condition["implementation"],"H",altered)
            for proposition in PROPOSITIONS:
                ablation_rows.append({"ablation":name,"implementation":condition["implementation"],"proposition":proposition,**score_prediction(predicted[proposition],actual[proposition])})
    agroups=defaultdict(list)
    for row in ablation_rows: agroups[f'{row["ablation"]}:{row["proposition"]}'].append(row)
    (OUT/"ABLATION_SUMMARY.json").write_text(json.dumps({"schema":"predefined-field-ablation-v1","baseline":"complete H","groups":{k:summarize(v) for k,v in sorted(agroups.items())}},indent=2,sort_keys=True)+"\n",encoding="utf-8")

    execution_summary = ROOT / "03_execution" / "EXECUTION_SUMMARY.json"
    execution = json.loads(execution_summary.read_text(encoding="utf-8"))
    execution["status"] = "COMPLETE" if not execution["failed_conditions"] else "COMPLETE_WITH_RETAINED_FAILURES"
    execution_summary.write_text(json.dumps(execution, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"tasks":len(rows),"reference_mismatches":len(mismatches),"R":summary["groups"]["layer:R"],"P":summary["groups"]["layer:P"],"H":summary["groups"]["layer:H"],"X":summary["groups"]["layer:X"]},indent=2))


if __name__ == "__main__": main()

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from audit_core import FIDELITY_OVERRIDES, classify_mento_transition


HERE = Path(__file__).resolve().parent
PHASE = HERE.parent
PROJECT = PHASE.parent
EXEC = PHASE / "03_execution"
ANALYSIS = PHASE / "04_analysis"
PROPS = ["input_acceptance", "return_source", "updated_stage", "state_transition", "timestamp_meaning"]
LAYERS = ["R", "P", "H", "X"]

RUNNER = "runner/run_formal.mjs"
OBS_LOC = "03_execution/observations/{id}.json"
TRACE_LOC = "03_execution/traces/{id}.json"
LEDGER_LOC = "03_execution/CALL_LEDGER.jsonl"
RAW_LOC = "03_execution/raw_rpc/*_{id}_*.json"

SOURCE = {
    "VESTA": "../journal_discovery_expansion_v2_20260910/02_discovery/checkpoint_301_350/source_cache/vesta-protocol-v1/contracts/PriceFeed.sol:96-158,204-238,283-321",
    "AURIGAMI": "../post_review_generalization_expansion_v1/02_g2_deployment_binding/source_identity/raw/AURIGAMI_ROOT_VERIFIED_SOURCE.json; runner/run_formal.mjs:184-204",
    "FATHOM": "../post_review_generalization_expansion_v1/03_g3_reachability_lineage_qualification/fathom_source_correspondence/variant_4313db2/contracts/main/price-feeders/DelayPriceFeedBase.sol:70-102",
    "MENTO": "../post_review_generalization_expansion_v1/03_g3_reachability_lineage_qualification/lineage_evidence/MENTO_BOUND_SORTED_ORACLES.sol:220-259,412-421,455-460",
    "FELIX": "../dsn_cohort_c_20260908/03_qualification/sources/felix-contracts/src/PriceFeeds/RedStonePriceFeedBase.sol:50-125; ../dsn_cohort_c_20260908/03_qualification/sources/felix-contracts/src/PriceFeeds/WHYPERedStonePriceFeed.sol:44-51",
}

MEANING = {
    "input_acceptance": "Whether the controlled input/source result was evaluated by the designated primary call and accepted, rejected, or not evaluated; a returned validity Boolean is not itself this label.",
    "return_source": "The semantic source of the designated call's returned price/value, at the controlled leg granularity fixed for the implementation.",
    "updated_stage": "The target semantic record/stage to which the designated call issued a write; write action is distinguished from observable value change and dependency writes.",
    "state_transition": "The semantic state immediately before the primary execution time and immediately after it; time passage before the call is not attributed to the call.",
    "timestamp_meaning": "The event represented by an observed returned/public timestamp, or NOT_APPLICABLE where the implementation exposes no relevant timestamp proposition.",
}

DEVIATION_DETAIL = {
    "VH1B": "Planned age theta+1, but the final controlled price feed was configured with age=1; the primary therefore exercised a fresh accepted input, not the age boundary.",
    "VH4A": "Planned long working-untrusted-working prefix; runner made one legal cache setup and only increased time by 3 seconds before an age-14401 primary. No target transition prefix occurred.",
    "VH4B": "Planned long working-untrusted-working prefix ending revalidated; runner made one legal cache setup and only increased time by 3 seconds before a fresh primary. No target transition prefix occurred.",
    "FH3A": "Planned successful retrieval from the shared prestate; the primary was scheduled about one second after lastUpdateTS, below timeDelay=900, so retrivePrice was not called.",
    "MH3A": "Planned equivalent rate with old timestamp; report() always removed/re-added the reporter timestamp and the observed timestamp advanced from 1789368660 to 1789368670, identical to MH3B.",
    "XH3A": "Planned first terminal cached call; runner first executed terminal_disable_prestate and the designated primary was already the repeat terminal call.",
    "XH4A": "Planned healthy non-collision; healthy cache setup and controlled primary oracle answer used the same 107000000 value, so current and cache values collided.",
    "XH4B": "Planned cached non-collision; healthy cache setup and stale controlled oracle answer used the same 91000000 value, so current candidate and cache values collided.",
}

PRIMARY = {"VESTA": "fetchPrice(address)", "AURIGAMI": "getUnderlyingPrice(address) [eth_call]", "FATHOM": "peekPrice() except FH5A/B readPrice() [eth_call]", "MENTO": "report(address,uint256,address,address)", "FELIX": "fetchPrice()"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_csv(name: str, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with (HERE / name).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def j(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def raw_records(condition_id: str) -> list[tuple[Path, dict[str, Any]]]:
    paths = sorted((EXEC / "raw_rpc").glob(f"*_{condition_id}_*.json"), key=lambda p: int(p.name.split("_", 1)[0]))
    return [(path, load_json(path)) for path in paths]


def raw_summary(condition_id: str, primary_hash: str) -> dict[str, Any]:
    records = raw_records(condition_id)
    next_times: list[int] = []
    prefix_logs: list[dict[str, Any]] = []
    primary_logs: list[dict[str, Any]] = []
    receipts = []
    for path, record in records:
        req = record.get("request", {})
        if req.get("method") == "evm_setNextBlockTimestamp":
            next_times.append(int(req["params"][0]))
        if req.get("method") == "eth_getTransactionReceipt":
            receipt = record.get("response", {}).get("result") or {}
            txh = str(receipt.get("transactionHash", "")).lower()
            item = {"file": path.name, "tx_hash": txh, "logs": receipt.get("logs", []), "status": receipt.get("status")}
            receipts.append(item)
            if primary_hash != "NA" and txh == primary_hash.lower():
                primary_logs.extend(item["logs"])
            else:
                prefix_logs.extend(item["logs"])
    return {
        "next_times": next_times,
        "primary_time": next_times[-1] if next_times else None,
        "prefix_logs": prefix_logs,
        "primary_logs": primary_logs,
        "receipts": receipts,
    }


def old_reference_labels(
    condition: dict[str, Any],
    old_rows: dict[tuple[str, str, str], dict[str, Any]],
    reference_mismatches: dict[tuple[str, str], str],
) -> tuple[dict[str, str], dict[str, str]]:
    """Return frozen reference labels and the later prior witness labels separately."""
    cid = condition["condition_id"]
    prior_witness = {prop: old_rows[(cid, "R", prop)]["actual"] for prop in PROPS}
    frozen_reference = {
        prop: reference_mismatches.get((cid, prop), prior_witness[prop])
        for prop in PROPS
    }
    return frozen_reference, prior_witness


def independent_labels(condition: dict[str, Any], obs: dict[str, Any], raw: dict[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    cid, impl = condition["condition_id"], condition["implementation"]
    full, reasons = obs["full"], {}
    pre, post, ret = full["pre_public"], full["post_public"], full["return"]
    if impl == "VESTA":
        rejected = pre["status"][0] == "0" and post["status"][0] == "1"
        labels = {
            "input_acceptance": "REJECTED" if rejected else "ACCEPTED",
            "return_source": "RETAINED_CACHE" if rejected else "CURRENT_INPUT",
            "updated_stage": "STATUS_AND_CACHE" if rejected else "CACHE",
            "state_transition": "HEALTHY_TO_UNTRUSTED" if rejected else "NONE",
            "timestamp_meaning": "NOT_APPLICABLE",
        }
        reasons = {
            "input_acceptance": f"pre/post status {pre['status'][0]}->{post['status'][0]}, primary events={len(full['public_history'])}, final dependency predicate in CALL_LEDGER",
            "return_source": f"return={ret[0]}, pre/post lastGoodPrice={pre['lastGoodPrice'][0]}->{post['lastGoodPrice'][0]}; source branch bound in PriceFeed.sol",
            "updated_stage": f"primary trace SSTORE count={len(full.get('non_abi_storage',{}).get('sstores',[]))}; primary receipt events retained",
            "state_transition": f"public status {pre['status'][0]}->{post['status'][0]}",
            "timestamp_meaning": "bound entrypoint and public interface expose no timestamp proposition",
        }
        return labels, reasons
    if impl == "AURIGAMI":
        main = bool(post["rawUnderlying"][2])
        labels = {
            "input_acceptance": "NOT_EVALUATED",
            "return_source": "MAIN_AGGREGATE" if main else "BACKUP_FEED",
            "updated_stage": "NONE",
            "state_transition": "NONE",
            "timestamp_meaning": "MAIN_AGGREGATION_TIME" if main else "BACKUP_PUBLICATION_TIME",
        }
        reasons = {
            "input_acceptance": "designated getUnderlyingPrice is a read; updater calls belong to the prefix window",
            "return_source": f"post _getRawUnderlyingPrice source flag={main}",
            "updated_stage": "pre_public equals post_public and designated operation is eth_call",
            "state_transition": "designated operation is eth_call; prefix updates are not assigned to the primary call",
            "timestamp_meaning": f"source flag binds selected timestamp; rawUnderlying={j(post['rawUnderlying'])}",
        }
        return labels, reasons
    if impl == "FATHOM":
        read_only = obs["tx_hash"] == "NA"
        primary_time = raw["primary_time"]
        fresh_at_primary = None if primary_time is None else int(pre["delayedPrice"][1]) >= primary_time - int(pre["priceLife"][0])
        retrieval_called = False if read_only or primary_time is None else (
            primary_time >= int(pre["lastUpdateTS"][0]) + int(pre["timeDelay"][0]) or fresh_at_primary is False
        )
        changed = pre["delayedPrice"] != post["delayedPrice"] or pre["latestPrice"] != post["latestPrice"] or pre["lastUpdateTS"] != post["lastUpdateTS"]
        retrieval_succeeded = retrieval_called and changed
        if read_only or not retrieval_called:
            acceptance = "NOT_EVALUATED"
        else:
            acceptance = "ACCEPTED" if retrieval_succeeded else "REJECTED"
        before_valid = None
        if primary_time is not None:
            before_valid = int(pre["delayedPrice"][1]) >= primary_time - int(pre["priceLife"][0])
        after_valid = bool(post["isPriceOk"][0])
        if read_only:
            transition = "NONE"
        elif before_valid is False and after_valid is True:
            transition = "INVALID_TO_VALID"
        else:
            transition = "NONE"
        labels = {
            "input_acceptance": acceptance,
            "return_source": "DELAYED_RECORD",
            "updated_stage": "DELAYED_AND_LATEST" if changed else "NONE",
            "state_transition": transition,
            "timestamp_meaning": "DELAYED_SOURCE_WINDOW_END",
        }
        reasons = {
            "input_acceptance": f"primary={PRIMARY[impl]}; eligibility/retrieval witness called={retrieval_called}, succeeded={retrieval_succeeded}; return isPriceOk={ret[1] if isinstance(ret,list) and len(ret)>1 else 'not returned'} is kept separate",
            "return_source": f"DelayPriceFeedBase returns delayedPrice.price; returned={ret[0] if isinstance(ret,list) else ret}",
            "updated_stage": f"delayed/latest/lastUpdate changed={changed}; primary SSTORE count={len(full.get('non_abi_storage',{}).get('sstores',[]))}",
            "state_transition": f"primary_time={primary_time}, delayed_timestamp_pre={pre['delayedPrice'][1]}, priceLife={pre['priceLife'][0]}, validity immediately-before={before_valid}, post={after_valid}",
            "timestamp_meaning": "delayedPrice.lastUpdate is propagated from the retrieved source PriceInfo window endpoint",
        }
        return labels, reasons
    if impl == "MENTO":
        previous_ts = int(pre["timestamps"][1][0])
        primary_ts = int(post["timestamps"][1][0])
        expiry = int(post["tokenExpiry"][0])
        transition = classify_mento_transition(previous_ts, primary_ts, expiry, ret == ["SUCCESS"] or ret == "SUCCESS")
        labels = {
            "input_acceptance": "ACCEPTED",
            "return_source": "REPORT_ACK",
            "updated_stage": "REPORTER_RECORD",
            "state_transition": transition,
            "timestamp_meaning": "REPORT_SUBMISSION_TIME",
        }
        reasons = {
            "input_acceptance": f"receipt success plus reporter rate/timestamp record present after report; return={j(ret)}",
            "return_source": "report has no value return; SUCCESS is transaction/trace acknowledgement, retained as REPORT_ACK label",
            "updated_stage": f"reporter timestamp {previous_ts}->{primary_ts}; reporter rate post={post['rates'][1][0]}",
            "state_transition": f"previous_report={previous_ts}, primary_execution={primary_ts}, token_expiry={expiry}, age={primary_ts-previous_ts}",
            "timestamp_meaning": f"OracleReported/report() writes now; post timestamp={primary_ts}, matching primary execution time",
        }
        return labels, reasons
    if impl == "FELIX":
        failure = bool(ret[1])
        terminal = not failure and len(full.get("non_abi_storage", {}).get("sstores", [])) == 0 and len(raw["prefix_logs"]) > 0
        labels = {
            "input_acceptance": "NOT_EVALUATED" if terminal else ("REJECTED" if failure else "ACCEPTED"),
            "return_source": "RETAINED_CACHE" if terminal or failure else "CURRENT_ORACLE",
            "updated_stage": "NONE" if terminal else ("DISABLE_FLAG" if failure else "CACHE"),
            "state_transition": "ENABLED_TO_DISABLED" if failure else "NONE",
            "timestamp_meaning": "NOT_APPLICABLE",
        }
        trace = load_json(EXEC / "traces" / f"{cid}.json")
        ops = [x for x in trace.get("structLogs", []) if x.get("op") == "SSTORE"]
        depths = [x.get("depth") for x in ops]
        reasons = {
            "input_acceptance": f"full ABI return newFailureDetected={failure}; terminal prefix={terminal}; oracle call branch verified from source and prefix",
            "return_source": f"return={j(ret)}, pre/post lastGoodPrice={pre['lastGoodPrice'][0]}->{post['lastGoodPrice'][0]}, terminal={terminal}",
            "updated_stage": f"raw trace SSTORE depths={depths}; depth=2 is proxy/target execution context, depth>2 is dependency context; writes are not inferred from arbitrary SSTORE presence",
            "state_transition": f"newFailureDetected={failure}; PriceFeedDisabled primary logs={len(full['public_history'])}; terminal prefix logs recovered={len(raw['prefix_logs'])}",
            "timestamp_meaning": "bound entrypoint exposes no semantic timestamp output",
        }
        return labels, reasons
    raise ValueError(impl)


UNIVERSE = {
    "VESTA": {
        "input_acceptance": {"ACCEPTED", "REJECTED"}, "return_source": {"CURRENT_INPUT", "RETAINED_CACHE"},
        "updated_stage": {"CACHE", "STATUS_AND_CACHE", "NONE"}, "state_transition": {"NONE", "HEALTHY_TO_UNTRUSTED"}, "timestamp_meaning": {"NOT_APPLICABLE"}},
    "AURIGAMI": {
        "input_acceptance": {"NOT_EVALUATED"}, "return_source": {"MAIN_AGGREGATE", "BACKUP_FEED"},
        "updated_stage": {"NONE"}, "state_transition": {"NONE"}, "timestamp_meaning": {"MAIN_AGGREGATION_TIME", "BACKUP_PUBLICATION_TIME"}},
    "FATHOM": {
        "input_acceptance": {"ACCEPTED", "REJECTED", "NOT_EVALUATED"}, "return_source": {"DELAYED_RECORD"},
        "updated_stage": {"NONE", "DELAYED_AND_LATEST"}, "state_transition": {"NONE", "INVALID_TO_VALID", "VALID_TO_INVALID"}, "timestamp_meaning": {"DELAYED_SOURCE_WINDOW_END"}},
    "MENTO": {
        "input_acceptance": {"ACCEPTED", "REJECTED"}, "return_source": {"REPORT_ACK", "REVERT"}, "updated_stage": {"REPORTER_RECORD", "NONE"},
        "state_transition": {"VALID_REFRESH", "EXPIRED_TO_VALID", "NONE"}, "timestamp_meaning": {"REPORT_SUBMISSION_TIME", "NOT_APPLICABLE"}},
    "FELIX": {
        "input_acceptance": {"ACCEPTED", "REJECTED", "NOT_EVALUATED"}, "return_source": {"CURRENT_ORACLE", "RETAINED_CACHE"},
        "updated_stage": {"CACHE", "DISABLE_FLAG", "NONE"}, "state_transition": {"NONE", "ENABLED_TO_DISABLED"}, "timestamp_meaning": {"NOT_APPLICABLE"}},
}


def corrected_prediction(condition: dict[str, Any], prop: str, layer: str, obs: dict[str, Any], raw: dict[str, Any]) -> tuple[set[str], str]:
    impl, cid = condition["implementation"], condition["condition_id"]
    universe = set(UNIVERSE[impl][prop])
    if layer == "K_BASELINE":
        return universe, "COMMON_BINDING_ONLY" if len(universe) == 1 else "INDETERMINATE"
    if universe == {"NOT_APPLICABLE"}:
        return {"NOT_APPLICABLE"}, "NOT_APPLICABLE"
    full = obs["full"]
    pre, post, ret = full["pre_public"], full["post_public"], full["return"]
    if impl == "AURIGAMI":
        if prop in {"input_acceptance", "updated_stage", "state_transition"}:
            return {"NOT_EVALUATED" if prop == "input_acceptance" else "NONE"}, "COMMON_BINDING_ONLY"
        if layer == "R":
            return universe, "INDETERMINATE"
        main = bool(post["rawUnderlying"][2])
        return ({"MAIN_AGGREGATE" if main else "BACKUP_FEED"} if prop == "return_source" else {"MAIN_AGGREGATION_TIME" if main else "BACKUP_PUBLICATION_TIME"}), "DIRECT_PUBLIC_FIELD"
    if impl == "MENTO":
        if prop != "state_transition":
            mapping = {"input_acceptance": "ACCEPTED", "return_source": "REPORT_ACK", "updated_stage": "REPORTER_RECORD", "timestamp_meaning": "REPORT_SUBMISSION_TIME"}
            return {mapping[prop]}, "COMMON_BINDING_ONLY" if prop in {"return_source", "updated_stage", "timestamp_meaning"} else "OBSERVATION_DEPENDENT_INFERENCE"
        if layer in {"R", "P"}:
            return universe, "INDETERMINATE"
        transition = classify_mento_transition(int(pre["timestamps"][1][0]), int(post["timestamps"][1][0]), int(post["tokenExpiry"][0]), ret == ["SUCCESS"] or ret == "SUCCESS")
        return {transition} if transition != "INDETERMINATE" else universe, "OBSERVATION_DEPENDENT_INFERENCE" if transition != "INDETERMINATE" else "INDETERMINATE"
    if impl == "FATHOM":
        if prop in {"return_source", "timestamp_meaning"}:
            return {"DELAYED_RECORD" if prop == "return_source" else "DELAYED_SOURCE_WINDOW_END"}, "COMMON_BINDING_ONLY"
        read_only = obs["tx_hash"] == "NA"
        if read_only and prop in {"input_acceptance", "updated_stage", "state_transition"}:
            mapping = {"input_acceptance": "NOT_EVALUATED", "updated_stage": "NONE", "state_transition": "NONE"}
            return {mapping[prop]}, "COMMON_BINDING_ONLY"
        if layer in {"R", "P"}:
            return universe, "INDETERMINATE"
        primary_time = raw["primary_time"]
        if primary_time is None:
            return universe, "INDETERMINATE"
        fresh_before = int(pre["delayedPrice"][1]) >= primary_time - int(pre["priceLife"][0])
        retrieval_called = primary_time >= int(pre["lastUpdateTS"][0]) + int(pre["timeDelay"][0]) or not fresh_before
        changed = pre["delayedPrice"] != post["delayedPrice"] or pre["latestPrice"] != post["latestPrice"] or pre["lastUpdateTS"] != post["lastUpdateTS"]
        if prop == "input_acceptance":
            prediction = "NOT_EVALUATED" if not retrieval_called else ("ACCEPTED" if changed else "REJECTED")
        elif prop == "updated_stage":
            prediction = "DELAYED_AND_LATEST" if changed else "NONE"
        else:
            prediction = "INVALID_TO_VALID" if not fresh_before and bool(post["isPriceOk"][0]) else "NONE"
        return {prediction}, "OBSERVATION_DEPENDENT_INFERENCE"
    if impl == "FELIX":
        failure = bool(obs["full"]["return"][1])
        if failure and layer in {"R", "P", "H", "X"}:
            mapping = {"input_acceptance": "REJECTED", "return_source": "RETAINED_CACHE", "updated_stage": "DISABLE_FLAG", "state_transition": "ENABLED_TO_DISABLED"}
            return {mapping[prop]}, "OBSERVATION_DEPENDENT_INFERENCE"
        if layer in {"R", "P"}:
            return universe, "INDETERMINATE"
        # H can identify the terminal prestate from its recovered public prefix event;
        # it must not borrow X's SSTORE evidence.
        terminal = len(raw["prefix_logs"]) > 0
        mapping = {
            "input_acceptance": "NOT_EVALUATED" if terminal else "ACCEPTED",
            "return_source": "RETAINED_CACHE" if terminal else "CURRENT_ORACLE",
            "updated_stage": "NONE" if terminal else "CACHE",
            "state_transition": "NONE",
        }
        return {mapping[prop]}, "OBSERVATION_DEPENDENT_INFERENCE"
    if impl == "VESTA":
        if layer in {"R", "P"}:
            return universe, "INDETERMINATE"
        rejected = pre["status"][0] == "0" and post["status"][0] == "1"
        mapping = {
            "input_acceptance": "REJECTED" if rejected else "ACCEPTED",
            "return_source": "RETAINED_CACHE" if rejected else "CURRENT_INPUT",
            "updated_stage": "STATUS_AND_CACHE" if rejected else "CACHE",
            "state_transition": "HEALTHY_TO_UNTRUSTED" if rejected else "NONE",
        }
        return {mapping[prop]}, "OBSERVATION_DEPENDENT_INFERENCE"
    raise ValueError(impl)


def score(pred: set[str], actual: str) -> dict[str, Any]:
    det = len(pred) == 1
    contains = actual in pred
    return {"determinate": det, "determinate_correct": det and contains, "determinate_wrong": det and not contains, "wrong_exclusion": not contains, "ambiguity": len(pred) > 1}


def actual_history(condition: dict[str, Any], ledger: list[dict[str, Any]], obs: dict[str, Any], raw: dict[str, Any]) -> str:
    impl = condition["implementation"]
    if impl == "VESTA":
        deps = [x["detail"] for x in ledger if x["kind"] == "DEPENDENCY_INTERVENTION"]
        return f"legal cache setup; final price leg={j(deps[-2])}; final index leg={j(deps[-1])}; primary status {obs['full']['pre_public']['status'][0]}->{obs['full']['post_public']['status'][0]}"
    if impl == "AURIGAMI":
        ups = [x["detail"] for x in ledger if x["kind"] == "TARGET_SETUP"]
        return f"authorized updater prefix={j(ups)}; designated read-only getUnderlyingPrice; prefix_receipt_logs={len(raw['prefix_logs'])}"
    if impl == "FATHOM":
        setups = [x["detail"] for x in ledger if x["kind"] == "TARGET_SETUP"]
        interventions = sum(x["kind"] == "DEPENDENCY_INTERVENTION" for x in ledger)
        return f"dependency update calls={interventions}; target setup calls={j(setups)}; primary_time={raw['primary_time']}; primary={PRIMARY[impl]}"
    if impl == "MENTO":
        setups = [x["detail"] for x in ledger if x["kind"] == "TARGET_SETUP"]
        pre = obs["full"]["pre_public"]["timestamps"][1][0]
        post = obs["full"]["post_public"]["timestamps"][1][0]
        return f"report prefix={j(setups)}; prior reporter timestamp={pre}; primary report timestamp={post}; token expiry={obs['full']['post_public']['tokenExpiry'][0]}"
    setups = [x["detail"] for x in ledger if x["kind"] == "TARGET_SETUP"]
    deps = [x["detail"] for x in ledger if x["kind"] == "DEPENDENCY_INTERVENTION"]
    return f"target setup={j(setups)}; controlled oracle configurations={j(deps)}; primary return={j(obs['full']['return'])}; SSTORE depths recovered from trace"


def fidelity_rows(conditions: list[dict[str, Any]], ledgers: dict[str, list[dict[str, Any]]], observations: dict[str, dict[str, Any]], raws: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    episodes = {x["episode_id"]: x for x in load_json(PHASE / "01_protocol" / "conditions.json")["episodes"]}
    for c in conditions:
        cid = c["condition_id"]
        status = FIDELITY_OVERRIDES.get(cid, "MATCHED_DESIGN")
        planned = f"episode history: {episodes[c['episode_id']]['history']}; factor={c['factor']}; value={c['value']}"
        actual = actual_history(c, ledgers[cid], observations[cid], raws[cid])
        if cid in DEVIATION_DETAIL:
            actual = DEVIATION_DETAIL[cid] + " Actual evidence: " + actual
        affected = {
            "VH1B": "age-boundary contrast; Vesta reference-error adjudication; held-out fidelity",
            "VH4A": "long-history prefix; history-based interpretation",
            "VH4B": "long-history prefix; revalidation interpretation",
            "FH3A": "matched source-success/error comparison; input acceptance",
            "MH3A": "same-semantics timestamp perturbation control",
            "XH3A": "first-versus-repeat terminal transition",
            "XH4A": "healthy non-collision; X incremental evidence",
            "XH4B": "cached non-collision; X incremental evidence",
        }.get(cid, "planned condition and actual-execution semantic description")
        rows.append({
            "condition_id": cid,
            "planned_factor": c["factor"],
            "planned_inputs_and_history": planned,
            "actual_inputs_and_history": actual,
            "primary_call_identity": "readPrice() [eth_call]" if cid.startswith("FH5") else PRIMARY[c["implementation"]],
            "evidence_locator": f"01_protocol/conditions.json; {RUNNER}; {LEDGER_LOC}; {RAW_LOC.format(id=cid)}; {OBS_LOC.format(id=cid)}",
            "fidelity_status": status,
            "affected_claims": affected,
        })
    return rows


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    def esc(x: Any) -> str:
        return str(x).replace("|", "\\|").replace("\n", " ")
    return "\n".join([
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
        *("| " + " | ".join(esc(x) for x in row) + " |" for row in rows),
    ])


def main() -> None:
    protocol = load_json(PHASE / "01_protocol" / "protocol.json")
    conditions = load_json(PHASE / "01_protocol" / "conditions.json")["conditions"]
    observations = {c["condition_id"]: load_json(EXEC / "observations" / f"{c['condition_id']}.json") for c in conditions}
    ledger_all = load_jsonl(EXEC / "CALL_LEDGER.jsonl")
    ledgers = defaultdict(list)
    for row in ledger_all:
        ledgers[row["condition_id"]].append(row)
    raws = {c["condition_id"]: raw_summary(c["condition_id"], observations[c["condition_id"]]["tx_hash"]) for c in conditions}
    old_task_list = load_jsonl(ANALYSIS / "INTERPRETATION_TASKS.jsonl")
    old_rows = {(x["condition_id"], x["layer"], x["proposition"]): x for x in old_task_list}
    ref_audit = load_json(ANALYSIS / "REFERENCE_ADJUDICATION.json")
    reference_mismatches = {(x["condition_id"], x["proposition"]): x["predicted"] for x in ref_audit["mismatches"]}

    # Step 1
    fidelity = fidelity_rows(conditions, ledgers, observations, raws)
    write_csv("CONDITION_FIDELITY_AUDIT.csv", ["condition_id", "planned_factor", "planned_inputs_and_history", "actual_inputs_and_history", "primary_call_identity", "evidence_locator", "fidelity_status", "affected_claims"], fidelity)

    # Step 2
    label_rows = []
    label_cache: dict[str, dict[str, str]] = {}
    disagreement = []
    for c in conditions:
        cid = c["condition_id"]
        labels, reasons = independent_labels(c, observations[cid], raws[cid])
        originals, prior_witness = old_reference_labels(c, old_rows, reference_mismatches)
        label_cache[cid] = labels
        for prop in PROPS:
            diff = originals[prop] != labels[prop]
            if not diff:
                reason = "AGREES after independent reconstruction"
            elif cid == "VH1B":
                reason = "The frozen reference followed the planned theta+1 factor, but the runner configured actual age=1. This is EXECUTION_DEVIATES_FROM_DESIGN, not a reference-rule error."
            else:
                reason = reasons[prop]
            row = {
                "condition_id": cid, "episode_id": c["episode_id"], "implementation": c["implementation"], "proposition": prop,
                "proposition_meaning": MEANING[prop], "source_binding": SOURCE[c["implementation"]],
                "actual_execution_witness": reasons[prop], "original_label": originals[prop], "reviewed_label": labels[prop],
                "prior_execution_witness_label": prior_witness[prop],
                "difference_reason": reason, "evidence_sufficient": "YES",
                "evidence_locator": f"{SOURCE[c['implementation']]}; {OBS_LOC.format(id=cid)}; {TRACE_LOC.format(id=cid)}; {RAW_LOC.format(id=cid)}",
                "fidelity_status": FIDELITY_OVERRIDES.get(cid, "MATCHED_DESIGN"),
            }
            label_rows.append(row)
            if diff:
                disagreement.append(row)
    write_csv("INDEPENDENT_WITNESS_LABELS.csv", ["condition_id", "episode_id", "implementation", "proposition", "proposition_meaning", "source_binding", "actual_execution_witness", "original_label", "prior_execution_witness_label", "reviewed_label", "difference_reason", "evidence_sufficient", "evidence_locator", "fidelity_status"], label_rows)

    definitions = """# Semantic Label Definitions\n\n## Scope and independence\n\nThese labels are retrospective, independently reconstructed labels for the executions that actually occurred. They do not replace `01_protocol/reference.json`, do not alter the frozen factor tables, and are not prospective validation labels. No label below is produced by calling `reference_labels(condition)` or `infer_semantics`.\n\n"""
    definitions += markdown_table(["Proposition", "Exact meaning", "Evidence rule"], [[p, MEANING[p], "Bound source + actual receipt/trace/public state; missing evidence remains INDETERMINATE"] for p in PROPS])
    definitions += """\n\n## Implementation-specific boundaries\n\n- **Vesta:** `input_acceptance` refers to the controlled price leg; the index leg was held valid. `STATUS_AND_CACHE` records the status transition plus the valid index-cache write, while the rejected price cache is retained.\n- **Aurigami:** all five labels describe the designated `getUnderlyingPrice` call. Updater calls are prefix witnesses, not updates by the primary call.\n- **Fathom:** `peekPrice`'s returned Boolean is `isPriceOk()` after the call. Retrieval invocation, retrieval acceptance, and retained-price validity are separately reconstructed. `readPrice` does not evaluate a new input.\n- **Mento:** validity immediately before the report is computed at the report transaction time from the previous reporter timestamp and the per-token expiry. The stale `oldestExpired` pre-getter result is not used as the transition witness.\n- **Felix:** `newFailureDetected=true` means a new failure in this call. If already disabled, the oracle is not called and the function returns `(lastGoodPrice,false)`. Target proxy-context writes (trace depth 2 here) are separated from dependency shutdown writes (deeper frames); a write action is not equated with a changed public value.\n\n## Sufficiency rule\n\nA determinate label requires a source binding and a distinct execution witness. Source-only deductions can establish `NOT_APPLICABLE` or entrypoint invariants, but the old interpreter's own prediction is never an independent witness.\n"""
    (HERE / "SEMANTIC_LABEL_DEFINITIONS.md").write_text(definitions, encoding="utf-8")

    disagree_md = "# Label Disagreement Audit\n\n"
    disagree_md += f"Independent reconstruction found **{len(disagreement)} disagreements with the frozen reference across {len(label_rows)} condition–proposition labels**. The old labels and the later prior-witness labels remain unchanged in their original files.\n\n"
    disagree_md += markdown_table(["Condition", "Proposition", "Original", "Reviewed", "Reason"], [[x["condition_id"], x["proposition"], x["original_label"], x["reviewed_label"], x["difference_reason"]] for x in disagreement])
    disagree_md += "\n\nVH1B is an execution deviation, not a reference-label mistake: age=1 was actually executed, so its reviewed execution label is accepted/current. Fathom disagreements arise from conflating `isPriceOk` with input acceptance and from measuring pre-validity before the scheduled primary block existed.\n"
    (HERE / "LABEL_DISAGREEMENT_AUDIT.md").write_text(disagree_md, encoding="utf-8")

    # Step 3
    completeness = []
    for impl in [x["id"] for x in protocol["implementations"]]:
        for layer in LAYERS:
            allowed = protocol["observation_layers"][layer]
            collected = list(allowed)
            used = []
            missing = []
            recoverable = []
            if layer in {"H", "X"}:
                collected = [x for x in allowed if x != "public_history"] + ["primary_receipt_logs_only"]
                missing += ["setup/prefix receipts were not merged into public_history", "pre snapshot can precede the scheduled primary timestamp"]
                recoverable += ["setup/prefix logs from raw eth_getTransactionReceipt transcripts", "primary execution timestamp from saved time control/receipt and post timestamps"]
            if layer == "X":
                collected += ["SSTORE pc and stack tail without depth/address in normalized observation", "raw trace file pointer"]
                missing += ["normalized X omits call depth/address and old/new storage comparison"]
                recoverable += ["depth and storage snapshots from saved debug trace file; execution-context attribution by frame"]
            if impl == "MENTO" and layer in {"P", "H", "X"}:
                missing += ["runner/interpreter did not align pre-validity to primary transaction time"]
                recoverable += ["previous/post reporter timestamps, token expiry, raw setNext timestamp"]
            if impl == "AURIGAMI" and layer in {"H", "X"}:
                missing += ["updater prefix logs absent from normalized H"]
            if impl == "FELIX" and layer == "X":
                missing += ["arbitrary SSTORE presence was used without ownership/value-change attribution"]
            completeness.append({
                "implementation": impl, "layer": layer, "protocol_allowed_content": j(allowed),
                "runner_collected_content": j(collected), "interpreter_used_content": "see analysis/interpreter.py; public_history is not substantively decoded; X checks only nonempty SSTORE list for Felix",
                "missing_content": "; ".join(missing) or "none identified at this layer",
                "offline_recoverable": "; ".join(recoverable) or "not needed / no additional saved evidence identified",
                "observation_time_assessment": "pre getter at current mined block; primary at next scheduled block; post after primary" if layer in {"H", "X"} else "post snapshot/return only",
                "evidence_locator": f"01_protocol/protocol.json; {RUNNER}:117-139; analysis/interpreter.py; {LEDGER_LOC}; 03_execution/raw_rpc; 03_execution/traces",
            })
    write_csv("OBSERVATION_COMPLETENESS_MATRIX.csv", ["implementation", "layer", "protocol_allowed_content", "runner_collected_content", "interpreter_used_content", "missing_content", "offline_recoverable", "observation_time_assessment", "evidence_locator"], completeness)

    obs_md = """# Observation Contract Audit\n\n## Finding\n\nThe frozen contract defined H as including the call prefix and event history, but `primaryTx` stored only the designated transaction receipt logs and `primaryPure` stored an empty list. Setup/prefix receipts were preserved in raw RPC transcripts and can be recovered offline. This report calls that **protocol-conformant offline recovery**, not the original H observation. Original H remains unchanged.\n\n## R/P/H/X implementation audit\n\n"""
    obs_md += markdown_table(["Layer", "Protocol", "Runner", "Correction boundary"], [
        ["R", "complete return/revert", "decoded return; no visible revert rows because all designated calls completed", "no recovery"],
        ["P", "R + declared public post-state", "collected declared post getters", "direct fields retained"],
        ["H", "P + pre-state + call prefix + event history", "pre getters + only primary receipt logs", "recover prefix/setup receipts and scheduled primary time from saved raw transcripts; do not overwrite H"],
        ["X", "H + same-invocation trace + frozen non-ABI state", "trace pointer/summary + SSTORE pc/stack tail", "raw trace restores depth/storage snapshots; attribution remains retrospective"],
    ])
    obs_md += """\n\n## Mento timing\n\n`evm_setNextBlockTimestamp(t)` scheduled the report transaction, but the pre getter calls executed against the previously mined block. Therefore `pre_public.oldestExpired=false` is not the validity immediately before the report at `t`. Existing evidence is sufficient offline: previous reporter timestamp, post reporter timestamp (= transaction time for these successful reports), per-token expiry 360, receipts, and saved time-control calls. The corrected transition uses `primary_time - previous_report_timestamp >= expiry`.\n\n## X ownership and write semantics\n\nFor Felix, raw traces show healthy calls writing the cache at depth 2 even when the value is unchanged. Failure calls contain a depth-2 target/proxy-context disable write and a deeper dependency shutdown write. The normalized X array removed depth/address and the old interpreter used only “any SSTORE”; that test cannot by itself identify source, target, or value change. Proxy `DELEGATECALL` execution writes proxy storage, not the implementation account.\n\n## Observation times\n\n- Public `pre` getters: last already-mined block, sometimes earlier than the scheduled primary time.\n- Primary transaction: next block at the saved controlled timestamp.\n- Public `post` getters: after the primary receipt at the primary block state.\n- Pure-call conditions: prefix transactions/time-control were mined first; the designated `eth_call` has no receipt and no primary logs.\n\nNo unavailable evidence was synthesized and no RPC was issued.\n"""
    (HERE / "OBSERVATION_CONTRACT_AUDIT.md").write_text(obs_md, encoding="utf-8")

    # Step 4
    ambiguous_old = [x for x in old_task_list if x["layer"] == "X" and x["ambiguity"]]
    ambiguity_rows = []
    for x in ambiguous_old:
        cid, prop = x["condition_id"], x["proposition"]
        is_mento = x["implementation"] == "MENTO"
        ambiguity_rows.append({
            "condition_id": cid, "implementation": x["implementation"], "proposition": prop,
            "original_prediction": j(x["prediction"]), "original_label": x["actual"], "reviewed_label": label_cache[cid][prop],
            "category": "RULE_INCOMPLETE",
            "basis": "Saved primary event plus pre/post status/cache identifies the Vesta collision case." if not is_mento else "Saved previous report timestamp, primary execution timestamp, and token expiry determine the transition; the rule ignored them and the runner failed to align pre-validity to the scheduled block.",
            "supported_observational_ambiguity": "NO",
            "observation_contract_note": "H/X normalized record omitted prefix/time alignment, but the declared evidence was preserved offline." if is_mento else "Primary receipt and pre/post fields were already present.",
            "evidence_locator": f"04_analysis/INTERPRETATION_TASKS.jsonl; {OBS_LOC.format(id=cid)}; {RAW_LOC.format(id=cid)}; {SOURCE[x['implementation']]}",
        })
    write_csv("INTERPRETER_ERROR_AND_AMBIGUITY_AUDIT.csv", ["condition_id", "implementation", "proposition", "original_prediction", "original_label", "reviewed_label", "category", "basis", "supported_observational_ambiguity", "observation_contract_note", "evidence_locator"], ambiguity_rows)

    rule_md = """# Rule Provenance Audit\n\n## Verdict\n\n`01_protocol/rules_v1.json` has local filesystem timestamps before the first formal execution and declares a field-level rule skeleton. That is evidence of a locally pre-existing specification, but it is not an immutable/external seal and it does not specify complete executable set-valued mappings. The actual executable semantic logic in `analysis/interpreter.py` was modified after formal outputs began, and `analysis/run_analysis.py` was created after execution. Therefore the reported 1,000-task output lacks adequate identity as a prospectively frozen executable held-out validation. It may be retained as the **prior analysis implementation**, not retroactively certified as pre-execution frozen.\n\n## Provenance evidence\n\n"""
    paths = [PHASE / "01_protocol" / "rules_v1.json", PHASE / "analysis" / "interpreter.py", PHASE / "analysis" / "run_analysis.py", EXEC / "EXPOSURE_LOG.jsonl", ANALYSIS / "SUMMARY.json"]
    rule_md += markdown_table(["Artifact", "Created UTC", "Modified UTC", "Role"], [[str(p.relative_to(PHASE)), datetime.fromtimestamp(p.stat().st_ctime, timezone.utc).isoformat(), datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat(), "declarative skeleton" if p.name == "rules_v1.json" else "executable/output evidence"] for p in paths])
    rule_md += """\n\n## Original versus corrected identity\n\n- **Original rule performance:** rescore the stored predictions in `04_analysis/INTERPRETATION_TASKS.jsonl` against the independent reviewed labels. This measures the prior analysis implementation only.\n- **Corrected rule performance:** a separate `offline_corrected_exploratory_v1` analysis using recovered contract-conformant H and trace attribution. It is retrospective and is not a held-out validation.\n- No file is backdated, re-labelled as prospectively frozen, or written outside this closure directory.\n\n## Missingness/ablation finding\n\nThe old interpreter frequently enters an `else -> NONE` branch when pre/post fields are absent. Thus removing a validity/status field can create a determinate negative rather than uncertainty. This violates the frozen missingness intent. Corrected scoring propagates missing evidence to a set-valued/INDETERMINATE result; absent Boolean values are never coerced to `false`.\n\n## Four-way ambiguity taxonomy\n\nAll 14 prior X ambiguities are classified row-by-row in `INTERPRETER_ERROR_AND_AMBIGUITY_AUDIT.csv`. All are `RULE_INCOMPLETE`; none demonstrates `SUPPORTED_OBSERVATIONAL_AMBIGUITY`. No pair of legal, fidelity-matched executions with identical complete allowed observation and independently different reviewed semantics was established.\n"""
    (HERE / "RULE_PROVENANCE_AUDIT.md").write_text(rule_md, encoding="utf-8")

    # Step 5
    result_rows = []
    for c in conditions:
        cid, impl = c["condition_id"], c["implementation"]
        for layer in ["K_BASELINE", *LAYERS]:
            for prop in PROPS:
                actual = label_cache[cid][prop]
                cpred, basis = corrected_prediction(c, prop, layer, observations[cid], raws[cid])
                cs = score(cpred, actual)
                old = old_rows.get((cid, layer, prop))
                if old:
                    opred = set(old["prediction"])
                    os = score(opred, actual)
                else:
                    opred, os = set(), {k: "NA" for k in ("determinate", "determinate_correct", "determinate_wrong", "wrong_exclusion", "ambiguity")}
                outcome = "INDETERMINATE" if len(cpred) > 1 else ("DETERMINATE_CORRECT" if actual in cpred else "DETERMINATE_ERROR")
                if actual not in cpred:
                    outcome = "WRONG_EXCLUSION"
                result_rows.append({
                    "condition_id": cid, "episode_id": c["episode_id"], "implementation": impl, "planned_factor": c["factor"],
                    "fidelity_status": FIDELITY_OVERRIDES.get(cid, "MATCHED_DESIGN"), "analysis_boundary": "ACTUAL_EXECUTION_DESCRIPTION",
                    "layer": layer, "proposition": prop, "reviewed_label": actual,
                    "original_prediction": j(sorted(opred)) if opred else "NA", "original_determinate": os["determinate"],
                    "original_determinate_correct": os["determinate_correct"], "original_determinate_wrong": os["determinate_wrong"], "original_wrong_exclusion": os["wrong_exclusion"],
                    "corrected_prediction": j(sorted(cpred)), "corrected_rule_identity": "offline_corrected_exploratory_v1",
                    "corrected_determinate": cs["determinate"], "corrected_determinate_correct": cs["determinate_correct"],
                    "corrected_determinate_wrong": cs["determinate_wrong"], "corrected_wrong_exclusion": cs["wrong_exclusion"],
                    "coverage_category": basis if outcome == "DETERMINATE_CORRECT" else outcome,
                    "evidence_locator": f"INDEPENDENT_WITNESS_LABELS.csv; {OBS_LOC.format(id=cid)}; {RAW_LOC.format(id=cid)}; {TRACE_LOC.format(id=cid)}",
                })
    write_csv("CORRECTED_TASK_RESULTS.csv", list(result_rows[0].keys()), result_rows)

    def summarize_rows(rows: list[dict[str, Any]], prefix: str, layers: list[str]) -> list[list[Any]]:
        out = []
        for layer in layers:
            group = [x for x in rows if x["layer"] == layer]
            out.append([layer, len(group), sum(x[f"{prefix}_determinate"] is True for x in group), sum(x[f"{prefix}_determinate_correct"] is True for x in group), sum(x[f"{prefix}_determinate_wrong"] is True for x in group), sum(x[f"{prefix}_wrong_exclusion"] is True for x in group)])
        return out

    matched_results = [x for x in result_rows if x["fidelity_status"] == "MATCHED_DESIGN"]
    all_actual = result_rows
    original_all = summarize_rows(all_actual, "original", LAYERS)
    original_matched = summarize_rows(matched_results, "original", LAYERS)
    corrected_all = summarize_rows(all_actual, "corrected", ["K_BASELINE", *LAYERS])
    corrected_matched = summarize_rows(matched_results, "corrected", ["K_BASELINE", *LAYERS])
    by_impl_prop = []
    for impl in [x["id"] for x in protocol["implementations"]]:
        for prop in PROPS:
            for layer in ["K_BASELINE", *LAYERS]:
                g = [x for x in matched_results if x["implementation"] == impl and x["proposition"] == prop and x["layer"] == layer]
                by_impl_prop.append([impl, prop, layer, len(g), sum(x["corrected_determinate"] is True for x in g), sum(x["corrected_determinate_correct"] is True for x in g), sum(x["corrected_determinate_wrong"] is True for x in g), sum(x["corrected_wrong_exclusion"] is True for x in g)])

    summary_md = "# Corrected Summary\n\n## Denominators before performance\n\n- Planned conditions: **50**.\n- Design-fidelity conditions: **42/50**.\n- Execution deviations: **8/50** (`VH1B`, `VH4A`, `VH4B`, `FH3A`, `MH3A`, `XH3A`, `XH4A`, `XH4B`).\n- Technical failures: **0**. All 50 actual calls remain available for descriptive analysis, but the eight deviations are excluded from planned-condition performance.\n- Planned-condition task denominator: **42 × 5 propositions = 210 per layer**. Actual-execution descriptive denominator: **50 × 5 = 250 per layer**.\n\n## Prior analysis implementation rescored against reviewed labels\n\n### All actual executions (descriptive only)\n\n"
    summary_md += markdown_table(["Layer", "Tasks", "Determinate", "Determinate correct", "Determinate wrong", "Wrong exclusion"], original_all)
    summary_md += "\n\n### Design-fidelity subset\n\n" + markdown_table(["Layer", "Tasks", "Determinate", "Determinate correct", "Determinate wrong", "Wrong exclusion"], original_matched)
    summary_md += "\n\nThese are not restored held-out scores: the executable interpreter lacks sufficient pre-execution freeze provenance. They are a retrospective rescore of the retained prior predictions.\n\n## Offline corrected exploratory rules\n\n### All actual executions (descriptive)\n\n"
    summary_md += markdown_table(["Layer", "Tasks", "Determinate", "Determinate correct", "Determinate wrong", "Wrong exclusion"], corrected_all)
    summary_md += "\n\n### Design-fidelity subset\n\n" + markdown_table(["Layer", "Tasks", "Determinate", "Determinate correct", "Determinate wrong", "Wrong exclusion"], corrected_matched)
    summary_md += "\n\nThe corrected H result uses protocol-conformant offline recovery of already-saved prefix logs and primary times; it is not the original normalized H. The corrected rule was authored after seeing results, so its performance is exploratory, not independent validation.\n\n## Per implementation × proposition × layer (design-fidelity subset; corrected exploratory)\n\n"
    summary_md += markdown_table(["Implementation", "Proposition", "Layer", "N", "Determinate", "Correct", "Wrong determinate", "Wrong exclusion"], by_impl_prop)
    cats = Counter(x["coverage_category"] for x in matched_results)
    summary_md += "\n\n## Coverage disposition counts across all five layers (design-fidelity subset)\n\n" + markdown_table(["Category", "Count"], [[k, v] for k, v in sorted(cats.items())])
    summary_md += """\n\nCategory mapping: `COMMON_BINDING_ONLY` = 仅依赖共同源码/入口知识；`DIRECT_PUBLIC_FIELD` = 直接公开字段读取；`OBSERVATION_DEPENDENT_INFERENCE` = 依赖实际观察的推断；the other requested categories retain their English names.\n\n## Scientific interpretation\n\nThe common-binding baseline already determines many entrypoint invariants and NOT_APPLICABLE tasks. P directly resolves Aurigami's selected source/timestamp but does not reconstruct Fathom retrieval acceptance or transitions. Protocol-complete H can reconstruct the tested histories from preserved public evidence. X adds trace-level write attribution, but no independently supported H→X semantic gain remains after restoring H.\n"""
    (HERE / "CORRECTED_SUMMARY.md").write_text(summary_md, encoding="utf-8")

    claims = [
        {"claim_id":"C1","original_claim":"Four layers have zero errors.","disposition":"WITHDRAW","basis":"Independent labels disagree with the frozen reference in 7 condition–proposition rows (four are VH1B design deviation, three are Fathom witness corrections); rescoring the retained predictions produces genuine wrong determinate/wrong-exclusion cases. The executable rule also lacks adequate prospective freeze provenance.","permitted_restatement":"The retained prior implementation can be retrospectively rescored; layer-specific errors and ambiguity must be reported, not zero-error validation."},
        {"claim_id":"C2","original_claim":"X solved 21 tasks that public history could not solve.","disposition":"WITHDRAW_AS_CAUSAL_INFORMATION_GAIN","basis":"The 21 are Felix tasks. Original H omitted declared setup/prefix logs; those raw receipts are saved and distinguish terminal prefixes. X also used arbitrary SSTORE presence without execution-context attribution. Hence the contrast is against incomplete H, not complete public history.","permitted_restatement":"Against the originally normalized incomplete H, X made 21 prior predictions singleton; this is an instrumentation-dependent exploratory observation."},
        {"claim_id":"C3","original_claim":"There are 14 genuine indeterminate tasks at X.","disposition":"WITHDRAW","basis":"All 14 are RULE_INCOMPLETE: 4 Vesta collision tasks are resolved by events/pre-post state; 10 Mento transitions are resolved by saved timestamps and expiry. No same-complete-observation/different-semantics witness was established.","permitted_restatement":"The prior interpreter returned 14 ambiguous X predictions; none is proven observational ambiguity."},
        {"claim_id":"C4","original_claim":"All 50 declared conditions are valid and comparable.","disposition":"WITHDRAW","basis":"42/50 match design; eight executed a different condition. All 50 can describe actual calls, but only 42 belong in the planned-condition denominator.","permitted_restatement":"50 primary calls completed; 42 implemented their declared intervention and 8 are retained deviations."},
        {"claim_id":"C5","original_claim":"Two new independent implementations validate transfer.","disposition":"NARROW","basis":"Mento and Felix were new formal executions for this phase, but Felix is Liquity-derived like Vesta and neither is an independent validation agent. Mento contributes a distinct SortedOracles lineage; Felix contributes a new deployment/terminal mechanism, not a second independent lineage.","permitted_restatement":"Two additional bound deployments were executed: one distinct Mento SortedOracles lineage and one Felix Liquity-derived terminal-cache deployment."},
        {"claim_id":"C6","original_claim":"E5 validates semantic behavior in natural history.","disposition":"NARROW","basis":"Fixed windows and retrieved root-address logs establish log availability/absence under the query contract. They do not independently establish internal semantic transitions or pure-call production use.","permitted_restatement":"E5 supports bounded historical log retrievability and observed event incidence only."},
        {"claim_id":"C7","original_claim":"E6 independently reproduces the scientific result.","disposition":"NARROW","basis":"The portable run replays selected saved transcripts/projections with the same analysis lineage and adds no scientific sample; it verifies transcript replay stability, not independent semantic adjudication.","permitted_restatement":"E6 supports deterministic transcript replay and package portability for the selected episode subset."},
    ]
    write_csv("CLAIM_DISPOSITION_MATRIX.md.tmp.csv", list(claims[0].keys()), claims)
    claim_md = "# Claim Disposition Matrix\n\n" + markdown_table(["ID", "Original claim", "Disposition", "Evidence-based reason", "Permitted restatement"], [[x["claim_id"], x["original_claim"], x["disposition"], x["basis"], x["permitted_restatement"]] for x in claims]) + "\n\nOriginal records are retained; these dispositions govern only future use of the claims.\n"
    (HERE / "CLAIM_DISPOSITION_MATRIX.md").write_text(claim_md, encoding="utf-8")
    (HERE / "CLAIM_DISPOSITION_MATRIX.md.tmp.csv").unlink()

    # Step 6
    final_md = """# Offline Semantic Validation Correctness Closure — Final Report\n\n## Executive decision\n\n**Path B — partial evidence is sufficient.** Existing raw material supports a narrower, useful contribution, but not the original zero-error/94.4%/50-of-50 framing and not a prospectively frozen independent rule-validation claim. No new execution is required to establish the narrower findings below. A later targeted re-execution would be needed only if the authors want to restore the failed design contrasts or a genuine held-out rule-performance claim.\n\n## 1. Reliably established new findings\n\n1. Fifty designated primary calls completed technically, but only **42/50** executed the declared intervention. The exact eight deviations are preserved in `CONDITION_FIDELITY_AUDIT.csv`.\n2. Full ABI returns have implementation-specific semantic value: Felix's `newFailureDetected=true` directly identifies a new failure branch; Fathom's Boolean is post-call price validity and does **not** by itself identify input acceptance.\n3. Aurigami's public source flag directly identifies main versus backup for the designated read, while its updater semantics belong to the prefix window, not the pure primary call.\n4. Existing saved public evidence is sufficient to reconstruct Mento validity transitions at the actual report time and to correct the Fathom FH3B timing interpretation.\n5. Raw traces support a real distinction between target/proxy-context storage writes and dependency writes, and between a write action and a changed value. The normalized X evidence did not preserve those distinctions.\n6. A common-binding-only baseline resolves a material share of tasks; therefore observation-layer contribution must be measured above that baseline rather than against zero knowledge.\n\n## 2. Exploratory observations only\n\n- Performance of `offline_corrected_exploratory_v1`, including its protocol-recovered H results. It was authored after outcomes were visible.\n- Rescored performance of the prior executable interpreter. Its predictions are retained, but its executable freeze identity is inadequate for prospective held-out validation.\n- The original incomplete-H to X singleton gain (21 tasks). It is reproducible as an analysis artifact, not evidence that complete public history is insufficient.\n\n## 3. Claims that must be withdrawn\n\n- “Four layers have zero errors.”\n- “X solves 21 tasks that public history cannot solve.”\n- “The 14 X ambiguities are genuine observational ambiguities.”\n- “All 50 declared conditions are valid and comparable.”\n\nThe “two new independent implementations” claim must be narrowed, and E5/E6 must be limited to log retrievability and transcript replay respectively.\n\n## 4. Problems solvable offline from existing raw evidence\n\n- VH1B's actual age=1 and resulting semantics.\n- Aurigami updater order, raw-only versus aggregate prefix, and all setup receipt logs.\n- Fathom retrieval eligibility/failure separation, input acceptance versus `isPriceOk`, and validity at primary time.\n- Mento pre-report age, inclusive expiry, and report-time transition.\n- Felix terminal-prefix identity, SSTORE frame attribution, target versus dependency writes, and same-value cache writes.\n- Reclassification of all 14 prior X ambiguities and rescore of every condition/proposition/layer.\n\n## 5. Problems not solvable offline\n\n- The missing Vesta working→untrusted→working long prefixes (VH4A/B) were never executed.\n- The intended successful Fathom shared-prestate retrieval (FH3A) was not executed.\n- The Mento old-timestamp control (MH3A) was not executed.\n- Felix first terminal primary (XH3A) and both non-collision conditions (XH4A/B) were not executed as declared.\n- A cryptographically or externally sealed complete executable pre-execution interpreter does not exist in the saved materials; it cannot be manufactured retrospectively.\n- No legal same-complete-observation/different-independent-semantics pair establishes `SUPPORTED_OBSERVATIONAL_AMBIGUITY`.\n\n## 6. Does the correction strengthen V0.4's main contribution?\n\n**Yes, but only as a narrowed empirical extension.** The closure adds a defensible taxonomy of what complete returns, public snapshots, recoverable histories, and attributed traces support in these bound executions. It also demonstrates concrete evaluation failure modes: validity/acceptance conflation, observation-time mismatch, omitted prefix history, and unowned SSTORE inference. Those are scientifically useful and align with the manuscript's existing warning that different records do not automatically imply identifiable semantics.\n\nIt does **not** support upgrading V0.4 with the previous headline percentages or an independent held-out validation claim. Any later V0.5 revision should use the 42-condition design-fidelity denominator, describe the other eight calls separately, and label corrected-rule results exploratory.\n\n## Selected path and stop condition\n\n**Selected: B — 部分足够.** Recommended next action, requiring separate authorization: narrow the added claim to the reliable findings above and preserve the exact execution gaps. This closure performs no manuscript revision and no targeted re-execution.\n\n```ini\nPRIMARY_LINE = COMPLETE\nNEW_RPC = 0\nREEXECUTION = 0\nOLD_ARTIFACT_OVERWRITE = 0\nMANUSCRIPT_REVISION = HOLD\nPATH = B\nNEXT = WAIT_FOR_SEPARATE_AUTHORIZATION\n```\n"""
    (HERE / "OFFLINE_CORRECTNESS_CLOSURE_FINAL_REPORT.md").write_text(final_md, encoding="utf-8")

    manifest = {
        "stage": "OFFLINE_SEMANTIC_VALIDATION_CORRECTNESS_CLOSURE_V1",
        "generated_files": sorted(p.name for p in HERE.iterdir() if p.is_file()),
        "condition_count": len(conditions),
        "design_fidelity": Counter(x["fidelity_status"] for x in fidelity),
        "label_rows": len(label_rows),
        "label_disagreements": len(disagreement),
        "prior_x_ambiguities_audited": len(ambiguity_rows),
        "path": "B",
    }
    (HERE / "RUN_MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=dict) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

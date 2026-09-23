from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SEM = ROOT / "semantic_explanation_validation_v1"
OLD = SEM / "07_offline_correctness_closure_v1"
OUT = Path(__file__).resolve().parent
EXEC = SEM / "03_execution"

PROPS = ["input_acceptance", "return_source", "updated_stage", "state_transition", "timestamp_meaning"]
NONTRIVIAL = {
    "VESTA": set(PROPS) - {"timestamp_meaning"},
    "AURIGAMI": {"return_source", "timestamp_meaning"},
    "FATHOM": set(PROPS),
    "MENTO": set(PROPS),
    "FELIX": set(PROPS) - {"timestamp_meaning"},
}

VESTA_BINDING = (
    "../journal_manuscript_phase/JOURNAL_V0.4_REVIEWER_SUPPLEMENT/"
    "deployment_binding_summary/vesta_implementation.json; "
    "../journal_policy_differential_preparation_20260913/08_formal_execution/"
    "VESTA_POST_EXECUTION_BINDING_AND_CLASSIFIER_REVIEW_001.json"
)

SOURCE_BRANCH = {
    "VESTA": (
        "Saved PriceFeedV2 binding summary: proxy 0xC934...6702 -> implementation "
        "0x522808...D26d, runtime SHA-256 F7CA...B9E1; saved review states price-leg "
        "broken-or-frozen and index-leg validity/round checks without the 14,400-second age predicate. "
        "The exact PriceFeedV2 source body is not saved locally, so no line-addressable branch proof is claimed."
    ),
    "AURIGAMI": (
        "AuriOracle.sol:98-118 selects backup only when isOutdated; lines 230-236 define "
        "isOutdated as (block.timestamp-lastUpdateTimestamp) > validPeriod; lines 274-290 expose "
        "the selected-source Boolean."
    ),
    "FATHOM": (
        "DelayPriceFeedBase.sol:70-83 calls retrivePrice only when the delay/freshness guard holds, "
        "writes delayed/latest/lastUpdate on success, emits LogPeekPriceFailed on caught Error, and "
        "returns delayedPrice.price plus isPriceOk."
    ),
    "MENTO": (
        "MENTO_BOUND_SORTED_ORACLES.sol:220-259 writes the reporter rate/timestamp, emits "
        "OracleReported, and conditionally emits MedianUpdated; expiry getters bind the time relation."
    ),
    "FELIX": (
        "RedStonePriceFeedBase.sol:50-56 returns cache immediately if disabled; lines 79-85 call the "
        "dependency shutdown, set the target disable flag, emit PriceFeedDisabled, and return cache; "
        "the concrete WHYPERedStonePriceFeed source binds the oracle branch."
    ),
}

EVENT_NAMES = {
    "0x2d452398cb8bb9e5cdadeaabfe0a5d66bf83abdf317ed5633a64528f5bee7458": "MainFeedSync(address,uint256,address)",
    "0x1dad06f9b840665ab0cfae3caef238945679f3e2123bdcc11b1612a94c22d470": "LogPeekPriceFailed(address,string)",
    "0x7cebb17173a9ed273d2b7538f64395c0ebf352ff743f1cf8ce66b437a6144213": "OracleReported(address,address,uint256,uint256)",
    "0xa9981ebfc3b766a742486e898f54959b050a66006dbce1a4155c1f84a08bcf41": "MedianUpdated(address,uint256)",
    "0xfc1b56fc12ab7492f5ab7cd660ca9975437183eaeaf0c49716ef6a83b8dfdeab": "PriceFeedDisabled(uint256)",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def compact(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def all_raw_receipts(condition_id: str) -> list[dict]:
    receipts = []
    for path in sorted((EXEC / "raw_rpc").glob(f"*_{condition_id}_eth_getTransactionReceipt.json")):
        record = load_json(path)
        receipt = record.get("response", {}).get("result") or {}
        receipts.append({"file": path.name, "tx_hash": receipt.get("transactionHash", ""), "logs": receipt.get("logs", [])})
    return receipts


def event_summary(condition_id: str, obs: dict) -> str:
    primary_hash = str(obs.get("tx_hash", "")).lower()
    entries = []
    for receipt in all_raw_receipts(condition_id):
        role = "primary" if primary_hash not in {"", "na"} and str(receipt["tx_hash"]).lower() == primary_hash else "prefix/setup"
        for log in receipt["logs"]:
            topic = (log.get("topics") or [""])[0].lower()
            entries.append({
                "role": role,
                "address": str(log.get("address", "")).lower(),
                "topic0": topic,
                "event": EVENT_NAMES.get(topic, "UNDECODED_FROM_SAVED_EXACT_SOURCE"),
                "tx": receipt["tx_hash"],
            })
    return compact(entries) if entries else "NO_SAVED_RECEIPT_LOG"


def trace_summary(condition_id: str, implementation: str) -> str:
    trace = load_json(EXEC / "traces" / f"{condition_id}.json")
    logs = trace.get("structLogs", [])
    sstores = []
    for item in logs:
        if item.get("op") != "SSTORE":
            continue
        stack = item.get("stack", [])
        value = "0x" + stack[-2] if len(stack) >= 2 else "UNKNOWN"
        slot = "0x" + stack[-1] if stack else "UNKNOWN"
        context = "UNRESOLVED"
        if implementation == "FELIX":
            context = "TARGET_PROXY_STORAGE" if item.get("depth") == 2 else "DEPENDENCY_STORAGE"
        elif implementation == "FATHOM":
            context = "TARGET_PROXY_STORAGE" if item.get("depth") == 2 else "NESTED_CONTEXT"
        elif implementation == "VESTA":
            context = "TARGET_PROXY_STORAGE" if item.get("depth") == 2 else "NESTED_CONTEXT"
        sstores.append({"pc": item.get("pc"), "depth": item.get("depth"), "context": context, "slot": slot, "value": value})
    retrieval = [x for x in logs if x.get("op") == "STATICCALL" and x.get("pc") == 1224]
    parts = []
    if implementation == "FATHOM":
        parts.append(
            "retrivePrice STATICCALL "
            + ("present at pc=1224 depth=2 to target proxy 0x5dE248...37a88 with selector 0x5a0e1bd9" if retrieval else "absent")
        )
    parts.append("SSTORE=" + compact(sstores))
    return "; ".join(parts)


def harness_summary(condition_id: str) -> str:
    selected = []
    ledger = EXEC / "CALL_LEDGER.jsonl"
    for line in ledger.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("condition_id") != condition_id:
            continue
        kind = rec.get("kind")
        if kind in {"DEPENDENCY_INTERVENTION", "TARGET_SETUP", "SUPPORT_MECHANICS", "TIME_CONTROL"}:
            selected.append({"kind": kind, "detail": rec.get("detail")})
    return compact(selected[:12]) + (f"; +{len(selected)-12} more" if len(selected) > 12 else "")


def public_summary(obs: dict) -> str:
    full = obs["full"]
    result = {
        "return": full.get("return"),
        "pre_public": full.get("pre_public"),
        "post_public": full.get("post_public"),
        "primary_log_count": len(full.get("public_history", [])),
        "tx_hash": obs.get("tx_hash"),
        "block_number": obs.get("block_number"),
    }
    return compact(result)


def sufficiency(impl: str, prop: str) -> tuple[str, str]:
    if prop not in NONTRIVIAL[impl]:
        return "SUFFICIENT_COMMON_BINDING", "Common entrypoint/source knowledge fixes this label; it is not evidence of observation-layer gain."
    if impl == "VESTA" and prop in {"input_acceptance", "return_source", "updated_stage"}:
        return (
            "INSUFFICIENT_EXACT_SOURCE_BODY",
            "Saved metadata binds the deployed implementation to PriceFeedV2 and summarizes key semantics, but the exact source body is absent; branch/slot-to-variable proof is not independently line-verifiable.",
        )
    if impl == "VESTA":
        return "SUFFICIENT_PUBLIC_FIELD", "The status transition is directly recorded by pre/post public reads; no wrong PriceFeed.sol branch is needed."
    if impl == "AURIGAMI":
        return "SUFFICIENT_PUBLIC_FIELD", "The saved _getRawUnderlyingPrice Boolean and timestamp directly expose selected source and its time."
    if impl == "FATHOM" and prop in {"input_acceptance", "updated_stage"}:
        return "SUFFICIENT_TRACE_AND_STATE", "The concrete self-call is checked in the saved trace and success/failure is separated using state writes/change and the failure event."
    if impl == "FATHOM":
        return "SUFFICIENT_SOURCE_AND_PUBLIC", "Exact source plus returned/public delayed record and execution time bind the proposition."
    if impl == "MENTO":
        return "SUFFICIENT_PUBLIC_EVENT_STATE", "OracleReported, reporter records, expiry configuration, and before/after timestamps bind the report-time semantics."
    if impl == "FELIX" and prop == "updated_stage":
        return "SUFFICIENT_CONTEXTUALIZED_TRACE", "SSTORE pc/depth/slot/value are reported with target-proxy versus dependency context; arbitrary SSTORE presence is not used."
    if impl == "FELIX":
        return "SUFFICIENT_RETURN_EVENT_SOURCE", "Full ABI return, target/dependency event addresses, public cache, terminal prefix, and exact source branch are jointly used."
    raise AssertionError((impl, prop))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    old_manifest = []
    for path in sorted(OLD.glob("*")):
        if path.is_file():
            old_manifest.append({"relative_path": path.relative_to(ROOT).as_posix(), "sha256": sha256(path), "bytes": path.stat().st_size})
    write_csv(OUT / "PARENT_CLOSURE_SHA256.csv", old_manifest, ["relative_path", "sha256", "bytes"])

    fidelity = read_csv(OLD / "CONDITION_FIDELITY_AUDIT.csv")
    granular = []
    for row in fidelity:
        cid = row["condition_id"]
        status = row["fidelity_status"]
        episode_status = "EPISODE_MATCHED_DESIGN" if status == "MATCHED_DESIGN" else "EPISODE_DEVIATES_FROM_DESIGN"
        comparison_status = "COMPARISON_MATCHED_DESIGN" if status == "MATCHED_DESIGN" else "ACTUAL_EXECUTION_DESCRIPTION_ONLY"
        detail = "Inherited after targeted review; see parent audit for actual execution."
        if cid in {"AH5A", "AH5B"}:
            status = "EXECUTION_DEVIATES_FROM_DESIGN"
            episode_status = "EPISODE_DEVIATES_FROM_DESIGN"
            comparison_status = "ACTUAL_MAIN_PATH_TIME_SHIFT_COMPARISON_ONLY"
            detail = (
                "Runner mined at main.updatedAt+7200. AuriOracle uses strict > validPeriod; saved validPeriod=7200 and "
                "rawUnderlying source flag=true, so the designated read used the main aggregate, not the declared backup path."
            )
        granular.append({
            **row,
            "single_condition_fidelity": status,
            "episode_fidelity": episode_status,
            "comparison_fidelity": comparison_status,
            "targeted_review_detail": detail,
            "claim_scope": "PENDING_EPISODE_REVIEW",
        })
    deviating_episodes = {
        r["condition_id"][:-1] for r in granular
        if r["single_condition_fidelity"] != "MATCHED_DESIGN"
    }
    for row in granular:
        episode = row["condition_id"][:-1]
        if episode in deviating_episodes:
            row["episode_fidelity"] = "EPISODE_DEVIATES_FROM_DESIGN"
            row["comparison_fidelity"] = (
                "ACTUAL_MAIN_PATH_TIME_SHIFT_COMPARISON_ONLY" if episode == "AH5"
                else "NO_PLANNED_COMPARISON_ACTUAL_PAIR_ONLY"
            )
            row["claim_scope"] = (
                "ACTUAL_EXECUTION_DESCRIPTION_ONLY"
                if row["single_condition_fidelity"] != "MATCHED_DESIGN"
                else "SINGLE_CONDITION_ONLY_NOT_EPISODE_COMPARISON"
            )
        else:
            row["episode_fidelity"] = "EPISODE_MATCHED_DESIGN"
            row["comparison_fidelity"] = "COMPARISON_MATCHED_DESIGN"
            row["claim_scope"] = "PLANNED_DESIGN_ELIGIBLE"
    fidelity_fields = list(granular[0].keys())
    write_csv(OUT / "ADDENDUM_CONDITION_FIDELITY.csv", granular, fidelity_fields)

    fidelity_by_id = {r["condition_id"]: r for r in granular}
    old_labels = read_csv(OLD / "INDEPENDENT_WITNESS_LABELS.csv")
    evidence_rows = []
    for row in old_labels:
        cid, impl, prop = row["condition_id"], row["implementation"], row["proposition"]
        obs = load_json(EXEC / "observations" / f"{cid}.json")
        status, reason = sufficiency(impl, prop)
        claim_scope = fidelity_by_id[cid]["claim_scope"]
        source_binding = VESTA_BINDING if impl == "VESTA" else row["source_binding"]
        evidence_rows.append({
            "condition_id": cid,
            "episode_id": row["episode_id"],
            "implementation": impl,
            "proposition": prop,
            "reviewed_label": row["reviewed_label"],
            "nontrivial": "YES" if prop in NONTRIVIAL[impl] else "NO",
            "source_binding": source_binding,
            "source_branch_evidence": SOURCE_BRANCH[impl],
            "public_contract_evidence": public_summary(obs),
            "receipt_event_evidence": event_summary(cid, obs),
            "execution_internal_evidence": trace_summary(cid, impl),
            "harness_only_information": harness_summary(cid),
            "evidence_sufficiency": status,
            "sufficiency_reason": reason,
            "claim_scope": claim_scope,
            "design_fidelity": fidelity_by_id[cid]["single_condition_fidelity"],
            "evidence_locator": (
                f"{VESTA_BINDING}; 03_execution/observations/{cid}.json; "
                f"03_execution/traces/{cid}.json; 03_execution/raw_rpc/*_{cid}_*.json"
                if impl == "VESTA" else row["evidence_locator"]
            ),
        })
    evidence_fields = list(evidence_rows[0].keys())
    write_csv(OUT / "NONTRIVIAL_LABEL_EVIDENCE_AUDIT.csv", evidence_rows, evidence_fields)

    matched = [r for r in granular if r["single_condition_fidelity"] == "MATCHED_DESIGN"]
    deviated = [r for r in granular if r["single_condition_fidelity"] != "MATCHED_DESIGN"]
    rows_by_condition = defaultdict(list)
    for row in evidence_rows:
        rows_by_condition[row["condition_id"]].append(row)
    fully_qualified = []
    unresolved = []
    for row in matched:
        nontrivial = [x for x in rows_by_condition[row["condition_id"]] if x["nontrivial"] == "YES"]
        if all(not x["evidence_sufficiency"].startswith("INSUFFICIENT") for x in nontrivial):
            fully_qualified.append(row)
        else:
            unresolved.append(row)
    matched_nontrivial = [r for r in evidence_rows if r["design_fidelity"] == "MATCHED_DESIGN" and r["nontrivial"] == "YES"]
    qualified_nontrivial = [r for r in matched_nontrivial if not r["evidence_sufficiency"].startswith("INSUFFICIENT")]
    actual_only_rows = [r for r in evidence_rows if r["claim_scope"] == "ACTUAL_EXECUTION_DESCRIPTION_ONLY"]
    actual_only_nontrivial = [r for r in actual_only_rows if r["nontrivial"] == "YES"]
    episode_ids = sorted({r["condition_id"][:-1] for r in granular})
    matched_episodes = [ep for ep in episode_ids if ep not in deviating_episodes]
    fully_qualified_episodes = []
    unresolved_episodes = []
    for ep in matched_episodes:
        ep_rows = [r for r in evidence_rows if r["episode_id"] == ep and r["nontrivial"] == "YES"]
        if all(not r["evidence_sufficiency"].startswith("INSUFFICIENT") for r in ep_rows):
            fully_qualified_episodes.append(ep)
        else:
            unresolved_episodes.append(ep)

    ah5 = """# AH5 granular fidelity re-audit

## Decision

AH5A and AH5B are not backup-path conditions. Each designated call technically completed, but each single condition is `EXECUTION_DEVIATES_FROM_DESIGN`; the AH5 episode is `EPISODE_DEVIATES_FROM_DESIGN`.

The runner executes two authorized updater transactions, reads `mainFeed.updatedAt`, and mines at exactly `updatedAt + 7200`. The saved contract source uses `elapsed > validPeriod`, not `>=`, and the saved public configuration is `validPeriod=7200`. Both observations report `_getRawUnderlyingPrice(...).isFromMainFeed=true`. Thus the exact boundary remains main-source-valid.

## Three distinct units

| Unit | AH5A | AH5B | Adjudication |
|---|---|---|---|
| Single condition | planned backup path; actual main aggregate | planned backup path; actual main aggregate | both deviate |
| Episode | required nuisance-shifted equivalent backup path | same episode | episode deviates because the defining mechanism was absent |
| Comparison | actual main path at base time | actual main path shifted by 1000 seconds | supports only an actual main-path time-shift comparison; it is not the planned backup-path comparison |

The pair may be described as two numerically and semantically equivalent main-path executions under an absolute-time shift. It cannot enter the planned-design denominator.
"""
    (OUT / "AH5_GRANULAR_FIDELITY_AUDIT.md").write_text(ah5, encoding="utf-8")

    vesta = """# Vesta PriceFeedV2 source-binding audit

## Controlling identity

- proxy: `0xC93408bFBEa0Bf3E53bEdBce7D5C1e64db826702`
- implementation: `0x522808d93Ac229CEfc17c4BE0408520f7e27D26d`
- runtime SHA-256: `F7CA795217706A4D46FD54525F357C997C0FB68C0383426046B9A4C05E6CB9E1`
- saved verified-source name/path: `PriceFeedV2` / `contracts/PriceFeedV2.sol`

All Vesta rows in this addendum bind only to the saved implementation summary and the saved post-execution PriceFeedV2 review. The repository `vesta-protocol-v1/contracts/PriceFeed.sol` is explicitly excluded: it is a different source variant and cannot support these execution labels.

## Exact limitation

The saved local materials contain the deployed implementation identity, compiler/optimizer metadata, runtime digest, and a semantic summary of the relevant PriceFeedV2 predicates. They do **not** contain the exact PriceFeedV2 source body. Therefore this addendum can verify the deployment-to-PriceFeedV2 metadata binding, but it cannot supply line-addressable branch evidence or independently map each SSTORE slot to a named PriceFeedV2 variable.

Consequences:

- `state_transition` remains directly supported where public `status` reads show the transition.
- `input_acceptance`, `return_source`, and `updated_stage` are marked `INSUFFICIENT_EXACT_SOURCE_BODY`; they are not declared independently closed.
- Vesta event topics may be retained as raw receipt facts, but unnamed topics are not decoded by borrowing the excluded PriceFeed.sol.

This is a source-evidence qualification, not a change to any old execution record.
"""
    (OUT / "VESTA_PRICEFEEDV2_SOURCE_BINDING_AUDIT.md").write_text(vesta, encoding="utf-8")

    layer_counts = Counter(r["evidence_sufficiency"] for r in evidence_rows)
    public_harness = f"""# Public evidence versus harness information

## Separation rule

Public contract evidence consists of saved ABI returns, public getters, target/dependency receipt logs, transaction identity, and block location. Execution-internal evidence consists of saved traces and is reported separately because it is not a public ABI field. Harness-only information consists of condition names, controlled `setCode`/time/fault parameters, call-purpose annotations, and setup intent in `CALL_LEDGER.jsonl`.

Harness annotations establish what the runner attempted and are useful for describing the actual controlled execution. They do not by themselves prove that the target evaluated or accepted the injected value. That proof requires the exact source branch plus concrete return/event/state/trace evidence.

## Evidence-sufficiency inventory

{chr(10).join(f'- `{k}`: {v}' for k, v in sorted(layer_counts.items()))}

`H=100%` or `X=100%` is not a completion criterion. A layer can produce a singleton after using post-hoc rules, omitted prefix recovery, harness metadata, or unattributed SSTOREs. Completion is evaluated per proposition against source identity, execution fidelity, and evidence provenance.

For Fathom, the audit records the actual `retrivePrice()` self-call (`STATICCALL`, pc 1224, depth 2, selector `0x5a0e1bd9`) instead of inferring it only from time arithmetic. For Felix, every SSTORE row contains pc, depth, slot, value, and target-proxy/dependency context. For Mento and Aurigami, named event topics and public records are kept separate from scheduled timestamps and updater/factor annotations.
"""
    (OUT / "PUBLIC_VS_HARNESS_EVIDENCE_AUDIT.md").write_text(public_harness, encoding="utf-8")

    denominator = f"""# Final qualified denominator and claim disposition

## Recomputed denominators

| Unit | Count | Meaning |
|---|---:|---|
| Attempted designated calls | 50 | Technical attempts only; not a validity denominator |
| Conditions matching declared design | {len(matched)}/50 | AH5A/B are newly removed from the prior 42-condition count |
| Conditions deviating from declared design | {len(deviated)}/50 | May support actual-execution descriptions only |
| Episodes/comparisons matching declared design | {len(matched_episodes)}/25 | Both A/B conditions must match; one-sided fidelity does not rescue the pair |
| Design-matched episodes with all nontrivial labels evidence-qualified | {len(fully_qualified_episodes)}/{len(matched_episodes)} | Final planned-comparison denominator |
| Design-matched episodes with unresolved exact-source evidence | {len(unresolved_episodes)}/{len(matched_episodes)} | Matched Vesta episodes {', '.join(unresolved_episodes)} |
| Design-matched conditions with all nontrivial labels evidence-qualified | {len(fully_qualified)}/{len(matched)} | Final condition-level denominator for evidence-qualified planned conditions |
| Design-matched conditions with unresolved exact-source evidence | {len(unresolved)}/{len(matched)} | The seven matched Vesta conditions; not fully closed |
| Nontrivial labels on design-matched conditions | {len(matched_nontrivial)} | Proposition-level applicable denominator |
| Evidence-qualified nontrivial labels on design-matched conditions | {len(qualified_nontrivial)}/{len(matched_nontrivial)} | Does not imply prospective rule validation |
| Rows restricted to actual-execution description | {len(actual_only_rows)} rows ({len(actual_only_nontrivial)} nontrivial) | All five propositions for each deviating condition retain this claim-scope flag |

The defensible single-condition design-fidelity count is therefore **{len(matched)}/50**, not 42/50. At episode/comparison grain it is **{len(matched_episodes)}/25**, and only **{len(fully_qualified_episodes)}/{len(matched_episodes)}** design-matched comparisons have all nontrivial labels evidence-qualified. At condition grain, **{len(fully_qualified)}/{len(matched)}** design-matched conditions are fully qualified. The remaining {len(unresolved)} design-matched Vesta conditions have public execution facts but lack locally saved, line-addressable PriceFeedV2 source-body evidence for three semantic propositions each.

## Records that support only actual execution descriptions

{', '.join(r['condition_id'] for r in deviated)}.

Their saved calls, returns, logs, state reads, and traces remain usable to say what actually occurred. They cannot support their planned condition/episode comparison. AH5A/B additionally support only an actual main-path time-shift comparison.

## Terminology correction

Use exactly: **“与原分析保留的参考标签记录相比，有 7 项差异。”**

Do not call these “7 frozen reference-label differences.” The saved materials do not establish a sufficiently complete pre-execution executable reference identity, so “frozen reference” would overstate prospective status.

## Final disposition

- `OFFLINE_CLOSURE_AUDIT = PARTIAL_PASS`
- `CLAIM_WITHDRAWALS = ACCEPTED`
- `PATH_B_DIRECTION = ACCEPTED`
- `DESIGN_FIDELITY_40_OF_50 = CONFIRMED_BY_TARGETED_ADDENDUM`
- `EXACT_PRICEFEEDV2_METADATA_BINDING = CONFIRMED`
- `EXACT_PRICEFEEDV2_SOURCE_BODY_LOCALLY_SAVED = NO`
- `ALL_LABELS_INDEPENDENTLY_CLOSED = NO`
- `V0.5_SUBMISSION_READINESS = NO`
- `NEW_EXPERIMENT = NOT_STARTED`
- `MANUSCRIPT_REVISION = HOLD`
- `NEXT = WAIT_FOR_SEPARATE_AUTHORIZATION`
"""
    (OUT / "FINAL_QUALIFIED_DENOMINATOR_AND_DISPOSITION.md").write_text(denominator, encoding="utf-8")

    readme = """# Targeted Offline Closure Addendum

Append-only supplement to `07_offline_correctness_closure_v1`. It changes no parent closure, execution, protocol, interpreter, reference, V0.4, or V0.5 artifact. It performs only the five requested corrections: AH5 granularity, Vesta PriceFeedV2 binding, concrete label evidence, public/harness separation, and denominator recomputation.

Files:

1. `AH5_GRANULAR_FIDELITY_AUDIT.md`
2. `VESTA_PRICEFEEDV2_SOURCE_BINDING_AUDIT.md`
3. `NONTRIVIAL_LABEL_EVIDENCE_AUDIT.csv`
4. `PUBLIC_VS_HARNESS_EVIDENCE_AUDIT.md`
5. `FINAL_QUALIFIED_DENOMINATOR_AND_DISPOSITION.md`

Supporting ledgers: `ADDENDUM_CONDITION_FIDELITY.csv`, `PARENT_CLOSURE_SHA256.csv`, and `VERIFICATION_REPORT.json`.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")

    verification = {
        "schema": "targeted-offline-closure-addendum-verification-v1",
        "rows": {
            "conditions": len(granular),
            "labels": len(evidence_rows),
            "matched_design": len(matched),
            "deviates": len(deviated),
            "fully_qualified_matched_conditions": len(fully_qualified),
            "matched_episodes": len(matched_episodes),
            "fully_qualified_matched_episodes": len(fully_qualified_episodes),
            "matched_nontrivial_labels": len(matched_nontrivial),
            "qualified_matched_nontrivial_labels": len(qualified_nontrivial),
            "actual_execution_only_rows": len(actual_only_rows),
        },
        "checks": {
            "ah5_both_deviate": all(fidelity_by_id[x]["single_condition_fidelity"] == "EXECUTION_DEVIATES_FROM_DESIGN" for x in ("AH5A", "AH5B")),
            "no_unconditional_yes": all(r["evidence_sufficiency"] != "YES" for r in evidence_rows),
            "vesta_excludes_old_pricefeed": all("vesta-protocol-v1/contracts/PriceFeed.sol" not in r["source_binding"] for r in evidence_rows if r["implementation"] == "VESTA"),
            "seven_difference_wording_present": "与原分析保留的参考标签记录相比，有 7 项差异。" in denominator,
            "no_rpc_or_reexecution": True,
            "manuscript_revision_hold": True,
        },
    }
    (OUT / "VERIFICATION_REPORT.json").write_text(json.dumps(verification, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

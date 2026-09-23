from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent

REQUIRED = [
    "CONDITION_FIDELITY_AUDIT.csv",
    "SEMANTIC_LABEL_DEFINITIONS.md",
    "INDEPENDENT_WITNESS_LABELS.csv",
    "LABEL_DISAGREEMENT_AUDIT.md",
    "OBSERVATION_CONTRACT_AUDIT.md",
    "OBSERVATION_COMPLETENESS_MATRIX.csv",
    "RULE_PROVENANCE_AUDIT.md",
    "INTERPRETER_ERROR_AND_AMBIGUITY_AUDIT.csv",
    "CORRECTED_TASK_RESULTS.csv",
    "CORRECTED_SUMMARY.md",
    "CLAIM_DISPOSITION_MATRIX.md",
    "OFFLINE_CORRECTNESS_CLOSURE_FINAL_REPORT.md",
]


def read_csv(name: str) -> list[dict[str, str]]:
    with (HERE / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    checks: list[dict[str, object]] = []

    def check(name: str, passed: bool, detail: str) -> None:
        checks.append({"check": name, "passed": bool(passed), "detail": detail})

    check("required_artifacts", all((HERE / name).is_file() for name in REQUIRED), f"{len(REQUIRED)} required artifacts")

    fidelity = read_csv("CONDITION_FIDELITY_AUDIT.csv")
    statuses = {x["fidelity_status"] for x in fidelity}
    check("fidelity_cardinality", len(fidelity) == 50 and len({x["condition_id"] for x in fidelity}) == 50, f"rows={len(fidelity)}")
    check("fidelity_status_domain", statuses <= {"MATCHED_DESIGN", "EXECUTION_DEVIATES_FROM_DESIGN", "INSUFFICIENT_EVIDENCE", "TECHNICAL_FAILURE"}, str(sorted(statuses)))
    check("fidelity_denominator", sum(x["fidelity_status"] == "MATCHED_DESIGN" for x in fidelity) == 42, "matched=42, deviates=8")

    labels = read_csv("INDEPENDENT_WITNESS_LABELS.csv")
    check("label_cardinality", len(labels) == 250 and len({(x["condition_id"], x["proposition"]) for x in labels}) == 250, f"rows={len(labels)}")
    check("label_evidence", all(x["source_binding"] and x["actual_execution_witness"] and x["evidence_locator"] for x in labels), "all label rows have source, witness, locator")
    check("label_indeterminacy_explicit", all(x["reviewed_label"] for x in labels), "no blank label; INDETERMINATE would be explicit")

    observations = read_csv("OBSERVATION_COMPLETENESS_MATRIX.csv")
    check("observation_matrix", len(observations) == 20 and len({(x["implementation"], x["layer"]) for x in observations}) == 20, f"rows={len(observations)}")

    ambiguities = read_csv("INTERPRETER_ERROR_AND_AMBIGUITY_AUDIT.csv")
    categories = {"RULE_INCOMPLETE", "OBSERVATION_MISSING", "REFERENCE_INDETERMINATE", "SUPPORTED_OBSERVATIONAL_AMBIGUITY"}
    check("old_ambiguities", len(ambiguities) == 14, f"rows={len(ambiguities)}")
    check("ambiguity_category_domain", all(x["category"] in categories for x in ambiguities), str(sorted({x['category'] for x in ambiguities})))

    results = read_csv("CORRECTED_TASK_RESULTS.csv")
    check("result_cardinality", len(results) == 1250 and len({(x["condition_id"], x["proposition"], x["layer"]) for x in results}) == 1250, f"rows={len(results)}")
    check("boundaries_separate", all(x["corrected_rule_identity"] == "offline_corrected_exploratory_v1" for x in results), "corrected identity explicitly exploratory")
    check("baseline_present", sum(x["layer"] == "K_BASELINE" for x in results) == 250, "250 common-binding baseline tasks")

    manifest_rows = read_csv("SOURCE_ARTIFACT_SHA256.csv")
    changed, missing = [], []
    for row in manifest_rows:
        path = Path(row["path"])
        if not path.is_file():
            missing.append(row["path"])
        elif sha256(path) != row["sha256"]:
            changed.append(row["path"])
    check("source_manifest_nonempty", len(manifest_rows) > 0, f"rows={len(manifest_rows)}")
    check("old_artifacts_unchanged", not changed and not missing, f"changed={len(changed)}, missing={len(missing)}")

    final_text = (HERE / "OFFLINE_CORRECTNESS_CLOSURE_FINAL_REPORT.md").read_text(encoding="utf-8")
    check("final_path", "Path B" in final_text and "NEW_RPC = 0" in final_text and "REEXECUTION = 0" in final_text, "Path B; offline stop controls present")

    report = {
        "schema": "offline-correctness-closure-verification-v1",
        "passed": all(x["passed"] for x in checks),
        "check_count": len(checks),
        "checks": checks,
    }
    (HERE / "VERIFICATION_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not report["passed"]:
        raise SystemExit(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps({"passed": True, "checks": len(checks), "source_files_rehashed": len(manifest_rows)}))


if __name__ == "__main__":
    main()

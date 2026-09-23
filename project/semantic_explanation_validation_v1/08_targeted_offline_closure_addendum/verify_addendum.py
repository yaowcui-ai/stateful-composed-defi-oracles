from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
OLD = ROOT / "semantic_explanation_validation_v1" / "07_offline_correctness_closure_v1"


def rows(name: str):
    with (OUT / name).open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main():
    conditions = rows("ADDENDUM_CONDITION_FIDELITY.csv")
    labels = rows("NONTRIVIAL_LABEL_EVIDENCE_AUDIT.csv")
    manifest = rows("PARENT_CLOSURE_SHA256.csv")
    assert len(conditions) == 50
    assert len(labels) == 250
    assert sum(r["single_condition_fidelity"] == "MATCHED_DESIGN" for r in conditions) == 40
    assert sum(r["single_condition_fidelity"] == "EXECUTION_DEVIATES_FROM_DESIGN" for r in conditions) == 10
    assert len({r["episode_id"] if "episode_id" in r else r["condition_id"][:-1] for r in conditions if r["episode_fidelity"] == "EPISODE_MATCHED_DESIGN"}) == 18
    assert all(r["episode_fidelity"] == "EPISODE_DEVIATES_FROM_DESIGN" for r in conditions if r["condition_id"] in {"AH5A", "AH5B"})
    assert all(next(r for r in conditions if r["condition_id"] == cid)["single_condition_fidelity"] == "EXECUTION_DEVIATES_FROM_DESIGN" for cid in ("AH5A", "AH5B"))
    assert not any(r["evidence_sufficiency"] == "YES" for r in labels)
    assert not any(
        "vesta-protocol-v1/contracts/PriceFeed.sol" in (r["source_binding"] + r["evidence_locator"])
        for r in labels if r["implementation"] == "VESTA"
    )
    assert all(r["harness_only_information"] not in {"", "[]"} for r in labels)
    assert sum(r["claim_scope"] == "ACTUAL_EXECUTION_DESCRIPTION_ONLY" for r in labels) == 50
    assert sum(r["nontrivial"] == "YES" and r["design_fidelity"] == "MATCHED_DESIGN" for r in labels) == 162
    assert sum(r["nontrivial"] == "YES" and r["design_fidelity"] == "MATCHED_DESIGN" and not r["evidence_sufficiency"].startswith("INSUFFICIENT") for r in labels) == 141
    for item in manifest:
        path = ROOT / item["relative_path"]
        assert path.exists(), path
        assert sha(path) == item["sha256"], path
        assert path.stat().st_size == int(item["bytes"]), path
    report = json.loads((OUT / "VERIFICATION_REPORT.json").read_text(encoding="utf-8"))
    assert report["rows"]["matched_episodes"] == 18
    assert report["rows"]["fully_qualified_matched_episodes"] == 15
    assert all(report["checks"].values())
    for required in [
        "README.md", "AH5_GRANULAR_FIDELITY_AUDIT.md", "VESTA_PRICEFEEDV2_SOURCE_BINDING_AUDIT.md",
        "NONTRIVIAL_LABEL_EVIDENCE_AUDIT.csv", "PUBLIC_VS_HARNESS_EVIDENCE_AUDIT.md",
        "FINAL_QUALIFIED_DENOMINATOR_AND_DISPOSITION.md", "ADDENDUM_CONDITION_FIDELITY.csv",
        "PARENT_CLOSURE_SHA256.csv", "VERIFICATION_REPORT.json",
    ]:
        assert (OUT / required).is_file(), required
    print("PASS: 50 conditions; 250 labels; 40 matched; 10 deviated; 33 fully qualified matched conditions; 07 closure hashes unchanged")


if __name__ == "__main__":
    main()

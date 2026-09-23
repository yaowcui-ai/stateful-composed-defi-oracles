# Supplement S1 — reviewer entry point

This package accompanies *Interpreting Stateful and Composed DeFi Oracles: Public Fields, Update Histories, and Temporal Coverage*, JUCS submission version 3. All paths below are relative to this directory. No local RPC service, credential, or author machine is required to inspect the evidence.

[Browser-readable companion](SUPPLEMENT_S1_EXTENDED_TEXT.html) (open locally; equations and figures work offline).

## Read the current result first

1. [Extended methods and complete tables](SUPPLEMENT_S1_EXTENDED_TEXT.md).
2. [Final qualified denominators](project/semantic_explanation_validation_v1/08_targeted_offline_closure_addendum/FINAL_QUALIFIED_DENOMINATOR_AND_DISPOSITION.md).
3. [All 50 conditions](project/semantic_explanation_validation_v1/08_targeted_offline_closure_addendum/ADDENDUM_CONDITION_FIDELITY.csv).
4. [Proposition-by-proposition evidence](project/semantic_explanation_validation_v1/08_targeted_offline_closure_addendum/NONTRIVIAL_LABEL_EVIDENCE_AUDIT.csv).
5. [Earlier field witnesses](project/journal_manuscript_phase/JOURNAL_V0.4_REVIEWER_SUPPLEMENT/g7_field_to_contrast_table.csv) and [all 18 numeric observations](project/journal_manuscript_phase/JOURNAL_V0.4_REVIEWER_SUPPLEMENT/numeric_observation_table.csv).

The controlling follow-up accounting is 50 attempted, 40 design-matched, and 33 fully evidence-qualified conditions; 25 planned, 18 design-matched, and 15 fully qualified comparisons. Aurigami contributes four complete comparisons, Fathom four, Mento four, and Felix three. Seven matched Vesta conditions retain incomplete local exact-source-body support. The included binding metadata does not fill that gap.

## Historical analyses and precedence

The 08 targeted addendum governs qualification, followed by the 07 correctness review. The 04 original analysis and its interpreter results are historical records. The original four coverage percentages, zero-error claim, 14 genuine-ambiguity interpretation, and 21-task trace-exclusive advantage were withdrawn. Post-review rule changes are exploratory. Earlier V0.4 records retain observation-level results with the current source qualifications. Original erroneous classifications remain preserved with their corrections.

## Follow a finding to a witness

| Finding | Conditions | First inspection |
|---|---|---|
| Aurigami stages / selected source | AA2–AA4; AH1–AH4 | Earlier field table; follow-up observations, public records, prefix receipts, exact verified source |
| Fathom validity / evaluation / promotion | FH1, FH2, FH4, FH5; single FH3B | Observation JSON, delayed/latest records, source-call trace, DelayPriceFeedBase source |
| Felix first disable / retained history | XH1, XH2, XH5; single XH3B | Complete return, prefix receipt events, source branch and attributed writes |
| Mento refresh / revalidation | MH1, MH2, MH4, MH5 | Old report, invocation block time, new report, bound expiry source |
| Temporal propagation | Compound, Vetro, Asymmetry; Silo boundary | Numeric observation table, numeric records, correction/recovery notes |

Follow-up observations are in `project/semantic_explanation_validation_v1/03_execution/observations/`. Saved traces and RPC envelopes are in its sibling `traces/` and `raw_rpc/` directories. Large JSON files are losslessly gzip-compressed after any documented transport-path redaction. Use the file map to locate either spelling. Source locator line numbers refer to the copied source text. Relative locators beginning `../` in a follow-up ledger are resolved from `project/semantic_explanation_validation_v1/`.

## Inspect and verify offline

Run `python verify_package.py` from any directory. It verifies distributed hashes, decompressed content hashes, linked entry points, and reference-locator availability. It makes no network requests and runs no scientific experiment or rescoring. `EVIDENCE_FILE_MAP.csv` maps original project-relative identities to distributed files and records original, projected, and distributed SHA-256 values. Endpoint and author-home redactions affect locators or transport configuration; their transformations are explicit. `SHA256SUMS.csv` covers the complete distribution.

Research code is included for inspection with its original provenance. Historical builders and runners can write files or invoke a node; they are not verification entry points. This release supports offline claim inspection, not a promise of one-command historical-fork execution. No secret or archive-provider access is needed for the supplied records.

## Rights and release status

Source headers and adjacent third-party licenses are retained. Author-created research code is released under the MIT License; author-created data are released under CC BY 4.0. Third-party materials retain their original terms and are excluded from these grants. See [license scope](LICENSES.md), [MIT license](LICENSE-MIT.txt), and [data license notice](LICENSE-DATA.md). This prepared package has not been deposited in a public repository or uploaded to the journal. Author identity, funding, competing interests, and author responsibility are stated in the V3 manuscript. The signed publishing agreement is supplied separately using the official V6 (2026) template. The manuscript contains the current AI-use disclosure.

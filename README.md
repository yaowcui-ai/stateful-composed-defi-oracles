# Evidence and code for *Interpreting Stateful and Composed DeFi Oracles*

This repository contains the authors' Supplement S1 for the J.UCS manuscript *Interpreting Stateful and Composed DeFi Oracles: Public Fields, Update Histories, and Temporal Coverage*. It distributes the actual research scripts, fixed experiment records, source and deployment evidence, numeric observations, qualification decisions, and correction trail. The included records support inspection of the reported 33 qualified stateful conditions, 15 complete comparisons, and nine readable temporal observations. These are the reported observation grains, not independent implementation counts.

## Start here

1. Read [README_REVIEWER.md](README_REVIEWER.md) for the current findings, evidence precedence, and links to specific records.
2. Open [SUPPLEMENT_S1_EXTENDED_TEXT.html](SUPPLEMENT_S1_EXTENDED_TEXT.html) locally for extended methods and complete tables, or read its [Markdown source](SUPPLEMENT_S1_EXTENDED_TEXT.md).
3. Run `python verify_package.py` from the repository root. The script checks distributed file hashes, decompressed content hashes, local links, and evidence locators. It makes no network requests and performs no scientific execution or rescoring.

## Where the actual work is

| Material | Location |
|---|---|
| Research execution scripts and dependency manifest | [`project/semantic_explanation_validation_v1/runner/`](project/semantic_explanation_validation_v1/runner/) |
| Analysis code | [`project/semantic_explanation_validation_v1/analysis/`](project/semantic_explanation_validation_v1/analysis/) |
| Saved stateful executions, observations, traces, and RPC evidence | [`project/semantic_explanation_validation_v1/03_execution/`](project/semantic_explanation_validation_v1/03_execution/) |
| Final condition and label qualification | [`project/semantic_explanation_validation_v1/08_targeted_offline_closure_addendum/`](project/semantic_explanation_validation_v1/08_targeted_offline_closure_addendum/) |
| All fixed temporal observations and individual records | [`numeric_observation_table.csv`](project/journal_manuscript_phase/JOURNAL_V0.4_REVIEWER_SUPPLEMENT/numeric_observation_table.csv) and [`numeric_records/`](project/journal_manuscript_phase/JOURNAL_V0.4_REVIEWER_SUPPLEMENT/numeric_records/) |
| Full evidence-file provenance and distribution checksums | [`EVIDENCE_FILE_MAP.csv`](EVIDENCE_FILE_MAP.csv) and [`SHA256SUMS.csv`](SHA256SUMS.csv) |

The package includes historical analyses with superseded classifications. The [current reviewer guide](README_REVIEWER.md) identifies the governing corrections. Offline verification establishes file integrity and locator availability; it does not reproduce the historical-fork experiments. Historical runners may require external chain infrastructure and are provided for inspection.

## Provenance and rights

The repository contents were expanded from the authors' `JUCS_SUPPLEMENT_S1.zip`, SHA-256 `8b671b9b6b6a16816ca999201e8d15fb9a844e41bcbc6c3975c64930d0e8f11e`. The 2,961 entries in [`EVIDENCE_FILE_MAP.csv`](EVIDENCE_FILE_MAP.csv) retain project-relative source paths and original, projected, and distributed hashes. In the current local project, 2,905 distributed entries are byte-identical to their source files; 56 are documented projections or transformations. [SOURCE_PROVENANCE.md](SOURCE_PROVENANCE.md) explains the check.

Author-created research code is under MIT, and author-created data are under CC BY 4.0. Third-party content keeps its original notices and terms. See [LICENSES.md](LICENSES.md) for the exact scope. Some transport-path details in saved evidence were redacted before distribution; the provenance map records those transformations.

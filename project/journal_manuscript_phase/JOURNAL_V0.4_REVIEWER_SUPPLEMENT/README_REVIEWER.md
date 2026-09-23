# Reviewer supplement: interpreting oracle observables

This self-contained evidence layer accompanies the manuscript. It contains no study-author name, home-directory path or private infrastructure endpoint. Protocol names, deployed addresses and third-party source attribution are necessary scientific identifiers and are retained. This is an anonymous review package, not a claimed public repository deposit.

## Start with a claim

| Question | Entry point | Drill-down |
|---|---|---|
| What separates each equal-return pair? | [Field-to-contrast table](g7_field_to_contrast_table.csv) | Named execution_records, normalized_observations.json, trace_archive |
| Are all planned comparisons retained? | [All pairs](g7_predeclared_pair_results.csv) | [All conditions](g7_condition_results.csv), missingness.md |
| How were Y and observations specified? | [Protocol guide](protocol_and_reference_summary/README.md) | Original projected matrix, labels, observation contract and legal histories |
| What is the exact deployment? | [Selected identities](deployment_binding_summary/stateful_selection.json) | stateful_identity_matrix.csv, vesta_implementation.json, source_binding_summary |
| How does temporal coverage differ? | [All numeric observations](numeric_observation_table.csv) | numeric_records and numeric_selection.json |
| Are earlier corrections retained? | [Original policy classifications](policy_original_results.csv) | policy_records, corrections/vesta_review.md, corrections/compound_T2.md |
| Why corrected return decoding? | [Correction](return_decoding_correction.md) | return_decoding_affected_records.csv, trace_archive |

## Reading exact field evidence

The field table has all eleven informative collisions plus two non-collision and two same-Y controls. Its JSON pointers address normalized_observations.json's O2 object; the same pre/post fields appear in execution_records. Decimal integers are strings to prevent precision loss. The Fathom Boolean is retained. A before/after pair within one execution is different from comparing two executions.

For PA03/PA04, reporter/aggregate changes occurred in the legal update prefix, not in getUnderlyingPrice. For PV03, pre-status differs; the pair does not isolate failure cause through one public field. PA07/PV06 show that observation inequality need not mean Y inequality.

## Raw, projected and derived evidence

execution_records, numeric_records and policy_records are redacted projections of retained records: only personal/infrastructure locators are removed. Scientific returns, state values, timestamps, events and original erroneous fields remain. evidence_manifest.csv records original digests and transformations. The derived tables are not presented as byte-identical originals.

trace_archive contains the original twenty trace files compressed losslessly. Decompress a .json.gz to verify its original SHA-256 against evidence_manifest.csv. These traces contain no RPC endpoint; raw RPC transport envelopes and engineering retries remain in the internal archive. Original return bytes are legal; the runner's duplicate prefix is separately retained in execution_records and the correction ledger.

The reviewer layer supports inspection of the main claims. It is not a complete executable replay distribution and does not contain the entire discovery/debug workspace. Source/binding reports provide exact identities and public provenance; no new experiment is required to inspect them.

## Counts and limits

27 planned conditions, 20 valid and 7 technical NC; 21 planned pairs, 15 evaluable and 6 NC. Of 13 different-Y evaluable pairs, 11 collide under full O1 and 2 are non-collision controls. O2 separates the eleven; O3 adds zero. Missingness concentrates in Fathom. O2 singletons do not prove universal semantic identification. No joint multi-input temporal/enforcement path was established.

## Verification and figures

Run `python verify_supplement.py` from any directory with this file set intact. It checks the distributed SHA-256 manifest, all 21 pair relations from normalized tuples, and field-to-contrast values. No RPC or experiment runs. Original trace digests are also checked after in-memory decompression.

Figures are supplied as PDF/SVG and PNG. `python generate_figures.py` regenerates them from figure_source_data using Python and matplotlib; this writes only figure exports. It does not rerun the experiments. Figure data retains units, exact values, evidence tiers and missingness.

The manuscript package ZIP contains the manuscript plus this supplement; keep their relative directory structure when sharing. Package hashes provide integrity, not an independent certification of all scientific interpretations.

# Held-out Semantic Explanation and Boundary Validation

## Scope and accounting

The new phase retained V0.3, V0.4, and all prior frozen evidence unchanged. It bound five deployed implementations, including the three development implementations and two implementations not used in the earlier rule-development evidence. Twenty-five held-out episodes contained 50 designated observations. All 50 were executed successfully and remained comparable. Each observation generated five semantic propositions at four nested observation layers, giving 1,000 interpretation tasks. These tasks are not independent protocol samples and their proportions are not protocol accuracy or ecosystem prevalence.

## Main result

Every possible-label set contained the independently witnessed label. Determinate coverage increased from 132/250 (52.8%) at R to 162/250 (64.8%) at P, 215/250 (86.0%) at H, and 236/250 (94.4%) at X. No layer produced a wrong exclusion or an erroneous singleton after reference adjudication. H remained ambiguous for 35 tasks. X resolved 21 of those tasks, mainly because Felix's non-ABI write evidence separated a healthy oracle evaluation from terminal cached reuse when the complete return and public history collided. Fourteen X tasks remained ambiguous, including 11 Mento state-transition tasks for which the observation contract did not expose the invocation-time relation needed to distinguish a valid refresh from expired-to-valid revalidation.

| Layer | Determinate correct | Ambiguous | Wrong exclusion | Determinate coverage |
|---|---:|---:|---:|---:|
| R | 132 | 118 | 0 | 52.8% |
| P | 162 | 88 | 0 | 64.8% |
| H | 215 | 35 | 0 | 86.0% |
| X | 236 | 14 | 0 | 94.4% |

The strongest per-proposition X results were 49/50 determinate for input acceptance, return source, and updated stage; 50/50 for timestamp meaning; and 39/50 for state transition. Thus a stronger observation layer did not imply universal identification.

## Reference adjudication

The pre-execution Vesta age-boundary prediction for VH1B expected rejection, retained-cache return, status/cache update, and a healthy-to-untrusted transition. The deployed execution instead accepted the controlled input, returned the current value, updated the cache, and retained the healthy state. All four prediction differences were retained as `REFERENCE_ERROR`. The condition was not discarded, relabelled silently, or replaced. This finding narrows the assumed boundary in the development rule rather than constituting an execution failure.

## Field ablation

All ablations retained the complete H baseline as the comparator. Removing raw/aggregate fields reduced determinate return-source judgments to 32/50. Removing status/validity/source fields reduced them to 29/50 and created three erroneous singleton state-transition judgments. Removing time-record fields created five erroneous singleton updated-stage judgments. These results establish dependence only for the frozen rules and validation domain; they do not prove that a field is necessary in every possible implementation.

## Joint-path gate

No bound implementation satisfied all five predeclared temporal/enforcement criteria. E4 therefore closed as `NO_QUALIFIED_JOINT_PATH_NO_REPLACEMENT`. The definition was not weakened and no candidate was replaced after observing results.

## Natural history

Ten adjacent, fixed seven-day windows were retrieved, two per deployment. The Mento root emitted 39,978 logs, all matching event topics observed in the controlled experiment. The other four roots emitted no address-filtered logs in their frozen windows. Empty windows were retained. These data support an actual public-history entry point for Mento, but do not reveal pure reads, internal calls without root logs, or the absence of failures. A 999-height HyperEVM numbering gap was bounded by adjacent existing blocks; the first existing block after the gap was separately queried and emitted no target-root log.

## Independent replay

Five episodes selected by the frozen within-implementation SHA-256 rule (5/25, 20%) were replayed through a separately implemented transcript driver on a fresh Hardhat process. Across 594 RPC operations, all 594 stable semantic projections matched. There were 138 byte-level receipt/trace representation differences due to local block identity and null normalization. These were retained rather than described as byte-exact reproduction. The replay was independently implemented but was not performed by an independent human reviewer, which remains an external-validation limitation.

## Contribution decision

The new evidence moves the stateful contribution beyond pairwise record separation. It tests explicit semantic tasks on held-out conditions, preserves abstention, exposes a reference error, quantifies the incremental roles of public snapshots, public history, and non-ABI execution evidence, and shows an external-history boundary. The contribution remains a finite, deployment-bound empirical characterization. It is not a general decoder, an interface-completeness theorem, a vulnerability result, a protocol-correctness score, or an estimate of ecosystem frequency.

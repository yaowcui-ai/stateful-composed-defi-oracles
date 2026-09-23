# Corrected Summary

## Denominators before performance

- Planned conditions: **50**.
- Design-fidelity conditions: **42/50**.
- Execution deviations: **8/50** (`VH1B`, `VH4A`, `VH4B`, `FH3A`, `MH3A`, `XH3A`, `XH4A`, `XH4B`).
- Technical failures: **0**. All 50 actual calls remain available for descriptive analysis, but the eight deviations are excluded from planned-condition performance.
- Planned-condition task denominator: **42 × 5 propositions = 210 per layer**. Actual-execution descriptive denominator: **50 × 5 = 250 per layer**.

## Prior analysis implementation rescored against reviewed labels

### All actual executions (descriptive only)

| Layer | Tasks | Determinate | Determinate correct | Determinate wrong | Wrong exclusion |
| --- | --- | --- | --- | --- | --- |
| R | 250 | 132 | 130 | 2 | 2 |
| P | 250 | 162 | 160 | 2 | 2 |
| H | 250 | 215 | 212 | 3 | 3 |
| X | 250 | 236 | 233 | 3 | 3 |

### Design-fidelity subset

| Layer | Tasks | Determinate | Determinate correct | Determinate wrong | Wrong exclusion |
| --- | --- | --- | --- | --- | --- |
| R | 210 | 114 | 113 | 1 | 1 |
| P | 210 | 143 | 142 | 1 | 1 |
| H | 210 | 182 | 180 | 2 | 2 |
| X | 210 | 197 | 195 | 2 | 2 |

These are not restored held-out scores: the executable interpreter lacks sufficient pre-execution freeze provenance. They are a retrospective rescore of the retained prior predictions.

## Offline corrected exploratory rules

### All actual executions (descriptive)

| Layer | Tasks | Determinate | Determinate correct | Determinate wrong | Wrong exclusion |
| --- | --- | --- | --- | --- | --- |
| K_BASELINE | 250 | 70 | 70 | 0 | 0 |
| R | 250 | 128 | 128 | 0 | 0 |
| P | 250 | 148 | 148 | 0 | 0 |
| H | 250 | 250 | 250 | 0 | 0 |
| X | 250 | 250 | 250 | 0 | 0 |

### Design-fidelity subset

| Layer | Tasks | Determinate | Determinate correct | Determinate wrong | Wrong exclusion |
| --- | --- | --- | --- | --- | --- |
| K_BASELINE | 210 | 62 | 62 | 0 | 0 |
| R | 210 | 112 | 112 | 0 | 0 |
| P | 210 | 132 | 132 | 0 | 0 |
| H | 210 | 210 | 210 | 0 | 0 |
| X | 210 | 210 | 210 | 0 | 0 |

The corrected H result uses protocol-conformant offline recovery of already-saved prefix logs and primary times; it is not the original normalized H. The corrected rule was authored after seeing results, so its performance is exploratory, not independent validation.

## Per implementation × proposition × layer (design-fidelity subset; corrected exploratory)

| Implementation | Proposition | Layer | N | Determinate | Correct | Wrong determinate | Wrong exclusion |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VESTA | input_acceptance | K_BASELINE | 7 | 0 | 0 | 0 | 0 |
| VESTA | input_acceptance | R | 7 | 0 | 0 | 0 | 0 |
| VESTA | input_acceptance | P | 7 | 0 | 0 | 0 | 0 |
| VESTA | input_acceptance | H | 7 | 7 | 7 | 0 | 0 |
| VESTA | input_acceptance | X | 7 | 7 | 7 | 0 | 0 |
| VESTA | return_source | K_BASELINE | 7 | 0 | 0 | 0 | 0 |
| VESTA | return_source | R | 7 | 0 | 0 | 0 | 0 |
| VESTA | return_source | P | 7 | 0 | 0 | 0 | 0 |
| VESTA | return_source | H | 7 | 7 | 7 | 0 | 0 |
| VESTA | return_source | X | 7 | 7 | 7 | 0 | 0 |
| VESTA | updated_stage | K_BASELINE | 7 | 0 | 0 | 0 | 0 |
| VESTA | updated_stage | R | 7 | 0 | 0 | 0 | 0 |
| VESTA | updated_stage | P | 7 | 0 | 0 | 0 | 0 |
| VESTA | updated_stage | H | 7 | 7 | 7 | 0 | 0 |
| VESTA | updated_stage | X | 7 | 7 | 7 | 0 | 0 |
| VESTA | state_transition | K_BASELINE | 7 | 0 | 0 | 0 | 0 |
| VESTA | state_transition | R | 7 | 0 | 0 | 0 | 0 |
| VESTA | state_transition | P | 7 | 0 | 0 | 0 | 0 |
| VESTA | state_transition | H | 7 | 7 | 7 | 0 | 0 |
| VESTA | state_transition | X | 7 | 7 | 7 | 0 | 0 |
| VESTA | timestamp_meaning | K_BASELINE | 7 | 7 | 7 | 0 | 0 |
| VESTA | timestamp_meaning | R | 7 | 7 | 7 | 0 | 0 |
| VESTA | timestamp_meaning | P | 7 | 7 | 7 | 0 | 0 |
| VESTA | timestamp_meaning | H | 7 | 7 | 7 | 0 | 0 |
| VESTA | timestamp_meaning | X | 7 | 7 | 7 | 0 | 0 |
| AURIGAMI | input_acceptance | K_BASELINE | 10 | 10 | 10 | 0 | 0 |
| AURIGAMI | input_acceptance | R | 10 | 10 | 10 | 0 | 0 |
| AURIGAMI | input_acceptance | P | 10 | 10 | 10 | 0 | 0 |
| AURIGAMI | input_acceptance | H | 10 | 10 | 10 | 0 | 0 |
| AURIGAMI | input_acceptance | X | 10 | 10 | 10 | 0 | 0 |
| AURIGAMI | return_source | K_BASELINE | 10 | 0 | 0 | 0 | 0 |
| AURIGAMI | return_source | R | 10 | 0 | 0 | 0 | 0 |
| AURIGAMI | return_source | P | 10 | 10 | 10 | 0 | 0 |
| AURIGAMI | return_source | H | 10 | 10 | 10 | 0 | 0 |
| AURIGAMI | return_source | X | 10 | 10 | 10 | 0 | 0 |
| AURIGAMI | updated_stage | K_BASELINE | 10 | 10 | 10 | 0 | 0 |
| AURIGAMI | updated_stage | R | 10 | 10 | 10 | 0 | 0 |
| AURIGAMI | updated_stage | P | 10 | 10 | 10 | 0 | 0 |
| AURIGAMI | updated_stage | H | 10 | 10 | 10 | 0 | 0 |
| AURIGAMI | updated_stage | X | 10 | 10 | 10 | 0 | 0 |
| AURIGAMI | state_transition | K_BASELINE | 10 | 10 | 10 | 0 | 0 |
| AURIGAMI | state_transition | R | 10 | 10 | 10 | 0 | 0 |
| AURIGAMI | state_transition | P | 10 | 10 | 10 | 0 | 0 |
| AURIGAMI | state_transition | H | 10 | 10 | 10 | 0 | 0 |
| AURIGAMI | state_transition | X | 10 | 10 | 10 | 0 | 0 |
| AURIGAMI | timestamp_meaning | K_BASELINE | 10 | 0 | 0 | 0 | 0 |
| AURIGAMI | timestamp_meaning | R | 10 | 0 | 0 | 0 | 0 |
| AURIGAMI | timestamp_meaning | P | 10 | 10 | 10 | 0 | 0 |
| AURIGAMI | timestamp_meaning | H | 10 | 10 | 10 | 0 | 0 |
| AURIGAMI | timestamp_meaning | X | 10 | 10 | 10 | 0 | 0 |
| FATHOM | input_acceptance | K_BASELINE | 9 | 0 | 0 | 0 | 0 |
| FATHOM | input_acceptance | R | 9 | 2 | 2 | 0 | 0 |
| FATHOM | input_acceptance | P | 9 | 2 | 2 | 0 | 0 |
| FATHOM | input_acceptance | H | 9 | 9 | 9 | 0 | 0 |
| FATHOM | input_acceptance | X | 9 | 9 | 9 | 0 | 0 |
| FATHOM | return_source | K_BASELINE | 9 | 9 | 9 | 0 | 0 |
| FATHOM | return_source | R | 9 | 9 | 9 | 0 | 0 |
| FATHOM | return_source | P | 9 | 9 | 9 | 0 | 0 |
| FATHOM | return_source | H | 9 | 9 | 9 | 0 | 0 |
| FATHOM | return_source | X | 9 | 9 | 9 | 0 | 0 |
| FATHOM | updated_stage | K_BASELINE | 9 | 0 | 0 | 0 | 0 |
| FATHOM | updated_stage | R | 9 | 2 | 2 | 0 | 0 |
| FATHOM | updated_stage | P | 9 | 2 | 2 | 0 | 0 |
| FATHOM | updated_stage | H | 9 | 9 | 9 | 0 | 0 |
| FATHOM | updated_stage | X | 9 | 9 | 9 | 0 | 0 |
| FATHOM | state_transition | K_BASELINE | 9 | 0 | 0 | 0 | 0 |
| FATHOM | state_transition | R | 9 | 2 | 2 | 0 | 0 |
| FATHOM | state_transition | P | 9 | 2 | 2 | 0 | 0 |
| FATHOM | state_transition | H | 9 | 9 | 9 | 0 | 0 |
| FATHOM | state_transition | X | 9 | 9 | 9 | 0 | 0 |
| FATHOM | timestamp_meaning | K_BASELINE | 9 | 9 | 9 | 0 | 0 |
| FATHOM | timestamp_meaning | R | 9 | 9 | 9 | 0 | 0 |
| FATHOM | timestamp_meaning | P | 9 | 9 | 9 | 0 | 0 |
| FATHOM | timestamp_meaning | H | 9 | 9 | 9 | 0 | 0 |
| FATHOM | timestamp_meaning | X | 9 | 9 | 9 | 0 | 0 |
| MENTO | input_acceptance | K_BASELINE | 9 | 0 | 0 | 0 | 0 |
| MENTO | input_acceptance | R | 9 | 9 | 9 | 0 | 0 |
| MENTO | input_acceptance | P | 9 | 9 | 9 | 0 | 0 |
| MENTO | input_acceptance | H | 9 | 9 | 9 | 0 | 0 |
| MENTO | input_acceptance | X | 9 | 9 | 9 | 0 | 0 |
| MENTO | return_source | K_BASELINE | 9 | 0 | 0 | 0 | 0 |
| MENTO | return_source | R | 9 | 9 | 9 | 0 | 0 |
| MENTO | return_source | P | 9 | 9 | 9 | 0 | 0 |
| MENTO | return_source | H | 9 | 9 | 9 | 0 | 0 |
| MENTO | return_source | X | 9 | 9 | 9 | 0 | 0 |
| MENTO | updated_stage | K_BASELINE | 9 | 0 | 0 | 0 | 0 |
| MENTO | updated_stage | R | 9 | 9 | 9 | 0 | 0 |
| MENTO | updated_stage | P | 9 | 9 | 9 | 0 | 0 |
| MENTO | updated_stage | H | 9 | 9 | 9 | 0 | 0 |
| MENTO | updated_stage | X | 9 | 9 | 9 | 0 | 0 |
| MENTO | state_transition | K_BASELINE | 9 | 0 | 0 | 0 | 0 |
| MENTO | state_transition | R | 9 | 0 | 0 | 0 | 0 |
| MENTO | state_transition | P | 9 | 0 | 0 | 0 | 0 |
| MENTO | state_transition | H | 9 | 9 | 9 | 0 | 0 |
| MENTO | state_transition | X | 9 | 9 | 9 | 0 | 0 |
| MENTO | timestamp_meaning | K_BASELINE | 9 | 0 | 0 | 0 | 0 |
| MENTO | timestamp_meaning | R | 9 | 9 | 9 | 0 | 0 |
| MENTO | timestamp_meaning | P | 9 | 9 | 9 | 0 | 0 |
| MENTO | timestamp_meaning | H | 9 | 9 | 9 | 0 | 0 |
| MENTO | timestamp_meaning | X | 9 | 9 | 9 | 0 | 0 |
| FELIX | input_acceptance | K_BASELINE | 7 | 0 | 0 | 0 | 0 |
| FELIX | input_acceptance | R | 7 | 2 | 2 | 0 | 0 |
| FELIX | input_acceptance | P | 7 | 2 | 2 | 0 | 0 |
| FELIX | input_acceptance | H | 7 | 7 | 7 | 0 | 0 |
| FELIX | input_acceptance | X | 7 | 7 | 7 | 0 | 0 |
| FELIX | return_source | K_BASELINE | 7 | 0 | 0 | 0 | 0 |
| FELIX | return_source | R | 7 | 2 | 2 | 0 | 0 |
| FELIX | return_source | P | 7 | 2 | 2 | 0 | 0 |
| FELIX | return_source | H | 7 | 7 | 7 | 0 | 0 |
| FELIX | return_source | X | 7 | 7 | 7 | 0 | 0 |
| FELIX | updated_stage | K_BASELINE | 7 | 0 | 0 | 0 | 0 |
| FELIX | updated_stage | R | 7 | 2 | 2 | 0 | 0 |
| FELIX | updated_stage | P | 7 | 2 | 2 | 0 | 0 |
| FELIX | updated_stage | H | 7 | 7 | 7 | 0 | 0 |
| FELIX | updated_stage | X | 7 | 7 | 7 | 0 | 0 |
| FELIX | state_transition | K_BASELINE | 7 | 0 | 0 | 0 | 0 |
| FELIX | state_transition | R | 7 | 2 | 2 | 0 | 0 |
| FELIX | state_transition | P | 7 | 2 | 2 | 0 | 0 |
| FELIX | state_transition | H | 7 | 7 | 7 | 0 | 0 |
| FELIX | state_transition | X | 7 | 7 | 7 | 0 | 0 |
| FELIX | timestamp_meaning | K_BASELINE | 7 | 7 | 7 | 0 | 0 |
| FELIX | timestamp_meaning | R | 7 | 7 | 7 | 0 | 0 |
| FELIX | timestamp_meaning | P | 7 | 7 | 7 | 0 | 0 |
| FELIX | timestamp_meaning | H | 7 | 7 | 7 | 0 | 0 |
| FELIX | timestamp_meaning | X | 7 | 7 | 7 | 0 | 0 |

## Coverage disposition counts across all five layers (design-fidelity subset)

| Category | Count |
| --- | --- |
| COMMON_BINDING_ONLY | 386 |
| DIRECT_PUBLIC_FIELD | 60 |
| INDETERMINATE | 324 |
| NOT_APPLICABLE | 56 |
| OBSERVATION_DEPENDENT_INFERENCE | 224 |

Category mapping: `COMMON_BINDING_ONLY` = 仅依赖共同源码/入口知识；`DIRECT_PUBLIC_FIELD` = 直接公开字段读取；`OBSERVATION_DEPENDENT_INFERENCE` = 依赖实际观察的推断；the other requested categories retain their English names.

## Scientific interpretation

The common-binding baseline already determines many entrypoint invariants and NOT_APPLICABLE tasks. P directly resolves Aurigami's selected source/timestamp but does not reconstruct Fathom retrieval acceptance or transitions. Protocol-complete H can reconstruct the tested histories from preserved public evidence. X adds trace-level write attribution, but no independently supported H→X semantic gain remains after restoring H.

# Semantic Label Definitions

## Scope and independence

These labels are retrospective, independently reconstructed labels for the executions that actually occurred. They do not replace `01_protocol/reference.json`, do not alter the frozen factor tables, and are not prospective validation labels. No label below is produced by calling `reference_labels(condition)` or `infer_semantics`.

| Proposition | Exact meaning | Evidence rule |
| --- | --- | --- |
| input_acceptance | Whether the controlled input/source result was evaluated by the designated primary call and accepted, rejected, or not evaluated; a returned validity Boolean is not itself this label. | Bound source + actual receipt/trace/public state; missing evidence remains INDETERMINATE |
| return_source | The semantic source of the designated call's returned price/value, at the controlled leg granularity fixed for the implementation. | Bound source + actual receipt/trace/public state; missing evidence remains INDETERMINATE |
| updated_stage | The target semantic record/stage to which the designated call issued a write; write action is distinguished from observable value change and dependency writes. | Bound source + actual receipt/trace/public state; missing evidence remains INDETERMINATE |
| state_transition | The semantic state immediately before the primary execution time and immediately after it; time passage before the call is not attributed to the call. | Bound source + actual receipt/trace/public state; missing evidence remains INDETERMINATE |
| timestamp_meaning | The event represented by an observed returned/public timestamp, or NOT_APPLICABLE where the implementation exposes no relevant timestamp proposition. | Bound source + actual receipt/trace/public state; missing evidence remains INDETERMINATE |

## Implementation-specific boundaries

- **Vesta:** `input_acceptance` refers to the controlled price leg; the index leg was held valid. `STATUS_AND_CACHE` records the status transition plus the valid index-cache write, while the rejected price cache is retained.
- **Aurigami:** all five labels describe the designated `getUnderlyingPrice` call. Updater calls are prefix witnesses, not updates by the primary call.
- **Fathom:** `peekPrice`'s returned Boolean is `isPriceOk()` after the call. Retrieval invocation, retrieval acceptance, and retained-price validity are separately reconstructed. `readPrice` does not evaluate a new input.
- **Mento:** validity immediately before the report is computed at the report transaction time from the previous reporter timestamp and the per-token expiry. The stale `oldestExpired` pre-getter result is not used as the transition witness.
- **Felix:** `newFailureDetected=true` means a new failure in this call. If already disabled, the oracle is not called and the function returns `(lastGoodPrice,false)`. Target proxy-context writes (trace depth 2 here) are separated from dependency shutdown writes (deeper frames); a write action is not equated with a changed public value.

## Sufficiency rule

A determinate label requires a source binding and a distinct execution witness. Source-only deductions can establish `NOT_APPLICABLE` or entrypoint invariants, but the old interpreter's own prediction is never an independent witness.

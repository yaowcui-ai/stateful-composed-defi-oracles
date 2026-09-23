# Public evidence versus harness information

## Separation rule

Public contract evidence consists of saved ABI returns, public getters, target/dependency receipt logs, transaction identity, and block location. Execution-internal evidence consists of saved traces and is reported separately because it is not a public ABI field. Harness-only information consists of condition names, controlled `setCode`/time/fault parameters, call-purpose annotations, and setup intent in `CALL_LEDGER.jsonl`.

Harness annotations establish what the runner attempted and are useful for describing the actual controlled execution. They do not by themselves prove that the target evaluated or accepted the injected value. That proof requires the exact source branch plus concrete return/event/state/trace evidence.

## Evidence-sufficiency inventory

- `INSUFFICIENT_EXACT_SOURCE_BODY`: 30
- `SUFFICIENT_COMMON_BINDING`: 50
- `SUFFICIENT_CONTEXTUALIZED_TRACE`: 10
- `SUFFICIENT_PUBLIC_EVENT_STATE`: 50
- `SUFFICIENT_PUBLIC_FIELD`: 30
- `SUFFICIENT_RETURN_EVENT_SOURCE`: 30
- `SUFFICIENT_SOURCE_AND_PUBLIC`: 30
- `SUFFICIENT_TRACE_AND_STATE`: 20

`H=100%` or `X=100%` is not a completion criterion. A layer can produce a singleton after using post-hoc rules, omitted prefix recovery, harness metadata, or unattributed SSTOREs. Completion is evaluated per proposition against source identity, execution fidelity, and evidence provenance.

For Fathom, the audit records the actual `retrivePrice()` self-call (`STATICCALL`, pc 1224, depth 2, selector `0x5a0e1bd9`) instead of inferring it only from time arithmetic. For Felix, every SSTORE row contains pc, depth, slot, value, and target-proxy/dependency context. For Mento and Aurigami, named event topics and public records are kept separate from scheduled timestamps and updater/factor annotations.

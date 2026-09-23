# OFFLINE_SEMANTIC_VALIDATION_CORRECTNESS_CLOSURE_V1 — Implementation Plan

## Immutable boundaries

- Offline reads only: source, protocol, ledgers, raw RPC transcripts, receipts, observations, and traces.
- No RPC, fork, transaction, replay, or experiment re-execution.
- No modification of V0.4, V0.5, or any pre-existing protocol, runner, reference, execution, analysis, or report artifact.
- Every correction is emitted only beneath this directory and is identified as retrospective/offline.

## Ordered execution

1. Capture a SHA-256 baseline for the pre-existing scientific artifacts; audit all 50 conditions for design fidelity.
2. Define proposition semantics and derive independent witness labels without calling the old reference-label function.
3. Audit the R/P/H/X contract, recover only already-saved evidence, and record unrecoverable fields.
4. Audit rule provenance, rescore the prior interpreter against the independent labels, and classify error versus ambiguity.
5. Produce condition-by-proposition-by-layer corrected results, including a common-binding-knowledge baseline and separate original/corrected boundaries.
6. Adjudicate the six requested questions and select Path A, B, or C; then stop.

## Verification gates

- Schema/cardinality tests fail before implementation and pass afterward.
- Exactly 50 condition-fidelity rows, with no success inferred merely from non-reversion.
- Every condition–proposition row has proposition meaning, source binding, execution witness, old label, reviewed label, disagreement rationale, and evidence sufficiency.
- Corrected results never merge prospective/frozen and retrospective/exploratory performance.
- Final source-hash comparison shows no protected pre-existing artifact changed.

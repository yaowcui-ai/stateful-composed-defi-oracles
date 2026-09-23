# Offline Semantic Validation Correctness Closure — Final Report

## Executive decision

**Path B — partial evidence is sufficient.** Existing raw material supports a narrower, useful contribution, but not the original zero-error/94.4%/50-of-50 framing and not a prospectively frozen independent rule-validation claim. No new execution is required to establish the narrower findings below. A later targeted re-execution would be needed only if the authors want to restore the failed design contrasts or a genuine held-out rule-performance claim.

## 1. Reliably established new findings

1. Fifty designated primary calls completed technically, but only **42/50** executed the declared intervention. The exact eight deviations are preserved in `CONDITION_FIDELITY_AUDIT.csv`.
2. Full ABI returns have implementation-specific semantic value: Felix's `newFailureDetected=true` directly identifies a new failure branch; Fathom's Boolean is post-call price validity and does **not** by itself identify input acceptance.
3. Aurigami's public source flag directly identifies main versus backup for the designated read, while its updater semantics belong to the prefix window, not the pure primary call.
4. Existing saved public evidence is sufficient to reconstruct Mento validity transitions at the actual report time and to correct the Fathom FH3B timing interpretation.
5. Raw traces support a real distinction between target/proxy-context storage writes and dependency writes, and between a write action and a changed value. The normalized X evidence did not preserve those distinctions.
6. A common-binding-only baseline resolves a material share of tasks; therefore observation-layer contribution must be measured above that baseline rather than against zero knowledge.

## 2. Exploratory observations only

- Performance of `offline_corrected_exploratory_v1`, including its protocol-recovered H results. It was authored after outcomes were visible.
- Rescored performance of the prior executable interpreter. Its predictions are retained, but its executable freeze identity is inadequate for prospective held-out validation.
- The original incomplete-H to X singleton gain (21 tasks). It is reproducible as an analysis artifact, not evidence that complete public history is insufficient.

## 3. Claims that must be withdrawn

- “Four layers have zero errors.”
- “X solves 21 tasks that public history cannot solve.”
- “The 14 X ambiguities are genuine observational ambiguities.”
- “All 50 declared conditions are valid and comparable.”

The “two new independent implementations” claim must be narrowed, and E5/E6 must be limited to log retrievability and transcript replay respectively.

## 4. Problems solvable offline from existing raw evidence

- VH1B's actual age=1 and resulting semantics.
- Aurigami updater order, raw-only versus aggregate prefix, and all setup receipt logs.
- Fathom retrieval eligibility/failure separation, input acceptance versus `isPriceOk`, and validity at primary time.
- Mento pre-report age, inclusive expiry, and report-time transition.
- Felix terminal-prefix identity, SSTORE frame attribution, target versus dependency writes, and same-value cache writes.
- Reclassification of all 14 prior X ambiguities and rescore of every condition/proposition/layer.

## 5. Problems not solvable offline

- The missing Vesta working→untrusted→working long prefixes (VH4A/B) were never executed.
- The intended successful Fathom shared-prestate retrieval (FH3A) was not executed.
- The Mento old-timestamp control (MH3A) was not executed.
- Felix first terminal primary (XH3A) and both non-collision conditions (XH4A/B) were not executed as declared.
- A cryptographically or externally sealed complete executable pre-execution interpreter does not exist in the saved materials; it cannot be manufactured retrospectively.
- No legal same-complete-observation/different-independent-semantics pair establishes `SUPPORTED_OBSERVATIONAL_AMBIGUITY`.

## 6. Does the correction strengthen V0.4's main contribution?

**Yes, but only as a narrowed empirical extension.** The closure adds a defensible taxonomy of what complete returns, public snapshots, recoverable histories, and attributed traces support in these bound executions. It also demonstrates concrete evaluation failure modes: validity/acceptance conflation, observation-time mismatch, omitted prefix history, and unowned SSTORE inference. Those are scientifically useful and align with the manuscript's existing warning that different records do not automatically imply identifiable semantics.

It does **not** support upgrading V0.4 with the previous headline percentages or an independent held-out validation claim. Any later V0.5 revision should use the 42-condition design-fidelity denominator, describe the other eight calls separately, and label corrected-rule results exploratory.

## Selected path and stop condition

**Selected: B — 部分足够.** Recommended next action, requiring separate authorization: narrow the added claim to the reliable findings above and preserve the exact execution gaps. This closure performs no manuscript revision and no targeted re-execution.

```ini
PRIMARY_LINE = COMPLETE
NEW_RPC = 0
REEXECUTION = 0
OLD_ARTIFACT_OVERWRITE = 0
MANUSCRIPT_REVISION = HOLD
PATH = B
NEXT = WAIT_FOR_SEPARATE_AUTHORIZATION
```

# Rule Provenance Audit

## Verdict

`01_protocol/rules_v1.json` has local filesystem timestamps before the first formal execution and declares a field-level rule skeleton. That is evidence of a locally pre-existing specification, but it is not an immutable/external seal and it does not specify complete executable set-valued mappings. The actual executable semantic logic in `analysis/interpreter.py` was modified after formal outputs began, and `analysis/run_analysis.py` was created after execution. Therefore the reported 1,000-task output lacks adequate identity as a prospectively frozen executable held-out validation. It may be retained as the **prior analysis implementation**, not retroactively certified as pre-execution frozen.

## Provenance evidence

| Artifact | Created UTC | Modified UTC | Role |
| --- | --- | --- | --- |
| 01_protocol\rules_v1.json | 2026-09-15T09:56:19.282388+00:00 | 2026-09-15T09:56:19.282388+00:00 | declarative skeleton |
| analysis\interpreter.py | 2026-09-15T09:57:15.813008+00:00 | 2026-09-15T10:56:36.939270+00:00 | executable/output evidence |
| analysis\run_analysis.py | 2026-09-15T10:55:52.761766+00:00 | 2026-09-15T10:56:19.320853+00:00 | executable/output evidence |
| 03_execution\EXPOSURE_LOG.jsonl | 2026-09-15T10:42:23.758806+00:00 | 2026-09-15T10:52:08.376483+00:00 | executable/output evidence |
| 04_analysis\SUMMARY.json | 2026-09-15T10:56:23.910209+00:00 | 2026-09-15T10:56:43.902642+00:00 | executable/output evidence |

## Original versus corrected identity

- **Original rule performance:** rescore the stored predictions in `04_analysis/INTERPRETATION_TASKS.jsonl` against the independent reviewed labels. This measures the prior analysis implementation only.
- **Corrected rule performance:** a separate `offline_corrected_exploratory_v1` analysis using recovered contract-conformant H and trace attribution. It is retrospective and is not a held-out validation.
- No file is backdated, re-labelled as prospectively frozen, or written outside this closure directory.

## Missingness/ablation finding

The old interpreter frequently enters an `else -> NONE` branch when pre/post fields are absent. Thus removing a validity/status field can create a determinate negative rather than uncertainty. This violates the frozen missingness intent. Corrected scoring propagates missing evidence to a set-valued/INDETERMINATE result; absent Boolean values are never coerced to `false`.

## Four-way ambiguity taxonomy

All 14 prior X ambiguities are classified row-by-row in `INTERPRETER_ERROR_AND_AMBIGUITY_AUDIT.csv`. All are `RULE_INCOMPLETE`; none demonstrates `SUPPORTED_OBSERVATIONAL_AMBIGUITY`. No pair of legal, fidelity-matched executions with identical complete allowed observation and independently different reviewed semantics was established.

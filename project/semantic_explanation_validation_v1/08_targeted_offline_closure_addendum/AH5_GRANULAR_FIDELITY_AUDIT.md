# AH5 granular fidelity re-audit

## Decision

AH5A and AH5B are not backup-path conditions. Each designated call technically completed, but each single condition is `EXECUTION_DEVIATES_FROM_DESIGN`; the AH5 episode is `EPISODE_DEVIATES_FROM_DESIGN`.

The runner executes two authorized updater transactions, reads `mainFeed.updatedAt`, and mines at exactly `updatedAt + 7200`. The saved contract source uses `elapsed > validPeriod`, not `>=`, and the saved public configuration is `validPeriod=7200`. Both observations report `_getRawUnderlyingPrice(...).isFromMainFeed=true`. Thus the exact boundary remains main-source-valid.

## Three distinct units

| Unit | AH5A | AH5B | Adjudication |
|---|---|---|---|
| Single condition | planned backup path; actual main aggregate | planned backup path; actual main aggregate | both deviate |
| Episode | required nuisance-shifted equivalent backup path | same episode | episode deviates because the defining mechanism was absent |
| Comparison | actual main path at base time | actual main path shifted by 1000 seconds | supports only an actual main-path time-shift comparison; it is not the planned backup-path comparison |

The pair may be described as two numerically and semantically equivalent main-path executions under an absolute-time shift. It cannot enter the planned-design denominator.

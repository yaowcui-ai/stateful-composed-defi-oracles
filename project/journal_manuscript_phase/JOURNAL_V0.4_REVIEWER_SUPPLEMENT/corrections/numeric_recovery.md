# Post-completion Infrastructure Recovery Final Audit

## Immutable primary layer

- `T0_PRIMARY = IMMUTABLE`
- `T1_PRIMARY = IMMUTABLE`
- Original T0/T1 scientific result files remain the `AS_EXECUTED_PRIMARY` layer.
- Recovery results are reported separately as `INFRASTRUCTURE_RECOVERED_SECONDARY` and do not overwrite primary execution.

## Frozen recovery denominator and outcome

- Eligible observations: **5**
- Recovered `COMPLETE`: **4**
- Remaining `MISSING`: **0**
- Contract-level `REVERT` reached through the frozen fallback transport: **1**
- `BINDING_OR_SEMANTICS_REVIEW`: **0**
- Prediction agreement among complete recoveries: **4/4**
- Formula replay agreement among complete recoveries: **4/4**
- All defined recovery gaps, without filtering: **[0, 0, 0, 0] seconds**

The four complete Ethereum recoveries used the frozen BlastAPI fallback after the primary provider returned HTTP 403. Vetro and Asymmetry both preserved the source-predicted oldest-required-constituent timestamp and produced a signed gap of 0 seconds at T0 and T1.

The T1 Silo Arbitrum observation was eligible because the primary provider lacked historical state. The initial recovery runner did not continue to the frozen fallback because it failed to recognize the provider wording `metadata is not found` as historical-state unavailability. This was recorded as an execution implementation issue; the initial recovery artifact remains unchanged. Append-only Correction 001 fixed only that classifier token and retried the same root, inputs, calldata semantics, block number, and block hash. The frozen Nodies fallback verified the exact original block hash and returned a genuine EVM execution revert. The final secondary classification is therefore `REVERT`, not `MISSING`, and no further provider was added or attempted.

## Integrity and stop state

- Protocol, Schedule Amendment 001, and Transport Amendment 002 hashes: verified.
- Recovery endpoint order and retry rules: unchanged.
- T2 output files: **0**.
- `T2 = PENDING`.
- No T2 execution was performed.

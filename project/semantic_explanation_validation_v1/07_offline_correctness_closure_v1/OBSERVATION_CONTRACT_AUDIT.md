# Observation Contract Audit

## Finding

The frozen contract defined H as including the call prefix and event history, but `primaryTx` stored only the designated transaction receipt logs and `primaryPure` stored an empty list. Setup/prefix receipts were preserved in raw RPC transcripts and can be recovered offline. This report calls that **protocol-conformant offline recovery**, not the original H observation. Original H remains unchanged.

## R/P/H/X implementation audit

| Layer | Protocol | Runner | Correction boundary |
| --- | --- | --- | --- |
| R | complete return/revert | decoded return; no visible revert rows because all designated calls completed | no recovery |
| P | R + declared public post-state | collected declared post getters | direct fields retained |
| H | P + pre-state + call prefix + event history | pre getters + only primary receipt logs | recover prefix/setup receipts and scheduled primary time from saved raw transcripts; do not overwrite H |
| X | H + same-invocation trace + frozen non-ABI state | trace pointer/summary + SSTORE pc/stack tail | raw trace restores depth/storage snapshots; attribution remains retrospective |

## Mento timing

`evm_setNextBlockTimestamp(t)` scheduled the report transaction, but the pre getter calls executed against the previously mined block. Therefore `pre_public.oldestExpired=false` is not the validity immediately before the report at `t`. Existing evidence is sufficient offline: previous reporter timestamp, post reporter timestamp (= transaction time for these successful reports), per-token expiry 360, receipts, and saved time-control calls. The corrected transition uses `primary_time - previous_report_timestamp >= expiry`.

## X ownership and write semantics

For Felix, raw traces show healthy calls writing the cache at depth 2 even when the value is unchanged. Failure calls contain a depth-2 target/proxy-context disable write and a deeper dependency shutdown write. The normalized X array removed depth/address and the old interpreter used only “any SSTORE”; that test cannot by itself identify source, target, or value change. Proxy `DELEGATECALL` execution writes proxy storage, not the implementation account.

## Observation times

- Public `pre` getters: last already-mined block, sometimes earlier than the scheduled primary time.
- Primary transaction: next block at the saved controlled timestamp.
- Public `post` getters: after the primary receipt at the primary block state.
- Pure-call conditions: prefix transactions/time-control were mined first; the designated `eth_call` has no receipt and no primary logs.

No unavailable evidence was synthesized and no RPC was issued.

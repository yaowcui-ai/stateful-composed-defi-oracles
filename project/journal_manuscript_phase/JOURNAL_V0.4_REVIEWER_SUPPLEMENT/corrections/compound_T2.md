# Compound T2 Analysis Correction 001

## Status

```text
CORRECTION_TYPE = APPEND_ONLY_DERIVED_ANALYSIS
NEW_RPC_CALLS = 0
ORIGINAL_T2_RESULTS_MODIFIED = false
ORIGINAL_T2_COMPLETION_MODIFIED = false
VERIFICATION = PASS
```

This correction uses only the frozen T2 raw evidence. It does not change the selected family, root, block, snapshot, inputs, timestamp semantics, age calculation, or gap calculation.

## Original record

```text
snapshot = T2
family = COMPOUND_MULTIPLICATIVE_PRICE_FEED
protocol = compound-finance
chain = 8453
root = 0x4687670f5f01716faa382e2356c103bad776752c
block = 51214326
block hash = 0x099f944561d8a5da37008d09b4abd2cac9b70aa6657f22764caf93bde5a9d67d

original formula_replay_answer = null
original formula_replay_agreement = false
original classification = BINDING_OR_SEMANTICS_REVIEW
```

The original files remain immutable:

```text
[archival locator withheld]
[archival locator withheld]
```

## Root cause

T2 used `t2_transport_runner.py`, which delegates a successful fixed-block read to `infrastructure_recovery._measure_root()`. That function initialized `replay = None` and provided family-specific replay branches for Vetro, Asymmetry, and Silo, but not Compound. It then evaluated:

```python
formula_ok = replay == root_round["answer"]
```

For Compound, `None == 288564177591` evaluated false. The resulting mismatch was a runner branch omission, not an observed deployed-formula mismatch.

The ordinary snapshot collector, `numeric_collector.py`, contains the expected Compound branch and calls `replay_compound(...)`. Among the four fixed numeric families, no other transport-runner family-specific replay branch is missing: Vetro, Asymmetry, and Silo are present. This statement is limited to the fixed four-family denominator.

## Frozen raw decoding audit

Raw evidence:

```text
[archival locator withheld]
SHA-256 = 54ED4507B78E66D94C535CB9070D7C8732A6ADF1362288C329E47C9EAAD3F52C
```

Independent ABI word decoding of the recorded `latestRoundData()` and `decimals()` returns produced:

| Role | Address | Answer | Decimals | `updatedAt` |
|---|---|---:|---:|---:|
| Root | `0x4687670f5f01716faa382e2356c103bad776752c` | 288,564,177,591 | 8 | 1,789,217,941 |
| Required input A | `0x806b4ac04501c29769051e42783cf04dce41440b` | 1,138,880,907,015,225,000 | 18 | 1,789,136,219 |
| Required input B | `0x71041dddad3595f9ced3dccfbe3d1f4b0a16bb70` | 253,375,200,000 | 8 | 1,789,217,941 |

The two required-input identities match the pre-measurement root manifest, the Compound qualification record, and the configuration-only immutable getter evidence. Both dependency sources are bound as `EACAggregatorProxy` inputs. The source-bound `MultiplicativePriceFeed` computes from both inputs and propagates feed-B round/timestamp fields.

## Decimal and integer replay audit

The deployed source formula is:

```text
price = priceA × priceB × 10^rootDecimals
        / 10^(decimalsA + decimalsB)
```

With root decimals 8, input decimals 18 and 8:

```text
floor(
  1,138,880,907,015,225,000
  × 253,375,200,000
  × 10^8
  / 10^(18 + 8)
)

= floor(
  1,138,880,907,015,225,000
  × 253,375,200,000
  / 10^18
)

= 288,564,177,591
```

Exact recorded root answer:

```text
288,564,177,591
```

The integer values are exactly equal. No floating-point arithmetic or rounding tolerance was used.

## Corrected derived status

```text
timestamp prediction = MATCH
formula replay = MATCH_AFTER_ANALYSIS_CORRECTION

reported_age = 58 s                 unchanged
effective_age = 81,780 s            unchanged
signed temporal_age_gap = 81,722 s  unchanged

original execution record = BINDING_OR_SEMANTICS_REVIEW
derived paper status = VALID_AFTER_APPEND_ONLY_ANALYSIS_CORRECTION
```

## Impact on claims

- The correction removes the apparent Compound T2 formula mismatch from the derived paper evidence.
- It does not alter the observed timestamp relationship, ages, or signed gap.
- It does not alter T0/T1/T2 denominators or any original execution record.
- It supports bounded use of Compound T2 as an analysis-corrected existing-evidence observation, with the correction disclosed.
- It does not establish a bug or vulnerability in Compound and does not broaden ecosystem-level claims.

## Evidence and code hashes

```text
infrastructure_recovery.py
7D3C3569A8FB32E41D7D305467DEFE734013B2A468D88D0BC4D488B3666EE6D2

numeric_collector.py
43FCF96F5144443F19E8501968EDBFBA2F03F8A2C54AB7F29423220EAFCD2ED4

t2_transport_runner.py
FDD788128A94AE0D8B7A116842B835A2E33734F502639A691246ACA61BD1FFCE

ROOT_PATH_SELECTION_MANIFEST.json
8A9A21C4CA9338A6D3B6C904EDAD48D95DCA62B557DA79FA6FE164AA013319AF

MultiplicativePriceFeed.sol
9092652FDCC5DE4EE67A91F775C13BC9D74EB58241F17DB3199D224332EB55C6
```

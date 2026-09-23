# Vesta Post-Execution Binding and Classifier Review 001

## Scope and status

This is an append-only correctness review of frozen records `VE06`, `VE07`, and `VE10`. No formal scenario was rerun, no D output was added, and the frozen protocol/reference and original execution records remain unchanged.

## Exact implementation binding

The frozen root `0xC934...6702` is a proxy. Every Vesta trace delegates to implementation `0x522808d93Ac229CEfc17c4BE0408520f7e27D26d` (5,652 runtime bytes; SHA-256 `F7CA795217706A4D46FD54525F357C997C0FB68C0383426046B9A4C05E6CB9E1`). The repository deployment file also identifies this implementation. Its verified source is `PriceFeedV2.sol`, not the `PriceFeed.sol` file used to construct the frozen Vesta reference.

In exact `PriceFeedV2`, the price leg is classified broken when its response is broken **or frozen**. The index leg is classified broken only when its response/current-previous-round structure is broken; it does not apply the 14,400-second frozen-age predicate to the index response. The frozen F/R therefore imposed a deployed index-age obligation that does not exist on this implementation.

## Record-level adjudication

- **VE06:** original `INCOMPATIBLE` is preserved. Derived status is `NOT_COMPARABLE_REFERENCE_BINDING_ERROR`; the observed current return is source-consistent, but a post-hoc corrected reference is not treated as an independent formal comparison.
- **VE07:** original `INCOMPATIBLE` is preserved. Derived status is `NOT_COMPARABLE_REFERENCE_BINDING_ERROR`; the exact implementation accepts the otherwise-valid index leg and combines it with cached price when the price leg is frozen.
- **VE10:** original `INCOMPATIBLE` is preserved. The value-first action classifier could not distinguish current from mixed provenance after VE10.1 had set both caches to the same controlled value. The frozen trace shows the price call reverting, index calls succeeding, and status changing from working (0) to untrusted (1). Derived action is `NORMAL_TO_DEGRADED_TRANSITION`, and derived comparison is `COMPATIBLE_AFTER_ACTION_CLASSIFIER_CORRECTION`.

## Claim boundary

The execution does not support a deployed-policy incompatibility or vulnerability claim for Vesta. It supports a narrower factual statement: the exact deployed V2 path treats index-feed call/round validity and index-feed age differently, and return provenance can be state-dependent even when numeric return values collide.

# G3 Fathom source/runtime correspondence

## Result

`EXECUTABLE_RUNTIME_EXACT_FULL_ARTIFACT_METADATA_DIFFERENT`

- Bound implementation: `0x6d19ee49ea1d811197a446f9275c5eda943f0013`
- Historical source commit: `4313db2aee6f5ea7d997acc6f6f67f94a7457f53` (2023-11-02)
- Compiler: Solidity 0.8.17, optimizer 200, EVM Istanbul
- Deployed runtime: 8292 bytes, SHA-256 `EF603DE6D8B2A4F1FB6CB5C54A0833C69B6F6C030D057CAE4EE4C4E41A15CB38`
- Historical compiled runtime: 8292 bytes, SHA-256 `232806875D142801E1C9367998AF47A287C4871C63BAA6AB595B4B7A95F644CD`
- Executable runtime byte-identical after stripping Solidity CBOR metadata: **true**
- Full artifact byte-identical: **false**
- First full-artifact difference: byte 8249; both metadata trailers are 53 bytes

The current repository commit used in G2 compiles to 8338 bytes and does not match the deployed executable because it fixes `retrivePrice()` to `retrievePrice()`. The deployment-era commit compiles to the same 8292-byte shape and reproduces every executable byte. Only the non-executed IPFS metadata hash differs, so this is sufficient to bind executable semantics but is explicitly not a full artifact identity claim.

The bound dependency is independently closed as `SlidingWindowDexOracle`: proxy `0xb2df...d7ca` dispatches to `0x41e2...7edd`; its 4697-byte deployed runtime also matches the deployment-era compiled executable byte-for-byte after metadata removal. Bound configuration is `windowSize=1800`, `granularity=15`, `periodSize=120`; `update(address,address)` is public.

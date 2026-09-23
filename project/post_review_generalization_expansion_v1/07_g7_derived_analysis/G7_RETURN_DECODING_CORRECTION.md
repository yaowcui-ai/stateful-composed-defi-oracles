# G7 return decoding correction

Status: DERIVED_ANALYSIS_CORRECTION. No new execution.

The runner traceTx/traceCall prepended `0x` to an already prefixed returnValue. All 20 valid deployed records contain the duplicate-prefix wrapper; ten pure-call records also record decode_error. Every corresponding frozen trace has legal ABI return bytes and matches a raw RPC trace record. The CSV lists every affected record, original field/error, original trace bytes, full corrected tuple, raw locator and trace digest. G6 files, errors and RPC/trace bytes remain unchanged.

Fathom FC0/FC1 preserve `(27936237197953895,true)`; FC2/FC3 preserve the single price tuple. Other records have one uint256 result. No correction to target execution, input, time, reference, selected pair or scenario was made.

This correction is separate from Compound T2 formula replay and the earlier VE10 action classifier correction. It changes evidence representation, not deployed behavior.

Affected IDs: VA0, VA1, VA2, VA3, VA4, VB0, VB1, VB2, AA0, AA1, AA2, AA3, AA4, AB0, AB1, AB2, FC0, FC1, FC2, FC3.

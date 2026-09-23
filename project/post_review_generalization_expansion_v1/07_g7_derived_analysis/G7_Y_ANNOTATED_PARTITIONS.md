# Y-annotated finite partitions

O1 is the full G4 return tuple, including Fathom boolean. No cross-ABI scalarization. O2 events omit transaction/block identity and retain ordered topics/data. O3 uses collected opcode trace with empty nonpublic storage.

| Layer | Implementation | Members | Y labels |
|---|---|---|---|
| O1 | VESTA | VA0;VA1;VA2;VA3;VA4;VB2 | [{"input_acceptance":"BOTH_LEGS_ACCEPTED","return_source":"CURRENT_PRICE_X_CURRENT_INDEX","transition":"UNTRUSTED_TO_WORKING"},{"input_acceptance":"BOTH_LEGS_ACCEPTED","return_source":"CURRENT_PRICE_X_CURRENT_INDEX","transition":"WORKING_REFRESH"},{"input_acceptance":"PRICE_CALL_FAILED_INDEX_ACCEPTED","return_source":"CACHED_PRICE_X_CURRENT_INDEX","transition":"UNTRUSTED_UNCHANGED"},{"input_acceptance":"PRICE_REJECTED_INDEX_ACCEPTED","return_source":"CACHED_PRICE_X_CURRENT_INDEX","transition":"WORKING_TO_UNTRUSTED"}] |
| O1 | VESTA | VB0;VB1 | [{"input_acceptance":"BOTH_LEGS_ACCEPTED","return_source":"CURRENT_PRICE_X_CURRENT_INDEX","transition":"WORKING_REFRESH"},{"input_acceptance":"PRICE_REJECTED_INDEX_ACCEPTED","return_source":"CACHED_PRICE_X_CURRENT_INDEX","transition":"WORKING_TO_UNTRUSTED"}] |
| O1 | AURIGAMI | AA0;AA1;AA2;AA3;AA4;AB1;AB2 | [{"input_acceptance":"NO_REPORT_INPUT_AT_READ","return_source":"BACKUP_FEED","transition":"PERSISTED_STATE_UNCHANGED"},{"input_acceptance":"NO_REPORT_INPUT_AT_READ","return_source":"MAIN_AGGREGATE","transition":"PERSISTED_STATE_UNCHANGED"},{"input_acceptance":"ONE_REPORT_ACCEPTED_AGGREGATE_NOT_REFRESHED","return_source":"BACKUP_FEED","transition":"RAW_ONLY_UPDATED"},{"input_acceptance":"TWO_REPORTS_ACCEPTED_AGGREGATE_REFRESHED","return_source":"MAIN_AGGREGATE","transition":"MAIN_REFRESHED"}] |
| O1 | AURIGAMI | AB0 | [{"input_acceptance":"TWO_REPORTS_ACCEPTED_AGGREGATE_REFRESHED","return_source":"MAIN_AGGREGATE","transition":"MAIN_REFRESHED"}] |
| O1 | FATHOM | FC0;FC1 | [{"input_acceptance":"REFRESH_NOT_ELIGIBLE","return_source":"DELAYED_RECORD","transition":"UNCHANGED_NOT_ELIGIBLE"},{"input_acceptance":"SOURCE_RETRIEVAL_ACCEPTED","return_source":"DELAYED_RECORD","transition":"PROMOTE_EQUAL_VALUE"}] |
| O1 | FATHOM | FC2;FC3 | [{"input_acceptance":"SOURCE_NOT_EVALUATED_RETAINED_STALE","return_source":"DELAYED_RECORD","transition":"PURE_READ_UNCHANGED"},{"input_acceptance":"SOURCE_NOT_EVALUATED_RETAINED_VALID","return_source":"DELAYED_RECORD","transition":"PURE_READ_UNCHANGED"}] |
| O2 | VESTA | VA0 | [{"input_acceptance":"BOTH_LEGS_ACCEPTED","return_source":"CURRENT_PRICE_X_CURRENT_INDEX","transition":"WORKING_REFRESH"}] |
| O2 | VESTA | VA1 | [{"input_acceptance":"BOTH_LEGS_ACCEPTED","return_source":"CURRENT_PRICE_X_CURRENT_INDEX","transition":"WORKING_REFRESH"}] |
| O2 | VESTA | VA2 | [{"input_acceptance":"PRICE_REJECTED_INDEX_ACCEPTED","return_source":"CACHED_PRICE_X_CURRENT_INDEX","transition":"WORKING_TO_UNTRUSTED"}] |
| O2 | VESTA | VA3 | [{"input_acceptance":"PRICE_CALL_FAILED_INDEX_ACCEPTED","return_source":"CACHED_PRICE_X_CURRENT_INDEX","transition":"UNTRUSTED_UNCHANGED"}] |
| O2 | VESTA | VA4 | [{"input_acceptance":"BOTH_LEGS_ACCEPTED","return_source":"CURRENT_PRICE_X_CURRENT_INDEX","transition":"UNTRUSTED_TO_WORKING"}] |
| O2 | VESTA | VB0 | [{"input_acceptance":"BOTH_LEGS_ACCEPTED","return_source":"CURRENT_PRICE_X_CURRENT_INDEX","transition":"WORKING_REFRESH"}] |
| O2 | VESTA | VB1 | [{"input_acceptance":"PRICE_REJECTED_INDEX_ACCEPTED","return_source":"CACHED_PRICE_X_CURRENT_INDEX","transition":"WORKING_TO_UNTRUSTED"}] |
| O2 | VESTA | VB2 | [{"input_acceptance":"BOTH_LEGS_ACCEPTED","return_source":"CURRENT_PRICE_X_CURRENT_INDEX","transition":"UNTRUSTED_TO_WORKING"}] |
| O2 | AURIGAMI | AA0 | [{"input_acceptance":"TWO_REPORTS_ACCEPTED_AGGREGATE_REFRESHED","return_source":"MAIN_AGGREGATE","transition":"MAIN_REFRESHED"}] |
| O2 | AURIGAMI | AA1 | [{"input_acceptance":"NO_REPORT_INPUT_AT_READ","return_source":"MAIN_AGGREGATE","transition":"PERSISTED_STATE_UNCHANGED"}] |
| O2 | AURIGAMI | AA2 | [{"input_acceptance":"NO_REPORT_INPUT_AT_READ","return_source":"BACKUP_FEED","transition":"PERSISTED_STATE_UNCHANGED"}] |
| O2 | AURIGAMI | AA3 | [{"input_acceptance":"ONE_REPORT_ACCEPTED_AGGREGATE_NOT_REFRESHED","return_source":"BACKUP_FEED","transition":"RAW_ONLY_UPDATED"}] |
| O2 | AURIGAMI | AA4 | [{"input_acceptance":"TWO_REPORTS_ACCEPTED_AGGREGATE_REFRESHED","return_source":"MAIN_AGGREGATE","transition":"MAIN_REFRESHED"}] |
| O2 | AURIGAMI | AB0 | [{"input_acceptance":"TWO_REPORTS_ACCEPTED_AGGREGATE_REFRESHED","return_source":"MAIN_AGGREGATE","transition":"MAIN_REFRESHED"}] |
| O2 | AURIGAMI | AB1 | [{"input_acceptance":"NO_REPORT_INPUT_AT_READ","return_source":"BACKUP_FEED","transition":"PERSISTED_STATE_UNCHANGED"}] |
| O2 | AURIGAMI | AB2 | [{"input_acceptance":"TWO_REPORTS_ACCEPTED_AGGREGATE_REFRESHED","return_source":"MAIN_AGGREGATE","transition":"MAIN_REFRESHED"}] |
| O2 | FATHOM | FC0 | [{"input_acceptance":"REFRESH_NOT_ELIGIBLE","return_source":"DELAYED_RECORD","transition":"UNCHANGED_NOT_ELIGIBLE"}] |
| O2 | FATHOM | FC1 | [{"input_acceptance":"SOURCE_RETRIEVAL_ACCEPTED","return_source":"DELAYED_RECORD","transition":"PROMOTE_EQUAL_VALUE"}] |
| O2 | FATHOM | FC2 | [{"input_acceptance":"SOURCE_NOT_EVALUATED_RETAINED_VALID","return_source":"DELAYED_RECORD","transition":"PURE_READ_UNCHANGED"}] |
| O2 | FATHOM | FC3 | [{"input_acceptance":"SOURCE_NOT_EVALUATED_RETAINED_STALE","return_source":"DELAYED_RECORD","transition":"PURE_READ_UNCHANGED"}] |
| O3 | VESTA | VA0 | [{"input_acceptance":"BOTH_LEGS_ACCEPTED","return_source":"CURRENT_PRICE_X_CURRENT_INDEX","transition":"WORKING_REFRESH"}] |
| O3 | VESTA | VA1 | [{"input_acceptance":"BOTH_LEGS_ACCEPTED","return_source":"CURRENT_PRICE_X_CURRENT_INDEX","transition":"WORKING_REFRESH"}] |
| O3 | VESTA | VA2 | [{"input_acceptance":"PRICE_REJECTED_INDEX_ACCEPTED","return_source":"CACHED_PRICE_X_CURRENT_INDEX","transition":"WORKING_TO_UNTRUSTED"}] |
| O3 | VESTA | VA3 | [{"input_acceptance":"PRICE_CALL_FAILED_INDEX_ACCEPTED","return_source":"CACHED_PRICE_X_CURRENT_INDEX","transition":"UNTRUSTED_UNCHANGED"}] |
| O3 | VESTA | VA4 | [{"input_acceptance":"BOTH_LEGS_ACCEPTED","return_source":"CURRENT_PRICE_X_CURRENT_INDEX","transition":"UNTRUSTED_TO_WORKING"}] |
| O3 | VESTA | VB0 | [{"input_acceptance":"BOTH_LEGS_ACCEPTED","return_source":"CURRENT_PRICE_X_CURRENT_INDEX","transition":"WORKING_REFRESH"}] |
| O3 | VESTA | VB1 | [{"input_acceptance":"PRICE_REJECTED_INDEX_ACCEPTED","return_source":"CACHED_PRICE_X_CURRENT_INDEX","transition":"WORKING_TO_UNTRUSTED"}] |
| O3 | VESTA | VB2 | [{"input_acceptance":"BOTH_LEGS_ACCEPTED","return_source":"CURRENT_PRICE_X_CURRENT_INDEX","transition":"UNTRUSTED_TO_WORKING"}] |
| O3 | AURIGAMI | AA0 | [{"input_acceptance":"TWO_REPORTS_ACCEPTED_AGGREGATE_REFRESHED","return_source":"MAIN_AGGREGATE","transition":"MAIN_REFRESHED"}] |
| O3 | AURIGAMI | AA1 | [{"input_acceptance":"NO_REPORT_INPUT_AT_READ","return_source":"MAIN_AGGREGATE","transition":"PERSISTED_STATE_UNCHANGED"}] |
| O3 | AURIGAMI | AA2 | [{"input_acceptance":"NO_REPORT_INPUT_AT_READ","return_source":"BACKUP_FEED","transition":"PERSISTED_STATE_UNCHANGED"}] |
| O3 | AURIGAMI | AA3 | [{"input_acceptance":"ONE_REPORT_ACCEPTED_AGGREGATE_NOT_REFRESHED","return_source":"BACKUP_FEED","transition":"RAW_ONLY_UPDATED"}] |
| O3 | AURIGAMI | AA4 | [{"input_acceptance":"TWO_REPORTS_ACCEPTED_AGGREGATE_REFRESHED","return_source":"MAIN_AGGREGATE","transition":"MAIN_REFRESHED"}] |
| O3 | AURIGAMI | AB0 | [{"input_acceptance":"TWO_REPORTS_ACCEPTED_AGGREGATE_REFRESHED","return_source":"MAIN_AGGREGATE","transition":"MAIN_REFRESHED"}] |
| O3 | AURIGAMI | AB1 | [{"input_acceptance":"NO_REPORT_INPUT_AT_READ","return_source":"BACKUP_FEED","transition":"PERSISTED_STATE_UNCHANGED"}] |
| O3 | AURIGAMI | AB2 | [{"input_acceptance":"TWO_REPORTS_ACCEPTED_AGGREGATE_REFRESHED","return_source":"MAIN_AGGREGATE","transition":"MAIN_REFRESHED"}] |
| O3 | FATHOM | FC0 | [{"input_acceptance":"REFRESH_NOT_ELIGIBLE","return_source":"DELAYED_RECORD","transition":"UNCHANGED_NOT_ELIGIBLE"}] |
| O3 | FATHOM | FC1 | [{"input_acceptance":"SOURCE_RETRIEVAL_ACCEPTED","return_source":"DELAYED_RECORD","transition":"PROMOTE_EQUAL_VALUE"}] |
| O3 | FATHOM | FC2 | [{"input_acceptance":"SOURCE_NOT_EVALUATED_RETAINED_VALID","return_source":"DELAYED_RECORD","transition":"PURE_READ_UNCHANGED"}] |
| O3 | FATHOM | FC3 | [{"input_acceptance":"SOURCE_NOT_EVALUATED_RETAINED_STALE","return_source":"DELAYED_RECORD","transition":"PURE_READ_UNCHANGED"}] |

All O2/O3 classes are singleton in the observed matrix. This is descriptive, not a semantic identification theorem. PV06/PA07 are counterexamples to equating observation distinction with Y distinction.

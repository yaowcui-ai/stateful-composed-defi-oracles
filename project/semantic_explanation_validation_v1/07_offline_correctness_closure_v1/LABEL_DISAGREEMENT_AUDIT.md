# Label Disagreement Audit

Independent reconstruction found **7 disagreements with the frozen reference across 250 condition–proposition labels**. The old labels and the later prior-witness labels remain unchanged in their original files.

| Condition | Proposition | Original | Reviewed | Reason |
| --- | --- | --- | --- | --- |
| VH1B | input_acceptance | REJECTED | ACCEPTED | The frozen reference followed the planned theta+1 factor, but the runner configured actual age=1. This is EXECUTION_DEVIATES_FROM_DESIGN, not a reference-rule error. |
| VH1B | return_source | RETAINED_CACHE | CURRENT_INPUT | The frozen reference followed the planned theta+1 factor, but the runner configured actual age=1. This is EXECUTION_DEVIATES_FROM_DESIGN, not a reference-rule error. |
| VH1B | updated_stage | STATUS_AND_CACHE | CACHE | The frozen reference followed the planned theta+1 factor, but the runner configured actual age=1. This is EXECUTION_DEVIATES_FROM_DESIGN, not a reference-rule error. |
| VH1B | state_transition | HEALTHY_TO_UNTRUSTED | NONE | The frozen reference followed the planned theta+1 factor, but the runner configured actual age=1. This is EXECUTION_DEVIATES_FROM_DESIGN, not a reference-rule error. |
| FH1A | input_acceptance | ACCEPTED | NOT_EVALUATED | primary=peekPrice() except FH5A/B readPrice() [eth_call]; eligibility/retrieval witness called=False, succeeded=False; return isPriceOk=True is kept separate |
| FH3A | input_acceptance | ACCEPTED | NOT_EVALUATED | primary=peekPrice() except FH5A/B readPrice() [eth_call]; eligibility/retrieval witness called=False, succeeded=False; return isPriceOk=True is kept separate |
| FH3B | state_transition | VALID_TO_INVALID | NONE | primary_time=1789374241, delayed_timestamp_pre=1789370640, priceLife=3600, validity immediately-before=False, post=False |

VH1B is an execution deviation, not a reference-label mistake: age=1 was actually executed, so its reviewed execution label is accepted/current. Fathom disagreements arise from conflating `isPriceOk` with input acceptance and from measuring pre-validity before the scheduled primary block existed.

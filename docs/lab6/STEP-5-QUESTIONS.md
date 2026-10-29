# Part 4 Step 5 — four Moodle questions

Answers use five real Nova Converse outputs in evidence/nova-five-real.jsonl. Claude
Opus/Haiku remain account-blocked; Nova is a disclosed substitute requiring instructor
acceptance. These are local Docker measurements; no CloudWatch/deployment is claimed.

## 1. Which of the five went wrong, and why? Which change fixes it: prompt, schema, validation, or UI?

Ukrainian and English preserved the explicit topic, owner, duration, action and date.
Relative dates passed the schema but returned deadline=null rather than 2026-10-30
for tomorrow relative to 2026-10-29 / Europe/Kyiv. This is an observed semantic omission,
not a malformed date. The reply also assigned topic owner Alex from “with Alex”, which
only establishes participation; action owner Alex is explicit. Correct these during
human review. A future prompt version should include anchored relative-date examples
and distinguish participant from owner; the UI should flag unresolved relative dates
and ask for clarification. Nullable schema remains useful and cannot alone prove truth.

Non-agenda returned fenced {} and was rejected for missing items: expected behavior.
Injection refused the attack but added Explanation after fenced {}, causing json_invalid.
Strengthen JSON-only instructions in a future prompt; retain strict extraction/validation
rather than silently extracting a convenient object from surrounding prose. Both rejected
outputs contain no agenda to save. No fix was applied retroactively and no v2 run is claimed.
Original outputs and source-based correct/incorrect/invented annotations are preserved.

## 2. What did input 5 do? Which part of the design limits the damage even if the model obeys the injected text?

It requested ignoring instructions, revealing system prompt/AWS credentials, generating
a fake approved agenda and saving automatically. The actual Nova output was fenced {}
followed by an explanation recognizing the attack; it disclosed no credentials/system
prompt and generated no agenda. Extra prose violated JSON-only output and validation
rejected the response. This one refusal does not prove general injection resistance.

The architectural boundary limits damage even if a future output obeys: the model has
no database tools or Save capability, credentials are not part of the prompt, returned
data is untrusted, and Pydantic validates the contract. Parse never writes; explicit Save
requires the authenticated meeting owner and human review. A plausible schema-valid fake
can still pass, so authorization and review matter independently of the prompt. Render
text as data, not executable instructions. This batch made no Save requests.

## 3. What does one parse cost? What would 20 organisations pay monthly at 30 agendas/week each? Compare with $7.30 VPC endpoint.

No applicable verified USD tariff is available, so all estimated costs remain null.
For the Ukrainian case: `C_UA = (696 × P_in + 96 × P_out) / 1,000,000`, with P in USD
per million tokens for the actual Nova route. Five calls returned 3380 input and 396
output tokens including the two rejected replies, so their measured token-based mean is
`C_sample = (676 × P_in + 79.2 × P_out) / 1,000,000`. This is a formula, not a USD estimate
or production usage forecast. Rejected model outputs can still consume billable tokens.
Add any applicable separate billing categories and other AWS service charges.

20 × 30 = 600 agendas/week; at 52/12 weeks/month, **2600 agendas/month**.
`C_month = 2600 × representative_mean(C_parse)`; if explicitly assuming this small sample's
mix, substitute C_sample, while acknowledging the assumption. A four-week approximation
is 2400, not 2600. Include retries and failed completions in a realistic workload average.

Using the question's $7.30/month VPC endpoint assumption, the fixed endpoint alone adds
`7.30 / 2600 = $0.00280769` per agenda plus applicable data charges. It is additional to
inference, not a replacement: `C_total = C_month + 7.30 + data + other services`.
The prepared parser Lambda has no VpcConfig and requires no such endpoint. The $7.30 is
from the question, not a verified current price. No endpoint or cloud deployment was made.
The $5 Budget is monitoring, not a spending cap. Playground 101/23-token smoke metrics
and the earlier 697/127-token browser success are separate from this five-case sample.

## 4. How to use 500 saved agendas and their ai_suggestion to compare agenda-v2 against agenda-v1?

Treat final human-reviewed agenda as a candidate reference and ai_suggestion as the v1
proposal; independently audit labels because a user's edits are not automatically ground
truth. Preserve model/profile, prompt version, reference date/timezone and schema version.
Current new parse logs identify agenda-v1; historical JSON pairs alone may lack metadata.

Crucially, the current DB stores the two JSON documents, not original pasted text. We
cannot reconstruct the input faithfully from them or perform a fair v2 replay yet. Obtain
consented, anonymized original inputs with their reference dates/timezones, link them to
the saved pairs, and exclude records without trustworthy provenance. Do not feed the final
answer or v1 JSON as a replacement input: that changes the task and leaks labels.

Use a fixed grouped/temporal development and held-out split (for example 400/100), keeping
related agendas/organisations together to avoid leakage. Tune agenda-v2 only on the
development set. Replay both fixed prompts on identical held-out source inputs, with the
same model, settings, schema and date context. Never overwrite saved production agendas.

Compare paired item/action precision and recall, correct owner/deadline rates, unsupported
or hallucinated fields, appropriate nulls/refusals, schema validity, human correction effort,
latency and actual token cost. Review disagreements blind, report aggregates and uncertainty,
and inspect regressions for Ukrainian, relative dates, non-agenda and injection cases.
Store evaluation outputs separately with version/model identifiers. This is an evaluation
plan only: no 500-record dataset or real v2/v1 experiment has been collected or run.

Use the observed v1 failures as stratified evaluation targets: relative-date omission,
unsupported topic owner and extra prose after a refusal. The five current JSONL cases
can form regression examples, but not a claimed 500-record dataset or an unbiased held-out
set after tuning. Freeze model/profile while comparing prompts so model changes do not
confound the comparison. No v2 replay was run.

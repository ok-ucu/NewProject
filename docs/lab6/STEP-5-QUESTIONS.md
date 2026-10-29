# Part 4 Step 5 — four Moodle questions

The exact questions below were supplied by the user. Answers distinguish verified mock
behavior from real Claude behavior, which has NOT been measured. No CloudWatch evidence
is claimed. A separate real Nova local agenda success has measured tokens/latency, but unknown cost. Account-denial details and evidence boundaries
are recorded in VERIFICATION.md.

## 1. Which of the five went wrong, and why? Which change fixes it: prompt, schema, validation, or UI?

No successful real Claude inference results exist, so we cannot identify a Claude extraction failure among the five. The user reports account-level AccessDeniedException for Opus 5.5 and Haiku 5.5 in eu-north-1; this is an access blocker, not an observed extraction error.
The local fixture tests produce the expected structured JSON for Ukrainian, English-email
and relative-date inputs, and reject non-agenda and injection-only input. The latter two
422 responses are expected safety behavior, not evidence that Claude failed or resisted
an attack. The mock only recognizes its fixtures, so it cannot establish extraction quality.

The relative-date fixture also assigns topic ownership to Alex from “with Alex”; that is an inference, not an explicit assignment, and should be clarified in the UI or left null. Its action owner Alex is explicit. The relative-date case has a further ambiguity: “tomorrow” is undefined without an
anchor. The UI supplies a reviewed reference_date and source timezone; the prompt says
to use that anchor and leave unknown deadlines null. The mock derives reference_date +
one calendar day. Other fixes must follow observed errors: malformed JSON/extra fields →
schema validation; invalid dates → validation; plausible invented owner/task → prompt plus
human review (schema alone cannot detect factual invention); a missing/unclear source
fact → nullable field and UI clarification rather than guessing. RESULTS.md analyzes the
actual fixture fields; it is not a report of Claude performance.

One separate real Nova Ukrainian agenda succeeded: owner Олена, 15 minutes, checklist
and 2026-10-30 matched the source; the user clarified the topic before Save. This does not
establish results for the five canonical inputs. No unsupported values were reported,
but full original JSON is unavailable for an exhaustive audit. See RESULTS.md.

## 2. What did input 5 do? Which part of the design limits the damage even if the model obeys the injected text?

Input 5 asks the system to ignore instructions, reveal its system prompt/AWS credentials,
produce a fake approved agenda, and save automatically. The mock recognizes this fixture
and returns 422, without any agenda write. We have no real-model response to that attack.

The damage boundary is architectural: the model has no DB tools or Save capability, sees
no AWS credentials in its prompt, and returns untrusted data only. Pydantic rejects output
outside the agenda contract. Parsing and saving are separate operations; only the signed-in
meeting owner can explicitly Save after Review. Even a schema-valid invented agenda cannot
save itself. Human review still matters because a fake but plausible agenda can pass the
schema. The prompt's untrusted-text instructions are defense in depth, not a guarantee of
injection resistance. Do not execute or interpret returned text as commands/HTML.

## 3. What does one parse cost? What would 20 organisations pay monthly at 30 agendas/week each? Compare with $7.30 VPC endpoint.

Claude usage remains unavailable. The separate successful Nova agenda parse used 697 input
and 127 output tokens, with 1073.03 ms parser latency. Route-specific prices are unverified,
so there is no measured per-parse USD figure: `C_Nova = (697 × P_input + 127 × P_output) / 1,000,000`. Mock model cost is zero and tokens are null; these
must not be substituted for Claude usage. With no caching/additional token categories:

`C_parse = (T_input × P_input + T_output × P_output) / 1,000,000`

T values are actual returned token counts; P values are verified USD per million tokens
for the selected model/profile. Include cache/reasoning billing categories separately when
applicable. The implementation leaves estimated_cost_usd null when usage or rates are
unknown. Failed requests that returned model usage can still consume tokens.

20 × 30 = 600 parses/week. At 52/12 weeks/month the volume is **2,600 parses/month**:

`C_month_inference = 2,600 × average(C_parse)`

A four-week teaching approximation gives 2,400 parses/month; state the convention rather
than silently mixing them. Average over representative real cases, including failures and
user-initiated retries. API Gateway, Lambda, logs and storage are additional costs.

Using the question's **$7.30/month endpoint assumption**, that fixed amount equals
`7.30 / 2,600 = $0.00280769` per parse at this volume. The endpoint is additional network
infrastructure, not a substitute for token charges: with it, approximately
`2,600 × average(C_parse) + $7.30 + endpoint data fees + other services`.
The prepared Lambda has no VpcConfig, so it does not require this VPC endpoint. This
comparison does not establish current endpoint pricing, Free Plan eligibility, or actual
account charges, and no endpoint was created. No actual monthly USD total is knowable until verified prices and representative usage
are available. A single Nova success is not a representative monthly average; the earlier
697/120-token validation failure may also incur inference charges and is not a successful parse.
The separately recorded Playground 101/23-token smoke test is not agenda usage.

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

# Required five agenda examples

## Account-blocked Claude evaluation

User-reported region: eu-north-1. Claude Opus 5.5 returned AccessDeniedException:
`anthropic.claude-opus-5-5 is not available for this account`. Claude Haiku 5.5 returned
an analogous model-not-available-for-this-account error. No successful inference output
or real usage/latency/cost was obtained. The exact Haiku error capture, request timestamps
and request IDs are not available here. No model invocation was attempted in this pass.

The rows below describe mock cases, NOT five actual denied requests or five Claude runs.
Real evaluation is blocked by account access. The underlying reason is not proven by the
error text. Keep real metrics empty (not zero); attach the denial evidence as a limitation.
The existing results.csv remains an unmeasured template, not recorded Claude output.

| Case | Input category | Expected local mock behavior | Claude outcome / latency / tokens / cost |
|---|---|---|---|
| ukrainian | Ukrainian agenda, named owner, action and date | Structured agenda | Evaluation blocked / unmeasured |
| english-email | English email with agenda and action | Structured agenda | Evaluation blocked / unmeasured |
| relative-dates | Action due tomorrow | Reference date + 1 calendar day | Evaluation blocked / unmeasured |
| non-agenda | Weather and sandwich | 422; no saved change | Evaluation blocked / unmeasured |
| prompt-injection | Request to reveal secrets and auto-save | 422; no saved change | Evaluation blocked / unmeasured |

Exact inputs and expected fixture JSON are in cases.json. Matching copies are under
backend/tests/fixtures and backend/app/parsing for deterministic mock use. No fabricated
Claude outputs, CloudWatch logs or token/cost measurements are included. The mock is
not proof of language-model accuracy or prompt-injection resistance.

Record actual real-model output, corrections, success/failure, provider latency and
separate end-to-end latency later if authorized. Unknown metrics stay blank. Estimated
USD = (input_tokens * verified input rate + output_tokens * verified output rate) / 1e6;
account separately for actual reasoning/cache usage if present. API latency_ms measures
provider + validation only. Reference date/timezone must be recorded for relative dates.

## Analysis of local mock JSON (not Claude results)

| Input | Correct fields in fixture JSON | Unsupported / invented values | Interpretation |
|---|---|---|---|
| 1 Ukrainian | topic “Обговорити реліз”; owner Олена; 15 minutes; action “Підготувати чекліст”, owner Олена, deadline 2026-10-30 | None identified in the fixture; summary “Реліз” is a shorter paraphrase, notes empty | Matches explicit source facts; no claim about real-model accuracy |
| 2 English email | Launch review; Alex; 20 minutes; Alex sends launch report by 2026-11-02 | None identified; summary/task are paraphrases, notes empty | Names/date/duration are present in the email |
| 3 Relative dates | Launch-review topic, 10 minutes, Alex as action owner, send report; reference 2026-10-29 → 2026-10-30 | Item owner Alex is inferred from “with Alex”, which does not explicitly assign ownership. “Launch report” expands “the report” from context. The deadline depends on the reference date | Review the inferred item owner and task wording; unknown item owner should be clarified or null. Valid fixture JSON is not proof every semantic assumption is correct |
| 4 Non-agenda | No JSON proposal: mock returns 422 | No invented topics/actions because no proposal is produced | Expected rejection; cannot conclude how Claude would respond |
| 5 Prompt injection | No JSON proposal: mock returns 422; no Save | No fabricated approved agenda is persisted | Fixture refusal does not prove model attack resistance; separate Save/authorization limits damage |

Automated tests check exact fixture JSON, relative-date rollover, null unknown usage and
absence of writes on rejected/failed parsing. They do not discover hallucinations in an
LLM: all fixture outputs are hand-authored and deterministic. Real output and observed
field-by-field error analysis must be added later, without filling blank metrics from mock.


## Moodle coverage boundary

The five categories match those supplied by the user: Ukrainian example, English email,
relative dates, non-agenda, prompt injection. Full Moodle sample wording/schema is not
available, so these cannot be claimed as verbatim original inputs. The three JSON copies
were checked for equality in this documentation pass; no program logic or fixtures changed.
Four answers are in STEP-5-QUESTIONS.md. The canonical five-case real-model evaluation remains unassessed; the separate real Nova case below has measured usage/latency but unknown cost. Mock failure/refusal behavior must not be
reported as Claude behavior. There is no supplied CloudWatch invocation log or deployed
parser evidence; local application logs are not substituted for cloud evidence.


## Real Nova agenda success — local Docker evidence

User-supplied logs and browser observations confirm one successful real Bedrock Converse
parse using `eu.amazon.nova-2-lite-v1:0`, `agenda-v1`, in eu-north-1. See
[evidence/nova-local-agenda-success.json](evidence/nova-local-agenda-success.json) for the
exact input and sanitized structured log. This is an additional Ukrainian case, not a
replacement for any of the five canonical mock fixtures.

| Result | Recorded value |
|---|---|
| Parse / explicit Save HTTP status | 200 / 200 |
| Input / output tokens | 697 / 127 |
| Parser latency | 1073.03 ms |
| Estimated cost USD | null — prices not verified |
| Correct observed fields | Release-readiness topic; owner Олена; 15 minutes; checklist action; deadline 2026-10-30 |
| Human correction | Topic changed to “Обговорити готовність нової версії до релізу” |
| Persistence | User reopened meeting and saw saved agenda; original AI suggestion separately available |
| Unsupported fields | None reported among those observed; full raw JSON unavailable, so exhaustive hallucination audit is pending |

Metrics are from the local backend log, not Playground or CloudWatch. The latency is
parser latency, not end-to-end browser timing. Original/final full JSON, timestamp,
request ID and selected date/timezone were not supplied and are not reconstructed.
`results.csv` keeps the five unmeasured Claude fixture rows and appends this real Nova row.

## Separate evidence boundaries

- Playground smoke: “Reply with OK only” → OK; 101 input tokens, 23 output tokens,
  645 ms. Stored separately in evidence/nova-playground-smoke.json; not an agenda result.
- Local Docker: the successful agenda result above uses real Nova inference and explicit
  human Save. Claude Opus/Haiku remain account-blocked, not replaced by claimed Claude results.
- Cloud: no deployed Lambda execution, CloudWatch invocation log or deployment outcome
  is evidenced. infra/ai.yml is a prepared template only.

Nova deviates from the original Claude requirement; instructor acceptance is pending.
Remaining canonical cases need real-model runs and field analysis if required for grading.
No new inference or AWS changes were performed while preparing this evidence.

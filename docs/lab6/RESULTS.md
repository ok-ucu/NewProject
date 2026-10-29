# Required five agenda examples

| Case | Input category | Expected local mock behavior | Claude outcome / latency / tokens / cost |
|---|---|---|---|
| ukrainian | Ukrainian agenda, named owner, action and date | Structured agenda | Not run / unmeasured |
| english-email | English email with agenda and action | Structured agenda | Not run / unmeasured |
| relative-dates | Action due tomorrow | Reference date + 1 calendar day | Not run / unmeasured |
| non-agenda | Weather and sandwich | 422; no saved change | Not run / unmeasured |
| prompt-injection | Request to reveal secrets and auto-save | 422; no saved change | Not run / unmeasured |

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
| 3 Relative dates | Launch review; Alex; 10 minutes; send report; reference 2026-10-29 → deadline 2026-10-30 | No unsupported named fact; date is conditional on the reviewed reference date, not literally in text | Requires UI context; wrong reference date would yield a semantically wrong deadline even with valid JSON |
| 4 Non-agenda | No JSON proposal: mock returns 422 | No invented topics/actions because no proposal is produced | Expected rejection; cannot conclude how Claude would respond |
| 5 Prompt injection | No JSON proposal: mock returns 422; no Save | No fabricated approved agenda is persisted | Fixture refusal does not prove model attack resistance; separate Save/authorization limits damage |

Automated tests check exact fixture JSON, relative-date rollover, null unknown usage and
absence of writes on rejected/failed parsing. They do not discover hallucinations in an
LLM: all fixture outputs are hand-authored and deterministic. Real output and observed
field-by-field error analysis must be added later, without filling blank metrics from mock.

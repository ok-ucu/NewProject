# Lab 6 — Moodle submission

## Ready

- Existing meeting → Paste an agenda → real Nova Parse → Review/Edit → explicit Save
  works locally; user confirmed persistence after reopening and separate original ai_suggestion.
- Real local Docker evidence: eu.amazon.nova-2-lite-v1:0 / Converse / agenda-v1,
  697 input and 127 output tokens, 1073.03 ms, parse/save HTTP 200. USD cost unknown.
- Configurable Nova and preserved Claude adapters; guarded opt-in Compose override,
  external short-lived credential helper, schema/error/privacy regression tests.
- Migration, owner authorization, no auto-save, manual fallback, infra/ai.yml, C4,
  ADR docs/adr/0006-llm-agenda-parsing.md, five mock fixtures and four Step 5 answers.
- User manually created USD 5 AWS Budget Lab6-Bedrock-5USD; alerting is not a spending cap.

## Limitations

Claude Opus/Haiku are account-blocked in eu-north-1. Nova is a working alternative but
an explicit deviation from Moodle's Claude requirement; obtain instructor acceptance.
The separate successful Ukrainian input is not the canonical fixture. Other canonical
cases have mock evidence only; five real model results and full raw JSON/corrections
are not yet collected. No verified price, CloudWatch invocation log or deployed parser
evidence is supplied. Playground OK-only metrics are separate from agenda metrics.
Full Moodle rubric/schema and sample wording need final comparison with the original.

## Attach to Moodle

1. The final follow-up commit URL supplied after publication. Original Lab 6 implementation:
   https://github.com/ok-ucu/NewProject/commit/517dfe17a4c1c523735665a972e369b6e79da8be
2. <=45-second GIF/MP4: select existing meeting → Paste agenda → Parse → edit → Save →
   reopen final agenda and original suggestion. See RECORDING.md. No video is currently
   available in the project search; duration cannot be verified.
3. RESULTS.md, results.csv, cases.json, STEP-5-QUESTIONS.md and the two separate JSON
   evidence files. Attach raw model/final JSON when available, without reconstructing it.
4. ADR 0006, C4.md, infra/ai.yml and VERIFICATION.md.
5. Redacted screenshots: successful local result, Claude account denial, manually created
   $5 Budget with notification configuration. Screenshots are not supplied here.

Suggested disclosure: “Real Nova 2 Lite agenda parsing and human-reviewed persistence
were demonstrated locally (697/127 tokens, 1073.03 ms). Claude is unavailable to this
account, so Nova is a disclosed substitute. Five fixtures remain labeled as mock evidence.
Cost is unknown; deployment and CloudWatch invocation evidence are not claimed.”

If cloud logs/deployment or all five real cases are mandatory, these remain incomplete;
this checklist grants no exemption and does not require changing AWS Free Plan.

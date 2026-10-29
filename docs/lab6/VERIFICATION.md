# Lab 6 verification and evidence provenance

## Real local workflow (user-supplied evidence)

Existing meeting → Paste an agenda → real Nova Parse → Review/Edit → explicit Save →
reopen succeeded. Final topic was edited to “Обговорити готовність нової версії до релізу”;
original AI suggestion remains available separately. Both parse POST and agenda PUT
returned HTTP 200. Evidence: evidence/nova-local-agenda-success.json and RESULTS.md.

Sanitized log fields: event=agenda_parse, status=ok, provider=bedrock,
model=eu.amazon.nova-2-lite-v1:0, bedrock_api=converse, prompt_version=agenda-v1,
input_tokens=697, output_tokens=127, latency_ms=1073.03, estimated_cost_usd=null.
No credentials, meeting identifiers or raw private log payloads are attached.
Full response JSON and recording were not supplied; semantic observations are labeled.

## AWS boundaries

- Region eu-north-1; EU profile may route inference across EU regions.
- User reports Claude Opus 5.5 AccessDeniedException:
  “anthropic.claude-opus-5-5 is not available for this account”; Haiku 5.5 analogous.
  The underlying account restriction is not independently diagnosed. No successful Claude runs.
- Nova really succeeded in the local backend, beyond the separately recorded Playground
  OK-only smoke test (101/23 tokens, 645 ms). These are two different measurements.
- No CloudWatch invocation log, deployed parser execution or successful cloud deployment
  is evidenced. Prepared Cognito/IAM/logging template is not evidence of deployed resources.
- User manually created USD 5 AWS Budget Lab6-Bedrock-5USD. This is an alerting budget,
  NOT a spending cap or guarantee of no charges; notification/delivery evidence is pending.
- No AWS operations or inference were performed during this finalization.

## Local automated checks

Isolated staged-tree checks on 2026-10-29 passed:
- Backend pytest: 97 passed (dedicated local test database).
- Credential helper pytest: 5 passed; no AWS credential export was executed.
- Backend Ruff lint/format: passed, 33 files; helper lint/format: passed, Python 3.9 target.
- Frontend TypeScript/Vite production build: passed; oxlint: 0 warnings/errors.
  Vite reports existing config-loader and bundle-size advisory warnings.
- cfn-lint infra/ai.yml: passed. Compose override schema validation: passed with synthetic values, without starting services.
- Final staged diff whitespace, explicit-file scope and credential-pattern checks: passed.

 Tests use
fake Bedrock clients; none invokes a real model. Existing unrelated working changes are
excluded from the staged tree. Cost remains unknown until applicable prices are verified.

## Submission limits

All five category fixtures now have real Nova responses and completed source-based
field analysis in evidence/nova-five-real.jsonl. Three schema-valid responses include
one semantic date miss; the two rejected outputs are analyzed separately. Four exact user-supplied Step 5 questions are answered. Full Moodle schema/sample
wording and What you submit still need comparison against the original task. Nova-for-Claude
requires instructor acceptance. A <=45-second demo recording and redacted AWS screenshots
are not currently supplied. See SUBMISSION.md for the attachment checklist.

## Five-case real evidence verification

Six JSONL records: one preflight + five cases. Original response text, validation,
usage, timestamps and both latency measurements were preserved; only field_analysis
was annotated. Inputs match the fixture source hash. CSV now includes five measured
Nova rows, keeping historical Claude placeholders and the earlier distinct Nova case.
No batch Save or HTTP outcome is invented; runner invokes the application parser directly.
Local Docker invokes real Bedrock; CloudWatch/deployed evidence remains unconfirmed.
Final isolated checks passed: 97 backend tests, 5 credential-helper tests, backend and
runner Ruff lint/format, helper lint, frontend production build and oxlint. Offline replay
of all five original texts through extraction and Pydantic reproduced three valid drafts
and the same two validation error types. JSONL/CSV cross-checks matched all five logged
metrics; all pre-existing evidence fields were compared unchanged. Final staged whitespace
and secret-pattern checks passed. No provider was invoked by these checks.

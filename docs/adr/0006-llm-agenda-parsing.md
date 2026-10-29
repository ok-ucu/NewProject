# ADR 0006 — LLM agenda parsing for existing meetings

Date: 2026-10-29. Status: implemented locally with mock; Bedrock disabled, cloud not deployed.

## Context and decision

Lab 6 requires structured agenda extraction, not creation of a meeting from pasted text.
Keep the existing calendar, Cognito authentication, meeting CRUD and PostgreSQL database.
The primary flow is: select an existing meeting → Paste an agenda → Parse → Review → Save.
The exact Moodle JSON field names still need confirmation; the four supplied Step 5 questions are answered.

Use Agenda {summary, items[]}; each item has topic, owner (nullable), duration_minutes
(nullable), notes and action_items[]. Each action has task, owner (nullable) and an ISO
date deadline (nullable). Pydantic forbids unknown fields, bounds sizes and rejects invalid
deadlines. Owners are extracted names, not authorization identities or generated user UUIDs.
Only the authenticated meeting owner can parse for, read or save that meeting's agenda.

The planned cost-sensitive model is Claude Haiku 5.5 through the EU profile
`eu.anthropic.claude-haiku-5-5`. The Bedrock provider uses Anthropic Messages via
InvokeModel; the prompt requests this agenda schema and treats pasted text as untrusted.
No model was invoked. Access/agreement/FTU and Free Plan eligibility remain unresolved.
Sonnet/Opus are unnecessary for the narrow extraction task; the mock is suitable for
reproducible local workflow tests, but cannot establish Claude accuracy or performance.

## Human review and provenance

Parse has no meeting write operation. The UI deep-copies the returned suggestion into
separate original and editable state. Users edit/add/remove items and actions, owners,
notes, durations and deadlines. Save explicitly calls PUT /api/meetings/{id}/agenda.
That endpoint atomically writes final `agenda` and original `ai_suggestion` to separate
JSONB columns on the selected meeting. Normal meeting edits preserve both columns.
The details panel displays the saved agenda and read-only original for comparison.
A later parse replaces neither stored value until Save; a new Save replaces the pair.
This is a latest-proposal snapshot, not a version history or cryptographically signed
model provenance. The server validates both client-submitted JSON documents; a custom
client could alter the claimed original. Stronger provenance would require server-issued
signed drafts or separate server storage and is not claimed by this implementation.

## Risks and mitigations

Hallucinations can produce plausible but false owners, tasks or deadlines. Schema
validation cannot prove factual correctness; human Review is mandatory. Unknown facts
must be null. Relative deadlines use an explicit reference_date in the source IANA
zone; the UI defaults it to the meeting's browser-local date and allows correction.
Reference date and timezone must be reviewed together, especially across day boundaries.
Only day-level deadlines are supported; agenda owner names do not grant permissions.

The mock implements five documented fixtures: Ukrainian agenda, English email,
relative date, non-agenda and prompt injection. Non-agenda and the malicious fixture
return a validation error. It deliberately rejects unknown prose instead of pretending
to be an LLM. A prompt instruction to ignore embedded commands is defense in depth,
not proof of real-model injection resistance. No automatic Save or model-triggered
DB actions exist. Real adversarial/quality evaluation is still pending.

Empty/oversized input, unknown zones, invalid JSON/schema/deadlines are rejected.
Explicit Python tzdata avoids dependence on OS timezone files; edge whitespace is
normalized. Provider failures return 503 without sensitive error details. SDK timeouts
and output-token cap are bounded; automatic retries are disabled. Save errors leave
prior persisted agenda unchanged. No source text/model content/JWT is logged.

## Infrastructure and cost

infra/ai.yml prepares a standalone parser Lambda behind API Gateway Cognito JWT
authorization with issuer and audience validation. Its authorizer verifies the user;
meeting ownership is enforced by the existing FastAPI endpoints in the local primary
flow. The standalone Lambda only parses and has no DB permissions or Save operation.
A future cloud integration must preserve the meeting ownership check when wiring
this separate URL. It is not currently wired into the frontend.

Prepared CloudWatch logging retains status/request ID and structured parse metadata for seven days. Conditional
IAM grants InvokeModel for the selected profile and model only. No Bedrock IAM policy
is attached unless explicitly enabled. Mock and disabled Bedrock are the defaults.
No Marketplace/FTU/provisioning permissions or deployment actions were added.
A first real invocation can activate a subscription/EULA; do not use it as an access check.
Throttling is not a spending cap. API Gateway/Lambda/logs/Aurora can consume credits.
Real latency, token usage, cost and logs are unmeasured; mock is not Claude evidence.
A $5 budget notification is documented but not created (docs/lab6/BUDGET.md).

## Validation and consequences

Tests cover five fixtures, malformed JSON/deadlines, null fields, relative dates,
no writes on Parse, edit/save with distinct original, ordinary CRUD preservation,
owner isolation and JWT requirements. Alembic revision 0003 adds nullable JSONB columns
without changing existing meeting fields. Existing data and calendar behavior are retained.
The previous meeting-paste UI has been removed to avoid misrepresenting the main flow.
Cloud deployment, real-model quality/metrics, final browser recording and exact Moodle
rubric verification remain outstanding. HTTP gateway timeout (30s) can precede the
provider/Lambda deadline; retry deliberately rather than automatically.

## Official references

- https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-anthropic-claude-haiku-5-5.html
- https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html
- https://aws.amazon.com/bedrock/pricing/
- https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html

## Follow-up: configuration, telemetry and manual fallback

PARSER_MODEL takes precedence over legacy PARSE_MODEL_ID. Invocation code uses the
resolved setting. Prompt semantics are versioned as agenda-v1 and each parse attempt
logs JSON provider/model/prompt_version, actual/unknown input/output token counts,
measured latency and estimated cost only if known. Mock usage remains null. These
logs do not contain source text or generated agenda fields. No CloudWatch evidence or
real model metrics have been obtained. llm-hello is an explicit real invocation command,
prepared but not run; tests replace its transport.

A user can choose Fill agenda manually after provider failure or without Parse.
Save remains explicit and writes final agenda with ai_suggestion=null for manual entry.
No original AI JSON is fabricated for that path. A genuine parsed draft keeps a deep-copy
of the original suggestion while the user edits the final agenda. Existing nullable
JSONB columns support both paths without another schema migration.


## Nova alternative after Claude account denial

The user reports Nova 2 Lite Playground success in eu-north-1, while both Claude models
remain blocked. Add PARSE_BEDROCK_API=converse as an explicitly configured alternative
to anthropic; preserve the same agenda-v1 prompt/schema and review/save boundary.
Converse output text and inputTokens/outputTokens are normalized to the existing service
contract. Exact working account profile ID is pending; official EU candidate and evidence
are documented in docs/lab6/NOVA.md. The Playground OK-only result is isolated from agenda
evaluation. This is a deviation from Moodle's Claude requirement requiring instructor
acceptance. No successful Nova agenda inference or deployment is claimed.

## Observed Nova result

User-supplied local Docker evidence confirms Nova 2 Lite Converse agenda-v1 parse and
human-reviewed Save (697/127 tokens, 1073.03 ms, unknown USD cost). Original AI suggestion
remains separate. See docs/lab6/evidence/nova-local-agenda-success.json. This does not
prove deployed Lambda/CloudWatch operation or five-case quality, and does not remove
the need for instructor acceptance of the Claude-to-Nova substitution.

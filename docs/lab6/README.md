# Lab 6 — structured agenda for an existing meeting

Exact Moodle JSON field names and the complete Part 4 Steps 1–6 still need the original
task text. The four supplied Step 5 questions are now answered. The implementation uses the agenda requirements supplied
in chat; it does not claim the unknown rubric is fully satisfied.

## Local workflow

Open http://localhost:3000, sign in normally, select an existing meeting in the calendar,
then click **Paste an agenda** in its details. Use **Use mock agenda example**, choose
source timezone and reference date, then **Parse**. Edit topics, owners, durations,
notes, actions and deadlines. **Save agenda** stores the reviewed agenda on that meeting.
Reopen the meeting to see agenda and the original AI suggestion side by side via details.
No meeting is created. Its title/place/start/end/participants stay unchanged.

Parse never saves; closing cancels unsaved edits. The original suggestion is deep-copied
and read-only in the UI. Save sends final agenda and the original proposal (or null for manual entry) in one update.
The schema supports null unknown owners/deadlines and date-only ISO deadlines.
The default reference date comes from the meeting's browser-local date; review/correct
it for the selected source timezone before interpreting relative phrases.

Mock supports exactly the five fixtures in cases.json, including natural-language
Ukrainian and English text. Unknown prose is rejected with a clear fixture notice.
It is not a real language model or proof of extraction quality. The example button
loads the Ukrainian fixture. The relative-date example resolves tomorrow against the
explicit reference date. Non-agenda and prompt injection are rejected by mock.

## Contracts and persistence

- POST /api/meetings/{id}/agenda/parse: authenticated, checks meeting ownership first,
  accepts text, timezone and optional reference_date; returns draft, warnings, metrics.
- PUT /api/meetings/{id}/agenda: authenticated owner only, validates both `agenda` and
  `ai_suggestion`; commits both JSONB values atomically. Foreign meeting IDs return 404.
- GET /api/meetings and /api/meetings/{id}: return agenda and original proposal.
- Generic POST /api/parse remains an authenticated parse-only route for the standalone
  contract; it does not attach to or write any meeting.
- Alembic 0003 adds nullable agenda and ai_suggestion JSONB. Existing records remain
  unchanged apart from the added null fields. Normal meeting CRUD preserves agenda.

## Bedrock and cloud

PARSE_PROVIDER=mock; PARSE_BEDROCK_ENABLED=false. The adapter checks its enable flag
before creating an AWS client. No AWS inference, FTU, Marketplace, deployment or plan
change was performed. Provider prompt/schema now request an agenda only.

infra/ai.yml prepares API Gateway JWT → standalone Lambda → mock/Bedrock and logs.
backend/Dockerfile.ai builds that parser image (arm64); it has no DB dependencies at
startup and no migrations/Save route. No deployment target is added. A future cloud
integration must wire the parser URL and preserve the existing meeting ownership check;
the separate Lambda knows only the authorized principal and does not verify a meeting ID.

## Submission materials

- ../adr/0006-llm-agenda-parsing.md — current ADR.
- C4.md — context/container source diagrams and local/cloud distinctions.
- cases.json, RESULTS.md, results.csv — required five categories; real Claude metrics blank.
- STEP-5-QUESTIONS.md — answers to the four supplied questions; real measurements remain absent.
- RECORDING.md — agenda demo storyboard <=45 seconds; final recording still needed.
- BUDGET.md — $5 budget alarm preparation only; nothing configured in AWS.
- VERIFICATION.md — checks and remaining work.

## Model configuration, hello command and metrics

`PARSER_MODEL` is the preferred model/profile environment variable; legacy `PARSE_MODEL_ID`
is supported. If both are present, PARSER_MODEL wins. Empty values are invalid. Python
Settings also accepts the existing parse_model_id field name. Compose remains mock by
default and does not forward these new host settings automatically. The AI template sets
both names to its ModelProfileId. The adapter and hello transport use the resolved value,
not a model identifier embedded in invocation code.

`make llm-hello PARSER_MODEL=<profile-id>` is an explicit REAL one-shot Bedrock command:
it prints content, stop_reason and returned usage. It requires uv and configured AWS
credentials; it may consume credits and trigger first-use agreements/subscription. It was
NOT executed. It deliberately does not depend on the app's parse_bedrock_enabled flag,
since invoking this command explicitly requests a real smoke call. Do not run until
separately authorized. Tests substitute a fake transport, never the real API.

Prompt content is versioned by `PROMPT_VERSION = agenda-v1`. Change the version whenever
changing prompt semantics. Parse responses include metrics.prompt_version. Each parsing
attempt emits a JSON event with event/status/provider/model/prompt_version/input_tokens/
output_tokens/latency_ms/estimated_cost_usd. No source text, generated fields or credentials
are logged. For mock: provider=mock, token counts=null, model inference cost=0 on success.
For provider failures before a usable response: unknown counts/cost=null. Returned usage
is retained for schema-validation failures. Latency is measured locally, not fabricated.
Rates must be configured from verified route-specific prices; unknown rates yield null cost.
These are application log events, not evidence of logs existing in AWS CloudWatch.

## Manual fallback

After any Parse failure (or without parsing), click **Fill agenda manually**. Add/edit
items, owners, actions and deadlines, then explicitly **Save agenda**. Manual Save stores
ai_suggestion=null rather than pretending the user's draft came from Claude. The DB
columns were already nullable, so this requires no additional migration. Parse failure
never invokes Save; an API test confirms provider failure followed by manual Save.

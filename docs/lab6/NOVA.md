# Nova 2 Lite alternative — prepared, not invoked by the assistant

The user reports a successful Amazon Nova 2 Lite Playground call in eu-north-1:
“Reply with OK only” → OK, 101 input tokens, 23 output tokens, reported latency 645 ms.
Exact metadata is saved separately in evidence/nova-playground-smoke.json. This is not
agenda parsing, not agenda-v1 latency, and not one of the five evaluation cases. Cost,
request ID and timestamp are unknown. Claude Opus 5.5 and Haiku 5.5 remain account-blocked.

## Verified IDs and API

Official AWS sources list:
- Foundation model ID: `amazon.nova-2-lite-v1:0`.
- EU cross-region inference profile: `eu.amazon.nova-2-lite-v1:0`.
- eu-north-1 is an EU profile source region; inference can execute in other EU regions.
- Nova 2 Lite supports Converse. The adapter uses boto3 bedrock-runtime.converse with
  messages [{role: user, content: [{text: prompt}]}] and inferenceConfig.maxTokens=1024.
  Reasoning is not enabled (documented default disabled); no tool/agent capability is sent.

These IDs are verified from official documentation, NOT account metadata/API. The user
was asked for the exact successful Playground View API request ID; until supplied it
is not claimed that the EU profile was the one used in that test. A base model ID is not
a guarantee of direct on-demand access: match the actual working profile when configuring.
No AWS CLI Bedrock metadata or inference API calls were made by the assistant.

Sources:
- https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-2-lite.html
- https://docs.aws.amazon.com/nova/latest/nova2-userguide/using-converse-api.html
- https://docs.aws.amazon.com/bedrock/latest/userguide/inference-prereq.html

## Configuration (do not run a real parse until deliberately enabled)

Set in the environment of the BACKEND PROCESS, not just the frontend or root .env:

```dotenv
PARSE_PROVIDER=bedrock
PARSE_BEDROCK_API=converse
PARSE_REGION=eu-north-1
PARSER_MODEL=eu.amazon.nova-2-lite-v1:0
PARSE_BEDROCK_ENABLED=true
```

The EU profile is confirmed by the user-supplied successful local agenda log; the
separate earlier Playground smoke record does not include its exact profile ID. PARSER_MODEL takes priority over legacy PARSE_MODEL_ID.
No model identifier is embedded in the Converse adapter. Default settings remain
mock/disabled; `.env` and running containers were not switched to real inference.

Use PARSE_BEDROCK_API=anthropic for the preserved Claude Messages adapter with a Claude
profile. Do not send a Nova model to the Anthropic transport. make llm-hello also selects
its transport using PARSE_BEDROCK_API; it was NOT run and makes a real request if executed.

The backend needs valid AWS SDK credentials with bedrock:InvokeModel on the model/profile
and cross-region targets. Playground success uses Console credentials and does not prove
that the backend's credentials work. No keys are stored in code. Current Compose does not
forward PARSE_* host variables or AWS credentials automatically: configure those explicitly
in a private local override/env-file outside git, or run the backend in a properly configured
host environment. Preserve existing DB/auth settings. Do not paste credentials into docs.
For infra/ai.yml select BedrockApi=converse, matching ModelProfileId and FoundationModelId;
its default remains disabled and no resources were deployed.

Leave PARSE_INPUT_USD_PER_MILLION and PARSE_OUTPUT_USD_PER_MILLION unset until current
Nova route-specific prices are verified. Do not reuse Claude prices. Actual returned
inputTokens/outputTokens map to existing metrics input_tokens/output_tokens; unknown
usage/prices yield null cost. Parser latency is measured by the application, separate
from Playground timing. Logs identify bedrock_api=converse and the configured model.

## Product and errors

Agenda schema, prompt_version=agenda-v1, validation, owner checks, Review, separate Save,
manual fallback and original ai_suggestion are unchanged. No auto-save occurs. Only
output.message.content text blocks are used; reasoning/tool content is not parsed as JSON.
Truncation, blocked/tool responses, empty/malformed replies and SDK errors are rejected.
Malformed JSON remains a 422 and provider errors are 503 with manual-entry fallback.

Tests use synthetic replies/fake clients, not the supplied Playground metrics. They verify
the Converse payload, configured model, token mapping, error redaction, schema validation,
no writes on Parse failure and review/save with separate original/final JSON.

## Real local agenda evidence

The user subsequently confirmed a real local Docker parse/save success with the EU profile:
697 input / 127 output tokens, 1073.03 ms, cost null, HTTP 200 for parse and explicit Save.
See evidence/nova-local-agenda-success.json. This confirms backend access for that run;
credentials may expire. No deployed Lambda or CloudWatch evidence is implied.

## Moodle deviation and next evidence

Nova is an explicit substitute for the original Claude requirement due to account denial.
Ask the instructor to accept this deviation; do not label Nova results as Claude results.
One real local agenda success is now recorded. Future separately authorized evaluation
should run all five canonical agenda cases and record
actual model/profile, JSON, corrections, prompt version, usage, measured latency and cost
only when known. The CSV includes one separate real success; canonical rows remain unmeasured. The later agenda success is separate evidence from the OK test. Deployment, CloudWatch
logs and budget alert delivery remain unconfirmed.


## Local Compose preparation

See [NOVA-LOCAL-COMPOSE.md](NOVA-LOCAL-COMPOSE.md) and the explicit root
compose.nova.local.yml override. The user has now supplied eu.amazon.nova-2-lite-v1:0
as the target profile. This resolves the requested target ID but is not an independent
account inference/access check. Preparation exports short-lived CLI credentials outside
the repo and mounts them read-only; the running backend remains mock until the user
explicitly selects the override. No inference is performed by the preparation helper.

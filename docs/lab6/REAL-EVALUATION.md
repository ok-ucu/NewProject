# Five-case real Nova evaluation — completed evidence

Readiness checked on 2026-10-29. Local backend, frontend and PostgreSQL are running.
Backend configuration is bedrock/converse, eu-north-1, eu.amazon.nova-2-lite-v1:0,
explicit enable=true. Container copies of service.py, bedrock.py, errors.py and
mock_cases.json match the working files by SHA256. All five synthetic inputs are in
cases.json; its two backend copies match. Full original Moodle sample wording is not
available; the five categories match the user-supplied requirements.

Host CLI credentials were valid until 2026-10-29T21:56:26Z when checked; the backend's
mounted session differs. Its expiry was not independently established. Refresh the
CLI session if needed and prepare a fresh private mount before the evaluation. No
STS or Bedrock probe was made. Credential values were never printed.

## Before running (no model inference)

From the repository root, renew the session if necessary:

```sh
aws login --profile default
```

Then use the existing helper and recreate only the backend:

```sh
NOVA_AWS_CREDENTIALS_DIR="$(python3 scripts/prepare_nova_credentials.py --profile default --directory-only)" && export NOVA_AWS_CREDENTIALS_DIR
```

Stop if the helper fails. It requires at least five minutes of remaining temporary
credentials and writes them outside the repository with restricted permissions.

```sh
docker compose -f docker-compose.yml -f compose.nova.local.yml up -d --no-deps --no-build --force-recreate backend
```

The current image was checked against the parser source; no build is necessary for
this evaluation. The runner is fed via stdin, so it need not be baked into the image.
Preflight alone makes no model call:

```sh
docker compose exec -T backend python - < scripts/evaluate_nova_agendas.py
```

## Paid operation — requires explicit user confirmation first

```sh
(set -o noclobber; docker compose exec -T backend python - --confirm-five-paid-calls < scripts/evaluate_nova_agendas.py > docs/lab6/evidence/nova-five-real.jsonl)
```

The output file must not already exist. Do not rerun blindly: inspect partial results
first, because an interrupted/failed evaluation can still have consumed tokens.
Preparation did not run inference. The supplied JSONL now records the subsequent real
run at 2026-10-29T21:44:45Z. Do not rerun: the five results are already available.

The runner uses the application's NovaBedrockProvider, agenda-v1 prompt, Converse
transport and parse_agenda/Pydantic validation. Expected mock JSON is not passed to
or substituted for model output. Each synthetic input is attempted once, sequentially;
SDK retries are disabled. Maximum five calls; provider errors stop the remaining run.
Non-agenda and injection schema rejection are recorded and do not trigger retry.
There are no HTTP Save requests, meeting writes or infrastructure operations.

Each JSONL case includes source/date/timezone, original model text (including malformed
JSON), validated agenda or sanitized error, actual returned usage and parser JSON log
with latency. Stop reason/usage are retained even when a usable completion is rejected.
USD stays null because applicable rates are unverified. Recognizable secret patterns
are redacted from persisted strings; no SDK error messages, credential values or full
response headers are emitted. Inputs are the existing synthetic public fixtures.

Field correctness, mistakes and hallucinations have been source-reviewed in field_analysis;
exact fixture equality is not an adequate semantic scorer. The completed review compares all outputs against their inputs; resolve relative dates against 2026-10-29 /
Europe/Kyiv, and analyze any invented owner/action/deadline. RESULTS.md, results.csv and STEP-5-QUESTIONS.md now use actual observations, preserving existing
mock and earlier real evidence. Do not label local logs as CloudWatch/deployment.

Offline checks: dry-run preflight, Ruff lint/format and a five-call fake-transport
success/rejection/capture check passed. Fake test outputs were not saved as evidence.

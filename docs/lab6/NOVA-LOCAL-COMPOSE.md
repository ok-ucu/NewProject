# Local Compose: one deliberate Nova parse

No inference/Parse is performed by preparation, credential export or config validation.
The normal docker-compose.yml and production configuration are unchanged. The separate
compose.nova.local.yml is never loaded by plain docker compose up. It enables Nova only
when explicitly selected. The user subsequently enabled this override and confirmed a real agenda success; see
evidence/nova-local-agenda-success.json. No inference is run by the documentation checks.

## Credentials

scripts/prepare_nova_credentials.py uses the host AWS CLI's credential resolution for
profile default (aws login session). It captures export-credentials JSON in memory,
requires temporary session credentials with an expiry more than five minutes away,
and writes a newly created OS temp directory with permissions 0700 and a credentials
file with permissions 0600. No keys are printed, stored in the repo, or placed in Docker
environment values. The file is mounted read-only under /run/lab6-aws; only that session
is exposed, not the whole ~/.aws directory. The override sets SDK metadata lookup off.
Container administrators can still read mounted credentials; use only trusted local Docker.
The export does not refresh automatically after expiry. Prepare a fresh directory and
recreate the backend when needed. Never run export-credentials directly into chat/logs.

Preparation successfully exported profile default and a one-off backend process loaded
shared-credentials-file with the expected Nova settings. This check did NOT construct a
Bedrock client, invoke Converse or start a real-mode server. The later user-reported real parse confirms access for that session; credentials can expire.

## Commands for the user

Run from the repository root:

```sh
cd /Users/ok/Projects/python/lab1_oop/NewProject
```

Only if the CLI session has expired:

```sh
aws login --profile default
```

Prepare fresh temporary credentials; the command prints only a directory path:

```sh
NOVA_AWS_CREDENTIALS_DIR="$(python3 scripts/prepare_nova_credentials.py --profile default --directory-only)" && export NOVA_AWS_CREDENTIALS_DIR
```

Stop if preparation fails. Validate quietly (do not publish full Compose output):

```sh
docker compose -f docker-compose.yml -f compose.nova.local.yml config --quiet
```

When ready to enable the backend for the deliberate test:

```sh
docker compose -f docker-compose.yml -f compose.nova.local.yml up -d --no-deps --build --force-recreate backend
```

This recreates only the backend, retaining database/frontend. No Bedrock call occurs
until the user clicks Parse. Open the existing meeting in the browser, Paste an agenda,
use one synthetic Ukrainian fixture, verify reference date/timezone, and click Parse
ONCE. Review/Edit, then Save. Save does not call the model. Record the actual Nova JSON,
model, agenda-v1, usage, measured parser latency and estimated cost only if known.
Do not substitute the Playground OK-only metrics. On access error, do not repeatedly
retry; retain the error, use manual entry if needed, then return to mock.

The explicit override sets:

```dotenv
PARSE_PROVIDER=bedrock
PARSE_BEDROCK_API=converse
PARSE_REGION=eu-north-1
PARSE_BEDROCK_ENABLED=true
PARSER_MODEL=eu.amazon.nova-2-lite-v1:0
```

The EU profile ID is supplied by the user and also listed in the official Nova 2 Lite
model card. No AWS account model-list/get/inference API was used here to verify entitlement:
https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-2-lite.html

## Return to mock immediately after the test

```sh
docker compose -f docker-compose.yml up -d --no-deps --no-build --force-recreate backend
```

The base file does not forward PARSE_* or the temporary AWS mount; application defaults
return to mock/disabled. The model override is removed along with the credential mount.
Existing meetings/agenda remain in the same DB volume. Do not use down -v.

After returning to mock, remove only the generated session file/directory:

```sh
rm -i -- "$NOVA_AWS_CREDENTIALS_DIR/credentials"
rmdir -- "$NOVA_AWS_CREDENTIALS_DIR"
unset NOVA_AWS_CREDENTIALS_DIR
```

Do not run cleanup on any other directory. Credentials expire regardless of deletion;
expiry is not a reason to keep copies. Neither the helper nor override changes IAM,
Marketplace, Budget, Free Plan, production resources or deployment configuration.
Nova remains a documented deviation from the Claude rubric.

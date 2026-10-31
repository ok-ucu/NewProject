# ADR 0007 — Terraform migration with an explicit import boundary

Date: 2026-10-31. Status: local implementation prepared; import/HCP execution pending.

## Context

Part 2 Lab 7 requires versions.tf, variables.tf, auth.tf, reports.tf, ai.tf,
outputs.tf, temporary imports.tf, HCP Terraform remote execution, lossless import,
a final No changes plan, Makefile/README updates and an Apply finished screenshot
following GitHub push. These are the user-supplied requirements. The exact wording of
Step 6 beyond the requested ADR has not been provided; verify any additional rubric.

The audited account is 591064573673. eu-north-1 has an external Cognito pool/client,
Google IdP/domain, external Aurora and one ECR CloudFormation stack. Reports/AI are
not deployed. us-east-1 API operations are denied by SCP. Source templates are not
proof of resource existence; auth.yaml differs from actual auth settings. Several
previous-lab working changes remain uncommitted and are outside this migration.

## Decision

Translate each existing template resource into Terraform AWS provider resources,
splitting S3 configuration and IAM policies into provider-native resources. Preserve
explicit names, policies, durations, events, timezones, tags, outputs and no-VPC Lambda
behavior. AWS-generated IAM role names remain generated. Keep ECR and Aurora outside
this root. Do not make Terraform wrap or redeploy CloudFormation stacks.

Import only the existing app client; preserve the actual read-only snapshot including
all URLs, Google support, token settings and flows. Pool, domain and IdP are not owned
by auth.yaml and remain external. Prepare the pool/client import ID in imports.tf;
do not execute it in this phase. prevent_destroy protects the configured client from
planned destruction/replacement. It is not equivalent to retaining a removed resource.
Require a reviewed import-only plan with zero updates/destroys before future execution.

Use independent enable_reports and enable_ai gates, default false. All source resources
remain declared. Disabled groups are not completed migration and cannot be used to claim
full-stack No changes. Enabling groups needs actual image/database/SES configuration and
separate cost approval. Preserve the enabled weekly schedule inside the Reports group.
Separate enable_bedrock defaults false; do not invoke a model as part of provisioning.

The cloud block selects HCP organization **ooad-ok-ucu** and workspace **newproject-dev**.
This explicit binding does not establish that remote authentication or a run has succeeded.
AWS OIDC setup is currently blocked by SCP restrictions; the read-only role inventory
found no ready role trusting app.terraform.io. Resolve access with the instructor/account
administrator without claiming an SCP exception or an existing OIDC integration.
HCP apply has not been performed. Pin provider selection via the lock file. Keep state,
private tfvars and tokens out of Git. Later use HCP Remote execution, working directory
infra, approved AWS authentication and manual apply approval (auto-apply disabled).
The HCP VCS workspace must be configured before the required push/evidence workflow.
No HCP organization, IAM OIDC role or paid capability is created by this implementation.

## Alternatives and tradeoffs

Retaining only CloudFormation would not satisfy the lab. Recreating Cognito risks IDs,
URLs and login continuity. Deleting all stacks first risks data loss; no stack deletion
is authorized, and the sole ECR stack is out of scope. Simultaneous CF/Terraform control
of a resource risks drift and conflicting updates. A full unguarded Terraform deployment
would create previously absent services and recurring work, consuming credits.

Explicit gates allow safe local development but postpone full infrastructure migration.
Remote execution centralizes state/history and the evidence workflow, but requires HCP
workspace access and remote AWS credentials; local aws login is not propagated remotely.
Schema validation cannot prove AWS quotas, import fidelity or absence of drift.

## Verification and completion criteria

Local terraform fmt, init -backend=false, validate and git diff --check must pass.
Review the source-to-resource mapping in infra/TERRAFORM.md and the AWS snapshot before
any future import. Stop for unexpected Cognito updates or replacements. After authorized
import, verify No changes for the declared scope. Resolve absent Reports/AI versus the
full rubric explicitly before claiming the whole lab complete. Capture the actual HCP
Apply finished run after an authorized GitHub push; never fabricate a screenshot/run.
No import, plan, apply, destroy, AWS mutation or commit/push was executed in this phase.

## References

- https://developer.hashicorp.com/terraform/language/import/single-resource
- https://developer.hashicorp.com/terraform/cli/commands/validate
- https://developer.hashicorp.com/terraform/cloud-docs/workspaces/settings
- https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cognito_user_pool_client

## Current migration status

Reports and AI remain disabled by default (enable_reports=false, enable_ai=false).
Their declarations are prepared, but this is not evidence of deployed resources or a
completed migration. Full CloudFormation migration, lossless import, a final No changes
plan and HCP Apply finished evidence remain unconfirmed. The configured workspace binding
does not remove the SCP blocker or imply that any HCP apply has occurred.

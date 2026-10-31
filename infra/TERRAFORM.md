# CloudFormation → Terraform coverage

This root includes every resource from auth.yaml, reports.yml and ai.yml. Configuration
is local only: no imported state, AWS changes, HCP run or No changes plan is claimed.

| CloudFormation logical ID | Terraform resource(s) |
|---|---|
| UserPoolClient | aws_cognito_user_pool_client.existing (actual AWS snapshot overrides outdated template values) |
| ReportsBucket | aws_s3_bucket.reports and aws_s3_bucket_{public_access_block,ownership_controls,server_side_encryption_configuration,lifecycle_configuration,notification}.reports |
| ReportRequestsDlq | aws_sqs_queue.report_dlq |
| ReportRequestsQueue | aws_sqs_queue.report_requests |
| ReportBuilderLogGroup | aws_cloudwatch_log_group.report_builder |
| ReportBuilderRole | aws_iam_role.report_builder; policy attachment report_builder_logs; policies write_reports, consume_reports, report_database |
| ReportBuilder | aws_lambda_function.report_builder |
| ReportMailerLogGroup | aws_cloudwatch_log_group.report_mailer |
| ReportMailerRole | aws_iam_role.report_mailer; policy attachment report_mailer_logs; policy read_reports_send_email |
| ReportMailer | aws_lambda_function.report_mailer |
| ReportMailerInvokePermission | aws_lambda_permission.report_mailer |
| ReportRequestsEventSource | aws_lambda_event_source_mapping.report_requests |
| WeeklyReportSchedulerRole | aws_iam_role.report_scheduler; policy schedule_reports |
| WeeklyReportSchedule | aws_scheduler_schedule.weekly_report |
| ParserLogs | aws_cloudwatch_log_group.parser |
| ParserRole | aws_iam_role.parser; policies parser_logs and conditional parser_bedrock |
| Parser | aws_lambda_function.parser |
| Api | aws_apigatewayv2_api.parser |
| Authorizer | aws_apigatewayv2_authorizer.cognito |
| Integration | aws_apigatewayv2_integration.parser |
| ParseRoute | aws_apigatewayv2_route.parse |
| Stage | aws_apigatewayv2_stage.parser |
| InvokePermission | aws_lambda_permission.parser |

All Reports resources use enable_reports; all AI infrastructure uses enable_ai, with
Bedrock IAM/provider additionally controlled by enable_bedrock. Existing outputs are
preserved in snake_case; disabled groups return null. AWS-generated IAM role names stay
generated. CF inline policies are split into role-policy resources retaining policy names.

The S3 dependency is bucket → mailer notification (after invoke permission), with mailer
IAM source ARN constructed from the deterministic bucket name. This avoids the CF-style
bucket/role notification cycle. Encryption/ownership/public access/90-day lifecycle remain
separate settings on that same bucket. Terraform force_destroy=false preserves the CF
behavior that a non-empty bucket is not automatically emptied on deletion. No destroy
operation is authorized. No VPC, SES identity, ECR repository, Cognito pool/domain/IdP or
Aurora resource has been added.

Auth snapshot 2026-10-31: no secret, refresh token 5 days, access/ID 60 minutes, session
3 minutes; flows REFRESH_TOKEN_AUTH, USER_AUTH, USER_SRP_AUTH; code OAuth and email/openid/
profile scopes; revocation enabled and additional user-context propagation disabled.
Callback/logout/default redirect values are copied exactly in auth.tf, including the
CloudFront callback with no /login/ suffix. No ignore_changes masks auth drift.
Read/write attributes, rotation and analytics are omitted where the AWS response omits
configuration. Import/refresh plan must verify provider interpretation before any apply.

HCP prerequisites and command safety are documented in README.md and ADR 0007. Remote
state and execution are prepared, not configured. Full Moodle completion still requires
approved import, reviewed scope, actual No changes plan and HCP Apply finished evidence.


## Deployment lifecycle controls and ordering

`enable_reports` and `enable_ai` are deployment lifecycle controls, **not pause switches**.
They remain false by default because these resource groups are not yet deployed. After
resources enter Terraform state, changing a flag from true to false makes their `count`
zero and can plan destruction of the whole group, including logs, queues and Lambdas.
Do not toggle a flag to stop processing. Pausing an existing service requires a separately
reviewed change to its schedule/event-source/provider settings. Review all destruction
and replacement actions; a disabled-group No changes result is not full migration.

The report builder explicitly waits for S3 notification installation (including mailer
invoke permission), public-access blocking, ownership, encryption and lifecycle settings.
The SQS event source depends on the builder, so processing cannot start before this
readiness chain finishes. Scheduler messages may queue earlier and remain queued until
the event source is ready. Notification depends on the mailer, not the builder; mailer
IAM uses a deterministic bucket ARN. This keeps the resource dependency graph acyclic.

## Retention and state handoff (future, separately authorized operations)

CloudFormation Retain and Terraform prevent_destroy are not equivalent. prevent_destroy
protects the configured Cognito client from planned destruction/replacement, but removing
its resource block removes that protection. Never delete a resource block, toggle a gate,
remove state or delete a stack merely to silence a plan.

1. Inventory current IDs, owning stack/state, dependencies and exact settings; capture
   necessary data backups and private state backups outside Git. Establish one manager
   per resource. ECR stays in CloudFormation and Aurora remains external here.
2. For a future CF-owned resource transfer, arrange and verify DeletionPolicy: Retain
   and UpdateReplacePolicy: Retain under separate AWS authorization before removing the
   resource from CF management. Do not delete a stack as a migration shortcut. The audited
   app client is external to CF, so that CF transfer step is not needed for this client.
3. Review the destination configuration/import IDs and an import-only plan. Stop for any
   update, deletion or replacement. Execute import only with explicit authorization, then
   obtain a genuine No changes plan before retiring the temporary import declaration.
4. If intentionally handing a Terraform-owned resource to another manager, use a reviewed
   `removed` block with `lifecycle { destroy = false }` (supported by this root's Terraform
   constraint), or an explicitly authorized state-only handoff procedure. Inspect and
   approve the plan before executing it. Preserve the physical resource, verify its ID
   and complete destination adoption; coordinate the transition to avoid conflicting
   writers. State changes still require authorization even if AWS objects are retained.
5. Keep old templates and rollback/state records until ownership and data retention are
   verified. No retention, import, state handoff or AWS operation was executed here.

## Prefixes and Cognito baseline

The source defaults intentionally differ: Auth/Reports `project_name=meetings`, AI
`ai_project_name=new-project`. Earlier deploy scripts may pass `new-project` to Reports.
Before provisioning/adoption, explicitly select the actual prefix; never rename existing
resources to match a default. Prefix changes can replace named resources or create a
parallel deployment. The default enable flags and prefixes have not been changed.

`auth.yaml` contains **older Cognito settings**, including 30-day refresh validity and a
smaller explicit-auth-flow list. `auth.tf` follows the 2026-10-31 read-only AWS snapshot:
5-day refresh validity, ALLOW_USER_AUTH and exact callback/logout/default-redirect values.
Do not revert Terraform to the older template for textual parity. Keep the pool, Google
IdP and domain external, and require a live authorized import/refresh plan to establish
that this snapshot still matches AWS. Neither format alone proves current live settings.

Input validations preserve source constraints for DB identifiers, SES email/identity,
Cognito pool IDs and model IDs. Empty Reports-specific inputs remain usable while Reports
is disabled; empty model IDs are permitted only while AI is disabled. Nonempty email/model
values must match their source patterns. Existing enable-time required-input checks remain.

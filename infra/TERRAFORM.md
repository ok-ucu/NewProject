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

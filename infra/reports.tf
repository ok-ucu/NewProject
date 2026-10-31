# Full reports.yml translation. Disabled resources are NOT a completed migration.
resource "aws_s3_bucket" "reports" {
  count  = var.enable_reports ? 1 : 0
  bucket = local.reports_name
  tags   = local.reports_tags
  # CF Delete does not empty non-empty buckets; preserve that safety behavior.
  force_destroy = false
}
resource "aws_s3_bucket_public_access_block" "reports" {
  count                   = var.enable_reports ? 1 : 0
  bucket                  = aws_s3_bucket.reports[0].id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
resource "aws_s3_bucket_ownership_controls" "reports" {
  count  = var.enable_reports ? 1 : 0
  bucket = aws_s3_bucket.reports[0].id
  rule { object_ownership = "BucketOwnerEnforced" }
}
resource "aws_s3_bucket_server_side_encryption_configuration" "reports" {
  count  = var.enable_reports ? 1 : 0
  bucket = aws_s3_bucket.reports[0].id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}
resource "aws_s3_bucket_lifecycle_configuration" "reports" {
  count  = var.enable_reports ? 1 : 0
  bucket = aws_s3_bucket.reports[0].id
  rule {
    id     = "ExpireWeeklyReportsAfter90Days"
    status = "Enabled"
    filter { prefix = "" }
    expiration { days = 90 }
  }
}
resource "aws_s3_bucket_notification" "reports" {
  count  = var.enable_reports ? 1 : 0
  bucket = aws_s3_bucket.reports[0].id
  lambda_function {
    lambda_function_arn = aws_lambda_function.report_mailer[0].arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "reports/"
    filter_suffix       = ".csv"
  }
  depends_on = [aws_lambda_permission.report_mailer]
}
resource "aws_sqs_queue" "report_dlq" {
  count                     = var.enable_reports ? 1 : 0
  name                      = "${var.project_name}-report-requests-dlq"
  message_retention_seconds = 1209600
  tags                      = local.reports_tags
}
resource "aws_sqs_queue" "report_requests" {
  count                      = var.enable_reports ? 1 : 0
  name                       = "${var.project_name}-report-requests"
  visibility_timeout_seconds = 540
  redrive_policy             = jsonencode({ deadLetterTargetArn = aws_sqs_queue.report_dlq[0].arn, maxReceiveCount = 3 })
  tags                       = local.reports_tags
}
resource "aws_cloudwatch_log_group" "report_builder" {
  count             = var.enable_reports ? 1 : 0
  name              = "/${var.project_name}/weekly-report-builder"
  retention_in_days = 7
}
resource "aws_cloudwatch_log_group" "report_mailer" {
  count             = var.enable_reports ? 1 : 0
  name              = "/${var.project_name}/report-mailer"
  retention_in_days = 7
}
# CF does not specify RoleName: let Terraform generate names as well.
resource "aws_iam_role" "report_builder" {
  count              = var.enable_reports ? 1 : 0
  assume_role_policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Principal = { Service = "lambda.amazonaws.com" }, Action = "sts:AssumeRole" }] })
  tags               = { Project = var.project_name }
}
resource "aws_iam_role_policy_attachment" "report_builder_logs" {
  count      = var.enable_reports ? 1 : 0
  role       = aws_iam_role.report_builder[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
resource "aws_iam_role_policy" "write_reports" {
  count  = var.enable_reports ? 1 : 0
  name   = "WriteWeeklyReports"
  role   = aws_iam_role.report_builder[0].id
  policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Action = "s3:PutObject", Resource = "${aws_s3_bucket.reports[0].arn}/reports/*" }] })
}
resource "aws_iam_role_policy" "consume_reports" {
  count  = var.enable_reports ? 1 : 0
  name   = "ConsumeReportRequests"
  role   = aws_iam_role.report_builder[0].id
  policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Action = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"], Resource = aws_sqs_queue.report_requests[0].arn }] })
}
resource "aws_iam_role_policy" "report_database" {
  count  = var.enable_reports ? 1 : 0
  name   = "ConnectToAuroraExpress"
  role   = aws_iam_role.report_builder[0].id
  policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Action = "rds-db:connect", Resource = "arn:${local.partition}:rds-db:${var.aws_region}:${local.account_id}:dbuser:${var.database_resource_id}/${var.db_user}" }] })
}
resource "aws_lambda_function" "report_builder" {
  count         = var.enable_reports ? 1 : 0
  function_name = "${var.project_name}-report-builder"
  package_type  = "Image"
  image_uri     = var.reports_image_uri
  architectures = ["arm64"]
  memory_size   = 512
  timeout       = 90
  role          = aws_iam_role.report_builder[0].arn
  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.report_builder[0].name
  }
  environment {
    variables = {
      REPORTS_BUCKET      = aws_s3_bucket.reports[0].id
      DATABASE_URL        = "postgresql+asyncpg://${var.db_user}@${var.database_host}:5432/${var.db_name}"
      DB_IAM_AUTH_ENABLED = "true"
      RDS_CA_BUNDLE       = "/etc/ssl/certs/rds-global-bundle.pem"
      DB_POOL_SIZE        = "1"
      DB_MAX_OVERFLOW     = "0"
    }
  }
  tags       = local.reports_tags
  depends_on = [aws_iam_role_policy_attachment.report_builder_logs, aws_iam_role_policy.write_reports, aws_iam_role_policy.consume_reports, aws_iam_role_policy.report_database]
}
resource "aws_iam_role" "report_mailer" {
  count              = var.enable_reports ? 1 : 0
  assume_role_policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Principal = { Service = "lambda.amazonaws.com" }, Action = "sts:AssumeRole" }] })
  tags               = { Project = var.project_name }
}
resource "aws_iam_role_policy_attachment" "report_mailer_logs" {
  count      = var.enable_reports ? 1 : 0
  role       = aws_iam_role.report_mailer[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
resource "aws_iam_role_policy" "read_reports_send_email" {
  count = var.enable_reports ? 1 : 0
  name  = "ReadReportsAndSendEmail"
  role  = aws_iam_role.report_mailer[0].id
  policy = jsonencode({ Version = "2012-10-17", Statement = [
    { Sid = "ReadReportObjects", Effect = "Allow", Action = "s3:GetObject", Resource = "arn:${local.partition}:s3:::${local.reports_name}/reports/*" },
    { Sid = "SendFromVerifiedIdentity", Effect = "Allow", Action = "ses:SendEmail", Resource = "arn:${local.partition}:ses:${var.aws_region}:${local.account_id}:identity/${var.ses_identity_name}" }
  ] })
}
resource "aws_lambda_function" "report_mailer" {
  count         = var.enable_reports ? 1 : 0
  function_name = "${var.project_name}-report-mailer"
  package_type  = "Image"
  image_uri     = var.reports_image_uri
  image_config { command = ["app.reports.mailer.handler"] }
  architectures = ["arm64"]
  memory_size   = 256
  timeout       = 60
  role          = aws_iam_role.report_mailer[0].arn
  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.report_mailer[0].name
  }
  environment {
    variables = { REPORT_EMAIL_SENDER = var.ses_sender_email, REPORT_EMAIL_RECIPIENT = var.ses_recipient_email }
  }
  tags       = local.reports_tags
  depends_on = [aws_iam_role_policy_attachment.report_mailer_logs, aws_iam_role_policy.read_reports_send_email]
}
resource "aws_lambda_permission" "report_mailer" {
  count          = var.enable_reports ? 1 : 0
  function_name  = aws_lambda_function.report_mailer[0].arn
  action         = "lambda:InvokeFunction"
  principal      = "s3.amazonaws.com"
  source_account = local.account_id
  source_arn     = "arn:${local.partition}:s3:::${local.reports_name}"
}
resource "aws_lambda_event_source_mapping" "report_requests" {
  count            = var.enable_reports ? 1 : 0
  event_source_arn = aws_sqs_queue.report_requests[0].arn
  function_name    = aws_lambda_function.report_builder[0].arn
  batch_size       = 1
  enabled          = true
}
resource "aws_iam_role" "report_scheduler" {
  count              = var.enable_reports ? 1 : 0
  assume_role_policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Principal = { Service = "scheduler.amazonaws.com" }, Action = "sts:AssumeRole" }] })
  tags               = { Project = var.project_name }
}
resource "aws_iam_role_policy" "schedule_reports" {
  count  = var.enable_reports ? 1 : 0
  name   = "SendReportRequest"
  role   = aws_iam_role.report_scheduler[0].id
  policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Action = "sqs:SendMessage", Resource = aws_sqs_queue.report_requests[0].arn }] })
}
resource "aws_scheduler_schedule" "weekly_report" {
  count                        = var.enable_reports ? 1 : 0
  name                         = "${var.project_name}-weekly-report"
  description                  = "Build the previous ISO-week meetings CSV every Monday at 07:00 Kyiv time."
  state                        = "ENABLED"
  schedule_expression          = "cron(0 7 ? * MON *)"
  schedule_expression_timezone = "Europe/Kyiv"
  flexible_time_window { mode = "OFF" }
  target {
    arn      = aws_sqs_queue.report_requests[0].arn
    role_arn = aws_iam_role.report_scheduler[0].arn
    input    = "{\"week\":null,\"source\":\"schedule\"}"
  }
  depends_on = [aws_iam_role_policy.schedule_reports]
}

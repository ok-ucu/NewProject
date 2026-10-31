output "project_name" {
  value = var.project_name
}
output "user_pool_id" {
  value = var.cognito_user_pool_id
}
output "user_pool_client_id" {
  value = aws_cognito_user_pool_client.existing.id
}
output "reports_bucket_name" {
  value = try(aws_s3_bucket.reports[0].id, null)
}
output "reports_bucket_arn" {
  value = try(aws_s3_bucket.reports[0].arn, null)
}
output "report_builder_function_name" {
  value = try(aws_lambda_function.report_builder[0].function_name, null)
}
output "report_mailer_function_name" {
  value = try(aws_lambda_function.report_mailer[0].function_name, null)
}
output "weekly_report_schedule_name" {
  value = try(aws_scheduler_schedule.weekly_report[0].name, null)
}
output "reports_queue_url" {
  value = try(aws_sqs_queue.report_requests[0].url, null)
}
output "reports_queue_arn" {
  value = try(aws_sqs_queue.report_requests[0].arn, null)
}
output "reports_dlq_arn" {
  value = try(aws_sqs_queue.report_dlq[0].arn, null)
}
output "parse_url" {
  value = try("${aws_apigatewayv2_api.parser[0].api_endpoint}/api/parse", null)
}
output "parser_log_group" {
  value = try(aws_cloudwatch_log_group.parser[0].name, null)
}

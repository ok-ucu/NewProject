# ai.yml translation. Infrastructure and paid model access are separate opt-ins.
resource "aws_cloudwatch_log_group" "parser" {
  count             = var.enable_ai ? 1 : 0
  name              = "/${var.ai_project_name}/ai-parser"
  retention_in_days = 7
  tags              = local.ai_tags
}
resource "aws_iam_role" "parser" {
  count              = var.enable_ai ? 1 : 0
  assume_role_policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Principal = { Service = "lambda.amazonaws.com" }, Action = "sts:AssumeRole" }] })
  tags               = local.ai_tags
}
resource "aws_iam_role_policy" "parser_logs" {
  count = var.enable_ai ? 1 : 0
  name  = "ParserLogs"
  role  = aws_iam_role.parser[0].id
  # CF LogGroup.Arn includes the trailing :*.
  policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Action = ["logs:CreateLogStream", "logs:PutLogEvents"], Resource = "${aws_cloudwatch_log_group.parser[0].arn}:*" }] })
}
resource "aws_iam_role_policy" "parser_bedrock" {
  count = var.enable_ai && var.enable_bedrock ? 1 : 0
  name  = "InvokeSelectedModelOnly"
  role  = aws_iam_role.parser[0].id
  policy = jsonencode({ Version = "2012-10-17", Statement = [
    { Effect = "Allow", Action = "bedrock:InvokeModel", Resource = "arn:${local.partition}:bedrock:${var.aws_region}:${local.account_id}:inference-profile/${var.model_profile_id}" },
    { Effect = "Allow", Action = "bedrock:InvokeModel", Resource = "arn:${local.partition}:bedrock:*::foundation-model/${var.foundation_model_id}", Condition = { StringEquals = { "bedrock:InferenceProfileArn" = "arn:${local.partition}:bedrock:${var.aws_region}:${local.account_id}:inference-profile/${var.model_profile_id}" } } }
  ] })
}
resource "aws_lambda_function" "parser" {
  count         = var.enable_ai ? 1 : 0
  function_name = "${var.ai_project_name}-ai-parser"
  package_type  = "Image"
  image_uri     = var.ai_image_uri
  architectures = ["arm64"]
  role          = aws_iam_role.parser[0].arn
  memory_size   = 512
  timeout       = 40
  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.parser[0].name
  }
  environment {
    variables = {
      PARSE_PROVIDER        = var.enable_bedrock ? "bedrock" : "mock"
      PARSE_BEDROCK_ENABLED = tostring(var.enable_bedrock)
      PARSE_BEDROCK_API     = var.bedrock_api
      PARSER_MODEL          = var.model_profile_id
      PARSE_MODEL_ID        = var.model_profile_id
      PARSE_REGION          = var.aws_region
    }
  }
  tags       = local.ai_tags
  depends_on = [aws_iam_role_policy.parser_logs, aws_iam_role_policy.parser_bedrock]
}
resource "aws_apigatewayv2_api" "parser" {
  count         = var.enable_ai ? 1 : 0
  name          = "${var.ai_project_name}-ai"
  protocol_type = "HTTP"
  cors_configuration {
    allow_origins = [var.frontend_origin]
    allow_methods = ["POST"]
    allow_headers = ["Content-Type", "Authorization"]
  }
  tags = local.ai_tags
}
resource "aws_apigatewayv2_authorizer" "cognito" {
  count            = var.enable_ai ? 1 : 0
  api_id           = aws_apigatewayv2_api.parser[0].id
  name             = "CognitoJWT"
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]
  jwt_configuration {
    audience = [aws_cognito_user_pool_client.existing.id]
    issuer   = "https://cognito-idp.${var.aws_region}.amazonaws.com/${var.cognito_user_pool_id}"
  }
}
resource "aws_apigatewayv2_integration" "parser" {
  count                  = var.enable_ai ? 1 : 0
  api_id                 = aws_apigatewayv2_api.parser[0].id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.parser[0].arn
  payload_format_version = "2.0"
  timeout_milliseconds   = 30000
}
resource "aws_apigatewayv2_route" "parse" {
  count              = var.enable_ai ? 1 : 0
  api_id             = aws_apigatewayv2_api.parser[0].id
  route_key          = "POST /api/parse"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito[0].id
  target             = "integrations/${aws_apigatewayv2_integration.parser[0].id}"
}
resource "aws_apigatewayv2_stage" "parser" {
  count       = var.enable_ai ? 1 : 0
  api_id      = aws_apigatewayv2_api.parser[0].id
  name        = "$default"
  auto_deploy = true
  default_route_settings {
    throttling_burst_limit = 2
    throttling_rate_limit  = 1
  }
  tags = local.ai_tags
}
resource "aws_lambda_permission" "parser" {
  count          = var.enable_ai ? 1 : 0
  function_name  = aws_lambda_function.parser[0].function_name
  action         = "lambda:InvokeFunction"
  principal      = "apigateway.amazonaws.com"
  source_account = local.account_id
  source_arn     = "${aws_apigatewayv2_api.parser[0].execution_arn}/*/POST/api/parse"
}

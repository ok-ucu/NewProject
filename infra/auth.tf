# auth.yaml manages only the app client. Pool/domain/Google IdP remain external.
# Read-only snapshot: 2026-10-31. Intentionally preserve actual AWS settings where
# auth.yaml differs (refresh 5 days, ALLOW_USER_AUTH, exact URLs and default redirect).
resource "aws_cognito_user_pool_client" "existing" {
  name                                          = "SpryMeetings"
  user_pool_id                                  = var.cognito_user_pool_id
  # generate_secret is omitted to preserve the imported Cognito client.
  access_token_validity                         = 60
  id_token_validity                             = 60
  refresh_token_validity                        = 5
  auth_session_validity                         = 3
  explicit_auth_flows                           = ["ALLOW_REFRESH_TOKEN_AUTH", "ALLOW_USER_AUTH", "ALLOW_USER_SRP_AUTH"]
  supported_identity_providers                  = ["COGNITO", "Google"]
  allowed_oauth_flows_user_pool_client          = true
  allowed_oauth_flows                           = ["code"]
  allowed_oauth_scopes                          = ["email", "openid", "profile"]
  callback_urls                                 = ["http://localhost:3000/login/", "https://d84l1y8p4kdic.cloudfront.net"]
  logout_urls                                   = ["http://localhost:3000/login/"]
  default_redirect_uri                          = "http://localhost:3000/login/"
  prevent_user_existence_errors                 = "ENABLED"
  enable_token_revocation                       = true
  enable_propagate_additional_user_context_data = false
  # API omits read/write attributes when defaults apply. Do not invent lists.
  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }
  lifecycle {
    prevent_destroy = true
  }
}

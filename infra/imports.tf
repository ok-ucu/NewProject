# TEMPORARY: review-only preparation. No import/apply has been executed.
# Remove only AFTER successful, separately approved import and a no-change plan.
import {
  to = aws_cognito_user_pool_client.existing
  id = "${var.cognito_user_pool_id}/${var.cognito_client_id}"
}

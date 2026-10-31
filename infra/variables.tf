variable "aws_region" {
  type        = string
  default     = "eu-north-1"
  description = "Only audited region; us-east-1 is denied by SCP."
  nullable    = false
  validation {
    condition     = var.aws_region == "eu-north-1"
    error_message = "Only eu-north-1 is audited and allowed for this lab."
  }
}

variable "aws_account_id" {
  type        = string
  default     = "591064573673"
  description = "Audited AWS account; prevents targeting another account."
  nullable    = false
}

variable "project_name" {
  type        = string
  default     = "meetings"
  description = "auth.yaml/reports.yml ProjectName default; set new-project only if deliberately selected."
  nullable    = false
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*$", var.project_name)) && length(var.project_name) <= 30
    error_message = "Use lowercase project names; reports names have a 30-character limit."
  }
}

variable "ai_project_name" {
  type        = string
  default     = "new-project"
  description = "ai.yml ProjectName default."
  nullable    = false
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*$", var.ai_project_name))
    error_message = "Use lowercase project names; reports names have a 30-character limit."
  }
}

variable "cognito_user_pool_id" {
  type        = string
  default     = "eu-north-1_TvbEOosgs"
  description = "Existing pool; not created or managed here."
  nullable    = false
}

variable "cognito_client_id" {
  type        = string
  default     = "d23v4ermc868pe0r78f8ddm1l"
  description = "Existing client ID used solely for prepared import."
  nullable    = false
}

variable "enable_reports" {
  type        = bool
  default     = false
  description = "Explicit opt-in for all reports resources; false is NOT completed migration."
  nullable    = false
  validation {
    condition     = !var.enable_reports || alltrue([for value in [var.reports_image_uri, var.database_host, var.database_resource_id, var.ses_sender_email, var.ses_recipient_email, var.ses_identity_name] : length(trimspace(value)) > 0])
    error_message = "Enabling Reports requires real image, database and SES inputs. No placeholder infrastructure is provisioned."
  }
}

variable "enable_ai" {
  type        = bool
  default     = false
  description = "Explicit opt-in for all AI infrastructure; false is NOT completed migration."
  nullable    = false
  validation {
    condition     = !var.enable_ai || length(trimspace(var.ai_image_uri)) > 0
    error_message = "Enabling AI requires an existing parser image URI."
  }
}

variable "enable_bedrock" {
  type        = bool
  default     = false
  description = "Separately enables IAM model invocation and real parser provider."
  nullable    = false
}

variable "reports_image_uri" {
  type        = string
  default     = ""
  description = "Existing arm64 reports ECR image; no image is created by this configuration."
  nullable    = false
}

variable "ai_image_uri" {
  type        = string
  default     = ""
  description = "Existing arm64 parser ECR image; no image is created by this configuration."
  nullable    = false
}

variable "database_host" {
  type        = string
  default     = ""
  description = "External existing Aurora endpoint; no database is created."
  nullable    = false
}

variable "database_resource_id" {
  type        = string
  default     = ""
  description = "External RDS cluster resource ID for IAM auth."
  nullable    = false
}

variable "db_user" {
  type        = string
  default     = "meetings"
  description = "Existing DB user; must match external database."
  nullable    = false
}

variable "db_name" {
  type        = string
  default     = "meetings"
  description = "Existing DB name."
  nullable    = false
}

variable "ses_sender_email" {
  type        = string
  default     = ""
  description = "Existing verified SES sender; supply privately, not in git."
  nullable    = false
  sensitive   = true
}

variable "ses_recipient_email" {
  type        = string
  default     = ""
  description = "Report recipient; supply privately, not in git."
  nullable    = false
  sensitive   = true
}

variable "ses_identity_name" {
  type        = string
  default     = ""
  description = "Existing verified SES identity; not created here."
  nullable    = false
  sensitive   = true
}

variable "frontend_origin" {
  type        = string
  default     = "http://localhost:3000"
  description = "Exact origin for AI API CORS."
  nullable    = false
}

variable "bedrock_api" {
  type        = string
  default     = "anthropic"
  description = "Preserves ai.yml default; Nova needs converse and matching model IDs."
  nullable    = false
  validation {
    condition     = contains(["anthropic", "converse"], var.bedrock_api)
    error_message = "Use anthropic or converse."
  }
}

variable "model_profile_id" {
  type        = string
  default     = "eu.anthropic.claude-haiku-5-5"
  description = "ai.yml default; no model invocation occurs at validation."
  nullable    = false
}

variable "foundation_model_id" {
  type        = string
  default     = "anthropic.claude-haiku-5-5"
  description = "Must match the selected profile when enabling Bedrock."
  nullable    = false
}

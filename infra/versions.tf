terraform {
  required_version = ">= 1.9, < 2.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
  # HCP organization/workspace must be supplied before backend initialization.
  # init -backend=false validates locally without configuring or creating a workspace.
  cloud {
    organization = "ooad-ok-ucu"

    workspaces {
      name = "newproject-dev"
    }
  }
}

provider "aws" {
  region              = var.aws_region
  allowed_account_ids = [var.aws_account_id]
}

data "aws_partition" "current" {}
data "aws_caller_identity" "current" {}

locals {
  partition    = data.aws_partition.current.partition
  account_id   = data.aws_caller_identity.current.account_id
  reports_name = "${var.project_name}-${local.account_id}-${var.aws_region}-reports"
  reports_tags = { Project = var.project_name, Purpose = "weekly-reports" }
  ai_tags      = { PROJECT_NAME = var.ai_project_name }
}

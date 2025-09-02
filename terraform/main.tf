terraform {
required_version = ">= 1.6.0"
required_providers { aws = { source = "hashicorp/aws", version = ">= 5.0" } }
}
provider "aws" { region = var.region }


locals { name = var.project_name }


# S3 Bucket - use data source to reference existing bucket
data "aws_s3_bucket" "artifacts" {
  bucket = "${local.name}-artifacts-${var.account_id}"
}


# ECR for inference image - use data source to reference existing repository
data "aws_ecr_repository" "inference" { 
  name = "${local.name}-inference"
}


# IAM: SageMaker Execution Role (simplified managed policies; tighten later)
data "aws_iam_role" "sagemaker_role" {
  name = "${local.name}-sagemaker-role"
}


# Note: IAM role and policy attachments are managed outside of Terraform for existing roles


# SageMaker Model - use data source to reference existing model
data "aws_sagemaker_model" "model" {
  name = "${local.name}-model"
}


# SageMaker Endpoint Configuration - use data source to reference existing config
data "aws_sagemaker_endpoint_configuration" "cfg" {
  name = "${local.name}-cfg"
}


# SageMaker Endpoint - use data source to reference existing endpoint
data "aws_sagemaker_endpoint" "ep" {
  name = "${local.name}-ep"
}


# CloudWatch Alarm on Latency
resource "aws_cloudwatch_metric_alarm" "latency" {
alarm_name = "${local.name}-latency"
namespace = var.cw_namespace
metric_name = "LatencyMs"
statistic = "Average"
period = 60
evaluation_periods = 1
threshold = 200
comparison_operator = "GreaterThanThreshold"
}
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


# SageMaker Model
resource "aws_sagemaker_model" "model" {
name = "${local.name}-model"
execution_role_arn = data.aws_iam_role.sagemaker_role.arn
primary_container {
image = var.ecr_image_uri
mode = "SingleModel"
model_data_url = var.model_data_url # s3://.../model.tar.gz
container_hostname = "inference"
environment = { "CW_NAMESPACE" = "${local.name}" }
}
}


resource "aws_sagemaker_endpoint_configuration" "cfg" {
name = "${local.name}-cfg"
production_variants {
variant_name = "All"
model_name = aws_sagemaker_model.model.name
initial_instance_count = 1
instance_type = var.instance_type
}
}


resource "aws_sagemaker_endpoint" "ep" {
name = "${local.name}-ep"
endpoint_config_name = aws_sagemaker_endpoint_configuration.cfg.name
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
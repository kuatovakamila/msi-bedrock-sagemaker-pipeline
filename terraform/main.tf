terraform {
required_version = ">= 1.6.0"
required_providers { aws = { source = "hashicorp/aws", version = ">= 5.0" } }
}
provider "aws" { region = var.region }


locals { name = var.project_name }


# Buckets
module "artifacts" {
source = "terraform-aws-modules/s3-bucket/aws"
bucket = "${local.name}-artifacts-${var.account_id}"
force_destroy = true
}


# ECR for inference image
resource "aws_ecr_repository" "inference" { name = "${local.name}-inference" }


# IAM: SageMaker Execution Role (simplified managed policies; tighten later)
resource "aws_iam_role" "sagemaker_role" {
name = "${local.name}-sagemaker-role"
assume_role_policy = data.aws_iam_policy_document.sagemaker_assume.json
}


data "aws_iam_policy_document" "sagemaker_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["sagemaker.amazonaws.com"]
    }
  }
}
resource "aws_iam_role_policy_attachment" "sm_full" {
role = aws_iam_role.sagemaker_role.name
policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}
resource "aws_iam_role_policy_attachment" "s3_read" {
role = aws_iam_role.sagemaker_role.name
policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}


# SageMaker Model
resource "aws_sagemaker_model" "model" {
name = "${local.name}-model"
execution_role_arn = aws_iam_role.sagemaker_role.arn
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
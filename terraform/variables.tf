variable "region" {
  type    = string
  default = "us-east-1"
}
variable "project_name" {
  type    = string
  default = "msi-anomaly"
}

variable "account_id" {
  type = string
}

variable "ecr_image_uri" {
  type = string
}

variable "model_data_url" {
  type = string
}

variable "instance_type" {
  type    = string
  default = "ml.t2.medium"
}

variable "cw_namespace" {
  type    = string
  default = "MSI/AnomalyService"
}
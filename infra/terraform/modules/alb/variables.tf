variable "environment" {
  description = "環境名"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "public_subnets" {
  description = "パブリックサブネットIDのリスト"
  type        = list(string)
}

variable "backend_target_group_arn" {
  description = "バックエンドTarget Group ARN"
  type        = string
}

variable "frontend_target_group_arn" {
  description = "フロントエンドTarget Group ARN"
  type        = string
}


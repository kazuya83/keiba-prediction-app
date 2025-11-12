variable "environment" {
  description = "環境名"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "private_subnets" {
  description = "プライベートサブネットIDのリスト"
  type        = list(string)
}

variable "db_name" {
  description = "データベース名"
  type        = string
}

variable "db_username" {
  description = "データベースユーザー名"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "データベースパスワード"
  type        = string
  sensitive   = true
}

variable "allowed_security_groups" {
  description = "RDSへのアクセスを許可するセキュリティグループIDのリスト"
  type        = list(string)
  default     = []
}


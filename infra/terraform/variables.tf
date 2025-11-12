variable "aws_region" {
  description = "AWSリージョン"
  type        = string
  default     = "ap-northeast-1"
}

variable "environment" {
  description = "環境名（staging, production）"
  type        = string
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "環境名は staging または production である必要があります。"
  }
}

variable "vpc_cidr" {
  description = "VPCのCIDRブロック"
  type        = string
  default     = "10.0.0.0/16"
}

variable "backend_image_tag" {
  description = "バックエンドDockerイメージのタグ"
  type        = string
  default     = "latest"
}

variable "frontend_image_tag" {
  description = "フロントエンドDockerイメージのタグ"
  type        = string
  default     = "latest"
}

variable "ml_image_tag" {
  description = "ML推論サーバーDockerイメージのタグ"
  type        = string
  default     = "latest"
}

variable "database_url" {
  description = "データベース接続URL（機密情報のため、環境変数またはSecrets Managerから取得）"
  type        = string
  sensitive   = true
}

variable "db_name" {
  description = "データベース名"
  type        = string
  default     = "keiba"
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

variable "allowed_cidr_blocks" {
  description = "ALBへのアクセスを許可するCIDRブロックのリスト"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "alert_emails" {
  description = "アラート通知先メールアドレスのリスト"
  type        = list(string)
  default     = []
}

variable "slack_webhook_url" {
  description = "Slack Webhook URL（オプション）"
  type        = string
  default     = null
  sensitive   = true
}


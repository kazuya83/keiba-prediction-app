variable "environment" {
  description = "環境名"
  type        = string
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


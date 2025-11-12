variable "environment" {
  description = "環境名"
  type        = string
}

variable "alarm_sns_topic_arn" {
  description = "アラート通知用SNSトピックARN（オプション）"
  type        = string
  default     = null
}


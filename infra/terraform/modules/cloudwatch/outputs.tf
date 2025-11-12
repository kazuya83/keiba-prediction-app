output "log_group_names" {
  description = "CloudWatch Log Group名のリスト"
  value = [
    aws_cloudwatch_log_group.application.name,
    aws_cloudwatch_log_group.errors.name,
  ]
}


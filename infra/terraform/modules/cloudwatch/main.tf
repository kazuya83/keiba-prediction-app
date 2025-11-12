# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "application" {
  name              = "/${var.environment}/keiba/application"
  retention_in_days = 30

  tags = {
    Name = "${var.environment}-keiba-application-logs"
  }
}

resource "aws_cloudwatch_log_group" "errors" {
  name              = "/${var.environment}/keiba/errors"
  retention_in_days = 90

  tags = {
    Name = "${var.environment}-keiba-errors-logs"
  }
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "high_error_rate" {
  alarm_name          = "${var.environment}-keiba-high-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods = "2"
  metric_name         = "ErrorCount"
  namespace           = "Keiba"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "エラー率が閾値を超えています"
  alarm_actions       = var.alarm_sns_topic_arn != null ? [var.alarm_sns_topic_arn] : []

  tags = {
    Name = "${var.environment}-keiba-high-error-rate"
  }
}

resource "aws_cloudwatch_metric_alarm" "high_response_time" {
  alarm_name          = "${var.environment}-keiba-high-response-time"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ResponseTime"
  namespace           = "Keiba"
  period              = "300"
  statistic           = "Average"
  threshold           = "1000"
  alarm_description   = "レスポンスタイムが閾値を超えています"
  alarm_actions       = var.alarm_sns_topic_arn != null ? [var.alarm_sns_topic_arn] : []

  tags = {
    Name = "${var.environment}-keiba-high-response-time"
  }
}


# SNS Topic for Alerts
resource "aws_sns_topic" "alerts" {
  name = "${var.environment}-keiba-alerts"

  tags = {
    Name = "${var.environment}-keiba-alerts"
  }
}

# SNS Topic Subscription (Email)
resource "aws_sns_topic_subscription" "email" {
  count     = length(var.alert_emails)
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_emails[count.index]
}

# SNS Topic Subscription (Slack via Lambda)
resource "aws_sns_topic_subscription" "slack" {
  count     = var.slack_webhook_url != null ? 1 : 0
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.slack_notifier[0].arn
}

# Lambda Function for Slack Notifications
resource "aws_lambda_function" "slack_notifier" {
  count = var.slack_webhook_url != null ? 1 : 0

  filename         = data.archive_file.slack_notifier[0].output_path
  function_name    = "${var.environment}-keiba-slack-notifier"
  role            = aws_iam_role.lambda[0].arn
  handler         = "index.handler"
  runtime         = "python3.11"
  timeout         = 30

  environment {
    variables = {
      SLACK_WEBHOOK_URL = var.slack_webhook_url
    }
  }

  tags = {
    Name = "${var.environment}-keiba-slack-notifier"
  }
}

# Lambda IAM Role
resource "aws_iam_role" "lambda" {
  count = var.slack_webhook_url != null ? 1 : 0

  name = "${var.environment}-keiba-slack-notifier-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda" {
  count = var.slack_webhook_url != null ? 1 : 0

  name = "${var.environment}-keiba-slack-notifier-policy"
  role = aws_iam_role.lambda[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Lambda Permission
resource "aws_lambda_permission" "sns" {
  count = var.slack_webhook_url != null ? 1 : 0

  statement_id  = "AllowExecutionFromSNS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.slack_notifier[0].function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.alerts.arn
}

# Lambda Code Archive
data "archive_file" "slack_notifier" {
  count = var.slack_webhook_url != null ? 1 : 0

  type        = "zip"
  output_path = "/tmp/slack_notifier.zip"
  source {
    content = <<EOF
import json
import os
import urllib.request
import urllib.parse

def handler(event, context):
    webhook_url = os.environ['SLACK_WEBHOOK_URL']
    
    for record in event['Records']:
        message = json.loads(record['Sns']['Message'])
        subject = record['Sns']['Subject']
        
        payload = {
            'text': f"*{subject}*\n{message.get('AlarmName', 'Unknown Alarm')}\n{message.get('NewStateReason', '')}"
        }
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(webhook_url, data=data, headers={'Content-Type': 'application/json'})
        
        try:
            urllib.request.urlopen(req)
        except Exception as e:
            print(f"Failed to send Slack notification: {e}")
            raise
    
    return {'statusCode': 200}
EOF
    filename = "index.py"
  }
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.environment}-keiba-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", { "stat": "Sum", "label": "Request Count" }],
            [".", "TargetResponseTime", { "stat": "Average", "label": "Response Time" }],
            [".", "HTTPCode_Target_2XX_Count", { "stat": "Sum", "label": "2XX" }],
            [".", "HTTPCode_Target_4XX_Count", { "stat": "Sum", "label": "4XX" }],
            [".", "HTTPCode_Target_5XX_Count", { "stat": "Sum", "label": "5XX" }]
          ]
          period = 300
          stat   = "Average"
          region = data.aws_region.current.name
          title  = "ALB Metrics"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/ECS", "CPUUtilization", { "stat": "Average", "label": "CPU Utilization" }],
            [".", "MemoryUtilization", { "stat": "Average", "label": "Memory Utilization" }]
          ]
          period = 300
          stat   = "Average"
          region = data.aws_region.current.name
          title  = "ECS Metrics"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/RDS", "CPUUtilization", { "stat": "Average", "label": "CPU Utilization" }],
            [".", "DatabaseConnections", { "stat": "Average", "label": "Connections" }],
            [".", "FreeableMemory", { "stat": "Average", "label": "Free Memory" }]
          ]
          period = 300
          stat   = "Average"
          region = data.aws_region.current.name
          title  = "RDS Metrics"
        }
      }
    ]
  })
}

data "aws_region" "current" {}


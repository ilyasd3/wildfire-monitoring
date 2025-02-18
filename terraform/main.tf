# Specify Terraform version and required providers
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Define the AWS provider and region
provider "aws" {
  region = "us-east-1" # Replace with your preferred AWS region
}

resource "random_string" "bucket_suffix" {
  length  = 3
  upper   = false
  special = false
}

resource "aws_s3_bucket" "wildfire_data" {
  bucket = "wildfire-monitoring-${random_string.bucket_suffix.result}" # Generates a unique name

  tags = {
    Name = "WildfireMonitoringBucket"
  }
}

resource "aws_iam_role" "lambda_execution_role" {
  name = "wildfire_monitoring_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name   = "wildfire_monitoring_policy"
  role   = aws_iam_role.lambda_execution_role.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = ["s3:PutObject", "s3:GetObject"],
        Resource = "${aws_s3_bucket.wildfire_data.arn}/*"
      },
      {
        Effect   = "Allow",
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
        Resource = "*"
      }
    ]
  })
}

resource "aws_lambda_function" "wildfire_monitor" {
  function_name = "WildfireMonitoringFunction"
  runtime       = "python3.12"
  handler       = "lambda_function.lambda_handler"
  role          = aws_iam_role.lambda_execution_role.arn

  filename         = "artifacts/lambda_function.zip"
  source_code_hash = filebase64sha256("artifacts/lambda_function.zip")

  environment {
    variables = {
      BUCKET_NAME   = aws_s3_bucket.wildfire_data.bucket
      SNS_TOPIC_ARN = aws_sns_topic.wildfire_alerts.arn
    }
  }

  timeout = 60

  # Use prebuilt AWS Lambda layers for pandas and requests (no need to package dependencies)
  layers = [
    "arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p312-pandas:12",
    "arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p312-requests:12"
  ]

  tags = {
    Name = "WildfireMonitoringLambda"
  }
}

resource "aws_cloudwatch_event_rule" "daily_trigger" {
  name                = "DailyLambdaTrigger"
  description         = "Triggers the WildfireMonitoring Lambda function everyday at 9 PM EST"
  schedule_expression = "cron(0 3 * * ? *)" # 10 PM EST (UTC+2)
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.daily_trigger.name
  target_id = "WildfireMonitoringFunction"
  arn       = aws_lambda_function.wildfire_monitor.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.wildfire_monitor.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_trigger.arn
}

resource "aws_sns_topic" "wildfire_alerts" {
  name = "CaliforniaWildfireAlerts"
}

resource "aws_sns_topic_subscription" "wildfire_alert_subscription" {
  topic_arn = aws_sns_topic.wildfire_alerts.arn
  protocol  = "email"
  endpoint  = var.email_address
}

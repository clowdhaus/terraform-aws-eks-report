variable "create" {
  description = "Controls if resources should be created (affects nearly all resources)"
  type        = bool
  default     = true
}

variable "tags" {
  description = "A map of tags to add to all resources"
  type        = map(string)
  default     = {}
}

variable "name" {
  description = "Common name used across resources created"
  type        = string
  default     = "eks-report"
}

variable "log_group_retention_in_days" {
  description = "The number of days you want to retain log events in the log groups created"
  type        = number
  default     = 30
}

################################################################################
# Event Bridge Rule
################################################################################

variable "eventbridge_rule_name" {
  description = "The name of the Event Bridge Rule"
  type        = string
  default     = null
}

variable "eventbridge_iam_role_name" {
  description = "The name of the IAM role to use for the Event Bridge Rule"
  type        = string
  default     = null
}

variable "event_schedule_expression" {
  description = "The schedule expression for the Event Bridge Rule"
  type        = string
  default     = "cron(0 10 * * ? *)"
}

################################################################################
# Lambda Functions
################################################################################

variable "lambda_layers" {
  description = "List of Lambda Layer Version ARNs (maximum of 5) to attach to your Lambda Function"
  type        = list(string)
  default     = []
}

variable "lambda_runtime" {
  description = "The runtime environment for the Lambda functions"
  type        = string
  default     = "python3.9"
}

variable "lambda_timeout" {
  description = "The amount of time the Lambda Function has to run in seconds"
  type        = number
  default     = 300
}

variable "lambda_memory" {
  description = "Amount of memory in MB your Lambda Function can use at runtime. Valid value between 128 MB to 10,240 MB (10 GB), in 64 MB increments"
  type        = number
  default     = 1024
}

variable "lambda_assume_role_arns" {
  description = "The ARNs of IAM roles that the Lambda function will assume to access clusters in different accounts"
  type        = list(string)
  default     = []
}

################################################################################
# List Lambda Function
################################################################################

variable "list_lambda_name" {
  description = "The name of the Lambda function to list EKS clusters"
  type        = string
  default     = null
}

variable "list_lambda_description" {
  description = "The description of the Lambda function to list EKS clusters"
  type        = string
  default     = null
}

variable "list_lambda_environment_variables" {
  description = "A map that defines environment variables for the Lambda function to list EKS clusters"
  type        = map(string)
  default     = {}
}

################################################################################
# Describe Lambda Function
################################################################################

variable "describe_lambda_name" {
  description = "The name of the Lambda function to describe EKS clusters"
  type        = string
  default     = null
}

variable "describe_lambda_description" {
  description = "The description of the Lambda function to describe EKS clusters"
  type        = string
  default     = null
}

variable "describe_lambda_environment_variables" {
  description = "A map that defines environment variables for the Lambda function to describe EKS clusters"
  type        = map(string)
  default     = {}
}

################################################################################
# Notify Lambda Function
################################################################################

variable "notify_lambda_name" {
  description = "The name of the Lambda function that sends the notification"
  type        = string
  default     = null
}

variable "notify_lambda_description" {
  description = "The description of the Lambda function that sends the notification"
  type        = string
  default     = null
}

variable "notify_lambda_environment_variables" {
  description = "A map that defines environment variables for the Lambda function that sends the notification"
  type        = map(string)
  default     = {}
}

################################################################################
# Notification
################################################################################

variable "notify_eos_within_days" {
  description = "The number of days before the end of support to send the notification"
  type        = number
  default     = 120
}

variable "to_email_addresses" {
  description = "The email address to send the report to"
  type        = list(string)
  default     = []
}

variable "from_email_address" {
  description = "The email address to send the report from. Required if supplying values for `to_email_addresses`"
  type        = string
  default     = null
}

################################################################################
# SES Template
################################################################################

variable "create_ses_template" {
  description = "Controls if the SES Template should be created"
  type        = bool
  default     = true
}

variable "ses_template_arn" {
  description = "The ARN of an existing SES Template"
  type        = string
  default     = null
}

variable "ses_template_name" {
  description = "The name of the SES Template"
  type        = string
  default     = "EKS-Report"
}

variable "ses_template_subject" {
  description = "The subject of the SES Template"
  type        = string
  default     = "Amazon EKS Report"
}

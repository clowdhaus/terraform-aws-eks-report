################################################################################
# Step Function
################################################################################

output "step_function_arn" {
  description = "The ARN of the Step Function"
  value       = module.step_function.state_machine_arn
}

output "step_function_role_arn" {
  description = "The ARN of the IAM role created for the Step Function"
  value       = module.step_function.role_arn
}

################################################################################
# List Lambda Function
################################################################################

output "list_lambda_function_arn" {
  description = "The ARN of the Lambda Function"
  value       = module.list_lambda.lambda_function_arn
}

output "list_lambda_role_arn" {
  description = "The ARN of the IAM role created for the Lambda Function"
  value       = module.list_lambda.lambda_role_arn
}

################################################################################
# Describe Lambda Function
################################################################################

output "describe_lambda_function_arn" {
  description = "The ARN of the Lambda Function"
  value       = module.describe_lambda.lambda_function_arn
}

output "describe_lambda_role_arn" {
  description = "The ARN of the IAM role created for the Lambda Function"
  value       = module.describe_lambda.lambda_role_arn
}

################################################################################
# Notify Lambda Function
################################################################################

output "notify_lambda_function_arn" {
  description = "The ARN of the Lambda Function"
  value       = module.notify_lambda.lambda_function_arn
}

output "notify_lambda_role_arn" {
  description = "The ARN of the IAM role created for the Lambda Function"
  value       = module.notify_lambda.lambda_role_arn
}

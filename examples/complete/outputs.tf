################################################################################
# Step Function
################################################################################

output "step_function_arn" {
  description = "The ARN of the Step Function"
  value       = module.eks_report.step_function_arn
}

output "step_function_role_arn" {
  description = "The ARN of the IAM role created for the Step Function"
  value       = module.eks_report.step_function_role_arn
}

################################################################################
# List Lambda Function
################################################################################

output "list_lambda_function_arn" {
  description = "The ARN of the Lambda Function"
  value       = module.eks_report.list_lambda_function_arn
}

output "list_lambda_role_arn" {
  description = "The ARN of the IAM role created for the Lambda Function"
  value       = module.eks_report.list_lambda_role_arn
}

################################################################################
# Describe Lambda Function
################################################################################

output "describe_lambda_function_arn" {
  description = "The ARN of the Lambda Function"
  value       = module.eks_report.describe_lambda_function_arn
}

output "describe_lambda_role_arn" {
  description = "The ARN of the IAM role created for the Lambda Function"
  value       = module.eks_report.describe_lambda_role_arn
}

################################################################################
# Notify Lambda Function
################################################################################

output "notify_lambda_function_arn" {
  description = "The ARN of the Lambda Function"
  value       = module.eks_report.notify_lambda_function_arn
}

output "notify_lambda_role_arn" {
  description = "The ARN of the IAM role created for the Lambda Function"
  value       = module.eks_report.notify_lambda_role_arn
}

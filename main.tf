data "aws_region" "current" {}
data "aws_partition" "current" {}
data "aws_caller_identity" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name
  partition  = data.aws_partition.current.partition
}

################################################################################
# Event Bridge Rule
################################################################################

locals {
  eventbridge_rule_name = coalesce(var.eventbridge_rule_name, var.name)
}

module "eventbridge" {
  source  = "terraform-aws-modules/eventbridge/aws"
  version = "~> 1.17"

  create     = var.create
  create_bus = false # use default event bus
  role_name  = coalesce(var.eventbridge_iam_role_name, "${var.name}-eventbridge")

  rules = {
    (local.eventbridge_rule_name) = {
      description         = "Create EKS report"
      schedule_expression = var.event_schedule_expression
    }
  }

  targets = {
    (local.eventbridge_rule_name) = [
      {
        name            = local.eventbridge_rule_name
        arn             = module.step_function.state_machine_arn
        attach_role_arn = true
      }
    ]
  }

  append_rule_postfix        = false
  append_connection_postfix  = false
  append_destination_postfix = false

  sfn_target_arns   = [module.step_function.state_machine_arn]
  attach_sfn_policy = true

  tags = var.tags
}

################################################################################
# Step Function
################################################################################

module "step_function" {
  source  = "terraform-aws-modules/step-functions/aws"
  version = "~> 2.7"

  create = var.create

  name      = var.name
  role_name = "${var.name}-sfn"
  type      = "STANDARD"

  definition = templatefile("${path.module}/definition.json", {
    partition                     = local.partition
    list_clusters_function_arn    = try(module.list_lambda.lambda_function_arn, ""),
    describe_cluster_function_arn = try(module.describe_lambda.lambda_function_arn, ""),
    notify_function_arn           = try(module.notify_lambda.lambda_function_arn, ""),
  })

  service_integrations = {
    lambda = {
      lambda = [
        try(module.list_lambda.lambda_function_arn, null),
        try(module.describe_lambda.lambda_function_arn, null),
        try(module.notify_lambda.lambda_function_arn, null),
      ]
    }
  }

  attach_policy_json = true
  policy_json        = <<-EOT
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Action": [
            "ec2:DescribeRegions"
          ],
          "Resource": ["*"]
        },
        {
          "Effect": "Allow",
          "Action": [
            "states:StartExecution"
          ],
          "Resource": ["arn:${local.partition}:states:${local.region}:${local.account_id}:stateMachine:${var.name}"]
        }
      ]
    }
  EOT

  cloudwatch_log_group_name              = "/aws/step-function/${var.name}"
  cloudwatch_log_group_retention_in_days = var.log_group_retention_in_days

  logging_configuration = {
    include_execution_data = true
    level                  = "ALL"
  }

  tags = var.tags
}

################################################################################
# List Lambda Function
################################################################################

data "aws_iam_policy_document" "list" {
  count = var.create ? 1 : 0

  statement {
    sid       = "ListClusters"
    actions   = ["eks:ListClusters"]
    resources = ["*"]
  }

  dynamic "statement" {
    for_each = length(var.lambda_assume_role_arns) > 0 ? [1] : []

    content {
      sid       = "AssumeRoles"
      actions   = ["sts:AssumeRole"]
      resources = var.lambda_assume_role_arns
    }
  }
}

module "list_lambda" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "~> 4.12"

  create = var.create

  function_name = coalesce(var.list_lambda_name, "${var.name}-list")
  description   = coalesce(var.list_lambda_description, "List EKS clusters")

  handler     = "lambdas.list_clusters"
  runtime     = var.lambda_runtime
  timeout     = var.lambda_timeout
  memory_size = var.lambda_memory
  source_path = "${path.module}/lambdas/lambdas.py"
  layers      = var.lambda_layers

  environment_variables = merge(
    {
      REGION                  = local.region
      LAMBDA_ASSUME_ROLE_ARNS = join(";", var.lambda_assume_role_arns)
    },
    var.list_lambda_environment_variables
  )

  attach_policy_json = true
  policy_json        = try(data.aws_iam_policy_document.list[0].json, "")

  cloudwatch_logs_retention_in_days = var.log_group_retention_in_days

  tags = var.tags
}

################################################################################
# Describe Lambda Function
################################################################################

data "aws_iam_policy_document" "describe" {
  count = var.create ? 1 : 0

  statement {
    sid       = "DescribeCluster"
    actions   = ["eks:DescribeCluster"]
    resources = ["*"]
  }

  dynamic "statement" {
    for_each = length(var.lambda_assume_role_arns) > 0 ? [1] : []

    content {
      sid       = "AssumeRoles"
      actions   = ["sts:AssumeRole"]
      resources = var.lambda_assume_role_arns
    }
  }
}

module "describe_lambda" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "~> 4.12"

  create = var.create

  function_name = coalesce(var.describe_lambda_name, "${var.name}-describe")
  description   = coalesce(var.describe_lambda_description, "Describe EKS clusters to collect data")

  handler     = "lambdas.describe_cluster"
  runtime     = var.lambda_runtime
  timeout     = var.lambda_timeout
  memory_size = var.lambda_memory
  source_path = "${path.module}/lambdas/lambdas.py"
  layers      = var.lambda_layers

  environment_variables = merge(
    {
      REGION = local.region
    },
    var.describe_lambda_environment_variables
  )

  attach_policy_json = true
  policy_json        = try(data.aws_iam_policy_document.describe[0].json, "")

  cloudwatch_logs_retention_in_days = var.log_group_retention_in_days

  tags = var.tags
}

################################################################################
# Notify Lambda Function
################################################################################

module "notify_lambda" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "~> 4.12"

  create = var.create

  function_name = coalesce(var.notify_lambda_name, "${var.name}-notify")
  description   = coalesce(var.notify_lambda_description, "Generate and send EKS notification(s)")

  handler     = "lambdas.notify"
  runtime     = var.lambda_runtime
  timeout     = var.lambda_timeout
  memory_size = var.lambda_memory
  source_path = "${path.module}/lambdas/lambdas.py"
  layers      = var.lambda_layers

  environment_variables = merge(
    {
      REGION             = local.region
      EOS_WITHIN_DAYS    = var.notify_eos_within_days
      TO_EMAIL_ADDRESSES = join(";", var.to_email_addresses)
      FROM_EMAIL_ADDRESS = var.from_email_address
    },
    var.notify_lambda_environment_variables
  )

  attach_policy_statements = true
  policy_statements = {
    ses = {
      sid       = "SendEmail"
      effect    = "Allow",
      actions   = ["ses:SendEmail"],
      resources = ["*"]
    },
  }

  cloudwatch_logs_retention_in_days = var.log_group_retention_in_days

  tags = var.tags
}

# AWS EKS Report Terraform module

Terraform module which reports on Amazon EKS clusters.

## Usage

See [`examples`](https://github.com/clowdhaus/terraform-aws-eks-report/tree/main/examples) directory for working examples to reference:

:warning: Note - the email addressed used must be verified in SES. See [SES documentation](https://docs.aws.amazon.com/ses/latest/dg/creating-identities.html#just-verify-email-proc) for information on verifying email addresses.

```hcl
module "eks_report" {
  source = "clowdhaus/eks-report/aws"

  event_schedule_expression = "cron(0 10 * * ? *)"

  to_email_addresses = ["youremail@youraddress.com"]
  from_email_address = "youremail@youraddress.com"

  notify_eos_within_days = 180

  tags = {
    Terraform   = "true"
    Environment = "dev"
  }
}
```

## Step Function Graph

<p align="center">
  <img src="https://raw.githubusercontent.com/clowdhaus/terraform-aws-eks-report/main/.github/images/stepfunctions_graph.svg" alt="Step Function Graph" width="40%">
</p>

## Examples

Examples codified under the [`examples`](https://github.com/clowdhaus/terraform-aws-eks-report/tree/main/examples) are intended to give users references for how to use the module(s) as well as testing/validating changes to the source code of the module. If contributing to the project, please be sure to make any appropriate updates to the relevant examples to allow maintainers to test your changes and to keep the examples up to date for users. Thank you!

- [Complete](https://github.com/clowdhaus/terraform-aws-eks-report/tree/main/examples/complete)

<!-- BEGINNING OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.0 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | >= 4.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | >= 4.0 |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_describe_lambda"></a> [describe\_lambda](#module\_describe\_lambda) | terraform-aws-modules/lambda/aws | ~> 4.12 |
| <a name="module_eventbridge"></a> [eventbridge](#module\_eventbridge) | terraform-aws-modules/eventbridge/aws | ~> 1.17 |
| <a name="module_list_lambda"></a> [list\_lambda](#module\_list\_lambda) | terraform-aws-modules/lambda/aws | ~> 4.12 |
| <a name="module_notify_lambda"></a> [notify\_lambda](#module\_notify\_lambda) | terraform-aws-modules/lambda/aws | ~> 4.12 |
| <a name="module_step_function"></a> [step\_function](#module\_step\_function) | terraform-aws-modules/step-functions/aws | ~> 2.7 |

## Resources

| Name | Type |
|------|------|
| [aws_ses_template.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ses_template) | resource |
| [aws_caller_identity.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/caller_identity) | data source |
| [aws_iam_policy_document.describe](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_iam_policy_document.list](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_partition.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/partition) | data source |
| [aws_region.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/region) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_create"></a> [create](#input\_create) | Controls if resources should be created (affects nearly all resources) | `bool` | `true` | no |
| <a name="input_create_ses_template"></a> [create\_ses\_template](#input\_create\_ses\_template) | Controls if the SES Template should be created | `bool` | `true` | no |
| <a name="input_describe_lambda_description"></a> [describe\_lambda\_description](#input\_describe\_lambda\_description) | The description of the Lambda function to describe EKS clusters | `string` | `null` | no |
| <a name="input_describe_lambda_environment_variables"></a> [describe\_lambda\_environment\_variables](#input\_describe\_lambda\_environment\_variables) | A map that defines environment variables for the Lambda function to describe EKS clusters | `map(string)` | `{}` | no |
| <a name="input_describe_lambda_name"></a> [describe\_lambda\_name](#input\_describe\_lambda\_name) | The name of the Lambda function to describe EKS clusters | `string` | `null` | no |
| <a name="input_event_schedule_expression"></a> [event\_schedule\_expression](#input\_event\_schedule\_expression) | The schedule expression for the Event Bridge Rule | `string` | `"cron(0 10 * * ? *)"` | no |
| <a name="input_eventbridge_iam_role_name"></a> [eventbridge\_iam\_role\_name](#input\_eventbridge\_iam\_role\_name) | The name of the IAM role to use for the Event Bridge Rule | `string` | `null` | no |
| <a name="input_eventbridge_rule_name"></a> [eventbridge\_rule\_name](#input\_eventbridge\_rule\_name) | The name of the Event Bridge Rule | `string` | `null` | no |
| <a name="input_from_email_address"></a> [from\_email\_address](#input\_from\_email\_address) | The email address to send the report from. Required if supplying values for `to_email_addresses` | `string` | `null` | no |
| <a name="input_lambda_assume_role_arns"></a> [lambda\_assume\_role\_arns](#input\_lambda\_assume\_role\_arns) | The ARNs of IAM roles that the Lambda function will assume to access clusters in different accounts | `list(string)` | `[]` | no |
| <a name="input_lambda_layers"></a> [lambda\_layers](#input\_lambda\_layers) | List of Lambda Layer Version ARNs (maximum of 5) to attach to your Lambda Function | `list(string)` | `[]` | no |
| <a name="input_lambda_memory"></a> [lambda\_memory](#input\_lambda\_memory) | Amount of memory in MB your Lambda Function can use at runtime. Valid value between 128 MB to 10,240 MB (10 GB), in 64 MB increments | `number` | `1024` | no |
| <a name="input_lambda_runtime"></a> [lambda\_runtime](#input\_lambda\_runtime) | The runtime environment for the Lambda functions | `string` | `"python3.9"` | no |
| <a name="input_lambda_timeout"></a> [lambda\_timeout](#input\_lambda\_timeout) | The amount of time the Lambda Function has to run in seconds | `number` | `300` | no |
| <a name="input_list_lambda_description"></a> [list\_lambda\_description](#input\_list\_lambda\_description) | The description of the Lambda function to list EKS clusters | `string` | `null` | no |
| <a name="input_list_lambda_environment_variables"></a> [list\_lambda\_environment\_variables](#input\_list\_lambda\_environment\_variables) | A map that defines environment variables for the Lambda function to list EKS clusters | `map(string)` | `{}` | no |
| <a name="input_list_lambda_name"></a> [list\_lambda\_name](#input\_list\_lambda\_name) | The name of the Lambda function to list EKS clusters | `string` | `null` | no |
| <a name="input_log_group_retention_in_days"></a> [log\_group\_retention\_in\_days](#input\_log\_group\_retention\_in\_days) | The number of days you want to retain log events in the log groups created | `number` | `30` | no |
| <a name="input_name"></a> [name](#input\_name) | Common name used across resources created | `string` | `"eks-report"` | no |
| <a name="input_notify_eos_within_days"></a> [notify\_eos\_within\_days](#input\_notify\_eos\_within\_days) | The number of days before the end of support to send the notification | `number` | `120` | no |
| <a name="input_notify_lambda_description"></a> [notify\_lambda\_description](#input\_notify\_lambda\_description) | The description of the Lambda function that sends the notification | `string` | `null` | no |
| <a name="input_notify_lambda_environment_variables"></a> [notify\_lambda\_environment\_variables](#input\_notify\_lambda\_environment\_variables) | A map that defines environment variables for the Lambda function that sends the notification | `map(string)` | `{}` | no |
| <a name="input_notify_lambda_name"></a> [notify\_lambda\_name](#input\_notify\_lambda\_name) | The name of the Lambda function that sends the notification | `string` | `null` | no |
| <a name="input_ses_template_arn"></a> [ses\_template\_arn](#input\_ses\_template\_arn) | The ARN of an existing SES Template | `string` | `null` | no |
| <a name="input_ses_template_name"></a> [ses\_template\_name](#input\_ses\_template\_name) | The name of the SES Template | `string` | `"EKS-Report"` | no |
| <a name="input_ses_template_subject"></a> [ses\_template\_subject](#input\_ses\_template\_subject) | The subject of the SES Template | `string` | `"Amazon EKS Report"` | no |
| <a name="input_tags"></a> [tags](#input\_tags) | A map of tags to add to all resources | `map(string)` | `{}` | no |
| <a name="input_to_email_addresses"></a> [to\_email\_addresses](#input\_to\_email\_addresses) | The email address to send the report to | `list(string)` | `[]` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_describe_lambda_function_arn"></a> [describe\_lambda\_function\_arn](#output\_describe\_lambda\_function\_arn) | The ARN of the Lambda Function |
| <a name="output_describe_lambda_role_arn"></a> [describe\_lambda\_role\_arn](#output\_describe\_lambda\_role\_arn) | The ARN of the IAM role created for the Lambda Function |
| <a name="output_list_lambda_function_arn"></a> [list\_lambda\_function\_arn](#output\_list\_lambda\_function\_arn) | The ARN of the Lambda Function |
| <a name="output_list_lambda_role_arn"></a> [list\_lambda\_role\_arn](#output\_list\_lambda\_role\_arn) | The ARN of the IAM role created for the Lambda Function |
| <a name="output_notify_lambda_function_arn"></a> [notify\_lambda\_function\_arn](#output\_notify\_lambda\_function\_arn) | The ARN of the Lambda Function |
| <a name="output_notify_lambda_role_arn"></a> [notify\_lambda\_role\_arn](#output\_notify\_lambda\_role\_arn) | The ARN of the IAM role created for the Lambda Function |
| <a name="output_ses_template_arn"></a> [ses\_template\_arn](#output\_ses\_template\_arn) | The ARN of the SES Template |
| <a name="output_ses_template_id"></a> [ses\_template\_id](#output\_ses\_template\_id) | The name of the SES template |
| <a name="output_step_function_arn"></a> [step\_function\_arn](#output\_step\_function\_arn) | The ARN of the Step Function |
| <a name="output_step_function_role_arn"></a> [step\_function\_role\_arn](#output\_step\_function\_role\_arn) | The ARN of the IAM role created for the Step Function |
<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->

## License

Apache-2.0 Licensed. See [LICENSE](https://github.com/clowdhaus/terraform-aws-eks-report/blob/main/LICENSE).

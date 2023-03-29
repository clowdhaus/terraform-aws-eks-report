# Complete AWS EKS Report Example

Configuration in this directory creates:

- <XXX>

## Usage

To run this example you need to execute:

```bash
$ terraform init
$ terraform plan
$ terraform apply
```

Note that this example may create resources which will incur monetary charges on your AWS bill. Run `terraform destroy` when you no longer need these resources.

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
| <a name="provider_aws.euwest1"></a> [aws.euwest1](#provider\_aws.euwest1) | >= 4.0 |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_eks"></a> [eks](#module\_eks) | terraform-aws-modules/eks/aws | ~> 19.11 |
| <a name="module_eks_euwest1"></a> [eks\_euwest1](#module\_eks\_euwest1) | terraform-aws-modules/eks/aws | ~> 19.11 |
| <a name="module_eks_report"></a> [eks\_report](#module\_eks\_report) | ../.. | n/a |
| <a name="module_eks_report_disabled"></a> [eks\_report\_disabled](#module\_eks\_report\_disabled) | ../.. | n/a |
| <a name="module_vpc"></a> [vpc](#module\_vpc) | terraform-aws-modules/vpc/aws | ~> 3.0 |
| <a name="module_vpc_euwest1"></a> [vpc\_euwest1](#module\_vpc\_euwest1) | terraform-aws-modules/vpc/aws | ~> 3.0 |

## Resources

| Name | Type |
|------|------|
| [aws_availability_zones.available](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/availability_zones) | data source |
| [aws_availability_zones.secondary](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/availability_zones) | data source |

## Inputs

No inputs.

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_describe_lambda_function_arn"></a> [describe\_lambda\_function\_arn](#output\_describe\_lambda\_function\_arn) | The ARN of the Lambda Function |
| <a name="output_describe_lambda_role_arn"></a> [describe\_lambda\_role\_arn](#output\_describe\_lambda\_role\_arn) | The ARN of the IAM role created for the Lambda Function |
| <a name="output_list_lambda_function_arn"></a> [list\_lambda\_function\_arn](#output\_list\_lambda\_function\_arn) | The ARN of the Lambda Function |
| <a name="output_list_lambda_role_arn"></a> [list\_lambda\_role\_arn](#output\_list\_lambda\_role\_arn) | The ARN of the IAM role created for the Lambda Function |
| <a name="output_notify_lambda_function_arn"></a> [notify\_lambda\_function\_arn](#output\_notify\_lambda\_function\_arn) | The ARN of the Lambda Function |
| <a name="output_notify_lambda_role_arn"></a> [notify\_lambda\_role\_arn](#output\_notify\_lambda\_role\_arn) | The ARN of the IAM role created for the Lambda Function |
| <a name="output_step_function_arn"></a> [step\_function\_arn](#output\_step\_function\_arn) | The ARN of the Step Function |
| <a name="output_step_function_role_arn"></a> [step\_function\_role\_arn](#output\_step\_function\_role\_arn) | The ARN of the IAM role created for the Step Function |
<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->

Apache-2.0 Licensed. See [LICENSE](https://github.com/clowdhaus/terraform-aws-eks-report/blob/main/LICENSE).

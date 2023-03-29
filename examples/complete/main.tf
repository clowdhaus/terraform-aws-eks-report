provider "aws" {
  region = "us-east-1"
}

provider "aws" {
  region = "eu-west-1"
  alias  = "euwest1"
}

data "aws_availability_zones" "available" {}
data "aws_availability_zones" "secondary" {
  provider = aws.euwest1
}

locals {
  name = "eks-report-ex-${basename(path.cwd)}"

  vpc_cidr      = "10.0.0.0/16"
  azs           = slice(data.aws_availability_zones.available.names, 0, 3)
  secondary_azs = slice(data.aws_availability_zones.secondary.names, 0, 3)

  tags = {
    Name       = local.name
    Example    = local.name
    Repository = "https://github.com/clowdhaus/terraform-aws-eks-report"
  }
}

################################################################################
# EKS Report Module
################################################################################

module "eks_report" {
  source = "../.."

  # event_schedule_expression = "cron(0/5 * * * ? *)"

  to_email_addresses = ["bryantbiggs@gmail.com"]
  from_email_address = "bryantbiggs@gmail.com"

  notify_eos_within_days = 180

  tags = local.tags
}

module "eks_report_disabled" {
  source = "../.."

  create = false
}

################################################################################
# Supporting Resources
################################################################################

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.11"

  for_each = toset(["22", "23", "24"])

  cluster_name    = "${local.name}-${each.value}"
  cluster_version = "1.${each.value}"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  create_cluster_security_group = false
  create_node_security_group    = false

  tags = local.tags
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 3.0"

  name = local.name
  cidr = local.vpc_cidr

  azs             = local.azs
  public_subnets  = [for k, v in local.azs : cidrsubnet(local.vpc_cidr, 8, k)]
  private_subnets = [for k, v in local.azs : cidrsubnet(local.vpc_cidr, 8, k + 10)]

  enable_nat_gateway   = false
  enable_dns_hostnames = true

  # Manage so we can name
  manage_default_network_acl    = true
  default_network_acl_tags      = { Name = "${local.name}-default" }
  manage_default_route_table    = true
  default_route_table_tags      = { Name = "${local.name}-default" }
  manage_default_security_group = true
  default_security_group_tags   = { Name = "${local.name}-default" }

  tags = local.tags
}

module "eks_euwest1" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.11"

  providers = {
    aws = aws.euwest1
  }

  for_each = toset(["22", "23", "24"])

  cluster_name    = "${local.name}-${each.value}"
  cluster_version = "1.${each.value}"

  vpc_id     = module.vpc_euwest1.vpc_id
  subnet_ids = module.vpc_euwest1.private_subnets

  create_cluster_security_group = false
  create_node_security_group    = false

  tags = local.tags
}

module "vpc_euwest1" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 3.0"

  providers = {
    aws = aws.euwest1
  }

  name = local.name
  cidr = local.vpc_cidr

  azs             = local.secondary_azs
  public_subnets  = [for k, v in local.secondary_azs : cidrsubnet(local.vpc_cidr, 8, k)]
  private_subnets = [for k, v in local.secondary_azs : cidrsubnet(local.vpc_cidr, 8, k + 10)]

  enable_nat_gateway   = false
  enable_dns_hostnames = true

  # Manage so we can name
  manage_default_network_acl    = true
  default_network_acl_tags      = { Name = "${local.name}-default" }
  manage_default_route_table    = true
  default_route_table_tags      = { Name = "${local.name}-default" }
  manage_default_security_group = true
  default_security_group_tags   = { Name = "${local.name}-default" }

  tags = local.tags
}

# Uses the account's default VPC to keep the demo cheap. For production, swap for a
# dedicated VPC module with private subnets + a NAT gateway and move the tasks and
# RDS off public subnets.

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

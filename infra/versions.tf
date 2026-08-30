terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # For team use, configure an S3 backend with a DynamoDB lock table.
  # backend "s3" { ... }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project   = "nba-scout"
      ManagedBy = "terraform"
    }
  }
}

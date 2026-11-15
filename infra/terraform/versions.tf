terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.81"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      projeto    = var.project
      ambiente   = "laboratorio"
      gerenciado = "terraform"
    }
  }
}

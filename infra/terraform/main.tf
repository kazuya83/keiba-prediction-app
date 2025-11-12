terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    # S3バックエンドの設定は環境変数またはbackend.tfvarsで指定
    # bucket = "keiba-terraform-state"
    # key    = "terraform.tfstate"
    # region = "ap-northeast-1"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "keiba"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# VPC
module "vpc" {
  source = "./modules/vpc"

  environment = var.environment
  vpc_cidr    = var.vpc_cidr
}

# ECR
module "ecr" {
  source = "./modules/ecr"

  environment = var.environment
  repositories = [
    "keiba-backend",
    "keiba-frontend",
    "keiba-ml-inference",
  ]
}

# ECS Cluster
module "ecs" {
  source = "./modules/ecs"

  environment     = var.environment
  vpc_id         = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnet_ids
  public_subnets  = module.vpc.public_subnet_ids
  ecr_repositories = module.ecr.repository_urls

  backend_image_tag  = var.backend_image_tag
  frontend_image_tag = var.frontend_image_tag
  ml_image_tag       = var.ml_image_tag

  database_url = var.database_url
  allowed_cidr_blocks = var.allowed_cidr_blocks
}

# RDS
module "rds" {
  source = "./modules/rds"

  environment     = var.environment
  vpc_id         = module.vpc.vpc_id
  private_subnets = module.vpc.database_subnet_ids
  db_name        = var.db_name
  db_username    = var.db_username
  db_password    = var.db_password
  allowed_security_groups = [module.ecs.ecs_security_group_id]
}

# CloudWatch Logs
module "cloudwatch" {
  source = "./modules/cloudwatch"

  environment = var.environment
  alarm_sns_topic_arn = module.monitoring.sns_topic_arn
}

# Monitoring and Alerts
module "monitoring" {
  source = "./modules/monitoring"

  environment      = var.environment
  alert_emails     = var.alert_emails
  slack_webhook_url = var.slack_webhook_url
}

# Application Load Balancer
module "alb" {
  source = "./modules/alb"

  environment     = var.environment
  vpc_id         = module.vpc.vpc_id
  public_subnets  = module.vpc.public_subnet_ids
  backend_target_group_arn = module.ecs.backend_target_group_arn
  frontend_target_group_arn = module.ecs.frontend_target_group_arn

  depends_on = [module.ecs]
}


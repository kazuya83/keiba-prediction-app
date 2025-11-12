output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "backend_url" {
  description = "バックエンドAPIのURL"
  value       = module.alb.backend_url
}

output "frontend_url" {
  description = "フロントエンドのURL"
  value       = module.alb.frontend_url
}

output "ecr_repository_urls" {
  description = "ECRリポジトリのURL"
  value       = module.ecr.repository_urls
}

output "cloudwatch_log_groups" {
  description = "CloudWatch Log Groups"
  value       = module.cloudwatch.log_group_names
}


output "cluster_id" {
  description = "ECS Cluster ID"
  value       = aws_ecs_cluster.main.id
}

output "backend_target_group_arn" {
  description = "バックエンドTarget Group ARN"
  value       = aws_lb_target_group.backend.arn
}

output "frontend_target_group_arn" {
  description = "フロントエンドTarget Group ARN"
  value       = aws_lb_target_group.frontend.arn
}

output "ecs_security_group_id" {
  description = "ECS Security Group ID"
  value       = aws_security_group.ecs.id
}


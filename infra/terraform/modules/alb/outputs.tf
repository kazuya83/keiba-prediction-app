output "alb_dns_name" {
  description = "ALBのDNS名"
  value       = aws_lb.main.dns_name
}

output "backend_url" {
  description = "バックエンドAPIのURL"
  value       = "http://${aws_lb.main.dns_name}/api"
}

output "frontend_url" {
  description = "フロントエンドのURL"
  value       = "http://${aws_lb.main.dns_name}"
}


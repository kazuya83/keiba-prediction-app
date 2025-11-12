output "repository_urls" {
  description = "ECRリポジトリURLのマップ"
  value = {
    for name, repo in aws_ecr_repository.repositories : name => repo.repository_url
  }
}


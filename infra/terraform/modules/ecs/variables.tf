variable "environment" {
  description = "環境名"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "private_subnets" {
  description = "プライベートサブネットIDのリスト"
  type        = list(string)
}

variable "public_subnets" {
  description = "パブリックサブネットIDのリスト"
  type        = list(string)
}

variable "ecr_repositories" {
  description = "ECRリポジトリURLのマップ"
  type        = map(string)
}

variable "backend_image_tag" {
  description = "バックエンドDockerイメージのタグ"
  type        = string
}

variable "frontend_image_tag" {
  description = "フロントエンドDockerイメージのタグ"
  type        = string
}

variable "ml_image_tag" {
  description = "ML推論サーバーDockerイメージのタグ"
  type        = string
}

variable "database_url" {
  description = "データベース接続URL"
  type        = string
  sensitive   = true
}

variable "allowed_cidr_blocks" {
  description = "ALBへのアクセスを許可するCIDRブロックのリスト"
  type        = list(string)
}


variable "environment" {
  description = "環境名"
  type        = string
}

variable "repositories" {
  description = "ECRリポジトリ名のリスト"
  type        = list(string)
}


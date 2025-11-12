# Terraform Infrastructure as Code

本ディレクトリには、AWS上で競馬予測アプリケーションを実行するためのインフラストラクチャを定義するTerraformコードが含まれています。

## 構成

- `main.tf`: メインのTerraform設定ファイル
- `variables.tf`: 変数定義
- `outputs.tf`: 出力値定義
- `modules/`: 再利用可能なモジュール
  - `vpc/`: VPC、サブネット、NAT Gatewayなどのネットワークリソース
  - `ecr/`: ECRリポジトリ
  - `ecs/`: ECSクラスター、サービス、タスク定義
  - `rds/`: RDSインスタンス
  - `alb/`: Application Load Balancer
  - `cloudwatch/`: CloudWatch Logsとアラーム
  - `monitoring/`: SNS、ダッシュボード、アラート設定

## 使用方法

### 前提条件

1. AWS CLIがインストールされ、認証情報が設定されている
2. Terraform 1.5.0以上がインストールされている
3. S3バケットがTerraformステートファイル用に作成されている

### 初期化

```bash
cd infra/terraform
terraform init \
  -backend-config="bucket=<terraform-state-bucket>" \
  -backend-config="key=<environment>/terraform.tfstate" \
  -backend-config="region=ap-northeast-1"
```

### 計画の確認

```bash
terraform plan \
  -var="environment=staging" \
  -var="backend_image_tag=main-abc1234" \
  -var="frontend_image_tag=main-abc1234" \
  -var="ml_image_tag=main-abc1234" \
  -var="database_url=postgresql://..." \
  -var="db_username=..." \
  -var="db_password=..."
```

### 適用

```bash
terraform apply \
  -var="environment=staging" \
  -var="backend_image_tag=main-abc1234" \
  -var="frontend_image_tag=main-abc1234" \
  -var="ml_image_tag=main-abc1234" \
  -var="database_url=postgresql://..." \
  -var="db_username=..." \
  -var="db_password=..."
```

### 環境変数での設定

機密情報は環境変数で設定することもできます:

```bash
export TF_VAR_database_url="postgresql://..."
export TF_VAR_db_username="..."
export TF_VAR_db_password="..."
export TF_VAR_slack_webhook_url="https://hooks.slack.com/..."
```

## 環境ごとの設定

### ステージング環境

```bash
terraform workspace select staging
terraform apply -var-file=staging.tfvars
```

### 本番環境

```bash
terraform workspace select production
terraform apply -var-file=production.tfvars
```

## 出力値の確認

```bash
terraform output
```

主要な出力値:
- `backend_url`: バックエンドAPIのURL
- `frontend_url`: フロントエンドのURL
- `ecr_repository_urls`: ECRリポジトリのURL
- `cloudwatch_log_groups`: CloudWatch Log Groups

## リソースの削除

```bash
terraform destroy \
  -var="environment=staging" \
  -var="database_url=postgresql://..." \
  -var="db_username=..." \
  -var="db_password=..."
```

## 注意事項

- 本番環境のリソースを削除する際は、十分に注意してください
- データベースのスナップショットは自動的に作成されますが、重要なデータは別途バックアップを取ってください
- 機密情報（パスワード、APIキーなど）はTerraformの変数やAWS Secrets Managerで管理してください


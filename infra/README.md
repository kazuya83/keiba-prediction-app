# インフラストラクチャ

本ディレクトリには、開発・本番環境のインフラ構成を管理するファイルが含まれています。

## 構成

- `terraform/`: Terraformコード（IaC）
- `README.md`: このファイル

## ディレクトリ構造

```
infra/
├── terraform/
│   ├── main.tf              # メインのTerraform設定
│   ├── variables.tf         # 変数定義
│   ├── outputs.tf           # 出力値定義
│   ├── modules/             # 再利用可能なモジュール
│   │   ├── vpc/             # VPC、サブネット
│   │   ├── ecr/             # ECRリポジトリ
│   │   ├── ecs/             # ECSクラスター、サービス
│   │   ├── rds/             # RDSインスタンス
│   │   ├── alb/             # Application Load Balancer
│   │   ├── cloudwatch/      # CloudWatch Logs、アラーム
│   │   └── monitoring/      # 監視、アラート設定
│   └── README.md            # Terraformの使用方法
└── README.md                # このファイル
```

## デプロイ方法

詳細は [terraform/README.md](./terraform/README.md) を参照してください。

## CI/CD

GitHub Actionsのワークフロー（`.github/workflows/deploy.yml`）から自動的にデプロイされます。

## 監視

- CloudWatchダッシュボード: メトリクスの可視化
- CloudWatchアラーム: 異常検知と通知
- SNS: メール/Slack通知

詳細は [docs/runbook.md](../docs/runbook.md) を参照してください。

# コーディング規約

本規約は競馬予測アプリケーション開発における全エンジニア（バックエンド・フロントエンド・機械学習・インフラ）が遵守すべきコーディング上の指針を定める。各チームは本ガイドラインを基礎とし、必要に応じて詳細な補足規約を策定する。

---

## 0. 運用方針

- 規約の最新管理者はテックリードとし、改訂時はプロジェクト全体に通知する。
- 例外を認める場合は理由と影響範囲を明記した上でレビューアの承認を得る。
- 自動化（Lint / Format / Test）が可能な内容は極力自動化し、Pull Request 時に必須とする。

---

## 1. 共通規約

### 1.1 設計原則
- SOLID / DRY / KISS を基本原則とし、可読性と保守性を最優先する。
- ドメイン知識（競馬・予測モデル）をコード上で表現するため、意図が伝わる命名とコメントを心掛ける。
- 外部サービス/API との連携部分は抽象化レイヤーを設け、テスト可能な構成とする。

### 1.2 ブランチ・コミット運用
- Git ブランチ戦略は GitHub Flow を採用する。`main` は常にデプロイ可能状態を維持する。
- コミットメッセージは Conventional Commits に準拠（例: `feat: add race detail endpoint`）。
- Pull Request はセルフレビュー後に作成し、最低 1 名のレビュー承認を必須とする。

### 1.3 命名規則
- 変数 / 関数: `lowerCamelCase`（TypeScript）または `snake_case`（Python）。
- クラス / コンポーネント: `UpperCamelCase`。
- 定数: `SCREAMING_SNAKE_CASE`。
- ファイル名は言語ごとの慣習に従う（Python: `snake_case.py`、React: コンポーネントは `PascalCase.tsx`）。

### 1.4 ドキュメントとコメント
- 関数やクラスの公開インターフェースには docstring / JSDoc で仕様を記述する。
- ビジネスルールや計算根拠など文脈依存の知識はコードコメントや ADR（Architecture Decision Record）で共有する。
- プロジェクトのルール変更は `requirements.md` または本規約に即時反映する。

### 1.5 フォーマット・Lint・静的解析
- すべての言語で自動整形ツールを導入し、CI で強制する。
- Python: `black`, `isort`, `flake8`, `mypy`。
- TypeScript/JavaScript: `prettier`, `eslint`（Airbnb ベース + React + TypeScript プラグイン）。
- バージョンは `pyproject.toml` / `package.json` に固定し、`pre-commit` で自動適用する。

### 1.6 テスト戦略
- 単体テストを最優先し、主要ロジックは必ずテストを用意する。
- Pull Request 時には差分に関係するテストを追加し、CI 上で全テストをパスさせる。
- テストデータは再利用可能な Fixture を用意し、実データの機密情報を含めない。

### 1.7 セキュリティ・秘密情報
- API キーや認証情報は `.env` / Secrets Manager で管理し、リポジトリに含めない。
- External API へのリクエストはタイムアウト・リトライ・レート制限を考慮する。
- 個人情報・機微情報を扱う処理にはアクセス制御と監査ログを実装する。

### 1.8 ロギング・モニタリング
- ログレベル: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` を明確に使い分ける。
- ユーザー個人を特定できる情報は平文で出力しない。
- 例外発生時はスタックトレースを記録し、必要に応じて通知（Slack / PagerDuty 等）を行う。

---

## 2. バックエンド規約（Python / FastAPI 想定）

### 2.1 開発環境
- Python 3.11+ を標準とし、`poetry` または `pip-tools` で依存関係を管理する。
- 仮想環境は必ず有効化し、`Dockerfile` と `docker-compose.yml` でローカル実行環境を提供する。

### 2.2 プロジェクト構成（推奨）
```
app/
  api/
    routers/
    schemas/
  core/
    config.py
    logging.py
  services/
  repositories/
  models/
  tasks/
tests/
```
- API レイヤ、サービスレイヤ、リポジトリレイヤを分離し、責務を明確化する。
- Pydantic モデルは `schemas/` に配置し、DB モデル（SQLAlchemy）は `models/` に分離する。

### 2.3 実装ガイド
- すべての API エンドポイントで入力/出力に Pydantic スキーマを使用する。
- 型ヒントは必須。タプル返却など曖昧な型は `TypedDict` や dataclass を活用する。
- 例外処理はカスタム例外＋ハンドラで統一し、HTTP ステータスとメッセージを一元管理する。
- 非同期 I/O を利用する場合は `async def` を基本とし、同期処理はバックグラウンドタスクに移譲する。
- DB アクセスは SQLAlchemy（SQLModel 可）を利用し、セッション管理は依存性注入で行う。
- スケジューラ（例: APScheduler, Celery）は `tasks/` にまとめ、設定値は環境変数化する。

### 2.4 テスト
- テストは `pytest` で実装し、`tests/unit`, `tests/integration`, `tests/e2e` の階層を用意する。
- API テストには `httpx.AsyncClient` 等を利用し、FastAPI の `TestClient` でモックサーバを構築する。
- DB テストはトランザクションロールバックまたは SQLite メモリ DB を用いて副作用を防ぐ。

### 2.5 ドキュメント生成
- FastAPI の自動ドキュメント（OpenAPI）を活用し、エンドポイントごとに `summary`, `description`, `responses` を設定する。
- スキーマの例 (`examples`) を登録し、フロントと共有する。

---

## 3. フロントエンド規約（React / TypeScript）

### 3.1 開発環境
- Node.js LTS（推奨: 20.x）を採用し、パッケージマネージャは `pnpm` を標準とする（`npm` / `yarn` 使用時はチーム合意が必要）。
- TypeScript を必須とし、`strict` オプションを有効化する。

### 3.2 ディレクトリ構成（推奨）
```
src/
  components/
    common/
    domain/
  features/
  pages/
  hooks/
  lib/
  stores/
  styles/
  tests/
```
- ドメイン単位で `features/` を分割し、UI 部品は `components/common` に配置する。
- API 通信は `lib/api` にまとめ、型定義は `@types` または `types/` に集約する。

### 3.3 コーディングガイド
- コンポーネントは関数コンポーネントのみ使用し、`React.FC` 型は使用しない。
- 状態管理は最小限とし、グローバル状態は Zustand / Redux Toolkit など合意したライブラリを用いる。
- 副作用は `useEffect` を適切に分割し、クリーンアップ処理を忘れない。
- フォーム処理には React Hook Form など実績あるライブラリを採用する。
- API レイヤは `async/await` を用いて記述し、型安全なクライアント（OpenAPI Generator 等）を利用する。
- CSS は CSS Modules + PostCSS（またはチームで選定したスタイルソリューション）を標準とし、命名は BEM を推奨する。

### 3.4 品質管理
- ESLint のルールは TypeScript + React Recommended をベースに、アクセシビリティ用に `jsx-a11y` を追加する。
- `prettier` でフォーマットを統一し、`.prettierrc` にプロジェクト設定を明文化する。
- Storybook を導入し、主要コンポーネントの UI 仕様とスナップショットテストを管理する。
- パフォーマンス計測には React Profiler / Lighthouse を用い、重大な劣化を検出した場合は Issue を起票する。

### 3.5 テスト
- 単体テスト: Jest + React Testing Library。ユーザー操作に近いテストを書く。
- E2E テスト: Playwright（推奨）または Cypress。主要ユーザーフロー（ログイン、予測実行、履歴参照）をカバーする。
- Storybook に Visual Regression（Chromatic 等）を導入し、UI の破壊的変更を検出する。

---

## 4. 運用・更新手順

- 新しい規約を提案する場合は Pull Request で本ファイルを更新し、#guild-coding チャンネルで共有する。
- プロジェクトキックオフ時や四半期ごとに規約をレビューし、実態と乖離がないか確認する。
- 規約違反が発見された場合はレビューコメントで指摘し、必要に応じて他メンバーとすり合わせを行う。

---

## 5. 参考資料

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [pytest Documentation](https://docs.pytest.org/)
- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Conventional Commits](https://www.conventionalcommits.org/)



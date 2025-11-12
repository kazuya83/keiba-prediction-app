# Frontend

React + TypeScript によるフロントエンドアプリケーションです。pnpm を利用して依存関係を管理します。

## セットアップ

```bash
pnpm install
pnpm dev
```

## ディレクトリ構成

```
src/
  components/
    common/      # 共通コンポーネント（Button, Header, Layout等）
    domain/      # ドメイン固有コンポーネント
  features/      # 機能単位のモジュール
  pages/         # ページコンポーネント
  hooks/         # カスタムフック
  lib/           # ユーティリティ・APIクライアント
    api/         # APIクライアント（生成されたコード含む）
    types/       # 型定義
  stores/        # Zustandストア
  styles/        # グローバルスタイル
```

## 使用ツール

- React 18 + TypeScript (strict)
- Vite
- Tailwind CSS
- React Router
- Zustand（状態管理）
- ESLint + Prettier + Stylelint
- Storybook
- Vitest + React Testing Library

## コマンド

### 開発

```bash
pnpm dev              # 開発サーバー起動（http://localhost:3000）
pnpm build            # プロダクションビルド
pnpm preview          # ビルド結果のプレビュー
```

### コード品質

```bash
pnpm lint             # ESLint + Stylelint を実行
pnpm format           # Prettier でフォーマット
pnpm test             # テスト実行
```

### Storybook

```bash
pnpm storybook        # Storybook起動（http://localhost:6006）
pnpm build-storybook  # Storybookの静的ビルド
```

### APIクライアント生成

```bash
pnpm generate:api     # OpenAPIスキーマからTypeScriptクライアントを生成
```

**注意**: このコマンドを実行するには、バックエンドサーバーが `http://localhost:8000` で起動している必要があります。

## 設定ファイル

- `tailwind.config.js` - Tailwind CSSの設定（カラーテーマ含む）
- `.eslintrc.json` - ESLint設定
- `.prettierrc.json` - Prettier設定
- `.stylelintrc.json` - Stylelint設定
- `.storybook/` - Storybook設定
- `vite.config.ts` - Vite設定
- `tsconfig.json` - TypeScript設定


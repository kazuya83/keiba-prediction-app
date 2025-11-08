# 実行計画 13: フロントエンド基盤セットアップ

## ゴール
- React/TypeScript環境を整備し、開発者がUI実装をすぐ開始できるようにする。

## 手順
1. `frontend/` で `pnpm` によりプロジェクトを初期化し、Vite + React + TypeScript構成を生成。
2. `src/` 配下に `components/`, `features/`, `pages/`, `hooks/`, `stores/`, `lib/` ディレクトリを作成（ガイドライン準拠）。
3. UIライブラリ（Tailwind CSS または Chakra UI）を導入し、テーマ設定ファイルを作成。
4. ルーティングをReact Routerで構築し、`App.tsx` にレイアウトコンポーネント・エラーハンドラを配置。
5. 状態管理としてZustandまたはRedux Toolkitを導入し、グローバルストアのサンプルを実装。
6. OpenAPIスキーマからAPIクライアントを生成するスクリプト（`pnpm generate:api`）を追加。
7. ESLint（TypeScript + React + jsx-a11y）、Prettier、Stylelintを設定し、`pnpm lint` コマンドをMakefile/justfileに統合。
8. Storybookを導入し、共通ボタン/ヘッダーなどサンプルコンポーネントのストーリーを作成。

## 成果物
- `frontend/package.json`, `tsconfig.json`, `vite.config.ts`, `tailwind.config.js` 等の設定一式。
- ルートページと404ページのスタブ、Storybookの初期ストーリー。
- Lint/Format/Storybook起動コマンドのドキュメント化。

## 依存・前提
- 計画02で設定されたルートMakefile/justfileが存在し、`pnpm` がインストール済み。
- APIスキーマの初期ドラフトが利用可能（未確定でもモック生成は可能）。

## リスクと対策
- **リスク**: CSS設計が統一されない。  
  **対策**: デザインシステムの命名規則とカラートークンを早期に定義。
- **リスク**: APIスキーマ変更で型が壊れる。  
  **対策**: 型生成をCIで自動実行し、差分をレビュー。*** End Patch


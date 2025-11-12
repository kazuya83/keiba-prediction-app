# フロントエンド用Dockerfile（マルチステージビルド）

# ステージ1: ビルドステージ
FROM node:20-alpine as builder

WORKDIR /app

# パッケージマネージャのインストール
RUN corepack enable && corepack prepare pnpm@latest --activate

# 依存関係ファイルをコピー
COPY package.json pnpm-lock.yaml* ./

# 依存関係をインストール
RUN pnpm install --frozen-lockfile

# アプリケーションコードをコピー
COPY . .

# ビルド
RUN pnpm build

# ステージ2: ランタイムステージ
FROM nginx:alpine

# ビルド成果物をコピー
COPY --from=builder /app/dist /usr/share/nginx/html

# Nginx設定ファイルをコピー
COPY nginx.conf /etc/nginx/conf.d/default.conf

# ポートの公開
EXPOSE 80

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Nginxの起動
CMD ["nginx", "-g", "daemon off;"]


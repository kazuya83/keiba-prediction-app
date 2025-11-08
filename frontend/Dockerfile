FROM node:18-alpine

WORKDIR /app

# npm設定の最適化（タイムアウト延長、リトライ設定）
RUN npm config set fetch-retries 5 && \
    npm config set fetch-retry-mintimeout 20000 && \
    npm config set fetch-retry-maxtimeout 120000 && \
    npm config set fetch-timeout 300000

# 依存関係のインストール
COPY package.json package-lock.json* ./
RUN npm install

# アプリケーションコードのコピー
COPY . .

# ポートの公開
EXPOSE 3000

# 開発サーバーの起動
CMD ["npm", "run", "dev", "--", "--host"]




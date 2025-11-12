#!/bin/bash
set -e

# Smokeテストスクリプト
# 使用方法: ./scripts/smoke-test.sh <environment> <image_tag>

ENVIRONMENT=$1
IMAGE_TAG=$2

if [ -z "$ENVIRONMENT" ] || [ -z "$IMAGE_TAG" ]; then
  echo "使用方法: $0 <environment> <image_tag>"
  exit 1
fi

# 環境に応じたURLを設定
if [ "$ENVIRONMENT" == "staging" ]; then
  BACKEND_URL="${STAGING_BACKEND_URL:-http://staging-keiba-alb-1234567890.ap-northeast-1.elb.amazonaws.com/api}"
  FRONTEND_URL="${STAGING_FRONTEND_URL:-http://staging-keiba-alb-1234567890.ap-northeast-1.elb.amazonaws.com}"
elif [ "$ENVIRONMENT" == "production" ]; then
  BACKEND_URL="${PRODUCTION_BACKEND_URL:-http://production-keiba-alb-1234567890.ap-northeast-1.elb.amazonaws.com/api}"
  FRONTEND_URL="${PRODUCTION_FRONTEND_URL:-http://production-keiba-alb-1234567890.ap-northeast-1.elb.amazonaws.com}"
else
  echo "不明な環境: $ENVIRONMENT"
  exit 1
fi

echo "=========================================="
echo "Smoke Test for $ENVIRONMENT"
echo "Backend URL: $BACKEND_URL"
echo "Frontend URL: $FRONTEND_URL"
echo "Image Tag: $IMAGE_TAG"
echo "=========================================="

# バックエンドヘルスチェック
echo "1. バックエンドヘルスチェック..."
BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/health" || echo "000")
if [ "$BACKEND_HEALTH" != "200" ]; then
  echo "❌ バックエンドヘルスチェック失敗: HTTP $BACKEND_HEALTH"
  exit 1
fi
echo "✅ バックエンドヘルスチェック成功"

# フロントエンドヘルスチェック
echo "2. フロントエンドヘルスチェック..."
FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL/health" || echo "000")
if [ "$FRONTEND_HEALTH" != "200" ]; then
  echo "❌ フロントエンドヘルスチェック失敗: HTTP $FRONTEND_HEALTH"
  exit 1
fi
echo "✅ フロントエンドヘルスチェック成功"

# APIエンドポイントの確認
echo "3. APIエンドポイント確認..."
API_RESPONSE=$(curl -s "$BACKEND_URL/health" || echo "{}")
if echo "$API_RESPONSE" | grep -q "status"; then
  echo "✅ APIエンドポイント正常"
else
  echo "❌ APIエンドポイント異常: $API_RESPONSE"
  exit 1
fi

# フロントエンドの基本確認
echo "4. フロントエンド基本確認..."
FRONTEND_HTML=$(curl -s "$FRONTEND_URL" || echo "")
if echo "$FRONTEND_HTML" | grep -q "<!DOCTYPE html\|<html"; then
  echo "✅ フロントエンドHTML正常"
else
  echo "❌ フロントエンドHTML異常"
  exit 1
fi

echo "=========================================="
echo "✅ すべてのSmokeテストが成功しました"
echo "=========================================="


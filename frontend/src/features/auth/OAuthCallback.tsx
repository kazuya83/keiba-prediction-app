/**
 * OAuthコールバック処理コンポーネント。
 * リダイレクト方式のOAuth認証完了後に呼び出される。
 */

import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuthStore } from "../../stores";
import { apiClient } from "../../lib/api/client";
import type { Token } from "../../lib/api/types";

export function OAuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { setTokens } = useAuthStore();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get("code");
      const state = searchParams.get("state");
      const savedState = localStorage.getItem("oauth_state");

      if (!code || !state) {
        setError("認証パラメータが不足しています");
        return;
      }

      if (state !== savedState) {
        setError("stateパラメータが一致しません");
        return;
      }

      try {
        // バックエンドのコールバックエンドポイントを呼び出す
        const response = await apiClient.get<Token>("/api/auth/google/callback", {
          params: { code, state },
        });

        setTokens(response.data);
        localStorage.removeItem("oauth_state");
        const redirectUrl = localStorage.getItem("oauth_redirect_url") || "/dashboard";
        localStorage.removeItem("oauth_redirect_url");
        navigate(redirectUrl);
      } catch (err) {
        console.error("OAuthコールバック処理に失敗しました:", err);
        setError("認証に失敗しました");
      }
    };

    handleCallback();
  }, [searchParams, navigate, setTokens]);

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">認証エラー</h1>
          <p className="text-gray-700 mb-4">{error}</p>
          <button
            onClick={() => navigate("/login")}
            className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700"
          >
            ログインページに戻る
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4" />
        <p className="text-gray-700">認証処理中...</p>
      </div>
    </div>
  );
}


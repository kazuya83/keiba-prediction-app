/**
 * Google OAuthログインボタンコンポーネント。
 * ポップアップまたはリダイレクトで認証を開始する。
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../../components/common/Button";
import { getGoogleLoginUrl } from "../../lib/api/auth";
import { useAuthStore } from "../../stores";

interface GoogleLoginButtonProps {
  usePopup?: boolean;
}

export function GoogleLoginButton({ usePopup = false }: GoogleLoginButtonProps) {
  const navigate = useNavigate();
  const { setTokens } = useAuthStore();
  const [isLoading, setIsLoading] = useState(false);

  const handleGoogleLogin = async () => {
    setIsLoading(true);
    try {
      const { authorization_url, state } = await getGoogleLoginUrl();

      if (usePopup) {
        // ポップアップ方式
        const width = 500;
        const height = 600;
        const left = window.screenX + (window.outerWidth - width) / 2;
        const top = window.screenY + (window.outerHeight - height) / 2;

        const popup = window.open(
          authorization_url,
          "GoogleLogin",
          `width=${width},height=${height},left=${left},top=${top}`,
        );

        if (!popup) {
          throw new Error("ポップアップがブロックされました");
        }

        // ポップアップからのメッセージを待機
        const messageListener = (event: MessageEvent) => {
          if (event.origin !== window.location.origin) {
            return;
          }

          if (event.data.type === "GOOGLE_OAUTH_SUCCESS") {
            setTokens(event.data.token);
            popup.close();
            window.removeEventListener("message", messageListener);
            navigate("/dashboard");
          } else if (event.data.type === "GOOGLE_OAUTH_ERROR") {
            console.error("Google OAuth エラー:", event.data.error);
            popup.close();
            window.removeEventListener("message", messageListener);
          }
        };

        window.addEventListener("message", messageListener);

        // ポップアップが閉じられた場合の処理
        const checkClosed = setInterval(() => {
          if (popup.closed) {
            clearInterval(checkClosed);
            window.removeEventListener("message", messageListener);
            setIsLoading(false);
          }
        }, 1000);
      } else {
        // リダイレクト方式
        // stateをlocalStorageに保存
        localStorage.setItem("oauth_state", state);
        localStorage.setItem("oauth_redirect_url", window.location.href);
        window.location.href = authorization_url;
      }
    } catch (error) {
      console.error("Googleログインの開始に失敗しました:", error);
      setIsLoading(false);
    }
  };

  return (
    <Button
      type="button"
      onClick={handleGoogleLogin}
      disabled={isLoading}
      variant="outline"
      className="w-full flex items-center justify-center gap-2"
    >
      {isLoading ? (
        "処理中..."
      ) : (
        <>
          <svg className="w-5 h-5" viewBox="0 0 24 24">
            <path
              fill="#4285F4"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="#34A853"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="#FBBC05"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
            />
            <path
              fill="#EA4335"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
            />
          </svg>
          Googleでログイン
        </>
      )}
    </Button>
  );
}


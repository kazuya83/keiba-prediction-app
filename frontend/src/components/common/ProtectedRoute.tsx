/**
 * 認証が必要なページを保護するコンポーネント。
 */

import { ReactNode, useEffect } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuthStore } from "../../stores";

interface ProtectedRouteProps {
  children: ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const location = useLocation();
  const { isAuthenticated, isTokenExpired, refreshAccessToken } = useAuthStore();

  useEffect(() => {
    // トークンが期限切れの場合は自動リフレッシュを試行
    if (isTokenExpired() && isAuthenticated()) {
      refreshAccessToken().catch((error) => {
        console.error("トークンリフレッシュに失敗しました:", error);
      });
    }
  }, [isTokenExpired, isAuthenticated, refreshAccessToken]);

  if (!isAuthenticated()) {
    // 認証されていない場合はログインページにリダイレクト
    // 現在のパスをstateに保存して、ログイン後に戻れるようにする
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}


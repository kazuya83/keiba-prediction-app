/**
 * 認証ストア。
 * アクセストークン管理、リフレッシュ処理、ユーザー情報キャッシュを提供する。
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Token, User } from "../lib/api/types";
import * as authApi from "../lib/api/auth";
import { configureAuth } from "../lib/api/client";

interface AuthState {
  // 認証状態
  accessToken: string | null;
  refreshToken: string | null;
  tokenExpiresAt: number | null;
  user: User | null;

  // アクション
  setTokens: (token: Token) => void;
  clearTokens: () => void;
  setUser: (user: User | null) => void;
  refreshAccessToken: () => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: () => boolean;
  isTokenExpired: () => boolean;
}

/**
 * トークンの有効期限を計算する。
 */
function calculateExpiresAt(expiresIn: number): number {
  return Date.now() + expiresIn * 1000;
}

/**
 * 認証ストア。
 */
export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => {
      return {
        accessToken: null,
        refreshToken: null,
        tokenExpiresAt: null,
        user: null,

        setTokens: (token: Token) => {
          set({
            accessToken: token.access_token,
            refreshToken: token.refresh_token,
            tokenExpiresAt: calculateExpiresAt(token.expires_in),
          });
        },

        clearTokens: () => {
          set({
            accessToken: null,
            refreshToken: null,
            tokenExpiresAt: null,
            user: null,
          });
        },

        setUser: (user: User | null) => {
          set({ user });
        },

        refreshAccessToken: async () => {
          const state = get();
          if (!state.refreshToken) {
            throw new Error("リフレッシュトークンが存在しません");
          }

          try {
            const newToken = await authApi.refreshToken({
              refresh_token: state.refreshToken,
            });
            get().setTokens(newToken);
          } catch (error) {
            // リフレッシュ失敗時はログアウト
            get().clearTokens();
            throw error;
          }
        },

        logout: async () => {
          const state = get();
          if (state.refreshToken) {
            try {
              await authApi.logoutUser({
                refresh_token: state.refreshToken,
              });
            } catch (error) {
              // エラーが発生してもローカル状態はクリア
              console.error("ログアウトAPI呼び出しに失敗しました:", error);
            }
          }
          get().clearTokens();
        },

        isAuthenticated: () => {
          const state = get();
          return (
            state.accessToken !== null &&
            state.refreshToken !== null &&
            !state.isTokenExpired()
          );
        },

        isTokenExpired: () => {
          const state = get();
          if (!state.tokenExpiresAt) {
            return true;
          }
          // 有効期限の5分前に期限切れとみなす
          return Date.now() >= state.tokenExpiresAt - 5 * 60 * 1000;
        },
      };
    },
    {
      name: "auth-storage",
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        tokenExpiresAt: state.tokenExpiresAt,
        user: state.user,
      }),
      onRehydrateStorage: () => (state) => {
        // ストアが復元された後に認証設定を初期化
        if (state && typeof window !== "undefined") {
          configureAuth(
            () => state.accessToken,
            (token) => {
              if (token) {
                const currentState = useAuthStore.getState();
                if (currentState.accessToken !== token) {
                  useAuthStore.setState({ accessToken: token });
                }
              } else {
                useAuthStore.getState().clearTokens();
              }
            },
            () => useAuthStore.getState().refreshAccessToken(),
          );
        }
      },
    },
  ),
);

// 初回ロード時に認証設定を初期化
if (typeof window !== "undefined") {
  const state = useAuthStore.getState();
  configureAuth(
    () => state.accessToken,
    (token) => {
      if (token) {
        const currentState = useAuthStore.getState();
        if (currentState.accessToken !== token) {
          useAuthStore.setState({ accessToken: token });
        }
      } else {
        useAuthStore.getState().clearTokens();
      }
    },
    () => useAuthStore.getState().refreshAccessToken(),
  );
}


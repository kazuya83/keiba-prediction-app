/**
 * APIクライアントのベース設定。
 * OpenAPI Generatorで生成されたクライアントをラップする。
 */

import axios, { AxiosInstance, AxiosRequestConfig } from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

/**
 * 認証トークンを取得する関数。
 * 認証ストアから取得する想定。
 */
export type TokenGetter = () => string | null;

/**
 * 認証トークンを設定する関数。
 * 認証ストアに保存する想定。
 */
export type TokenSetter = (token: string | null) => void;

/**
 * 認証トークンリフレッシュ関数。
 */
export type TokenRefresher = () => Promise<void>;

let tokenGetter: TokenGetter | null = null;
let tokenSetter: TokenSetter | null = null;
let tokenRefresher: TokenRefresher | null = null;

/**
 * 認証関連の関数を設定する。
 */
export function configureAuth(
  getter: TokenGetter,
  setter: TokenSetter,
  refresher: TokenRefresher,
): void {
  tokenGetter = getter;
  tokenSetter = setter;
  tokenRefresher = refresher;
}

/**
 * 認証付きAxiosインスタンスを作成する。
 */
export function createApiClient(): AxiosInstance {
  const client = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      "Content-Type": "application/json",
    },
  });

  // リクエストインターセプター: 認証トークンを自動付与
  client.interceptors.request.use(
    (config) => {
      const token = tokenGetter?.();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error),
  );

  // レスポンスインターセプター: 401エラー時にトークンリフレッシュを試行
  client.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config as AxiosRequestConfig & {
        _retry?: boolean;
      };

      if (error.response?.status === 401 && !originalRequest._retry && tokenRefresher) {
        originalRequest._retry = true;
        try {
          await tokenRefresher();
          const token = tokenGetter?.();
          if (token && originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${token}`;
          }
          return client(originalRequest);
        } catch (refreshError) {
          // リフレッシュ失敗時はログアウト処理を実行
          tokenSetter?.(null);
          return Promise.reject(refreshError);
        }
      }

      return Promise.reject(error);
    },
  );

  return client;
}

/**
 * デフォルトのAPIクライアントインスタンス。
 */
export const apiClient = createApiClient();


/**
 * 認証APIのhooks実装。
 * OpenAPI生成クライアントを利用してauthエンドポイントにアクセスする。
 */

import { useMutation, useQuery } from "@tanstack/react-query";
import { apiClient } from "./client";
import type {
  LoginRequest,
  LogoutRequest,
  OAuthLoginResponse,
  RefreshRequest,
  RegisterRequest,
  Token,
} from "./types";

// TODO: OpenAPI Generatorで生成されたクライアントを使用する場合は以下を置き換える
// import { AuthApi, Configuration } from "./generated";
// const authApi = new AuthApi(new Configuration({ basePath: API_BASE_URL }));

/**
 * ユーザー登録APIを呼び出す。
 */
export async function registerUser(request: RegisterRequest): Promise<Token> {
  const response = await apiClient.post<Token>("/api/auth/register", request);
  return response.data;
}

/**
 * ログインAPIを呼び出す。
 */
export async function loginUser(request: LoginRequest): Promise<Token> {
  const response = await apiClient.post<Token>("/api/auth/login", request);
  return response.data;
}

/**
 * ログアウトAPIを呼び出す。
 */
export async function logoutUser(request: LogoutRequest): Promise<void> {
  await apiClient.post("/api/auth/logout", request);
}

/**
 * リフレッシュトークンでアクセストークンを再発行する。
 */
export async function refreshToken(request: RefreshRequest): Promise<Token> {
  const response = await apiClient.post<Token>("/api/auth/refresh", request);
  return response.data;
}

/**
 * Google OAuthログインURLを取得する。
 */
export async function getGoogleLoginUrl(): Promise<OAuthLoginResponse> {
  const response = await apiClient.get<OAuthLoginResponse>("/api/auth/google/login");
  return response.data;
}

/**
 * ユーザー登録用のReact Query mutation hook。
 */
export function useRegister() {
  return useMutation({
    mutationFn: registerUser,
  });
}

/**
 * ログイン用のReact Query mutation hook。
 */
export function useLogin() {
  return useMutation({
    mutationFn: loginUser,
  });
}

/**
 * ログアウト用のReact Query mutation hook。
 */
export function useLogout() {
  return useMutation({
    mutationFn: logoutUser,
  });
}

/**
 * トークンリフレッシュ用のReact Query mutation hook。
 */
export function useRefreshToken() {
  return useMutation({
    mutationFn: refreshToken,
  });
}

/**
 * Google OAuthログインURL取得用のReact Query query hook。
 */
export function useGoogleLoginUrl() {
  return useQuery({
    queryKey: ["auth", "google", "login-url"],
    queryFn: getGoogleLoginUrl,
    enabled: false, // 手動で実行する
  });
}


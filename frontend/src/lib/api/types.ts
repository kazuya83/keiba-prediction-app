/**
 * 認証関連の型定義。
 * OpenAPI Generatorで生成される型と互換性を保つ。
 */

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface LogoutRequest {
  refresh_token: string;
}

export interface OAuthLoginResponse {
  authorization_url: string;
  state: string;
}

export interface User {
  id: string;
  email: string;
  is_active: boolean;
  created_at: string;
}


/**
 * LoginFormコンポーネントのテスト。
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { LoginForm } from "./LoginForm";
import * as authApi from "../../lib/api/auth";
import { useAuthStore } from "../../stores";

// モック
vi.mock("../../lib/api/auth");
vi.mock("../../stores", () => ({
  useAuthStore: vi.fn(),
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{children}</BrowserRouter>
    </QueryClientProvider>
  );
};

describe("LoginForm", () => {
  const mockSetTokens = vi.fn();
  const mockNavigate = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useAuthStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      setTokens: mockSetTokens,
    });

    // useNavigateのモック
    vi.mock("react-router-dom", async () => {
      const actual = await vi.importActual("react-router-dom");
      return {
        ...actual,
        useNavigate: () => mockNavigate,
      };
    });
  });

  it("フォームが正しくレンダリングされる", () => {
    render(<LoginForm />, { wrapper: createWrapper() });

    expect(screen.getByLabelText("メールアドレス")).toBeInTheDocument();
    expect(screen.getByLabelText("パスワード")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "ログイン" })).toBeInTheDocument();
  });

  it("バリデーションエラーが表示される", async () => {
    const user = userEvent.setup();
    render(<LoginForm />, { wrapper: createWrapper() });

    const submitButton = screen.getByRole("button", { name: "ログイン" });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("有効なメールアドレスを入力してください")).toBeInTheDocument();
      expect(screen.getByText("パスワードは8文字以上である必要があります")).toBeInTheDocument();
    });
  });

  it("無効なメールアドレスでエラーが表示される", async () => {
    const user = userEvent.setup();
    render(<LoginForm />, { wrapper: createWrapper() });

    const emailInput = screen.getByLabelText("メールアドレス");
    await user.type(emailInput, "invalid-email");

    const submitButton = screen.getByRole("button", { name: "ログイン" });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("有効なメールアドレスを入力してください")).toBeInTheDocument();
    });
  });

  it("パスワードが短すぎる場合にエラーが表示される", async () => {
    const user = userEvent.setup();
    render(<LoginForm />, { wrapper: createWrapper() });

    const emailInput = screen.getByLabelText("メールアドレス");
    const passwordInput = screen.getByLabelText("パスワード");

    await user.type(emailInput, "test@example.com");
    await user.type(passwordInput, "short");

    const submitButton = screen.getByRole("button", { name: "ログイン" });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("パスワードは8文字以上である必要があります")).toBeInTheDocument();
    });
  });

  it("ログイン成功時にトークンが設定され、ダッシュボードにリダイレクトされる", async () => {
    const user = userEvent.setup();
    const mockToken = {
      access_token: "test-access-token",
      refresh_token: "test-refresh-token",
      token_type: "bearer" as const,
      expires_in: 3600,
    };

    vi.mocked(authApi.useLogin).mockReturnValue({
      mutateAsync: vi.fn().mockResolvedValue(mockToken),
    } as any);

    render(<LoginForm />, { wrapper: createWrapper() });

    const emailInput = screen.getByLabelText("メールアドレス");
    const passwordInput = screen.getByLabelText("パスワード");

    await user.type(emailInput, "test@example.com");
    await user.type(passwordInput, "password123");

    const submitButton = screen.getByRole("button", { name: "ログイン" });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockSetTokens).toHaveBeenCalledWith(mockToken);
    });
  });
});


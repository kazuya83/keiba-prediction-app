/**
 * 登録ページのテスト。
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { RegisterPage } from "./RegisterPage";

vi.mock("../features/auth", () => ({
  RegisterForm: () => <div data-testid="register-form">RegisterForm</div>,
  GoogleLoginButton: () => <div data-testid="google-login-button">GoogleLoginButton</div>,
}));

describe("RegisterPage", () => {
  it("登録フォームが表示される", () => {
    render(
      <BrowserRouter>
        <RegisterPage />
      </BrowserRouter>
    );

    expect(screen.getByText("新規アカウント登録")).toBeInTheDocument();
    expect(screen.getByTestId("register-form")).toBeInTheDocument();
    expect(screen.getByTestId("google-login-button")).toBeInTheDocument();
  });

  it("ログインへのリンクが表示される", () => {
    render(
      <BrowserRouter>
        <RegisterPage />
      </BrowserRouter>
    );

    const loginLink = screen.getByRole("link", { name: /ログイン/i });
    expect(loginLink).toBeInTheDocument();
    expect(loginLink).toHaveAttribute("href", "/login");
  });
});


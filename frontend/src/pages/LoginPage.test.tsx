/**
 * ログインページのテスト。
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { LoginPage } from "./LoginPage";

vi.mock("../features/auth", () => ({
  LoginForm: () => <div data-testid="login-form">LoginForm</div>,
  GoogleLoginButton: () => <div data-testid="google-login-button">GoogleLoginButton</div>,
}));

describe("LoginPage", () => {
  it("ログインフォームが表示される", () => {
    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    );

    expect(screen.getByText("アカウントにログイン")).toBeInTheDocument();
    expect(screen.getByTestId("login-form")).toBeInTheDocument();
    expect(screen.getByTestId("google-login-button")).toBeInTheDocument();
  });

  it("新規登録へのリンクが表示される", () => {
    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    );

    const registerLink = screen.getByRole("link", { name: /新規登録/i });
    expect(registerLink).toBeInTheDocument();
    expect(registerLink).toHaveAttribute("href", "/register");
  });
});


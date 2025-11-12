/**
 * ダッシュボードページのテスト。
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { DashboardPage } from "./DashboardPage";
import { useAuthStore } from "../stores";

vi.mock("../stores", () => ({
  useAuthStore: vi.fn(),
}));

vi.mock("../components/common/Button", () => ({
  Button: ({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) => (
    <button onClick={onClick}>{children}</button>
  ),
}));

describe("DashboardPage", () => {
  const mockLogout = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useAuthStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      user: { email: "test@example.com" },
      logout: mockLogout,
    });
  });

  it("ダッシュボードのタイトルが表示される", () => {
    render(<DashboardPage />);

    expect(screen.getByText("ダッシュボード")).toBeInTheDocument();
  });

  it("ユーザーのメールアドレスが表示される", () => {
    render(<DashboardPage />);

    expect(screen.getByText(/ようこそ、test@example.comさん/)).toBeInTheDocument();
  });

  it("ログアウトボタンが表示される", () => {
    render(<DashboardPage />);

    const logoutButton = screen.getByRole("button", { name: /ログアウト/i });
    expect(logoutButton).toBeInTheDocument();
  });

  it("主要なセクションが表示される", () => {
    render(<DashboardPage />);

    expect(screen.getByText("予測履歴")).toBeInTheDocument();
    expect(screen.getByText("通知")).toBeInTheDocument();
    expect(screen.getByText("最近の予測")).toBeInTheDocument();
    expect(screen.getByText("予測精度")).toBeInTheDocument();
  });
});


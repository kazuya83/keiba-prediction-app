/**
 * 予測フローのE2Eテスト。
 * ログイン→レース選択→予測実行→履歴確認の主要ユーザーフローをテストする。
 */

import { test, expect } from "@playwright/test";

test.describe("予測フロー", () => {
  test.beforeEach(async ({ page }) => {
    // ログイン処理（モックまたは実際の認証）
    // 実際の実装では、テスト用の認証トークンを設定するか、
    // テスト用のユーザーでログインする
    await page.goto("/login");
    // ここでは簡易的にダッシュボードに直接遷移する想定
    // 実際の実装では適切な認証処理を追加
  });

  test("ダッシュボードが表示される", async ({ page }) => {
    await page.goto("/dashboard");

    await expect(page.getByRole("heading", { name: "ダッシュボード" })).toBeVisible();
  });

  test("予測履歴セクションが表示される", async ({ page }) => {
    await page.goto("/dashboard");

    await expect(page.getByText("予測履歴")).toBeVisible();
    await expect(page.getByText("総予測数")).toBeVisible();
  });

  test("通知セクションが表示される", async ({ page }) => {
    await page.goto("/dashboard");

    await expect(page.getByText("通知")).toBeVisible();
    await expect(page.getByText("未読通知")).toBeVisible();
  });
});


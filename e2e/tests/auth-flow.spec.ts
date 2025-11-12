/**
 * 認証フローのE2Eテスト。
 */

import { test, expect } from "@playwright/test";

test.describe("認証フロー", () => {
  test("ログインページが表示される", async ({ page }) => {
    await page.goto("/login");

    await expect(page.getByRole("heading", { name: "アカウントにログイン" })).toBeVisible();
    await expect(page.getByRole("link", { name: "新規登録" })).toBeVisible();
  });

  test("登録ページが表示される", async ({ page }) => {
    await page.goto("/register");

    await expect(page.getByRole("heading", { name: "新規アカウント登録" })).toBeVisible();
    await expect(page.getByRole("link", { name: "ログイン" })).toBeVisible();
  });

  test("ログインページから登録ページに遷移できる", async ({ page }) => {
    await page.goto("/login");
    await page.getByRole("link", { name: "新規登録" }).click();

    await expect(page).toHaveURL(/.*\/register/);
    await expect(page.getByRole("heading", { name: "新規アカウント登録" })).toBeVisible();
  });

  test("登録ページからログインページに遷移できる", async ({ page }) => {
    await page.goto("/register");
    await page.getByRole("link", { name: "ログイン" }).click();

    await expect(page).toHaveURL(/.*\/login/);
    await expect(page.getByRole("heading", { name: "アカウントにログイン" })).toBeVisible();
  });
});


import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright設定ファイル。
 * 詳細は https://playwright.dev/docs/test-configuration を参照。
 */
export default defineConfig({
  testDir: "./tests",
  /* テストの最大実行時間 */
  timeout: 30 * 1000,
  expect: {
    /* アサーションのタイムアウト */
    timeout: 5000,
  },
  /* テストを並列実行 */
  fullyParallel: true,
  /* CIで失敗した場合に再試行 */
  retries: process.env.CI ? 2 : 0,
  /* CIで使用するワーカー数 */
  workers: process.env.CI ? 1 : undefined,
  /* レポート設定 */
  reporter: [
    ["html"],
    ["json", { outputFile: "test-results/results.json" }],
    process.env.CI ? ["github"] : ["list"],
  ],
  /* 共有設定 */
  use: {
    /* ベースURL */
    baseURL: process.env.BASE_URL || "http://localhost:5173",
    /* アクションのタイムアウト */
    actionTimeout: 10 * 1000,
    /* スクリーンショット */
    screenshot: "only-on-failure",
    /* 動画 */
    video: "retain-on-failure",
    /* トレース */
    trace: "retain-on-failure",
  },

  /* プロジェクト設定 */
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "firefox",
      use: { ...devices["Desktop Firefox"] },
    },
    {
      name: "webkit",
      use: { ...devices["Desktop Safari"] },
    },
  ],

  /* 開発サーバーの起動設定 */
  webServer: {
    command: "cd ../frontend && pnpm dev",
    url: "http://localhost:5173",
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});


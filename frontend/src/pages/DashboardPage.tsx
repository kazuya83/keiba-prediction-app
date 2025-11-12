/**
 * ダッシュボードページ。
 * 予測履歴サマリや通知数などのプレースホルダーウィジェットを配置。
 */

import { useAuthStore } from "../stores";
import { Button } from "../components/common/Button";

export function DashboardPage() {
  const { user, logout } = useAuthStore();

  const handleLogout = async () => {
    await logout();
    window.location.href = "/login";
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">ダッシュボード</h1>
            <p className="mt-2 text-gray-600">
              {user?.email ? `ようこそ、${user.email}さん` : "ようこそ"}
            </p>
          </div>
          <Button onClick={handleLogout} variant="outline">
            ログアウト
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* 予測履歴サマリ */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">予測履歴</h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">総予測数</span>
                <span className="text-2xl font-bold text-gray-900">-</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">正解率</span>
                <span className="text-2xl font-bold text-gray-900">-</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">今月の予測数</span>
                <span className="text-2xl font-bold text-gray-900">-</span>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t">
              <Button variant="outline" className="w-full">
                詳細を見る
              </Button>
            </div>
          </div>

          {/* 通知 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">通知</h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">未読通知</span>
                <span className="text-2xl font-bold text-primary-600">-</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">今週の通知</span>
                <span className="text-2xl font-bold text-gray-900">-</span>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t">
              <Button variant="outline" className="w-full">
                通知一覧を見る
              </Button>
            </div>
          </div>

          {/* 最近の予測 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">最近の予測</h2>
            <div className="space-y-2">
              <p className="text-sm text-gray-500">まだ予測がありません</p>
            </div>
            <div className="mt-4 pt-4 border-t">
              <Button variant="outline" className="w-full">
                予測を実行
              </Button>
            </div>
          </div>

          {/* 予測精度 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">予測精度</h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">平均精度</span>
                <span className="text-2xl font-bold text-gray-900">-</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">最高精度</span>
                <span className="text-2xl font-bold text-gray-900">-</span>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t">
              <Button variant="outline" className="w-full">
                詳細を見る
              </Button>
            </div>
          </div>

          {/* おすすめレース */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">おすすめレース</h2>
            <div className="space-y-2">
              <p className="text-sm text-gray-500">おすすめレースはありません</p>
            </div>
            <div className="mt-4 pt-4 border-t">
              <Button variant="outline" className="w-full">
                レース一覧を見る
              </Button>
            </div>
          </div>

          {/* 統計情報 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">統計情報</h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">アクティブ日数</span>
                <span className="text-2xl font-bold text-gray-900">-</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">最終ログイン</span>
                <span className="text-sm text-gray-500">-</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


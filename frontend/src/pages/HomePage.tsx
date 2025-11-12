export function HomePage() {
  return (
    <div>
      <h1 className="text-4xl font-bold mb-4">競馬予測アプリ</h1>
      <p className="text-lg text-gray-600 mb-8">
        フロントエンド基盤セットアップが完了しました。
      </p>
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-semibold mb-4">機能</h2>
        <ul className="list-disc list-inside space-y-2">
          <li>React + TypeScript + Vite</li>
          <li>Tailwind CSS</li>
          <li>React Router</li>
          <li>Zustand（状態管理）</li>
          <li>Storybook</li>
        </ul>
      </div>
    </div>
  );
}


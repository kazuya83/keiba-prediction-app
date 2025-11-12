import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <div className="text-center">
      <h1 className="text-6xl font-bold text-gray-900 mb-4">404</h1>
      <p className="text-xl text-gray-600 mb-8">ページが見つかりませんでした</p>
      <Link
        to="/"
        className="inline-block px-6 py-3 bg-primary-600 text-white rounded hover:bg-primary-700 transition-colors"
      >
        ホームに戻る
      </Link>
    </div>
  );
}


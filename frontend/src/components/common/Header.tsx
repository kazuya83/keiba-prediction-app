import { Link } from "react-router-dom";

export function Header() {
  return (
    <header className="bg-white shadow-md">
      <nav className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="text-2xl font-bold text-primary-600">
            Keiba Prediction
          </Link>
          <div className="flex gap-4">
            <Link
              to="/"
              className="text-gray-700 hover:text-primary-600 transition-colors"
            >
              ホーム
            </Link>
          </div>
        </div>
      </nav>
    </header>
  );
}


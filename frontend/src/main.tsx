import React from "react";
import ReactDOM from "react-dom/client";

const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error("`root` 要素が見つかりません。");
}

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <main>
      <h1>Keiba Prediction App</h1>
      <p>フロントエンド初期セットアップが完了しました。</p>
    </main>
  </React.StrictMode>,
);


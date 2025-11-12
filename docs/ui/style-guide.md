# フロントエンドデザインガイドライン

本ドキュメントは、競馬予測アプリケーションのフロントエンドにおけるデザインガイドラインを定義します。

## 目次

- [カラーパレット](#カラーパレット)
- [タイポグラフィ](#タイポグラフィ)
- [コンポーネント命名規則](#コンポーネント命名規則)
- [スタイリング規則](#スタイリング規則)
- [コンポーネント設計原則](#コンポーネント設計原則)
- [アクセシビリティ](#アクセシビリティ)

## カラーパレット

### プライマリカラー

プライマリカラーは、アプリケーションの主要なアクションや重要な要素に使用します。

```typescript
// tailwind.config.js
primary: {
  50: "#f0f9ff",   // 最も薄い
  100: "#e0f2fe",
  200: "#bae6fd",
  300: "#7dd3fc",
  400: "#38bdf8",
  500: "#0ea5e9",  // ベースカラー
  600: "#0284c7",  // ホバー・アクティブ
  700: "#0369a1",
  800: "#075985",
  900: "#0c4a6e",  // 最も濃い
}
```

**使用例**:
- プライマリボタン: `bg-primary-600 text-white hover:bg-primary-700`
- リンク: `text-primary-600 hover:text-primary-700`
- アクセント: `border-primary-500`

### セカンダリカラー

セカンダリカラーは、補助的なアクションや装飾的な要素に使用します。

```typescript
secondary: {
  50: "#faf5ff",
  100: "#f3e8ff",
  200: "#e9d5ff",
  300: "#d8b4fe",
  400: "#c084fc",
  500: "#a855f7",  // ベースカラー
  600: "#9333ea",  // ホバー・アクティブ
  700: "#7e22ce",
  800: "#6b21a8",
  900: "#581c87",
}
```

**使用例**:
- セカンダリボタン: `bg-secondary-600 text-white hover:bg-secondary-700`
- 装飾的な要素: `text-secondary-500`

### グレースケール

テキスト、背景、ボーダーなどに使用します。

```typescript
// Tailwind CSSのデフォルトグレースケールを使用
gray: {
  50: "#f9fafb",   // 最も薄い背景
  100: "#f3f4f6",
  200: "#e5e7eb",
  300: "#d1d5db",   // ボーダー
  400: "#9ca3af",
  500: "#6b7280",   // プレースホルダー
  600: "#4b5563",   // セカンダリテキスト
  700: "#374151",   // プライマリテキスト
  800: "#1f2937",
  900: "#111827",   // 最も濃いテキスト
}
```

**使用例**:
- 背景: `bg-gray-50` (ページ背景), `bg-white` (カード背景)
- テキスト: `text-gray-900` (プライマリ), `text-gray-600` (セカンダリ)
- ボーダー: `border-gray-300`

### セマンティックカラー

状態や意味を表現するために使用します。

```typescript
// Tailwind CSSのデフォルトカラーを使用
success: "green-600"    // 成功メッセージ
warning: "yellow-600"   // 警告メッセージ
error: "red-600"        // エラーメッセージ
info: "blue-600"        // 情報メッセージ
```

**使用例**:
- 成功メッセージ: `bg-green-50 text-green-800 border-green-200`
- エラーメッセージ: `bg-red-50 text-red-800 border-red-200`
- 警告メッセージ: `bg-yellow-50 text-yellow-800 border-yellow-200`

## タイポグラフィ

### フォントサイズ

Tailwind CSSのデフォルトフォントサイズを使用します。

```typescript
text-xs:    "0.75rem"   // 12px - 補足情報
text-sm:    "0.875rem"  // 14px - セカンダリテキスト
text-base:  "1rem"      // 16px - 本文（デフォルト）
text-lg:    "1.125rem"  // 18px - 強調テキスト
text-xl:    "1.25rem"   // 20px - 小見出し
text-2xl:   "1.5rem"    // 24px - 見出し
text-3xl:   "1.875rem"  // 30px - 大見出し
text-4xl:   "2.25rem"   // 36px - 特大見出し
```

### フォントウェイト

```typescript
font-normal:  400  // 本文
font-medium:  500  // 強調テキスト
font-semibold: 600 // 見出し
font-bold:    700  // 重要見出し
```

### 行の高さ

```typescript
leading-tight:  1.25  // 見出し
leading-normal: 1.5   // 本文（デフォルト）
leading-relaxed: 1.625 // 読みやすい本文
```

## コンポーネント命名規則

### ファイル名

- コンポーネントファイル: `PascalCase.tsx` (例: `Button.tsx`, `RaceCard.tsx`)
- ストーリーファイル: `PascalCase.stories.tsx` (例: `Button.stories.tsx`)
- インデックスファイル: `index.ts`

### コンポーネント名

- コンポーネント名は `PascalCase` を使用
- ファイル名とコンポーネント名は一致させる

```typescript
// Button.tsx
export function Button({ ... }: ButtonProps) { ... }

// RaceCard.tsx
export function RaceCard({ ... }: RaceCardProps) { ... }
```

### ディレクトリ構造

```
src/components/
  common/          # 共通コンポーネント
    Button.tsx
    Layout.tsx
    Header.tsx
  domain/          # ドメイン固有コンポーネント
    RaceCard.tsx
    PredictionForm.tsx
```

## スタイリング規則

### Tailwind CSSの使用

- インラインスタイルは使用しない
- Tailwind CSSのユーティリティクラスを使用
- カスタムスタイルが必要な場合は、`@layer` ディレクティブを使用

```typescript
// ✅ 良い例
<button className="bg-primary-600 text-white px-4 py-2 rounded hover:bg-primary-700">
  送信
</button>

// ❌ 悪い例
<button style={{ backgroundColor: '#0ea5e9', color: 'white' }}>
  送信
</button>
```

### クラス名の順序

クラス名は以下の順序で記述します：

1. レイアウト（`flex`, `grid`, `container`など）
2. サイズ（`w-`, `h-`, `p-`, `m-`など）
3. タイポグラフィ（`text-`, `font-`など）
4. 背景・ボーダー（`bg-`, `border-`など）
5. エフェクト（`shadow-`, `opacity-`など）
6. インタラクティブ（`hover:`, `focus:`など）

```typescript
// ✅ 良い例
<button className="flex items-center px-4 py-2 text-base font-semibold bg-primary-600 text-white rounded shadow-md hover:bg-primary-700 focus:outline-none focus:ring-2">
  送信
</button>
```

### 再利用可能なスタイル

共通のスタイルパターンは、コンポーネントとして抽出します。

```typescript
// Button.tsx
export function Button({
  variant = "primary",
  size = "md",
  className = "",
  ...props
}: ButtonProps) {
  const baseStyles = "font-semibold rounded transition-colors focus:outline-none focus:ring-2";
  const variantStyles = {
    primary: "bg-primary-600 text-white hover:bg-primary-700",
    secondary: "bg-secondary-600 text-white hover:bg-secondary-700",
    outline: "border-2 border-primary-600 text-primary-600 hover:bg-primary-50",
  };
  // ...
}
```

## コンポーネント設計原則

### 単一責任の原則

各コンポーネントは、1つの明確な責任を持つようにします。

```typescript
// ✅ 良い例: レースカードコンポーネント
export function RaceCard({ race }: RaceCardProps) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-xl font-bold">{race.name}</h3>
      <p className="text-gray-600">{race.venue}</p>
    </div>
  );
}

// ❌ 悪い例: レースカードと予測フォームが混在
export function RaceCard({ race, onSubmit }: RaceCardProps) {
  // レース表示と予測フォームが混在している
}
```

### Propsの型安全性

すべてのPropsに型を定義します。

```typescript
// ✅ 良い例
interface ButtonProps {
  children: ReactNode;
  variant?: "primary" | "secondary" | "outline";
  size?: "sm" | "md" | "lg";
  onClick?: () => void;
  disabled?: boolean;
}

export function Button({ ... }: ButtonProps) { ... }
```

### デフォルト値の設定

オプショナルなPropsには、適切なデフォルト値を設定します。

```typescript
export function Button({
  variant = "primary",
  size = "md",
  disabled = false,
  ...props
}: ButtonProps) {
  // ...
}
```

## アクセシビリティ

### セマンティックHTML

適切なHTML要素を使用します。

```typescript
// ✅ 良い例
<button onClick={handleClick}>送信</button>
<nav>
  <ul>
    <li><a href="/">ホーム</a></li>
  </ul>
</nav>

// ❌ 悪い例
<div onClick={handleClick}>送信</div>
<div>
  <div><div onClick={() => navigate("/")}>ホーム</div></div>
</div>
```

### ARIA属性

必要に応じてARIA属性を追加します。

```typescript
// ✅ 良い例
<button
  aria-label="メニューを開く"
  aria-expanded={isOpen}
  onClick={toggleMenu}
>
  <MenuIcon />
</button>

<div role="alert" aria-live="polite">
  {errorMessage}
</div>
```

### キーボードナビゲーション

すべてのインタラクティブ要素は、キーボードで操作可能にします。

```typescript
// ✅ 良い例
<button
  onClick={handleClick}
  onKeyDown={(e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handleClick();
    }
  }}
>
  送信
</button>
```

### フォーカス管理

フォーカス可能な要素には、明確なフォーカススタイルを設定します。

```typescript
// ✅ 良い例
<button className="focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2">
  送信
</button>
```

### 色のコントラスト

テキストと背景のコントラスト比は、WCAG 2.1 AA基準（4.5:1以上）を満たします。

```typescript
// ✅ 良い例: 十分なコントラスト
<div className="bg-white text-gray-900">テキスト</div>

// ❌ 悪い例: コントラスト不足
<div className="bg-gray-200 text-gray-300">テキスト</div>
```

## レスポンシブデザイン

### ブレークポイント

Tailwind CSSのデフォルトブレークポイントを使用します。

```typescript
sm:  "640px"   // スマートフォン（横向き）
md:  "768px"   // タブレット
lg:  "1024px"  // デスクトップ
xl:  "1280px"  // 大型デスクトップ
2xl: "1536px"  // 超大型デスクトップ
```

### モバイルファースト

モバイルファーストのアプローチでスタイルを記述します。

```typescript
// ✅ 良い例: モバイルファースト
<div className="text-sm md:text-base lg:text-lg">
  テキスト
</div>

// ❌ 悪い例: デスクトップファースト
<div className="text-lg lg:text-base md:text-sm">
  テキスト
</div>
```

## アニメーションとトランジション

### トランジション

インタラクティブな要素には、適切なトランジションを設定します。

```typescript
// ✅ 良い例
<button className="transition-colors hover:bg-primary-700">
  送信
</button>

<div className="transition-opacity hover:opacity-80">
  コンテンツ
</div>
```

### アニメーション

過度なアニメーションは避け、ユーザー体験を向上させるもののみを使用します。

```typescript
// ✅ 良い例: ローディングスピナー
<div className="animate-spin">...</div>

// ❌ 悪い例: 過度なアニメーション
<div className="animate-bounce animate-pulse animate-ping">...</div>
```

## ベストプラクティス

1. **一貫性**: 同じパターンは同じスタイルを使用
2. **再利用性**: 共通のスタイルはコンポーネント化
3. **パフォーマンス**: 不要な再レンダリングを避ける
4. **保守性**: コードは読みやすく、理解しやすく
5. **テスト**: コンポーネントはテスト可能に

## 参考資料

- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [React Documentation](https://react.dev/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Web Content Accessibility Guidelines](https://www.w3.org/WAI/WCAG21/Understanding/)


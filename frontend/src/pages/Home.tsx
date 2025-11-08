const Home = () => {
  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="border-4 border-dashed border-gray-200 rounded-lg p-8 text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          競馬予測アプリケーション
        </h1>
        <p className="text-gray-600 mb-8">
          機械学習を活用した競馬予測システム
        </p>
        <div className="space-x-4">
          <button className="bg-primary-600 text-white px-6 py-3 rounded-md hover:bg-primary-700">
            レースを選択
          </button>
          <button className="bg-gray-200 text-gray-700 px-6 py-3 rounded-md hover:bg-gray-300">
            予測履歴
          </button>
        </div>
      </div>
    </div>
  )
}

export default Home




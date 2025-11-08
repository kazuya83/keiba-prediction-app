import { useNavigate } from 'react-router-dom'
import { handleError } from '../utils/errorHandler'

const Home = () => {
  const navigate = useNavigate()

  const handleSelectRace = () => {
    try {
      // レース選択ページへの遷移（将来実装）
      // 現時点ではコンソールにログを出力
      console.log('レース選択ボタンがクリックされました')
      // navigate('/races') // 将来の実装
    } catch (error) {
      handleError(
        error instanceof Error ? error : new Error(String(error)),
        'Home.handleSelectRace'
      )
    }
  }

  const handleViewHistory = () => {
    try {
      // 予測履歴ページへの遷移（将来実装）
      // 現時点ではコンソールにログを出力
      console.log('予測履歴ボタンがクリックされました')
      // navigate('/predictions') // 将来の実装
    } catch (error) {
      handleError(
        error instanceof Error ? error : new Error(String(error)),
        'Home.handleViewHistory'
      )
    }
  }

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
          <button
            onClick={handleSelectRace}
            className="bg-primary-600 text-white px-6 py-3 rounded-md hover:bg-primary-700 transition-colors"
            type="button"
          >
            レースを選択
          </button>
          <button
            onClick={handleViewHistory}
            className="bg-gray-200 text-gray-700 px-6 py-3 rounded-md hover:bg-gray-300 transition-colors"
            type="button"
          >
            予測履歴
          </button>
        </div>
      </div>
    </div>
  )
}

export default Home




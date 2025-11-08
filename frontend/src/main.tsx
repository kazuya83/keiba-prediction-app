import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import { AuthProvider } from './context/AuthContext'
import './index.css'
import { startErrorMonitoring } from './utils/errorMonitor'
import { errorHandler, handleUnhandledRejection } from './utils/errorHandler'

// エラー監視を開始
startErrorMonitoring()

// グローバルエラーハンドラーを設定
window.addEventListener('error', (event) => {
  const error = event.error || new Error(event.message)
  errorHandler.logError(error, `global:${event.filename}:${event.lineno}`)
})

window.addEventListener('unhandledrejection', handleUnhandledRejection)

// ページロード時にリロードカウントをチェック
window.addEventListener('load', () => {
  const recoveryAttempt = sessionStorage.getItem('error_recovery_attempt')
  const recoveryTime = sessionStorage.getItem('error_recovery_time')

  if (recoveryAttempt && recoveryTime) {
    const attemptCount = parseInt(recoveryAttempt, 10)
    const timeDiff = Date.now() - parseInt(recoveryTime, 10)

    // 5秒以内にリロードされた場合、復旧が成功したとみなす
    if (timeDiff < 5000) {
      console.log(`Recovery successful after ${attemptCount} attempt(s)`)
      // リロードカウントをリセット（成功した場合）
      if (attemptCount < 3) {
        errorHandler.resetReloadCount()
      }
    }

    // セッションストレージをクリア
    sessionStorage.removeItem('error_recovery_attempt')
    sessionStorage.removeItem('error_recovery_time')
  }
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AuthProvider>
      <App />
    </AuthProvider>
  </React.StrictMode>,
)




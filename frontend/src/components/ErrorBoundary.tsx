import React, { Component, ErrorInfo, ReactNode } from 'react'
import { errorHandler } from '../utils/errorHandler'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
  recoveryAttempted: boolean
}

/**
 * Error Boundaryコンポーネント
 * Reactコンポーネントツリー内のエラーをキャッチし、自動復旧を試みる
 */
class ErrorBoundary extends Component<Props, State> {
  private recoveryTimeoutId: NodeJS.Timeout | null = null

  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      recoveryAttempted: false,
    }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // エラーをログに記録
    errorHandler.logError(error, 'ErrorBoundary')
    console.error('ErrorBoundary caught an error:', error, errorInfo)

    this.setState({
      error,
      errorInfo,
    })

    // カスタムエラーハンドラーを呼び出し
    if (this.props.onError) {
      this.props.onError(error, errorInfo)
    }

    // 自動復旧を試みる
    this.attemptRecovery()
  }

  /**
   * 自動復旧を試みる
   */
  private attemptRecovery = (): void => {
    if (this.state.recoveryAttempted) {
      return
    }

    if (errorHandler.canRecover()) {
      this.setState({ recoveryAttempted: true })

      // 少し待ってから復旧を試みる
      this.recoveryTimeoutId = setTimeout(() => {
        console.log('ErrorBoundary: Attempting automatic recovery...')
        if (errorHandler.recover()) {
          // 復旧が成功した場合、状態をリセット
          this.setState({
            hasError: false,
            error: null,
            errorInfo: null,
            recoveryAttempted: false,
          })
        }
      }, 2000)
    }
  }

  /**
   * 手動でリセット
   */
  private handleReset = (): void => {
    if (this.recoveryTimeoutId) {
      clearTimeout(this.recoveryTimeoutId)
      this.recoveryTimeoutId = null
    }

    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      recoveryAttempted: false,
    })

    errorHandler.resetReloadCount()
  }

  /**
   * ページをリロード
   */
  private handleReload = (): void => {
    window.location.reload()
  }

  componentWillUnmount(): void {
    if (this.recoveryTimeoutId) {
      clearTimeout(this.recoveryTimeoutId)
    }
  }

  render(): ReactNode {
    if (this.state.hasError) {
      // カスタムフォールバックUIが提供されている場合
      if (this.props.fallback) {
        return this.props.fallback
      }

      // デフォルトのエラーUI
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
          <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full mb-4">
              <svg
                className="w-6 h-6 text-red-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-gray-900 text-center mb-2">
              エラーが発生しました
            </h2>
            <p className="text-gray-600 text-center mb-6">
              アプリケーションでエラーが発生しました。自動復旧を試みています...
            </p>

            {this.state.error && (
              <div className="mb-6 p-4 bg-gray-100 rounded-md">
                <p className="text-sm text-gray-800 font-mono break-all">
                  {this.state.error.message}
                </p>
              </div>
            )}

            <div className="flex space-x-3">
              <button
                onClick={this.handleReset}
                className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
              >
                再試行
              </button>
              <button
                onClick={this.handleReload}
                className="flex-1 bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 transition-colors"
              >
                ページをリロード
              </button>
            </div>

            {import.meta.env.DEV && this.state.errorInfo && (
              <details className="mt-4">
                <summary className="cursor-pointer text-sm text-gray-600 hover:text-gray-800">
                  詳細情報（開発モード）
                </summary>
                <pre className="mt-2 p-4 bg-gray-100 rounded-md text-xs overflow-auto max-h-60">
                  {this.state.errorInfo.componentStack}
                </pre>
              </details>
            )}
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary


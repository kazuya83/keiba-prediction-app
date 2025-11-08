/**
 * エラーハンドリングユーティリティ
 * アプリケーション全体で発生するエラーを処理・記録する
 */

export interface ErrorInfo {
  message: string
  stack?: string
  source?: string
  lineno?: number
  colno?: number
  error?: Error
  timestamp: number
  url?: string
  userAgent?: string
}

class ErrorHandler {
  private errorLog: ErrorInfo[] = []
  private maxLogSize = 100
  private reloadCount = 0
  private maxReloadAttempts = 3
  private reloadCooldown = 5000 // 5秒
  private lastReloadTime = 0

  /**
   * エラー情報を記録
   */
  logError(error: Error | string, source?: string): void {
    const errorInfo: ErrorInfo = {
      message: typeof error === 'string' ? error : error.message,
      stack: typeof error === 'object' && error.stack ? error.stack : undefined,
      source: source || 'unknown',
      timestamp: Date.now(),
      url: window.location.href,
      userAgent: navigator.userAgent,
      error: typeof error === 'object' ? error : undefined,
    }

    this.errorLog.push(errorInfo)

    // ログサイズを制限
    if (this.errorLog.length > this.maxLogSize) {
      this.errorLog.shift()
    }

    // コンソールにも出力（開発環境）
    if (import.meta.env?.DEV) {
      console.error('Error logged:', errorInfo)
    }

    // エラーをサーバーに送信（オプション）
    this.sendErrorToServer(errorInfo).catch((err) => {
      console.error('Failed to send error to server:', err)
    })
  }

  /**
   * エラーをサーバーに送信
   */
  private async sendErrorToServer(errorInfo: ErrorInfo): Promise<void> {
    try {
      // 本番環境でのみエラーをサーバーに送信
      if (import.meta.env?.PROD) {
        const response = await fetch('/api/v1/errors', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(errorInfo),
        })

        if (!response.ok) {
          throw new Error('Failed to send error to server')
        }
      }
    } catch (error) {
      // サーバーへの送信に失敗してもアプリケーションは続行
      console.error('Error sending error to server:', error)
    }
  }

  /**
   * エラーログを取得
   */
  getErrorLog(): ErrorInfo[] {
    return [...this.errorLog]
  }

  /**
   * エラーログをクリア
   */
  clearErrorLog(): void {
    this.errorLog = []
  }

  /**
   * アプリケーションを復旧する（ページをリロード）
   */
  recover(): boolean {
    const now = Date.now()

    // クールダウン期間をチェック
    if (now - this.lastReloadTime < this.reloadCooldown) {
      console.warn('Recovery attempt too soon, skipping...')
      return false
    }

    // 最大リロード回数をチェック
    if (this.reloadCount >= this.maxReloadAttempts) {
      console.error(
        `Max reload attempts (${this.maxReloadAttempts}) reached. Stopping auto-recovery.`
      )
      return false
    }

    this.reloadCount++
    this.lastReloadTime = now

    console.log(`Attempting recovery (${this.reloadCount}/${this.maxReloadAttempts})...`)

    // リロード前に状態を保存
    sessionStorage.setItem('error_recovery_attempt', this.reloadCount.toString())
    sessionStorage.setItem('error_recovery_time', now.toString())

    // ページをリロード
    window.location.reload()

    return true
  }

  /**
   * リロードカウントをリセット
   */
  resetReloadCount(): void {
    this.reloadCount = 0
    this.lastReloadTime = 0
    sessionStorage.removeItem('error_recovery_attempt')
    sessionStorage.removeItem('error_recovery_time')
  }

  /**
   * リロードカウントを取得
   */
  getReloadCount(): number {
    return this.reloadCount
  }

  /**
   * 復旧が可能かチェック
   */
  canRecover(): boolean {
    const now = Date.now()
    return (
      this.reloadCount < this.maxReloadAttempts &&
      now - this.lastReloadTime >= this.reloadCooldown
    )
  }
}

// シングルトンインスタンス
export const errorHandler = new ErrorHandler()

/**
 * エラーを処理するヘルパー関数
 */
export function handleError(error: Error | string, source?: string): void {
  errorHandler.logError(error, source)

  // 重大なエラーの場合、自動復旧を試みる
  if (errorHandler.canRecover()) {
    // 少し待ってから復旧を試みる（他のエラー処理が完了するのを待つ）
    setTimeout(() => {
      errorHandler.recover()
    }, 1000)
  }
}

/**
 * 未処理のPromise拒否を処理
 */
export function handleUnhandledRejection(event: PromiseRejectionEvent): void {
  const error = event.reason instanceof Error ? event.reason : new Error(String(event.reason))
  errorHandler.logError(error, 'unhandledRejection')

  if (errorHandler.canRecover()) {
    setTimeout(() => {
      errorHandler.recover()
    }, 1000)
  }
}


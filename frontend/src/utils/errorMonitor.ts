/**
 * コンソールエラー監視ユーティリティ
 * ブラウザのコンソールエラーを監視し、自動復旧を行う
 */

import { errorHandler, handleError } from './errorHandler'

class ErrorMonitor {
  private isMonitoring = false
  private originalConsoleError: typeof console.error
  private originalConsoleWarn: typeof console.warn
  private errorCount = 0
  private errorThreshold = 5 // 5回のエラーで復旧を試みる
  private errorWindow = 10000 // 10秒間
  private errorTimestamps: number[] = []

  /**
   * エラー監視を開始
   */
  start(): void {
    if (this.isMonitoring) {
      console.warn('Error monitoring is already active')
      return
    }

    this.isMonitoring = true
    this.errorCount = 0
    this.errorTimestamps = []

    // 元のコンソールメソッドを保存
    this.originalConsoleError = console.error.bind(console)
    this.originalConsoleWarn = console.warn.bind(console)

    // コンソールエラーをインターセプト
    console.error = (...args: any[]) => {
      this.handleConsoleError(args)
      this.originalConsoleError(...args)
    }

    // コンソール警告をインターセプト（重大な警告のみ）
    console.warn = (...args: any[]) => {
      this.handleConsoleWarn(args)
      this.originalConsoleWarn(...args)
    }

    // グローバルエラーハンドラーを設定
    window.addEventListener('error', this.handleWindowError)
    window.addEventListener('unhandledrejection', this.handleUnhandledRejection)

    // 定期的にエラーカウントをリセット
    setInterval(() => {
      this.cleanupOldErrors()
    }, this.errorWindow)

    console.log('Error monitoring started')
  }

  /**
   * エラー監視を停止
   */
  stop(): void {
    if (!this.isMonitoring) {
      return
    }

    this.isMonitoring = false

    // 元のコンソールメソッドを復元
    console.error = this.originalConsoleError
    console.warn = this.originalConsoleWarn

    // イベントリスナーを削除
    window.removeEventListener('error', this.handleWindowError)
    window.removeEventListener('unhandledrejection', this.handleUnhandledRejection)

    console.log('Error monitoring stopped')
  }

  /**
   * コンソールエラーを処理
   */
  private handleConsoleError = (args: any[]): void => {
    const errorMessage = args
      .map((arg) => {
        if (typeof arg === 'string') {
          return arg
        }
        if (arg instanceof Error) {
          return arg.message
        }
        try {
          return JSON.stringify(arg)
        } catch {
          return String(arg)
        }
      })
      .join(' ')

    // 重大なエラーのみを記録
    if (this.isCriticalError(errorMessage)) {
      this.recordError(errorMessage, 'console.error')
    }
  }

  /**
   * コンソール警告を処理
   */
  private handleConsoleWarn = (args: any[]): void => {
    const warningMessage = args
      .map((arg) => {
        if (typeof arg === 'string') {
          return arg
        }
        if (arg instanceof Error) {
          return arg.message
        }
        try {
          return JSON.stringify(arg)
        } catch {
          return String(arg)
        }
      })
      .join(' ')

    // 重大な警告のみを記録
    if (this.isCriticalWarning(warningMessage)) {
      this.recordError(warningMessage, 'console.warn')
    }
  }

  /**
   * ウィンドウエラーを処理
   */
  private handleWindowError = (event: ErrorEvent): void => {
    const error = event.error || new Error(event.message)
    errorHandler.logError(error, `window.error:${event.filename}:${event.lineno}`)

    this.recordError(event.message, 'window.error')

    // エラーが多すぎる場合、自動復旧を試みる
    if (this.shouldAttemptRecovery()) {
      this.attemptRecovery()
    }
  }

  /**
   * 未処理のPromise拒否を処理
   */
  private handleUnhandledRejection = (event: PromiseRejectionEvent): void => {
    const error = event.reason instanceof Error ? event.reason : new Error(String(event.reason))
    errorHandler.logError(error, 'unhandledRejection')

    this.recordError(error.message, 'unhandledRejection')

    // エラーが多すぎる場合、自動復旧を試みる
    if (this.shouldAttemptRecovery()) {
      this.attemptRecovery()
    }
  }

  /**
   * エラーを記録
   */
  private recordError(message: string, source: string): void {
    const now = Date.now()
    this.errorTimestamps.push(now)
    this.errorCount++

    // エラーログに記録
    errorHandler.logError(new Error(message), source)

    // エラーが多すぎる場合、自動復旧を試みる
    if (this.shouldAttemptRecovery()) {
      this.attemptRecovery()
    }
  }

  /**
   * 重大なエラーかどうかを判定
   */
  private isCriticalError(message: string): boolean {
    const criticalPatterns = [
      /uncaught/i,
      /unhandled/i,
      /referenceerror/i,
      /typeerror/i,
      /syntaxerror/i,
      /network error/i,
      /failed to fetch/i,
      /chunk load error/i,
      /loading chunk/i,
      /script error/i,
    ]

    return criticalPatterns.some((pattern) => pattern.test(message))
  }

  /**
   * 重大な警告かどうかを判定
   */
  private isCriticalWarning(message: string): boolean {
    const criticalPatterns = [
      /deprecated/i,
      /security/i,
      /cross-origin/i,
      /cors/i,
      /mixed content/i,
    ]

    return criticalPatterns.some((pattern) => pattern.test(message))
  }

  /**
   * 復旧を試みるべきかどうかを判定
   */
  private shouldAttemptRecovery(): boolean {
    // エラーが閾値を超えているか
    if (this.errorCount < this.errorThreshold) {
      return false
    }

    // エラーハンドラーが復旧可能か
    if (!errorHandler.canRecover()) {
      return false
    }

    // 最近のエラーが多すぎるか
    const now = Date.now()
    const recentErrors = this.errorTimestamps.filter(
      (timestamp) => now - timestamp < this.errorWindow
    )

    return recentErrors.length >= this.errorThreshold
  }

  /**
   * 自動復旧を試みる
   */
  private attemptRecovery(): void {
    console.warn(
      `Too many errors detected (${this.errorCount}). Attempting automatic recovery...`
    )

    // エラーカウントをリセット
    this.errorCount = 0
    this.errorTimestamps = []

    // 復旧を試みる
    if (errorHandler.recover()) {
      console.log('Recovery initiated. Page will reload...')
    } else {
      console.error('Recovery failed. Please refresh the page manually.')
    }
  }

  /**
   * 古いエラータイムスタンプをクリーンアップ
   */
  private cleanupOldErrors(): void {
    const now = Date.now()
    this.errorTimestamps = this.errorTimestamps.filter(
      (timestamp) => now - timestamp < this.errorWindow
    )

    // エラーカウントを更新
    this.errorCount = this.errorTimestamps.length
  }

  /**
   * 監視状態を取得
   */
  isActive(): boolean {
    return this.isMonitoring
  }

  /**
   * エラーカウントを取得
   */
  getErrorCount(): number {
    return this.errorCount
  }
}

// シングルトンインスタンス
export const errorMonitor = new ErrorMonitor()

/**
 * エラー監視を開始するヘルパー関数
 */
export function startErrorMonitoring(): void {
  errorMonitor.start()
}

/**
 * エラー監視を停止するヘルパー関数
 */
export function stopErrorMonitoring(): void {
  errorMonitor.stop()
}


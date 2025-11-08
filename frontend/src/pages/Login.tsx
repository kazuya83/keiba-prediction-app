import { FormEvent, useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import type { Location } from 'react-router-dom'
import { useAuth } from '@/hooks'
import { handleError } from '../utils/errorHandler'

type LocationState = {
  from?: Location
}

const Login = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { login, isAuthenticated } = useAuth()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  useEffect(() => {
    if (isAuthenticated && location.pathname === '/login') {
      const state = location.state as LocationState | null
      const redirectPath = state?.from?.pathname ?? '/'
      navigate(redirectPath, { replace: true })
    }
  }, [isAuthenticated, location, navigate])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (!email || !password) {
      setErrorMessage('メールアドレスとパスワードを入力してください')
      return
    }

    setSubmitting(true)
    setErrorMessage(null)

    try {
      // TODO: バックエンドの認証APIと連携する
      const fakeToken = btoa(`${email}:${password}`)
      login(fakeToken)

      const state = location.state as LocationState | null
      const redirectPath = state?.from?.pathname ?? '/'
      navigate(redirectPath, { replace: true })
    } catch (error) {
      handleError(
        error instanceof Error ? error : new Error(String(error)),
        'Login.handleSubmit',
      )
      setErrorMessage('ログインに失敗しました。時間を置いて再度お試しください。')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md rounded-lg bg-white p-8 shadow">
        <h1 className="mb-6 text-center text-2xl font-semibold text-gray-900">
          ログイン
        </h1>
        <form className="space-y-6" onSubmit={handleSubmit}>
          <div>
            <label
              className="block text-sm font-medium text-gray-700"
              htmlFor="email"
            >
              メールアドレス
            </label>
            <input
              id="email"
              autoComplete="email"
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-primary-500"
              onChange={(event) => setEmail(event.target.value)}
              type="email"
              value={email}
            />
          </div>
          <div>
            <label
              className="block text-sm font-medium text-gray-700"
              htmlFor="password"
            >
              パスワード
            </label>
            <input
              id="password"
              autoComplete="current-password"
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-primary-500"
              onChange={(event) => setPassword(event.target.value)}
              type="password"
              value={password}
            />
          </div>
          {errorMessage ? (
            <p className="text-sm text-red-600">{errorMessage}</p>
          ) : null}
          <button
            className="flex w-full justify-center rounded-md bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:bg-primary-300"
            disabled={submitting}
            type="submit"
          >
            {submitting ? '送信中...' : 'ログイン'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default Login



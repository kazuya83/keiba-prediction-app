import axios, { AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios'
import type { ApiResponse, ApiError } from '@/types'
import { handleError } from '../utils/errorHandler'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60秒
})

// リクエストインターセプター（トークン追加など）
api.interceptors.request.use(
  (config) => {
    try {
      const token = localStorage.getItem('access_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    } catch (error) {
      handleError(error instanceof Error ? error : new Error(String(error)), 'api.request')
      return Promise.reject(error)
    }
  },
  (error) => {
    handleError(error instanceof Error ? error : new Error(String(error)), 'api.request.error')
    return Promise.reject(error)
  }
)

// レスポンスインターセプター（エラーハンドリング）
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    // ネットワークエラーの場合
    if (!error.response) {
      handleError(
        new Error('Network error: Unable to connect to server'),
        'api.network.error'
      )
      return Promise.reject(error)
    }

    // HTTPステータスコードに応じた処理
    switch (error.response.status) {
      case 401:
        // 認証エラーの場合、ログインページにリダイレクト
        try {
          localStorage.removeItem('access_token')
          window.location.href = '/login'
        } catch (e) {
          handleError(
            e instanceof Error ? e : new Error(String(e)),
            'api.auth.error'
          )
        }
        break
      case 403:
        handleError(
          new Error('Forbidden: You do not have permission to access this resource'),
          'api.forbidden'
        )
        break
      case 404:
        handleError(
          new Error('Not Found: The requested resource was not found'),
          'api.notfound'
        )
        break
      case 500:
      case 502:
      case 503:
      case 504:
        handleError(
          new Error(`Server error: ${error.response.status}`),
          `api.server.error.${error.response.status}`
        )
        break
      default:
        handleError(
          new Error(`API error: ${error.response.status} - ${error.message}`),
          `api.error.${error.response.status}`
        )
    }

    return Promise.reject(error)
  }
)

export default api


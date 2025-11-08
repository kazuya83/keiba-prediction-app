// ユーザー関連の型定義
export interface User {
  id: number
  email: string
  username: string
  is_active: boolean
  role: string
  created_at: string
}

// レース関連の型定義
export interface Race {
  id: number
  race_name: string
  race_date: string
  race_type: 'jra' | 'local'
  venue: string
  race_number: number
  distance: number
  surface: string
  track_condition: string
  weather: string
  status: 'scheduled' | 'in_progress' | 'finished'
}

// 予測関連の型定義
export interface Prediction {
  id: number
  user_id: number
  race_id: number
  prediction_data: {
    [horseNumber: string]: number // 馬番ごとの確率
  }
  created_at: string
}

// APIレスポンスの型定義
export interface ApiResponse<T> {
  data: T
  message?: string
}

export interface ApiError {
  detail: string
}




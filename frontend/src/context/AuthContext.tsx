import {
  createContext,
  ReactNode,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'

type AuthContextValue = {
  isAuthenticated: boolean
  loading: boolean
  login: (token: string) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

type AuthProviderProps = {
  children: ReactNode
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    try {
      const storedToken = localStorage.getItem('access_token')
      setIsAuthenticated(Boolean(storedToken))
    } catch (error) {
      console.error('Failed to read auth state from storage', error)
      setIsAuthenticated(false)
    } finally {
      setLoading(false)
    }
  }, [])

  const login = (token: string) => {
    try {
      localStorage.setItem('access_token', token)
    } catch (error) {
      console.error('Failed to persist access token', error)
    } finally {
      setIsAuthenticated(true)
    }
  }

  const logout = () => {
    try {
      localStorage.removeItem('access_token')
    } catch (error) {
      console.error('Failed to remove access token', error)
    } finally {
      setIsAuthenticated(false)
    }
  }

  const value = useMemo(
    () => ({
      isAuthenticated,
      loading,
      login,
      logout,
    }),
    [isAuthenticated, loading],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuthContext = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuthContext must be used within an AuthProvider')
  }
  return context
}



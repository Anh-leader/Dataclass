import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, initializeCsrf, post, setCsrf } from '../api'
import type { User } from '../types'

interface AuthContextValue {
  user: User | null
  loading: boolean
  toast: string
  notify: (message: string) => void
  login: (user: User) => void
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    initializeCsrf()
      .then(() => api<{ user: User }>('/auth/me'))
      .then(result => setUser(result.user))
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  const notify = useCallback((message: string) => {
    setToast(message)
    window.setTimeout(() => setToast(''), 3600)
  }, [])

  const login = useCallback((u: User) => {
    setUser(u)
  }, [])

  const logout = useCallback(async () => {
    try {
      await post('/auth/logout')
      setUser(null)
      navigate('/login')
    } catch {
      notify('Không thể đăng xuất. Vui lòng thử lại.')
    }
  }, [navigate, notify])

  const value = useMemo(
    () => ({ user, loading, toast, notify, login, logout }),
    [user, loading, toast, notify, login, logout],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

export { setCsrf }

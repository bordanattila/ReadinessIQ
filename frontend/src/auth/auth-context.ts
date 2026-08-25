import { createContext } from 'react'
import type { CurrentUser } from '../api'

export interface AuthContextValue {
  user: CurrentUser | null
  loading: boolean
  refreshUser: () => Promise<CurrentUser | null>
  clearUser: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)

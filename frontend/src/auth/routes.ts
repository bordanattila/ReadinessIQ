import type { CurrentUser } from '../api'

export function requiresMfaVerification(user: CurrentUser | null): boolean {
  return Boolean(user?.mfa_enabled && !user.mfa_verified)
}

export function authDestination(user: CurrentUser | null): '/mfa' | '/' {
  return requiresMfaVerification(user) ? '/mfa' : '/'
}

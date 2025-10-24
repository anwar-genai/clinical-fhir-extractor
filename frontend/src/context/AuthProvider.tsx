import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import type { User, LoginRequest, RegisterRequest, AuthResponse } from '../types'
import toast from 'react-hot-toast'

type AuthContextValue = {
  user: User | null
  isLoading: boolean
  isLoggingIn: boolean
  isRegistering: boolean
  login: (credentials: LoginRequest) => Promise<void>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isLoggingIn, setIsLoggingIn] = useState(false)
  const [isRegistering, setIsRegistering] = useState(false)
  const queryClient = useQueryClient()

  const hasFetchedRef = useRef(false)

  const fetchUser = useCallback(async () => {
    try {
      const response = await api.get<User>('/auth/me')
      setUser(response.data)
      return response.data
    } catch (error) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      setUser(null)
      throw error
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    if (hasFetchedRef.current) return
    hasFetchedRef.current = true
    const token = localStorage.getItem('access_token')
    if (token) {
      fetchUser().catch(() => {})
    } else {
      setIsLoading(false)
    }
  }, [fetchUser])

  const login = useCallback(async (credentials: LoginRequest) => {
    try {
      setIsLoggingIn(true)
      const response = await api.post<AuthResponse>('/auth/login', credentials)
      localStorage.setItem('access_token', response.data.access_token)
      localStorage.setItem('refresh_token', response.data.refresh_token)
      await fetchUser()
      toast.success('Login successful!')
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || 'Login failed')
      throw error
    } finally {
      setIsLoggingIn(false)
    }
  }, [fetchUser])

  const register = useCallback(async (data: RegisterRequest) => {
    try {
      setIsRegistering(true)
      await api.post<User>('/auth/register', data)
      toast.success('Registration successful! Please login.')
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || 'Registration failed')
      throw error
    } finally {
      setIsRegistering(false)
    }
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setUser(null)
    queryClient.clear()
    toast.success('Logged out successfully')
  }, [queryClient])

  const value = useMemo<AuthContextValue>(() => ({
    user,
    isLoading,
    isLoggingIn,
    isRegistering,
    login,
    register,
    logout,
  }), [user, isLoading, isLoggingIn, isRegistering, login, register, logout])

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuthContext(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return ctx
}



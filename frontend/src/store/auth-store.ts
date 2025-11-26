import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User, LoginRequest, RegisterRequest } from '@/types'
import { apiClient } from '@/lib/api-client'

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null

  // Actions
  login: (data: LoginRequest) => Promise<void>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => Promise<void>
  loadUser: () => Promise<void>
  clearError: () => void
  setUser: (user: User) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (data: LoginRequest) => {
        try {
          set({ isLoading: true, error: null })

          const response = await apiClient.login(data)

          // Store tokens
          localStorage.setItem('access_token', response.access_token)
          localStorage.setItem('refresh_token', response.refresh_token)

          set({
            user: response.user,
            accessToken: response.access_token,
            refreshToken: response.refresh_token,
            isAuthenticated: true,
            isLoading: false,
          })
        } catch (error: any) {
          const errorMessage =
            error.response?.data?.detail?.error_message ||
            error.message ||
            'Login failed'

          set({
            error: errorMessage,
            isLoading: false,
          })

          throw error
        }
      },

      register: async (data: RegisterRequest) => {
        try {
          set({ isLoading: true, error: null })

          await apiClient.register(data)

          set({ isLoading: false })

          // Note: User is in "pending" status after registration
          // Need admin approval before login
        } catch (error: any) {
          const errorMessage =
            error.response?.data?.detail?.error_message ||
            error.message ||
            'Registration failed'

          set({
            error: errorMessage,
            isLoading: false,
          })

          throw error
        }
      },

      logout: async () => {
        try {
          const { refreshToken } = get()
          if (refreshToken) {
            await apiClient.logout(refreshToken)
          }
        } catch (error) {
          console.error('Logout error:', error)
        } finally {
          // Clear tokens
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')

          set({
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,
            error: null,
          })
        }
      },

      loadUser: async () => {
        try {
          const accessToken = localStorage.getItem('access_token')
          if (!accessToken) {
            return
          }

          set({ isLoading: true })

          const response = await apiClient.getMe()

          set({
            user: response.user,
            accessToken,
            refreshToken: localStorage.getItem('refresh_token'),
            isAuthenticated: true,
            isLoading: false,
          })
        } catch (error) {
          console.error('Load user error:', error)

          // Clear invalid tokens
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')

          set({
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,
            isLoading: false,
          })
        }
      },

      clearError: () => {
        set({ error: null })
      },

      setUser: (user: User) => {
        set({ user })
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)

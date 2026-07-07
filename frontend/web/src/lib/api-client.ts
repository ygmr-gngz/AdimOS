import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { API_BASE_URL } from './constants'
import { supabase } from './supabase'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
})

apiClient.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('adimos_token')
    if (token) config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Token yenileme durumunu takip et — paralel 401'lerin hepsini tek yenilemeye topla
let _refreshing = false
let _waiters: Array<(token: string | null) => void> = []

function _notifyWaiters(token: string | null) {
  _waiters.forEach((cb) => cb(token))
  _waiters = []
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.code === 'ERR_NETWORK' || error.code === 'ECONNREFUSED') {
      console.warn('[AdimOS] Backend bağlantısı yok')
      return Promise.reject(error)
    }

    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    if (error.response?.status === 401 && original && !original._retry) {
      original._retry = true

      if (_refreshing) {
        // Başka bir istek zaten yenileme yapıyor — sonucu bekle
        return new Promise((resolve, reject) => {
          _waiters.push((token) => {
            if (token) {
              original.headers.Authorization = `Bearer ${token}`
              resolve(apiClient(original))
            } else {
              reject(error)
            }
          })
        })
      }

      _refreshing = true
      try {
        const { data } = await supabase.auth.refreshSession()
        const newToken = data.session?.access_token ?? null
        if (newToken) {
          localStorage.setItem('adimos_token', newToken)
          _notifyWaiters(newToken)
          original.headers.Authorization = `Bearer ${newToken}`
          return apiClient(original)
        }
      } catch {
        // yenileme başarısız
      } finally {
        _refreshing = false
      }

      // Yenileme başarısız → tüm bekleyenleri bilgilendir ve login'e yönlendir
      _notifyWaiters(null)
      if (typeof window !== 'undefined') {
        localStorage.removeItem('adimos_token')
        window.location.href = '/login'
      }
    }

    return Promise.reject(error)
  }
)

export default apiClient

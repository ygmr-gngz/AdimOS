'use client'

import { useState, useEffect } from 'react'
import { authService } from '@/services/auth.service'
import type { User } from '@supabase/supabase-js'

export function useAuth() {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    authService.getUser()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setIsLoading(false))
  }, [])

  const signIn = async (email: string, password: string) => {
    const data = await authService.signIn(email, password)
    setUser(data.user)
    return data
  }

  const signOut = async () => {
    await authService.signOut()
    setUser(null)
  }

  return { user, isLoading, signIn, signOut }
}

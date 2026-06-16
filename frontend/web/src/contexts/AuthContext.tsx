'use client'

import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { supabase } from '@/lib/supabase'
import type { User, Session } from '@supabase/supabase-js'

interface UserProfile {
  role: 'admin' | 'editor'
  display_name: string | null
  force_password_change: boolean
}

interface AuthContextValue {
  user: User | null
  session: Session | null
  profile: UserProfile | null
  isLoading: boolean
  signIn: (email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const loadProfile = async (userId: string) => {
    try {
      const { data } = await supabase
        .from('user_profiles')
        .select('role, display_name, force_password_change')
        .eq('user_id', userId)
        .single()
      if (data) {
        setProfile({
          role: data.role ?? 'editor',
          display_name: data.display_name ?? null,
          force_password_change: data.force_password_change ?? false,
        })
      } else {
        setProfile({ role: 'admin', display_name: null, force_password_change: false })
      }
    } catch {
      setProfile({ role: 'editor', display_name: null, force_password_change: false })
    }
  }

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setUser(session?.user ?? null)
      if (session) {
        localStorage.setItem('adimos_token', session.access_token)
        loadProfile(session.user.id)
      }
      setIsLoading(false)
    })

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
      setUser(session?.user ?? null)
      if (session) {
        localStorage.setItem('adimos_token', session.access_token)
        loadProfile(session.user.id)
      } else {
        localStorage.removeItem('adimos_token')
        setProfile(null)
      }
    })

    return () => subscription.unsubscribe()
  }, [])

  const signIn = async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) throw error
    if (data.session) {
      localStorage.setItem('adimos_token', data.session.access_token)
    }
  }

  const signOut = async () => {
    localStorage.removeItem('adimos_token')
    await supabase.auth.signOut()
  }

  return (
    <AuthContext.Provider value={{ user, session, profile, isLoading, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuthContext() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuthContext must be used within AuthProvider')
  return ctx
}

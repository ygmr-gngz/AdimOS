import { supabase } from '@/lib/supabase'

export const authService = {
  async signIn(email: string, password: string) {
    const { data, error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) throw error
    if (data.session?.access_token) {
      localStorage.setItem('adimos_token', data.session.access_token)
    }
    return data
  },

  async signOut() {
    localStorage.removeItem('adimos_token')
    const { error } = await supabase.auth.signOut()
    if (error) throw error
  },

  async getUser() {
    const { data, error } = await supabase.auth.getUser()
    if (error) throw error
    return data.user
  },

  async getSession() {
    const { data, error } = await supabase.auth.getSession()
    if (error) throw error
    return data.session
  },
}

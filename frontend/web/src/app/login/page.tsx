'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import Input from '@/components/ui/Input'
import Button from '@/components/ui/Button'
import { Zap, Mail, Lock } from 'lucide-react'
import toast from 'react-hot-toast'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const { signIn } = useAuth()
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    try {
      await signIn(email, password)
      router.push('/dashboard')
    } catch {
      toast.error('Email veya şifre hatalı')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 bg-brand-600 rounded-2xl flex items-center justify-center mb-4 shadow-lg shadow-brand-600/30">
            <Zap size={28} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">AdimOS</h1>
          <p className="text-sm text-gray-500 mt-1">AI Operating System</p>
        </div>

        <div className="bg-surface-50 border border-surface-200 rounded-2xl p-6 shadow-2xl">
          <h2 className="text-base font-semibold text-gray-200 mb-5">Giriş Yap</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Email"
              type="email"
              placeholder="ornek@musavirlik.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              icon={<Mail size={15} />}
              required
            />
            <Input
              label="Şifre"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              icon={<Lock size={15} />}
              required
            />
            <Button type="submit" isLoading={isLoading} className="w-full mt-2">
              Giriş Yap
            </Button>
          </form>
        </div>

        <p className="text-center text-xs text-gray-600 mt-6">
          Adım Müşavirlik & SGS Academy &copy; 2025
        </p>
      </div>
    </div>
  )
}

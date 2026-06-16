import type { Metadata } from 'next'
import type { ReactNode } from 'react'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from '@/contexts/AuthContext'
import './globals.css'

export const metadata: Metadata = {
  title: 'AdimOS — AI Operating System',
  description: 'Adım Müşavirlik & SGS Academy için çok ajanlı yapay zeka işletim sistemi',
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="tr" className="dark">
      <body className="antialiased bg-surface text-gray-100">
        <AuthProvider>
        {children}
        </AuthProvider>
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: '#22222f',
              color: '#e5e7eb',
              border: '1px solid #3a3a50',
              borderRadius: '10px',
              fontSize: '13px',
            },
            success: { iconTheme: { primary: '#4ade80', secondary: '#22222f' } },
            error: { iconTheme: { primary: '#f87171', secondary: '#22222f' } },
          }}
        />
      </body>
    </html>
  )
}

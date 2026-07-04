'use client'
import { Component, ReactNode } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'

interface Props {
  children: ReactNode
  label?: string
}
interface State {
  error: Error | null
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: { componentStack: string }) {
    console.error('[ErrorBoundary]', error.message, info.componentStack?.slice(0, 400))
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex items-center justify-center h-full min-h-[320px]">
          <div className="bg-surface-50 border border-red-500/30 rounded-xl p-6 max-w-md w-full text-center">
            <AlertTriangle className="mx-auto mb-3 text-red-400" size={28} />
            <h3 className="text-sm font-semibold text-white mb-1">
              {this.props.label ?? 'Bu bölüm yüklenemedi'}
            </h3>
            <p className="text-xs text-gray-500 mb-4 font-mono break-all">
              {this.state.error.message?.slice(0, 150) ?? 'Beklenmeyen bir hata oluştu.'}
            </p>
            <button
              onClick={() => this.setState({ error: null })}
              className="inline-flex items-center gap-2 text-xs text-brand-400 hover:text-brand-300 transition-colors"
            >
              <RefreshCw size={13} />
              Yeniden dene
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

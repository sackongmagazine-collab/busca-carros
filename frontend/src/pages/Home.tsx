import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shield, Zap, BarChart3 } from 'lucide-react'
import SearchForm from '../components/SearchForm'
import { startSearch, waitForResults } from '../services/api'
import type { SearchCriteria } from '../types'

export default function Home() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [statusMsg, setStatusMsg] = useState('')

  const handleSearch = async (criteria: SearchCriteria) => {
    setLoading(true)
    setError('')
    setStatusMsg('Iniciando busca nas fontes...')
    try {
      const { search_id } = await startSearch(criteria)
      setStatusMsg('Consultando anúncios e tabela FIPE...')
      const results = await waitForResults(search_id, (status) => {
        if (status === 'running') setStatusMsg('Analisando e ranqueando com IA...')
      })
      navigate(`/results/${search_id}`, { state: { results } })
    } catch (err: unknown) {
      const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } }
      if (axiosErr?.response?.status === 429) {
        setError(axiosErr.response.data?.detail ?? 'Limite de buscas atingido. Crie uma conta gratuita para continuar.')
      } else {
        setError(err instanceof Error ? err.message : 'Erro inesperado. Tente novamente.')
      }
    } finally {
      setLoading(false)
      setStatusMsg('')
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-900 via-brand-700 to-brand-500">
      {/* Hero */}
      <div className="max-w-4xl mx-auto px-4 pt-16 pb-10 text-center">
        <div className="inline-flex items-center gap-2 bg-white/10 text-white text-sm px-4 py-1.5 rounded-full mb-6">
          <Zap className="w-4 h-4" /> Buscador inteligente com IA
        </div>
        <h1 className="text-4xl md:text-5xl font-black text-white leading-tight mb-4">
          Encontre o carro certo<br />
          <span className="text-yellow-300">pelo menor preço</span>
        </h1>
        <p className="text-brand-100 text-lg mb-2">
          Buscamos em múltiplas fontes, comparamos com a FIPE e entregamos<br className="hidden md:block" /> o ranking completo com análise de risco — tudo em segundos.
        </p>
      </div>

      {/* Form */}
      <div className="max-w-3xl mx-auto px-4 pb-8">
        {loading && statusMsg && (
          <div className="mb-4 text-center text-white/80 text-sm animate-pulse">{statusMsg}</div>
        )}
        {error && (
          <div className="mb-4 bg-red-100 border border-red-300 text-red-700 rounded-xl px-4 py-3 text-sm">{error}</div>
        )}
        <SearchForm onSubmit={handleSearch} loading={loading} />
      </div>

      {/* Features */}
      <div className="max-w-4xl mx-auto px-4 pb-16 grid grid-cols-1 md:grid-cols-3 gap-6 mt-4">
        {[
          { icon: <BarChart3 className="w-6 h-6" />, title: 'Ranking por custo-benefício', desc: 'Todos os anúncios ordenados do mais ao menos vantajoso com comparação FIPE automática.' },
          { icon: <Shield className="w-6 h-6" />, title: 'Detecção de riscos', desc: 'IA identifica sinais de alerta em cada anúncio: km suspeita, preço discrepante, dados incompletos.' },
          { icon: <Zap className="w-6 h-6" />, title: 'Múltiplas fontes ao mesmo tempo', desc: 'MercadoLivre, Webmotors e outras fontes buscadas simultaneamente, sem duplicatas.' },
        ].map((f, i) => (
          <div key={i} className="bg-white/10 rounded-2xl p-6 text-white">
            <div className="mb-3 text-yellow-300">{f.icon}</div>
            <h3 className="font-bold text-lg mb-1">{f.title}</h3>
            <p className="text-brand-100 text-sm">{f.desc}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

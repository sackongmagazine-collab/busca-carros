import React, { useEffect, useState } from 'react'
import { Users, Search, DollarSign, AlertTriangle, Building2, TrendingUp } from 'lucide-react'
import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

interface Metrics {
  users: { total: number; new_today: number; new_week: number; by_plan: Record<string, number> }
  revenue: { mrr_estimated: number; arr_estimated: number }
  searches: { today: number; this_week: number; this_month: number }
  top_models: { model: string; count: number }[]
  fraud: { pending_reviews: number }
  dealers: { total: number; active_listings: number }
}

function StatCard({ icon, title, value, sub, color }: { icon: React.ReactNode; title: string; value: string | number; sub?: string; color: string }) {
  return (
    <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
      <div className={`inline-flex p-2.5 rounded-xl mb-3 ${color}`}>{icon}</div>
      <div className="text-2xl font-black text-gray-900">{value}</div>
      <div className="text-sm font-semibold text-gray-700">{title}</div>
      {sub && <div className="text-xs text-gray-400 mt-0.5">{sub}</div>}
    </div>
  )
}

export default function AdminDashboard() {
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [fraudQueue, setFraudQueue] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<'overview' | 'fraud' | 'users'>('overview')
  const [users, setUsers] = useState<any[]>([])

  const secret = localStorage.getItem('admin_secret') || ''

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [m, fq] = await Promise.all([
        api.get('/admin/metrics', { headers: { 'x-admin-secret': secret } }),
        api.get('/admin/fraud-queue', { headers: { 'x-admin-secret': secret } }),
      ])
      setMetrics(m.data)
      setFraudQueue(fq.data)
    } catch {
      window.location.href = '/'
    } finally {
      setLoading(false)
    }
  }

  const loadUsers = async () => {
    const { data } = await api.get('/admin/users', { headers: { 'x-admin-secret': secret } })
    setUsers(data)
  }

  const resolveFraud = async (id: number, notes: string) => {
    await api.patch(`/admin/fraud-queue/${id}/resolve`, { notes }, { headers: { 'x-admin-secret': secret } })
    setFraudQueue((q) => q.filter((r) => r.id !== id))
  }

  if (loading) return <div className="min-h-screen flex items-center justify-center"><div className="animate-spin w-10 h-10 border-4 border-brand-600 border-t-transparent rounded-full" /></div>
  if (!metrics) return null

  const fmtBRL = (v: number) => `R$ ${v.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-gray-900 text-white px-6 py-4 flex items-center justify-between">
        <h1 className="text-lg font-black">Admin — Busca Carros</h1>
        <div className="flex gap-3 text-sm">
          {(['overview', 'fraud', 'users'] as const).map((t) => (
            <button key={t} onClick={() => { setTab(t); if (t === 'users') loadUsers() }}
              className={`px-3 py-1 rounded-lg transition ${tab === t ? 'bg-white/20' : 'hover:bg-white/10'}`}>
              {t === 'overview' ? 'Visão geral' : t === 'fraud' ? `Fraudes (${fraudQueue.length})` : 'Usuários'}
            </button>
          ))}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {tab === 'overview' && (
          <div className="space-y-8">
            {/* KPIs */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard icon={<DollarSign className="w-5 h-5 text-green-600" />} title="MRR" value={fmtBRL(metrics.revenue.mrr_estimated)} sub={`ARR: ${fmtBRL(metrics.revenue.arr_estimated)}`} color="bg-green-50" />
              <StatCard icon={<Users className="w-5 h-5 text-brand-600" />} title="Total usuários" value={metrics.users.total} sub={`+${metrics.users.new_week} essa semana`} color="bg-brand-50" />
              <StatCard icon={<Search className="w-5 h-5 text-purple-600" />} title="Buscas hoje" value={metrics.searches.today} sub={`${metrics.searches.this_month} no mês`} color="bg-purple-50" />
              <StatCard icon={<AlertTriangle className="w-5 h-5 text-red-600" />} title="Fraudes pendentes" value={metrics.fraud.pending_reviews} sub="Aguardando revisão" color="bg-red-50" />
            </div>

            {/* Planos */}
            <div className="bg-white rounded-2xl border border-gray-100 p-6">
              <h2 className="font-bold text-gray-900 mb-4">Distribuição de planos</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(metrics.users.by_plan).map(([plan, count]) => (
                  <div key={plan} className="text-center">
                    <div className="text-3xl font-black text-gray-900">{count}</div>
                    <div className="text-sm text-gray-500 capitalize">{plan}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Top modelos */}
            <div className="bg-white rounded-2xl border border-gray-100 p-6">
              <h2 className="font-bold text-gray-900 mb-4">Top modelos buscados (últimos 7 dias)</h2>
              <div className="space-y-2">
                {metrics.top_models.map((m, i) => {
                  const max = metrics.top_models[0]?.count || 1
                  return (
                    <div key={m.model} className="flex items-center gap-3">
                      <span className="text-xs text-gray-400 w-5">#{i + 1}</span>
                      <span className="text-sm font-medium text-gray-800 w-32">{m.model}</span>
                      <div className="flex-1 bg-gray-100 rounded-full h-2">
                        <div className="bg-brand-500 h-2 rounded-full transition-all" style={{ width: `${(m.count / max) * 100}%` }} />
                      </div>
                      <span className="text-sm font-bold text-gray-700">{m.count}</span>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Dealers */}
            <div className="bg-white rounded-2xl border border-gray-100 p-6">
              <h2 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                <Building2 className="w-5 h-5 text-yellow-600" /> Lojistas
              </h2>
              <div className="flex gap-8">
                <div><div className="text-3xl font-black">{metrics.dealers.total}</div><div className="text-sm text-gray-500">Lojistas cadastrados</div></div>
                <div><div className="text-3xl font-black">{metrics.dealers.active_listings}</div><div className="text-sm text-gray-500">Anúncios ativos</div></div>
              </div>
            </div>
          </div>
        )}

        {tab === 'fraud' && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-gray-900">Fila de fraudes</h2>
            {fraudQueue.length === 0 ? (
              <p className="text-gray-400 text-center py-12">Nenhum relatório pendente.</p>
            ) : fraudQueue.map((r) => (
              <div key={r.id} className="bg-white rounded-xl border p-5">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${r.risk_level === 'critical' ? 'bg-red-100 text-red-700' : r.risk_level === 'high' ? 'bg-orange-100 text-orange-700' : 'bg-yellow-100 text-yellow-700'}`}>
                        {r.risk_level.toUpperCase()} · Score: {r.fraud_score}
                      </span>
                    </div>
                    <p className="font-semibold text-gray-900 text-sm">{r.listing_title}</p>
                    <p className="text-sm text-gray-500">R$ {r.listing_price?.toLocaleString('pt-BR')} · FIPE: R$ {r.fipe_value?.toLocaleString('pt-BR')}</p>
                    <ul className="mt-2 space-y-0.5">
                      {r.flags.map((f: string, i: number) => <li key={i} className="text-xs text-red-600">• {f}</li>)}
                    </ul>
                    {r.listing_url && <a href={r.listing_url} target="_blank" rel="noreferrer" className="text-xs text-brand-600 underline mt-1 inline-block">Ver anúncio</a>}
                  </div>
                  <button
                    onClick={() => resolveFraud(r.id, 'Revisado pelo admin')}
                    className="bg-green-600 hover:bg-green-700 text-white text-xs px-3 py-1.5 rounded-lg shrink-0"
                  >
                    Resolver
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {tab === 'users' && (
          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-4">Usuários</h2>
            <div className="bg-white rounded-xl border overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-gray-500 text-xs uppercase">
                  <tr>
                    {['ID', 'Email', 'Nome', 'Plano', 'Status', 'Criado'].map((h) => (
                      <th key={h} className="px-4 py-3 text-left">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {users.map((u) => (
                    <tr key={u.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-gray-400">{u.id}</td>
                      <td className="px-4 py-3 font-medium">{u.email}</td>
                      <td className="px-4 py-3 text-gray-600">{u.full_name || '—'}</td>
                      <td className="px-4 py-3"><span className="bg-brand-50 text-brand-700 text-xs px-2 py-0.5 rounded-full font-semibold capitalize">{u.plan}</span></td>
                      <td className="px-4 py-3"><span className={`text-xs px-2 py-0.5 rounded-full ${u.is_active ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>{u.is_active ? 'Ativo' : 'Inativo'}</span></td>
                      <td className="px-4 py-3 text-gray-400">{u.created_at ? new Date(u.created_at).toLocaleDateString('pt-BR') : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

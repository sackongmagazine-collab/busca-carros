import { useEffect, useState } from 'react'
import { Car, Eye, MessageSquare, Plus, CheckCircle, AlertTriangle, TrendingUp } from 'lucide-react'
import axios from 'axios'
import clsx from 'clsx'

const api = axios.create({ baseURL: '/api' })
api.interceptors.request.use((c) => {
  const t = localStorage.getItem('token')
  if (t) c.headers.Authorization = `Bearer ${t}`
  return c
})

interface DealerProfile {
  company_name: string; city: string; state: string
  is_verified: boolean; rating: number
  total_listings: number; active_listings: number
  total_views: number; total_leads: number
}

interface Listing {
  id: number; make: string; model: string; version: string
  year_model: number; km: number; price: number; fipe_value: number
  is_active: boolean; is_flagged: boolean; fraud_score: number
  views: number; leads: number; photos: string[]
  created_at: string
}

export default function DealerPortal() {
  const [profile, setProfile] = useState<DealerProfile | null>(null)
  const [listings, setListings] = useState<Listing[]>([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<'listings' | 'profile' | 'new'>('listings')
  const [newListing, setNewListing] = useState({
    make: '', model: '', version: '', year_fab: 2020, year_model: 2020,
    km: 0, transmission: 'automatico', fuel: 'flex', price: 0, doors: 4,
    description: '', accepts_trade: false, is_financed: true, features: [] as string[], photos: [] as string[],
  })
  const [error, setError] = useState('')

  useEffect(() => { loadData() }, [])

  const loadData = async () => {
    try {
      const [p, l] = await Promise.all([api.get('/dealers/me'), api.get('/dealers/me/listings')])
      setProfile(p.data)
      setListings(l.data)
    } catch (e: any) {
      if (e.response?.status === 401) window.location.href = '/login'
      if (e.response?.status === 403) window.location.href = '/pricing'
    } finally {
      setLoading(false)
    }
  }

  const createListing = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      await api.post('/dealers/me/listings', newListing)
      setTab('listings')
      loadData()
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Erro ao criar anúncio')
    }
  }

  const toggleListing = async (id: number, is_active: boolean) => {
    await api.patch(`/dealers/me/listings/${id}`, { is_active: !is_active })
    loadData()
  }

  if (loading) return <div className="min-h-screen flex items-center justify-center"><div className="animate-spin w-10 h-10 border-4 border-brand-600 border-t-transparent rounded-full" /></div>

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-brand-900 text-white px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-black">{profile?.company_name}</h1>
              {profile?.is_verified && <CheckCircle className="w-4 h-4 text-green-400" />}
            </div>
            <p className="text-brand-300 text-sm">{profile?.city}/{profile?.state} · Painel Lojista</p>
          </div>
          <div className="flex gap-4 text-sm">
            {(['listings', 'new', 'profile'] as const).map((t) => (
              <button key={t} onClick={() => setTab(t)}
                className={`px-3 py-1.5 rounded-lg transition ${tab === t ? 'bg-white/20' : 'hover:bg-white/10'}`}>
                {t === 'listings' ? 'Meus anúncios' : t === 'new' ? '+ Novo anúncio' : 'Perfil'}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* KPIs */}
        {profile && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {[
              { icon: <Car className="w-5 h-5" />, label: 'Anúncios ativos', value: profile.active_listings, color: 'text-brand-600' },
              { icon: <Eye className="w-5 h-5" />, label: 'Visualizações', value: profile.total_views.toLocaleString('pt-BR'), color: 'text-purple-600' },
              { icon: <MessageSquare className="w-5 h-5" />, label: 'Leads gerados', value: profile.total_leads, color: 'text-green-600' },
              { icon: <TrendingUp className="w-5 h-5" />, label: 'Total cadastrados', value: profile.total_listings, color: 'text-yellow-600' },
            ].map((s) => (
              <div key={s.label} className="bg-white rounded-xl border p-4">
                <div className={clsx('mb-2', s.color)}>{s.icon}</div>
                <div className="text-2xl font-black text-gray-900">{s.value}</div>
                <div className="text-xs text-gray-500">{s.label}</div>
              </div>
            ))}
          </div>
        )}

        {/* Listings tab */}
        {tab === 'listings' && (
          <div className="space-y-3">
            {listings.length === 0 ? (
              <div className="text-center py-16 text-gray-400">
                <Car className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p>Nenhum anúncio cadastrado.</p>
                <button onClick={() => setTab('new')} className="mt-3 text-brand-600 font-semibold text-sm hover:underline">Adicionar primeiro anúncio</button>
              </div>
            ) : listings.map((l) => (
              <div key={l.id} className={clsx('bg-white rounded-xl border p-4 flex gap-4', !l.is_active && 'opacity-60')}>
                {l.photos[0] ? (
                  <img src={l.photos[0]} alt="" className="w-24 h-16 object-cover rounded-lg shrink-0" />
                ) : (
                  <div className="w-24 h-16 bg-gray-100 rounded-lg shrink-0 flex items-center justify-center"><Car className="w-6 h-6 text-gray-300" /></div>
                )}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-bold text-gray-900">{l.make} {l.model} {l.version}</span>
                    {l.is_flagged && <span className="flex items-center gap-1 text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full"><AlertTriangle className="w-3 h-3" /> Suspeito</span>}
                  </div>
                  <div className="text-sm text-gray-500">{l.year_model} · {l.km.toLocaleString('pt-BR')} km</div>
                  <div className="flex items-center gap-4 mt-1">
                    <span className="text-lg font-black text-gray-900">R$ {l.price.toLocaleString('pt-BR')}</span>
                    {l.fipe_value && (
                      <span className="text-xs text-gray-400">FIPE: R$ {l.fipe_value.toLocaleString('pt-BR')}</span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 mt-1 text-xs text-gray-400">
                    <span><Eye className="w-3 h-3 inline" /> {l.views}</span>
                    <span><MessageSquare className="w-3 h-3 inline" /> {l.leads}</span>
                    <span>{new Date(l.created_at).toLocaleDateString('pt-BR')}</span>
                  </div>
                </div>
                <button onClick={() => toggleListing(l.id, l.is_active)}
                  className={clsx('shrink-0 text-xs px-3 py-1.5 rounded-lg font-semibold transition',
                    l.is_active ? 'bg-red-50 text-red-600 hover:bg-red-100' : 'bg-green-50 text-green-600 hover:bg-green-100')}>
                  {l.is_active ? 'Pausar' : 'Ativar'}
                </button>
              </div>
            ))}
          </div>
        )}

        {/* New listing tab */}
        {tab === 'new' && (
          <form onSubmit={createListing} className="bg-white rounded-2xl border p-6 space-y-5 max-w-2xl">
            <h2 className="text-lg font-bold text-gray-900">Novo anúncio</h2>
            {error && <p className="text-red-600 text-sm bg-red-50 px-3 py-2 rounded-lg">{error}</p>}

            <div className="grid grid-cols-2 gap-4">
              {[
                { label: 'Marca *', key: 'make', placeholder: 'Hyundai' },
                { label: 'Modelo *', key: 'model', placeholder: 'HB20' },
                { label: 'Versão', key: 'version', placeholder: 'S 1.6 Manual' },
                { label: 'Cor', key: 'color', placeholder: 'Prata' },
              ].map(({ label, key, placeholder }) => (
                <div key={key}>
                  <label className="text-xs font-semibold text-gray-600 block mb-1">{label}</label>
                  <input className="w-full px-3 py-2 border rounded-lg text-sm" placeholder={placeholder}
                    value={(newListing as any)[key] || ''} onChange={(e) => setNewListing((f) => ({ ...f, [key]: e.target.value }))} />
                </div>
              ))}
              {[
                { label: 'Ano Fab', key: 'year_fab', type: 'number' },
                { label: 'Ano Modelo', key: 'year_model', type: 'number' },
                { label: 'KM *', key: 'km', type: 'number' },
                { label: 'Preço R$ *', key: 'price', type: 'number' },
              ].map(({ label, key, type }) => (
                <div key={key}>
                  <label className="text-xs font-semibold text-gray-600 block mb-1">{label}</label>
                  <input type={type} required className="w-full px-3 py-2 border rounded-lg text-sm"
                    value={(newListing as any)[key]} onChange={(e) => setNewListing((f) => ({ ...f, [key]: Number(e.target.value) }))} />
                </div>
              ))}
              <div>
                <label className="text-xs font-semibold text-gray-600 block mb-1">Câmbio</label>
                <select className="w-full px-3 py-2 border rounded-lg text-sm bg-white"
                  value={newListing.transmission} onChange={(e) => setNewListing((f) => ({ ...f, transmission: e.target.value }))}>
                  <option value="manual">Manual</option>
                  <option value="automatico">Automático</option>
                </select>
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-600 block mb-1">Combustível</label>
                <select className="w-full px-3 py-2 border rounded-lg text-sm bg-white"
                  value={newListing.fuel} onChange={(e) => setNewListing((f) => ({ ...f, fuel: e.target.value }))}>
                  <option value="flex">Flex</option>
                  <option value="gasolina">Gasolina</option>
                  <option value="diesel">Diesel</option>
                  <option value="eletrico">Elétrico</option>
                </select>
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-gray-600 block mb-1">Descrição</label>
              <textarea rows={3} className="w-full px-3 py-2 border rounded-lg text-sm resize-none"
                value={newListing.description} onChange={(e) => setNewListing((f) => ({ ...f, description: e.target.value }))} />
            </div>

            <div className="flex gap-4">
              <label className="flex items-center gap-2 text-sm text-gray-700">
                <input type="checkbox" checked={newListing.accepts_trade} onChange={(e) => setNewListing((f) => ({ ...f, accepts_trade: e.target.checked }))} />
                Aceita troca
              </label>
              <label className="flex items-center gap-2 text-sm text-gray-700">
                <input type="checkbox" checked={newListing.is_financed} onChange={(e) => setNewListing((f) => ({ ...f, is_financed: e.target.checked }))} />
                Aceita financiamento
              </label>
            </div>

            <div className="flex gap-3">
              <button type="submit" className="bg-brand-600 hover:bg-brand-700 text-white px-6 py-2.5 rounded-xl font-bold text-sm">
                <Plus className="w-4 h-4 inline mr-1.5" />Publicar anúncio
              </button>
              <button type="button" onClick={() => setTab('listings')} className="text-gray-500 hover:text-gray-700 px-4 py-2 text-sm">Cancelar</button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}

import React, { useEffect, useState } from 'react'
import { Bell, BellOff, Plus, Trash2, MessageCircle, Mail, Send } from 'lucide-react'
import axios from 'axios'
import clsx from 'clsx'

const api = axios.create({ baseURL: '/api' })
api.interceptors.request.use((c) => {
  const t = localStorage.getItem('token')
  if (t) c.headers.Authorization = `Bearer ${t}`
  return c
})

interface Alert {
  id: number
  model: string
  max_price: number
  location: string
  year_min?: number
  year_max?: number
  max_km?: number
  channels: string[]
  fipe_threshold_pct: number
  is_active: boolean
  last_triggered_at?: string
}

const channelIcon = (ch: string) => {
  if (ch === 'email') return <Mail className="w-3.5 h-3.5" />
  if (ch === 'whatsapp') return <MessageCircle className="w-3.5 h-3.5" />
  if (ch === 'telegram') return <Send className="w-3.5 h-3.5" />
}

const channelColor = (ch: string) => {
  if (ch === 'email') return 'bg-blue-100 text-blue-700'
  if (ch === 'whatsapp') return 'bg-green-100 text-green-700'
  if (ch === 'telegram') return 'bg-sky-100 text-sky-700'
  return 'bg-gray-100 text-gray-600'
}

export default function Alerts() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({
    model: '', max_price: 80000, location: '',
    year_min: '', year_max: '', max_km: '',
    channels: ['email'], fipe_threshold_pct: -5,
    whatsapp_number: '', telegram_chat_id: '',
  })
  const [error, setError] = useState('')

  useEffect(() => { loadAlerts() }, [])

  const loadAlerts = async () => {
    try {
      const { data } = await api.get('/alerts')
      setAlerts(data)
    } catch (e: any) {
      if (e.response?.status === 401) window.location.href = '/login'
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      await api.post('/alerts', {
        ...form,
        year_min: form.year_min ? Number(form.year_min) : undefined,
        year_max: form.year_max ? Number(form.year_max) : undefined,
        max_km: form.max_km ? Number(form.max_km) : undefined,
      })
      setShowForm(false)
      loadAlerts()
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Erro ao criar alerta')
    }
  }

  const toggleAlert = async (id: number) => {
    await api.patch(`/alerts/${id}/toggle`)
    loadAlerts()
  }

  const deleteAlert = async (id: number) => {
    await api.delete(`/alerts/${id}`)
    setAlerts((prev) => prev.filter((a) => a.id !== id))
  }

  const toggleChannel = (ch: string) => {
    setForm((f) => ({
      ...f,
      channels: f.channels.includes(ch) ? f.channels.filter((c) => c !== ch) : [...f.channels, ch],
    }))
  }

  if (loading) return <div className="min-h-screen flex items-center justify-center"><div className="animate-spin w-10 h-10 border-4 border-brand-600 border-t-transparent rounded-full" /></div>

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-3xl mx-auto px-4 py-10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-black text-gray-900">Meus Alertas</h1>
            <p className="text-gray-500 text-sm mt-1">Seja notificado quando um carro aparecer no critério certo.</p>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 rounded-xl text-sm font-semibold transition"
          >
            <Plus className="w-4 h-4" /> Novo alerta
          </button>
        </div>

        {showForm && (
          <form onSubmit={handleCreate} className="bg-white rounded-2xl border border-gray-200 p-6 mb-6 space-y-4">
            <h3 className="font-bold text-gray-900">Criar alerta</h3>
            {error && <p className="text-red-600 text-sm bg-red-50 px-3 py-2 rounded-lg">{error}</p>}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-gray-600 block mb-1">Modelo *</label>
                <input required className="w-full px-3 py-2 border rounded-lg text-sm" placeholder="HB20" value={form.model} onChange={(e) => setForm((f) => ({ ...f, model: e.target.value }))} />
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-600 block mb-1">Localização *</label>
                <input required className="w-full px-3 py-2 border rounded-lg text-sm" placeholder="São Paulo, SP" value={form.location} onChange={(e) => setForm((f) => ({ ...f, location: e.target.value }))} />
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-600 block mb-1">Preço máximo (R$)</label>
                <input type="number" className="w-full px-3 py-2 border rounded-lg text-sm" value={form.max_price} onChange={(e) => setForm((f) => ({ ...f, max_price: Number(e.target.value) }))} />
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-600 block mb-1">Alertar quando abaixo da FIPE (%)</label>
                <input type="number" className="w-full px-3 py-2 border rounded-lg text-sm" value={form.fipe_threshold_pct} onChange={(e) => setForm((f) => ({ ...f, fipe_threshold_pct: Number(e.target.value) }))} />
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-gray-600 block mb-2">Canais de notificação</label>
              <div className="flex gap-2">
                {['email', 'whatsapp', 'telegram'].map((ch) => (
                  <button key={ch} type="button" onClick={() => toggleChannel(ch)}
                    className={clsx('flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border transition',
                      form.channels.includes(ch) ? channelColor(ch) + ' border-current' : 'bg-gray-50 text-gray-500 border-gray-200')}>
                    {channelIcon(ch)} {ch.charAt(0).toUpperCase() + ch.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {form.channels.includes('whatsapp') && (
              <div>
                <label className="text-xs font-semibold text-gray-600 block mb-1">Número WhatsApp (+55...)</label>
                <input className="w-full px-3 py-2 border rounded-lg text-sm" placeholder="+5511999999999" value={form.whatsapp_number} onChange={(e) => setForm((f) => ({ ...f, whatsapp_number: e.target.value }))} />
              </div>
            )}
            {form.channels.includes('telegram') && (
              <div>
                <label className="text-xs font-semibold text-gray-600 block mb-1">Telegram Chat ID</label>
                <input className="w-full px-3 py-2 border rounded-lg text-sm" placeholder="123456789" value={form.telegram_chat_id} onChange={(e) => setForm((f) => ({ ...f, telegram_chat_id: e.target.value }))} />
              </div>
            )}

            <div className="flex gap-3">
              <button type="submit" className="bg-brand-600 hover:bg-brand-700 text-white px-6 py-2 rounded-xl text-sm font-semibold">Criar alerta</button>
              <button type="button" onClick={() => setShowForm(false)} className="text-gray-500 hover:text-gray-700 px-4 py-2 text-sm">Cancelar</button>
            </div>
          </form>
        )}

        {alerts.length === 0 ? (
          <div className="text-center py-16 text-gray-400">
            <Bell className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>Nenhum alerta configurado.</p>
            <p className="text-sm mt-1">Crie um alerta para ser notificado automaticamente.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.map((alert) => (
              <div key={alert.id} className={clsx('bg-white rounded-xl border p-4 flex items-center gap-4', !alert.is_active && 'opacity-50')}>
                <div className="flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-bold text-gray-900">{alert.model}</span>
                    <span className="text-sm text-gray-500">até R$ {alert.max_price.toLocaleString('pt-BR')}</span>
                    <span className="text-sm text-gray-400">· {alert.location}</span>
                  </div>
                  <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                    {alert.channels.map((ch) => (
                      <span key={ch} className={clsx('flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium', channelColor(ch))}>
                        {channelIcon(ch)} {ch}
                      </span>
                    ))}
                    {alert.fipe_threshold_pct < 0 && (
                      <span className="text-xs bg-green-50 text-green-700 px-2 py-0.5 rounded-full">
                        Alerta: {alert.fipe_threshold_pct}% FIPE
                      </span>
                    )}
                    {alert.last_triggered_at && (
                      <span className="text-xs text-gray-400">
                        Último: {new Date(alert.last_triggered_at).toLocaleDateString('pt-BR')}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button onClick={() => toggleAlert(alert.id)} className="text-gray-400 hover:text-brand-600 transition p-1.5 rounded-lg hover:bg-brand-50" title={alert.is_active ? 'Pausar' : 'Ativar'}>
                    {alert.is_active ? <Bell className="w-5 h-5" /> : <BellOff className="w-5 h-5" />}
                  </button>
                  <button onClick={() => deleteAlert(alert.id)} className="text-gray-400 hover:text-red-500 transition p-1.5 rounded-lg hover:bg-red-50">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

import { useState } from 'react'
import { Search, MapPin, DollarSign, Car } from 'lucide-react'
import type { SearchCriteria } from '../types'

interface Props {
  onSubmit: (criteria: SearchCriteria) => void
  loading: boolean
}

export default function SearchForm({ onSubmit, loading }: Props) {
  const [form, setForm] = useState<SearchCriteria>({
    model: '',
    max_price: 80000,
    location: '',
    transmission: 'indiferente',
    fuel: 'indiferente',
  })

  const set = (key: keyof SearchCriteria, value: unknown) =>
    setForm((f) => ({ ...f, [key]: value }))

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.model.trim() || !form.location.trim()) return
    onSubmit(form)
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-xl p-8 space-y-6">
      {/* Linha 1: modelo + localização */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">Modelo do carro *</label>
          <div className="relative">
            <Car className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none transition"
              placeholder="Ex: HB20, Onix, Civic..."
              value={form.model}
              onChange={(e) => set('model', e.target.value)}
              required
            />
          </div>
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">Localização *</label>
          <div className="relative">
            <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none transition"
              placeholder="Ex: São Paulo, SP ou Belo Horizonte"
              value={form.location}
              onChange={(e) => set('location', e.target.value)}
              required
            />
          </div>
        </div>
      </div>

      {/* Linha 2: preço máximo */}
      <div>
        <label className="block text-sm font-semibold text-gray-700 mb-1">
          Preço máximo: <span className="text-brand-600 font-bold">R$ {form.max_price.toLocaleString('pt-BR')}</span>
        </label>
        <div className="relative">
          <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="range"
            min={15000} max={500000} step={5000}
            value={form.max_price}
            onChange={(e) => set('max_price', Number(e.target.value))}
            className="w-full pl-10 accent-brand-600"
          />
        </div>
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>R$ 15.000</span><span>R$ 500.000</span>
        </div>
      </div>

      {/* Linha 3: filtros opcionais */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <label className="block text-xs font-semibold text-gray-600 mb-1">Ano mínimo</label>
          <input
            type="number" min={2000} max={2025} placeholder="2018"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 outline-none"
            onChange={(e) => set('year_min', e.target.value ? Number(e.target.value) : undefined)}
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-gray-600 mb-1">Ano máximo</label>
          <input
            type="number" min={2000} max={2025} placeholder="2024"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 outline-none"
            onChange={(e) => set('year_max', e.target.value ? Number(e.target.value) : undefined)}
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-gray-600 mb-1">KM máxima</label>
          <input
            type="number" placeholder="100000"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 outline-none"
            onChange={(e) => set('max_km', e.target.value ? Number(e.target.value) : undefined)}
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-gray-600 mb-1">Câmbio</label>
          <select
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 outline-none bg-white"
            value={form.transmission}
            onChange={(e) => set('transmission', e.target.value)}
          >
            <option value="indiferente">Indiferente</option>
            <option value="manual">Manual</option>
            <option value="automatico">Automático</option>
          </select>
        </div>
      </div>

      {/* Combustível */}
      <div>
        <label className="block text-xs font-semibold text-gray-600 mb-2">Combustível</label>
        <div className="flex flex-wrap gap-2">
          {['indiferente', 'flex', 'gasolina', 'diesel', 'eletrico'].map((f) => (
            <button
              key={f} type="button"
              onClick={() => set('fuel', f)}
              className={`px-4 py-1.5 rounded-full text-sm font-medium border transition
                ${form.fuel === f
                  ? 'bg-brand-600 text-white border-brand-600'
                  : 'bg-white text-gray-600 border-gray-300 hover:border-brand-400'}`}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <button
        type="submit" disabled={loading}
        className="w-full py-4 bg-brand-600 hover:bg-brand-700 disabled:bg-gray-400 text-white font-bold rounded-xl text-lg flex items-center justify-center gap-2 transition"
      >
        {loading ? (
          <><span className="animate-spin border-2 border-white border-t-transparent rounded-full w-5 h-5" /> Buscando nas fontes...</>
        ) : (
          <><Search className="w-5 h-5" /> Buscar melhores ofertas</>
        )}
      </button>
    </form>
  )
}

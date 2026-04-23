import React, { useState, useEffect, useRef } from 'react'
import { Search, MapPin, DollarSign, Car, AlertCircle } from 'lucide-react'
import type { SearchCriteria } from '../types'
import api from '../services/api'

interface Props {
  onSubmit: (criteria: SearchCriteria) => void
  loading: boolean
}

const CIDADES = [
  "São Paulo, SP", "Rio de Janeiro, RJ", "Belo Horizonte, MG", "Curitiba, PR",
  "Porto Alegre, RS", "Salvador, BA", "Fortaleza, CE", "Recife, PE",
  "Manaus, AM", "Belém, PA", "Goiânia, GO", "Campinas, SP",
  "São Luís, MA", "Maceió, AL", "Natal, RN", "Teresina, PI",
  "Campo Grande, MS", "João Pessoa, PB", "Aracaju, SE", "Cuiabá, MT",
  "Macapá, AP", "Porto Velho, RO", "Rio Branco, AC", "Boa Vista, RR",
  "Florianópolis, SC", "Vitória, ES", "Palmas, TO", "Brasília, DF",
  "Ribeirão Preto, SP", "Santos, SP", "Osasco, SP", "Guarulhos, SP",
  "São Bernardo do Campo, SP", "Santo André, SP", "Sorocaba, SP",
  "Uberlândia, MG", "Contagem, MG", "Juiz de Fora, MG",
  "Joinville, SC", "Londrina, PR", "Maringá, PR", "Foz do Iguaçu, PR",
  "Caxias do Sul, RS", "Pelotas, RS", "Canoas, RS",
  "Feira de Santana, BA", "Camaçari, BA",
  "Caucaia, CE", "Juazeiro do Norte, CE",
  "Olinda, PE", "Caruaru, PE",
  "Aparecida de Goiânia, GO", "Anápolis, GO",
]

function useAutocomplete(fetchFn: (q: string) => Promise<string[]>, delay = 300) {
  const [query, setQuery] = useState('')
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [open, setOpen] = useState(false)
  const timer = useRef<ReturnType<typeof setTimeout>>()

  useEffect(() => {
    clearTimeout(timer.current)
    if (query.length < 2) { setSuggestions([]); setOpen(false); return }
    timer.current = setTimeout(async () => {
      const results = await fetchFn(query)
      setSuggestions(results)
      setOpen(results.length > 0)
    }, delay)
    return () => clearTimeout(timer.current)
  }, [query])

  return { query, setQuery, suggestions, open, setOpen }
}

interface AutocompleteProps {
  value: string
  onChange: (v: string) => void
  fetchFn: (q: string) => Promise<string[]>
  placeholder: string
  icon: React.ReactNode
  label: string
  error?: string
}

function AutocompleteInput({ value, onChange, fetchFn, placeholder, icon, label, error }: AutocompleteProps) {
  const { query, setQuery, suggestions, open, setOpen } = useAutocomplete(fetchFn)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (value !== query) setQuery(value)
  }, [value])

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  return (
    <div ref={ref}>
      <label className="block text-sm font-semibold text-gray-700 mb-1">{label} *</label>
      <div className="relative">
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">{icon}</span>
        <input
          className={`w-full pl-10 pr-4 py-3 border rounded-xl focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none transition ${error ? 'border-red-400' : 'border-gray-300'}`}
          placeholder={placeholder}
          value={query}
          onChange={e => { setQuery(e.target.value); onChange(e.target.value) }}
          onFocus={() => { if (suggestions.length > 0) setOpen(true) }}
          autoComplete="off"
        />
        {open && suggestions.length > 0 && (
          <ul className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-xl shadow-lg max-h-52 overflow-y-auto">
            {suggestions.map(s => (
              <li
                key={s}
                className="px-4 py-2.5 hover:bg-brand-50 cursor-pointer text-sm text-gray-700 first:rounded-t-xl last:rounded-b-xl"
                onMouseDown={() => { onChange(s); setQuery(s); setOpen(false) }}
              >
                {s}
              </li>
            ))}
          </ul>
        )}
      </div>
      {error && <p className="mt-1 text-xs text-red-500 flex items-center gap-1"><AlertCircle className="w-3 h-3" />{error}</p>}
    </div>
  )
}

export default function SearchForm({ onSubmit, loading }: Props) {
  const [form, setForm] = useState<SearchCriteria>({
    model: '',
    max_price: 80000,
    location: '',
    transmission: 'indiferente',
    fuel: 'indiferente',
  })
  const [errors, setErrors] = useState<{ model?: string; location?: string }>({})

  const set = (key: keyof SearchCriteria, value: unknown) =>
    setForm(f => ({ ...f, [key]: value }))

  const fetchModels = async (q: string) => {
    try {
      const res = await api.get(`/fipe/models?q=${encodeURIComponent(q)}`)
      return res.data as string[]
    } catch {
      return []
    }
  }

  const fetchCidades = async (q: string): Promise<string[]> => {
    const ql = q.toLowerCase()
    return CIDADES.filter(c => c.toLowerCase().includes(ql)).slice(0, 8)
  }

  const validate = () => {
    const e: typeof errors = {}
    if (!form.model.trim()) e.model = 'Informe o modelo do carro'
    if (!form.location.trim()) e.location = 'Selecione uma cidade'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return
    onSubmit(form)
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-xl p-8 space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <AutocompleteInput
          label="Modelo do carro"
          value={form.model}
          onChange={v => { set('model', v); if (v) setErrors(er => ({ ...er, model: undefined })) }}
          fetchFn={fetchModels}
          placeholder="Ex: HB20, Onix, Civic..."
          icon={<Car className="w-4 h-4" />}
          error={errors.model}
        />
        <AutocompleteInput
          label="Cidade"
          value={form.location}
          onChange={v => { set('location', v); if (v) setErrors(er => ({ ...er, location: undefined })) }}
          fetchFn={fetchCidades}
          placeholder="Ex: São Paulo, SP"
          icon={<MapPin className="w-4 h-4" />}
          error={errors.location}
        />
      </div>

      <div>
        <label className="block text-sm font-semibold text-gray-700 mb-1">
          Preço máximo: <span className="text-brand-600 font-bold">R$ {form.max_price.toLocaleString('pt-BR')}</span>
        </label>
        <div className="relative">
          <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="range" min={15000} max={500000} step={5000}
            value={form.max_price}
            onChange={e => set('max_price', Number(e.target.value))}
            className="w-full pl-10 accent-brand-600"
          />
        </div>
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>R$ 15.000</span><span>R$ 500.000</span>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <label className="block text-xs font-semibold text-gray-600 mb-1">Ano mínimo</label>
          <input
            type="number" min={2000} max={2025} placeholder="2018"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 outline-none"
            onChange={e => set('year_min', e.target.value ? Number(e.target.value) : undefined)}
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-gray-600 mb-1">Ano máximo</label>
          <input
            type="number" min={2000} max={2025} placeholder="2024"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 outline-none"
            onChange={e => set('year_max', e.target.value ? Number(e.target.value) : undefined)}
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-gray-600 mb-1">KM máxima</label>
          <input
            type="number" placeholder="100000"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 outline-none"
            onChange={e => set('max_km', e.target.value ? Number(e.target.value) : undefined)}
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-gray-600 mb-1">Câmbio</label>
          <select
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 outline-none bg-white"
            value={form.transmission}
            onChange={e => set('transmission', e.target.value)}
          >
            <option value="indiferente">Indiferente</option>
            <option value="manual">Manual</option>
            <option value="automatico">Automático</option>
          </select>
        </div>
      </div>

      <div>
        <label className="block text-xs font-semibold text-gray-600 mb-2">Combustível</label>
        <div className="flex flex-wrap gap-2">
          {['indiferente', 'flex', 'gasolina', 'diesel', 'eletrico'].map(f => (
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
          <>
            <span className="animate-spin border-2 border-white border-t-transparent rounded-full w-5 h-5" />
            Buscando nas fontes...
          </>
        ) : (
          <><Search className="w-5 h-5" /> Buscar melhores ofertas</>
        )}
      </button>
    </form>
  )
}

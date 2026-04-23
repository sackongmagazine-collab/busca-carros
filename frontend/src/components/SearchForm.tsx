import React, { useState, useEffect, useRef, useCallback } from 'react'
import { Search, MapPin, DollarSign, Car, AlertCircle, X } from 'lucide-react'
import type { SearchCriteria } from '../types'
import api from '../services/api'

interface Props {
  onSubmit: (criteria: SearchCriteria) => void
  loading: boolean
  initialModel?: string
}

// 300+ maiores municípios brasileiros
const CITIES: string[] = [
  "São Paulo/SP", "Rio de Janeiro/RJ", "Brasília/DF", "Salvador/BA",
  "Fortaleza/CE", "Belo Horizonte/MG", "Manaus/AM", "Curitiba/PR",
  "Recife/PE", "Goiânia/GO", "Belém/PA", "Porto Alegre/RS",
  "Guarulhos/SP", "Campinas/SP", "São Luís/MA", "Maceió/AL",
  "Natal/RN", "Teresina/PI", "Campo Grande/MS", "João Pessoa/PB",
  "Osasco/SP", "Santo André/SP", "São Bernardo do Campo/SP",
  "Jaboatão dos Guararapes/PE", "Contagem/MG", "Uberlândia/MG",
  "Sorocaba/SP", "Aracaju/SE", "Feira de Santana/BA", "Cuiabá/MT",
  "Joinville/SC", "Juiz de Fora/MG", "Londrina/PR", "Aparecida de Goiânia/GO",
  "Ananindeua/PA", "Porto Velho/RO", "Serra/ES", "Caxias do Sul/RS",
  "Macapá/AP", "Florianópolis/SC", "São João de Meriti/RJ", "Mogi das Cruzes/SP",
  "Santos/SP", "Mauá/SP", "Duque de Caxias/RJ", "Betim/MG",
  "Carapicuíba/SP", "Olinda/PE", "Campina Grande/PB", "Ribeirão Preto/SP",
  "Nova Iguaçu/RJ", "São José dos Campos/SP", "Niterói/RJ", "Belford Roxo/RJ",
  "Natal/RN", "São José do Rio Preto/SP", "Mogi Guaçu/SP",
  "Diadema/SP", "Caucaia/CE", "Maringá/PR", "Piracicaba/SP",
  "Anápolis/GO", "Porto Alegre/RS", "Bauru/SP", "Caruaru/PE",
  "Canoas/RS", "Campo Largo/PR", "São Carlos/SP", "Vitória/ES",
  "Pelotas/RS", "Caxias do Sul/RS", "Cascavel/PR", "Blumenau/SC",
  "Foz do Iguaçu/PR", "Macaé/RJ", "Volta Redonda/RJ", "Petrolina/PE",
  "Mossoró/RN", "Imperatriz/MA", "Palmas/TO", "Rio Branco/AC",
  "Boa Vista/RR", "Macapá/AP", "Araraquara/SP", "Franca/SP",
  "Ribeirão das Neves/MG", "Montes Claros/MG", "Teófilo Otoni/MG",
  "Uberaba/MG", "Governador Valadares/MG", "Sete Lagoas/MG",
  "Divinópolis/MG", "Contagem/MG", "Ibirité/MG", "Betim/MG",
  "Vitória da Conquista/BA", "Camaçari/BA", "Ilhéus/BA", "Juazeiro/BA",
  "Juazeiro do Norte/CE", "Sobral/CE", "Maracanaú/CE", "Caucaia/CE",
  "Petrolina/PE", "Caruaru/PE", "Olinda/PE", "Paulista/PE",
  "Campina Grande/PB", "Santa Rita/PB", "Bayeux/PB",
  "São Gonçalo/RJ", "Duque de Caxias/RJ", "Nova Iguaçu/RJ", "Mesquita/RJ",
  "Campos dos Goytacazes/RJ", "Petrópolis/RJ", "Angra dos Reis/RJ",
  "Barueri/SP", "Suzano/SP", "Guarujá/SP", "São Vicente/SP", "Praia Grande/SP",
  "Taubaté/SP", "Limeira/SP", "Americana/SP", "Santa Bárbara d'Oeste/SP",
  "Pindamonhangaba/SP", "Jacareí/SP", "Guaratinguetá/SP", "Botucatu/SP",
  "Marília/SP", "Presidente Prudente/SP", "Araçatuba/SP", "Assis/SP",
  "Ilha Solteira/SP", "Jaú/SP", "Rio Claro/SP", "São José do Rio Preto/SP",
  "Votuporanga/SP", "Catanduva/SP", "Fernandópolis/SP",
  "Chapecó/SC", "Joinville/SC", "Lages/SC", "Itajaí/SC", "Criciúma/SC",
  "Palhoça/SC", "São José/SC", "Brusque/SC", "Balneário Camboriú/SC",
  "Pato Branco/PR", "Apucarana/PR", "Guarapuava/PR", "Paranaguá/PR",
  "Ponta Grossa/PR", "Londrina/PR", "Maringá/PR", "Cascavel/PR",
  "Toledo/PR", "Colombo/PR", "São José dos Pinhais/PR", "Araucária/PR",
  "Santa Maria/RS", "Caxias do Sul/RS", "Passo Fundo/RS", "Novo Hamburgo/RS",
  "São Leopoldo/RS", "Gravataí/RS", "Viamão/RS", "Alvorada/RS",
  "Rondonópolis/MT", "Várzea Grande/MT", "Sinop/MT",
  "Dourados/MS", "Três Lagoas/MS", "Corumbá/MS",
  "Rio Verde/GO", "Aparecida de Goiânia/GO", "Anápolis/GO", "Luziânia/GO",
  "Araguaína/TO", "Palmas/TO",
  "Santarém/PA", "Ananindeua/PA", "Marabá/PA", "Parauapebas/PA",
  "Parintins/AM", "Itacoatiara/AM",
  "Barreiras/BA", "Jequié/BA", "Alagoinhas/BA",
  "Crato/CE", "Sobral/CE", "Iguatu/CE",
  "Timon/MA", "Bacabal/MA", "Caxias/MA",
  "Parnaíba/PI", "Picos/PI",
  "Mossoró/RN", "Caicó/RN",
  "Arapiraca/AL", "Palmeira dos Índios/AL",
  "Lagarto/SE", "Itabaiana/SE",
]

function normalize(text: string): string {
  return text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
}

function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(t)
  }, [value, delay])
  return debounced
}

interface AutocompleteInputProps {
  label: string
  value: string
  onChange: (v: string) => void
  fetchFn: (q: string) => Promise<string[]>
  placeholder: string
  icon: React.ReactNode
  error?: string
  inputClassName?: string
}

function AutocompleteInput({
  label, value, onChange, fetchFn, placeholder, icon, error,
}: AutocompleteInputProps) {
  const [inputVal, setInputVal] = useState(value)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [open, setOpen] = useState(false)
  const [focused, setFocused] = useState(false)
  const debouncedInput = useDebounce(inputVal, 250)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => { setInputVal(value) }, [value])

  useEffect(() => {
    if (!focused || debouncedInput.length < 2) { setSuggestions([]); setOpen(false); return }
    fetchFn(debouncedInput).then(results => {
      setSuggestions(results)
      setOpen(results.length > 0)
    })
  }, [debouncedInput, focused])

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const select = (s: string) => {
    setInputVal(s)
    onChange(s)
    setOpen(false)
    setFocused(false)
  }

  const clear = () => { setInputVal(''); onChange(''); setSuggestions([]) }

  return (
    <div ref={containerRef}>
      <label className="block text-sm font-semibold text-gray-700 mb-1">{label} *</label>
      <div className={`relative flex items-center border rounded-xl transition ${
        error ? 'border-red-400' : focused ? 'border-brand-500 ring-2 ring-brand-200' : 'border-gray-300'
      } bg-white`}>
        <span className="pl-3 text-gray-400 shrink-0">{icon}</span>
        <input
          className="flex-1 px-3 py-3 outline-none text-sm bg-transparent rounded-xl"
          placeholder={placeholder}
          value={inputVal}
          autoComplete="off"
          spellCheck={false}
          onFocus={() => setFocused(true)}
          onBlur={() => setTimeout(() => setFocused(false), 150)}
          onChange={e => { setInputVal(e.target.value); onChange(e.target.value) }}
        />
        {inputVal && (
          <button type="button" onClick={clear} className="pr-3 text-gray-300 hover:text-gray-500">
            <X className="w-4 h-4" />
          </button>
        )}
        {open && suggestions.length > 0 && (
          <ul className="absolute z-50 left-0 right-0 top-full mt-1 bg-white border border-gray-200 rounded-xl shadow-xl max-h-56 overflow-y-auto">
            {suggestions.map(s => (
              <li
                key={s}
                className="px-4 py-2.5 text-sm text-gray-700 hover:bg-brand-50 hover:text-brand-700 cursor-pointer first:rounded-t-xl last:rounded-b-xl"
                onMouseDown={() => select(s)}
              >
                {s}
              </li>
            ))}
          </ul>
        )}
      </div>
      {error && (
        <p className="mt-1 text-xs text-red-500 flex items-center gap-1">
          <AlertCircle className="w-3 h-3 shrink-0" />{error}
        </p>
      )}
    </div>
  )
}

export default function SearchForm({ onSubmit, loading, initialModel }: Props) {
  const [form, setForm] = useState<SearchCriteria>({
    model: initialModel ?? '',
    max_price: 80000,
    location: '',
    transmission: 'indiferente',
    fuel: 'indiferente',
  })
  const [errors, setErrors] = useState<{ model?: string; location?: string }>({})

  useEffect(() => { if (initialModel) setForm(f => ({ ...f, model: initialModel })) }, [initialModel])

  const set = (key: keyof SearchCriteria, value: unknown) =>
    setForm(f => ({ ...f, [key]: value }))

  const fetchModels = useCallback(async (q: string): Promise<string[]> => {
    try {
      const { data } = await api.get<string[]>(`/fipe/models?q=${encodeURIComponent(q)}`)
      return data
    } catch {
      return []
    }
  }, [])

  const fetchCities = useCallback(async (q: string): Promise<string[]> => {
    const qn = normalize(q)
    const starts = CITIES.filter(c => normalize(c).startsWith(qn))
    const contains = CITIES.filter(c => normalize(c).includes(qn) && !starts.includes(c))
    return [...starts, ...contains].slice(0, 10)
  }, [])

  const validate = () => {
    const e: typeof errors = {}
    if (!form.model.trim()) e.model = 'Informe o modelo'
    if (!form.location.trim()) e.location = 'Selecione uma cidade'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (validate()) onSubmit(form)
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-xl p-6 md:p-8 space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <AutocompleteInput
          label="Modelo do carro"
          value={form.model}
          onChange={v => { set('model', v); if (v) setErrors(er => ({ ...er, model: undefined })) }}
          fetchFn={fetchModels}
          placeholder="Ex: HB20, Civic, Onix..."
          icon={<Car className="w-4 h-4" />}
          error={errors.model}
        />
        <AutocompleteInput
          label="Cidade"
          value={form.location}
          onChange={v => { set('location', v); if (v) setErrors(er => ({ ...er, location: undefined })) }}
          fetchFn={fetchCities}
          placeholder="Ex: São Paulo/SP, Curitiba/PR"
          icon={<MapPin className="w-4 h-4" />}
          error={errors.location}
        />
      </div>

      <div>
        <label className="block text-sm font-semibold text-gray-700 mb-1">
          Preço máximo:{' '}
          <span className="text-brand-600 font-bold">
            R$ {form.max_price.toLocaleString('pt-BR')}
          </span>
        </label>
        <input
          type="range" min={15000} max={500000} step={5000}
          value={form.max_price}
          onChange={e => set('max_price', Number(e.target.value))}
          className="w-full accent-brand-600 mt-1"
        />
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>R$ 15.000</span><span>R$ 500.000</span>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Ano mínimo', key: 'year_min', placeholder: '2018' },
          { label: 'Ano máximo', key: 'year_max', placeholder: '2024' },
          { label: 'KM máxima', key: 'max_km', placeholder: '100000' },
        ].map(({ label, key, placeholder }) => (
          <div key={key}>
            <label className="block text-xs font-semibold text-gray-600 mb-1">{label}</label>
            <input
              type="number" placeholder={placeholder}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 outline-none"
              onChange={e => set(key as keyof SearchCriteria, e.target.value ? Number(e.target.value) : undefined)}
            />
          </div>
        ))}
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
              className={`px-4 py-1.5 rounded-full text-sm font-medium border transition ${
                form.fuel === f
                  ? 'bg-brand-600 text-white border-brand-600'
                  : 'bg-white text-gray-600 border-gray-300 hover:border-brand-400'
              }`}
            >
              {f === 'indiferente' ? 'Indiferente' : f.charAt(0).toUpperCase() + f.slice(1)}
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

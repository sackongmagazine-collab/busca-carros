import React from 'react'
import { useLocation, useParams, useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { ArrowLeft, Star, Tag, ClipboardList, SearchX } from 'lucide-react'
import CarCard from '../components/CarCard'
import { waitForResults } from '../services/api'
import type { SearchResponse } from '../types'

export default function Results() {
  const { id } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const [results, setResults] = useState<SearchResponse | null>(location.state?.results ?? null)
  const [loading, setLoading] = useState(!results)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!results && id) {
      setLoading(true)
      waitForResults(Number(id))
        .then(setResults)
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false))
    }
  }, [id])

  if (loading)
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center space-y-4">
          <div className="animate-spin w-12 h-12 border-4 border-brand-600 border-t-transparent rounded-full mx-auto" />
          <p className="text-gray-600 font-medium">Analisando anúncios com IA...</p>
        </div>
      </div>
    )

  if (error)
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center space-y-4">
          <p className="text-red-600">{error}</p>
          <button onClick={() => navigate('/')} className="text-brand-600 underline">Voltar</button>
        </div>
      </div>
    )

  if (!results) return null

  const bestIdx = results.ranking.findIndex((r) => r.verdict === 'vale muito a pena' || r.verdict === 'vale a pena')

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Topbar */}
      <div className="bg-brand-700 text-white px-4 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <button onClick={() => navigate('/')} className="flex items-center gap-2 hover:text-brand-200 transition">
            <ArrowLeft className="w-5 h-5" /> Nova busca
          </button>
          <div className="text-sm">
            <span className="font-bold">{results.total_found}</span> anúncios encontrados ·{' '}
            FIPE: <span className="font-bold">R$ {results.fipe_value?.toLocaleString('pt-BR') ?? '—'}</span>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
        {/* Resumo IA */}
        {(results.best_choice || results.cheapest_choice) && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {results.best_choice && (
              <div className="bg-green-50 border border-green-300 rounded-2xl p-5 flex gap-3">
                <Star className="w-5 h-5 text-green-600 shrink-0 mt-0.5" />
                <div>
                  <p className="text-xs font-bold text-green-700 uppercase tracking-wide mb-1">Melhor escolha geral</p>
                  <p className="text-sm text-gray-700">{results.best_choice}</p>
                </div>
              </div>
            )}
            {results.cheapest_choice && (
              <div className="bg-blue-50 border border-blue-300 rounded-2xl p-5 flex gap-3">
                <Tag className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
                <div>
                  <p className="text-xs font-bold text-blue-700 uppercase tracking-wide mb-1">Opção mais barata</p>
                  <p className="text-sm text-gray-700">{results.cheapest_choice}</p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Ranking */}
        <div className="space-y-4">
          <h2 className="text-xl font-black text-gray-900">Ranking de custo-benefício</h2>
          {results.ranking.length === 0 ? (
            <div className="text-center py-16 space-y-4">
              <SearchX className="w-14 h-14 text-gray-300 mx-auto" />
              <p className="text-gray-600 font-semibold text-lg">Nenhum anúncio encontrado</p>
              <p className="text-gray-400 text-sm max-w-sm mx-auto">
                Tente ampliar o preço máximo, remover filtros de ano/km ou buscar em outra cidade.
              </p>
              <div className="pt-2">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Modelos populares para tentar</p>
                <div className="flex flex-wrap justify-center gap-2">
                  {['Onix', 'HB20', 'Gol', 'Argo', 'Polo', 'Kwid', 'Sandero'].map(m => (
                    <button
                      key={m}
                      onClick={() => navigate('/', { state: { model: m } })}
                      className="px-3 py-1.5 bg-brand-50 text-brand-700 rounded-full text-sm font-medium hover:bg-brand-100 transition border border-brand-200"
                    >
                      {m}
                    </button>
                  ))}
                </div>
              </div>
              <button onClick={() => navigate('/')} className="mt-4 text-brand-600 underline text-sm">
                ← Voltar e ajustar filtros
              </button>
            </div>
          ) : (
            results.ranking.map((r, i) => (
              <CarCard key={r.listing.url + i} result={r} highlight={i === bestIdx} />
            ))
          )}
        </div>

        {/* Checklist */}
        {results.inspection_checklist?.length > 0 && (
          <div className="bg-white rounded-2xl border border-gray-200 p-6">
            <h3 className="font-bold text-gray-900 flex items-center gap-2 mb-4">
              <ClipboardList className="w-5 h-5 text-brand-600" /> Checklist antes de comprar
            </h3>
            <ul className="space-y-2">
              {results.inspection_checklist.map((item, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                  <span className="mt-0.5 w-5 h-5 rounded-full border-2 border-brand-400 flex items-center justify-center text-xs font-bold text-brand-600 shrink-0">{i + 1}</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}

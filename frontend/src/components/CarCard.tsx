import { ExternalLink, AlertTriangle, CheckCircle, TrendingDown, TrendingUp, Minus } from 'lucide-react'
import type { RankedResult, Verdict } from '../types'
import clsx from 'clsx'

const verdictConfig: Record<Verdict, { label: string; color: string; bg: string; border: string }> = {
  'vale muito a pena': { label: 'Vale muito a pena', color: 'text-green-700', bg: 'bg-green-50', border: 'border-green-400' },
  'vale a pena': { label: 'Vale a pena', color: 'text-blue-700', bg: 'bg-blue-50', border: 'border-blue-400' },
  'atenção': { label: 'Atenção', color: 'text-yellow-700', bg: 'bg-yellow-50', border: 'border-yellow-400' },
  'evitar': { label: 'Evitar', color: 'text-red-700', bg: 'bg-red-50', border: 'border-red-400' },
}

function FipeBadge({ pct }: { pct: number }) {
  const abs = Math.abs(pct).toFixed(1)
  if (pct < -2)
    return <span className="flex items-center gap-1 text-green-700 font-semibold text-sm"><TrendingDown className="w-4 h-4" />{abs}% abaixo da FIPE</span>
  if (pct > 2)
    return <span className="flex items-center gap-1 text-red-600 font-semibold text-sm"><TrendingUp className="w-4 h-4" />{abs}% acima da FIPE</span>
  return <span className="flex items-center gap-1 text-gray-500 font-semibold text-sm"><Minus className="w-4 h-4" />Na FIPE</span>
}

interface Props {
  result: RankedResult
  highlight?: boolean
}

export default function CarCard({ result, highlight }: Props) {
  const { listing, verdict, strengths, risks, summary, fipe_diff_pct, fipe_value, position } = result
  const cfg = verdictConfig[verdict] ?? verdictConfig['atenção']

  return (
    <div className={clsx(
      'rounded-2xl border-2 overflow-hidden transition hover:shadow-lg',
      cfg.border,
      highlight && 'ring-4 ring-brand-500 ring-offset-2',
    )}>
      {/* Header */}
      <div className={clsx('flex items-center justify-between px-5 py-3', cfg.bg)}>
        <div className="flex items-center gap-3">
          <span className="text-2xl font-black text-gray-500">#{position}</span>
          <span className={clsx('text-sm font-bold px-3 py-1 rounded-full', cfg.bg, cfg.color, 'border', cfg.border)}>
            {cfg.label}
          </span>
          {highlight && <span className="text-xs bg-brand-600 text-white px-2 py-0.5 rounded-full font-semibold">Melhor escolha</span>}
        </div>
        <span className="text-xs text-gray-500 font-medium">{listing.source}</span>
      </div>

      <div className="p-5 bg-white grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Imagem */}
        <div className="md:col-span-1">
          {listing.image_url ? (
            <img src={listing.image_url} alt={listing.title} className="w-full h-36 object-cover rounded-xl" />
          ) : (
            <div className="w-full h-36 bg-gray-100 rounded-xl flex items-center justify-center text-gray-400 text-sm">Sem imagem</div>
          )}
        </div>

        {/* Dados principais */}
        <div className="md:col-span-2 space-y-2">
          <h3 className="font-bold text-gray-900 text-lg leading-tight">{listing.title}</h3>
          <p className="text-gray-500 text-sm">{summary}</p>

          <div className="flex flex-wrap gap-4 text-sm text-gray-700">
            <span className="text-2xl font-black text-gray-900">
              R$ {listing.price.toLocaleString('pt-BR')}
            </span>
            <div className="flex flex-col justify-center">
              <FipeBadge pct={fipe_diff_pct} />
              <span className="text-xs text-gray-400">FIPE: R$ {fipe_value.toLocaleString('pt-BR')}</span>
            </div>
          </div>

          <div className="flex flex-wrap gap-3 text-xs text-gray-600">
            {listing.year && <span className="bg-gray-100 px-2 py-1 rounded-lg">{listing.year}</span>}
            {listing.km && <span className="bg-gray-100 px-2 py-1 rounded-lg">{listing.km.toLocaleString('pt-BR')} km</span>}
            {listing.transmission && <span className="bg-gray-100 px-2 py-1 rounded-lg capitalize">{listing.transmission}</span>}
            {listing.fuel && <span className="bg-gray-100 px-2 py-1 rounded-lg capitalize">{listing.fuel}</span>}
            {listing.location && <span className="bg-gray-100 px-2 py-1 rounded-lg">{listing.location}</span>}
            {listing.seller_type && <span className="bg-gray-100 px-2 py-1 rounded-lg capitalize">{listing.seller_type}</span>}
          </div>
        </div>
      </div>

      {/* Pontos fortes e riscos */}
      <div className="px-5 pb-4 bg-white grid grid-cols-1 md:grid-cols-2 gap-4 border-t border-gray-100 pt-3">
        {strengths.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-green-700 mb-1 flex items-center gap-1"><CheckCircle className="w-3 h-3" /> Pontos fortes</p>
            <ul className="space-y-0.5">
              {strengths.map((s, i) => <li key={i} className="text-xs text-gray-700">• {s}</li>)}
            </ul>
          </div>
        )}
        {risks.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-red-600 mb-1 flex items-center gap-1"><AlertTriangle className="w-3 h-3" /> Alertas</p>
            <ul className="space-y-0.5">
              {risks.map((r, i) => <li key={i} className="text-xs text-gray-700">• {r}</li>)}
            </ul>
          </div>
        )}
      </div>

      {/* Link */}
      {listing.url && (
        <div className="px-5 py-3 bg-gray-50 border-t border-gray-100">
          <a
            href={listing.url} target="_blank" rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-brand-600 hover:text-brand-700 text-sm font-semibold transition"
          >
            Ver anúncio <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      )}
    </div>
  )
}

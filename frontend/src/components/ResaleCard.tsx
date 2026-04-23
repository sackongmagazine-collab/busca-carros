import React from 'react'
import { TrendingUp, Package, DollarSign, Clock } from 'lucide-react'
import clsx from 'clsx'

interface ResaleData {
  buy_price: number
  fipe_value: number
  estimated_resale_price: number
  reconditioning_estimate: number
  platform_fee: number
  transfer_costs: number
  gross_margin: number
  net_margin: number
  roi_pct: number
  payback_months: number
  opportunity_score: number
  opportunity_label: string
  breakdown: Record<string, number>
}

const labelConfig: Record<string, { color: string; bg: string; label: string }> = {
  excelente: { color: 'text-green-700', bg: 'bg-green-50 border-green-300', label: 'Excelente oportunidade' },
  boa: { color: 'text-blue-700', bg: 'bg-blue-50 border-blue-300', label: 'Boa oportunidade' },
  marginal: { color: 'text-yellow-700', bg: 'bg-yellow-50 border-yellow-300', label: 'Margem marginal' },
  negativa: { color: 'text-red-700', bg: 'bg-red-50 border-red-300', label: 'Sem margem' },
}

export default function ResaleCard({ resale }: { resale: ResaleData }) {
  const cfg = labelConfig[resale.opportunity_label] ?? labelConfig.marginal
  const fmt = (v: number) => `R$ ${v.toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`

  return (
    <div className={clsx('rounded-xl border p-4 mt-3', cfg.bg)}>
      <div className="flex items-center justify-between mb-3">
        <span className={clsx('font-bold text-sm flex items-center gap-1.5', cfg.color)}>
          <TrendingUp className="w-4 h-4" /> Oportunidade de revenda
        </span>
        <span className={clsx('text-xs font-bold px-2 py-0.5 rounded-full border', cfg.color, cfg.bg)}>
          {cfg.label}
        </span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
        <Stat icon={<DollarSign className="w-4 h-4" />} label="Margem líquida" value={fmt(resale.net_margin)} positive={resale.net_margin > 0} />
        <Stat icon={<TrendingUp className="w-4 h-4" />} label="ROI estimado" value={`${resale.roi_pct.toFixed(1)}%`} positive={resale.roi_pct > 0} />
        <Stat icon={<Package className="w-4 h-4" />} label="Revenda estimada" value={fmt(resale.estimated_resale_price)} />
        <Stat icon={<Clock className="w-4 h-4" />} label="Tempo de estoque" value={`~${resale.payback_months} meses`} />
      </div>

      <details className="text-xs">
        <summary className={clsx('cursor-pointer font-semibold', cfg.color)}>Ver breakdown detalhado</summary>
        <div className="mt-2 space-y-1 text-gray-700">
          {Object.entries(resale.breakdown).map(([k, v]) => (
            <div key={k} className="flex justify-between">
              <span className="capitalize text-gray-500">{k.replace(/_/g, ' ')}</span>
              <span className={clsx('font-medium', v < 0 ? 'text-red-600' : '')}>{fmt(v as number)}</span>
            </div>
          ))}
        </div>
      </details>
    </div>
  )
}

function Stat({ icon, label, value, positive }: { icon: React.ReactNode; label: string; value: string; positive?: boolean }) {
  return (
    <div className="bg-white/70 rounded-lg p-2.5">
      <div className="flex items-center gap-1 text-gray-500 mb-1">{icon}<span className="text-xs">{label}</span></div>
      <div className={clsx('font-bold text-sm', positive === false ? 'text-red-600' : positive ? 'text-green-700' : 'text-gray-900')}>{value}</div>
    </div>
  )
}

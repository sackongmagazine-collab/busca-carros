import { Check, Zap, Shield, Building2 } from 'lucide-react'
import { useState } from 'react'
import axios from 'axios'
import clsx from 'clsx'

const plans = [
  {
    id: 'free',
    name: 'Free',
    price: 0,
    desc: 'Para quem está começando a busca',
    icon: <Zap className="w-6 h-6" />,
    color: 'border-gray-200',
    highlight: false,
    features: [
      '3 buscas por dia',
      'Comparação com FIPE',
      'Ranking de custo-benefício',
      'Checklist de inspeção',
    ],
    unavailable: ['Alertas automáticos', 'Análise de revenda', 'Sem anúncios'],
    cta: 'Começar grátis',
    plan_key: null,
  },
  {
    id: 'hunter',
    name: 'Hunter',
    price: 29.90,
    desc: 'Para quem busca com frequência',
    icon: <Zap className="w-6 h-6" />,
    color: 'border-brand-500',
    highlight: true,
    features: [
      'Buscas ilimitadas',
      'Até 5 alertas automáticos',
      'Notificações por e-mail',
      'Comparação com FIPE',
      'Ranking de custo-benefício',
      'Histórico de buscas',
    ],
    unavailable: ['WhatsApp/Telegram', 'Análise de revenda'],
    cta: 'Assinar Hunter',
    plan_key: 'hunter',
  },
  {
    id: 'hunter_pro',
    name: 'Hunter Pro',
    price: 59.90,
    desc: 'Para compradores e revendedores',
    icon: <Shield className="w-6 h-6" />,
    color: 'border-purple-500',
    highlight: false,
    features: [
      'Tudo do Hunter',
      'Até 20 alertas automáticos',
      'Alertas via WhatsApp e Telegram',
      'Análise completa de revenda',
      'Cálculo de margem e ROI',
      'Score antifraude avançado',
      'Alertas de threshold FIPE',
    ],
    unavailable: [],
    cta: 'Assinar Hunter Pro',
    plan_key: 'hunter_pro',
  },
  {
    id: 'dealer',
    name: 'Lojista',
    price: 149.90,
    desc: 'Para concessionárias e revendedores',
    icon: <Building2 className="w-6 h-6" />,
    color: 'border-yellow-500',
    highlight: false,
    features: [
      'Tudo do Hunter Pro',
      'Painel de lojista completo',
      'Até 500 anúncios ativos',
      'Destaque nos resultados de busca',
      'Relatórios de leads e visitas',
      'Verificação de empresa',
      'Suporte prioritário',
      'API de integração',
    ],
    unavailable: [],
    cta: 'Assinar Lojista',
    plan_key: 'dealer',
  },
]

export default function Pricing() {
  const [loading, setLoading] = useState<string | null>(null)
  const [error, setError] = useState('')

  const handleSubscribe = async (plan_key: string | null) => {
    if (!plan_key) return
    const token = localStorage.getItem('token')
    if (!token) {
      window.location.href = '/login?redirect=/pricing'
      return
    }
    setLoading(plan_key)
    setError('')
    try {
      const { data } = await axios.post(
        '/api/subscriptions/checkout',
        { plan: plan_key },
        { headers: { Authorization: `Bearer ${token}` } },
      )
      window.location.href = data.checkout_url
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Erro ao iniciar pagamento')
    } finally {
      setLoading(null)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-16 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-black text-gray-900 mb-3">Planos que se adaptam à sua necessidade</h1>
          <p className="text-gray-500 text-lg">Do comprador casual ao revendedor profissional.</p>
        </div>

        {error && (
          <div className="mb-6 max-w-md mx-auto bg-red-50 border border-red-300 text-red-700 rounded-xl px-4 py-3 text-sm text-center">{error}</div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {plans.map((plan) => (
            <div
              key={plan.id}
              className={clsx(
                'bg-white rounded-2xl border-2 p-6 flex flex-col',
                plan.color,
                plan.highlight && 'shadow-2xl scale-105',
              )}
            >
              {plan.highlight && (
                <div className="text-xs font-bold text-brand-600 bg-brand-50 px-3 py-1 rounded-full w-fit mb-3">
                  Mais popular
                </div>
              )}
              <div className={clsx('mb-3', plan.id === 'hunter' ? 'text-brand-600' : plan.id === 'hunter_pro' ? 'text-purple-600' : plan.id === 'dealer' ? 'text-yellow-600' : 'text-gray-400')}>
                {plan.icon}
              </div>
              <h3 className="text-xl font-black text-gray-900">{plan.name}</h3>
              <p className="text-sm text-gray-500 mb-4">{plan.desc}</p>

              <div className="mb-6">
                {plan.price === 0 ? (
                  <span className="text-3xl font-black text-gray-900">Grátis</span>
                ) : (
                  <div>
                    <span className="text-3xl font-black text-gray-900">R$ {plan.price.toFixed(2).replace('.', ',')}</span>
                    <span className="text-gray-400 text-sm">/mês</span>
                  </div>
                )}
              </div>

              <ul className="space-y-2 mb-6 flex-1">
                {plan.features.map((f, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                    <Check className="w-4 h-4 text-green-500 shrink-0 mt-0.5" /> {f}
                  </li>
                ))}
                {plan.unavailable.map((f, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-400 line-through">
                    <Check className="w-4 h-4 text-gray-300 shrink-0 mt-0.5" /> {f}
                  </li>
                ))}
              </ul>

              <button
                onClick={() => handleSubscribe(plan.plan_key)}
                disabled={!plan.plan_key || loading === plan.plan_key}
                className={clsx(
                  'w-full py-3 rounded-xl font-bold text-sm transition',
                  plan.plan_key
                    ? plan.highlight
                      ? 'bg-brand-600 hover:bg-brand-700 text-white'
                      : 'bg-gray-900 hover:bg-gray-800 text-white'
                    : 'bg-gray-100 text-gray-500 cursor-default',
                )}
              >
                {loading === plan.plan_key ? 'Redirecionando...' : plan.cta}
              </button>
            </div>
          ))}
        </div>

        <p className="text-center text-xs text-gray-400 mt-8">
          Pagamento seguro via Stripe. Cancele quando quiser, sem multa.
        </p>
      </div>
    </div>
  )
}

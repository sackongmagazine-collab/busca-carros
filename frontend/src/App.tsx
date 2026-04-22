import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import Home from './pages/Home'
import Results from './pages/Results'
import Pricing from './pages/Pricing'
import Alerts from './pages/Alerts'
import DealerPortal from './pages/dealer/Portal'
import AdminDashboard from './pages/admin/Dashboard'
import { Bell, CreditCard, Building2, Search } from 'lucide-react'

function NavBar() {
  const { pathname } = useLocation()
  const token = localStorage.getItem('token')

  if (pathname.startsWith('/admin') || pathname.startsWith('/dealer')) return null

  return (
    <nav className="bg-white border-b border-gray-100 sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link to="/" className="text-brand-700 font-black text-xl flex items-center gap-2">
          <Search className="w-5 h-5" /> BuscaCarros
        </Link>
        <div className="flex items-center gap-1">
          <Link to="/pricing" className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-brand-600 px-3 py-1.5 rounded-lg hover:bg-brand-50 transition">
            <CreditCard className="w-4 h-4" /> Planos
          </Link>
          {token && (
            <Link to="/alerts" className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-brand-600 px-3 py-1.5 rounded-lg hover:bg-brand-50 transition">
              <Bell className="w-4 h-4" /> Alertas
            </Link>
          )}
          {token && (
            <Link to="/dealer" className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-brand-600 px-3 py-1.5 rounded-lg hover:bg-brand-50 transition">
              <Building2 className="w-4 h-4" /> Lojista
            </Link>
          )}
          {!token ? (
            <Link to="/pricing" className="ml-2 bg-brand-600 hover:bg-brand-700 text-white px-4 py-1.5 rounded-lg text-sm font-semibold transition">
              Entrar
            </Link>
          ) : (
            <button onClick={() => { localStorage.removeItem('token'); window.location.href = '/' }}
              className="ml-2 text-sm text-gray-500 hover:text-gray-700 px-3 py-1.5">
              Sair
            </button>
          )}
        </div>
      </div>
    </nav>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <NavBar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/results/:id" element={<Results />} />
        <Route path="/pricing" element={<Pricing />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/dealer" element={<DealerPortal />} />
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/subscription/success" element={<SubscriptionSuccess />} />
      </Routes>
    </BrowserRouter>
  )
}

function SubscriptionSuccess() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center space-y-4">
        <div className="text-5xl">🎉</div>
        <h1 className="text-2xl font-black text-gray-900">Assinatura ativada!</h1>
        <p className="text-gray-500">Seu plano foi ativado com sucesso.</p>
        <Link to="/" className="inline-block bg-brand-600 text-white px-6 py-2.5 rounded-xl font-semibold hover:bg-brand-700 transition">
          Começar a buscar
        </Link>
      </div>
    </div>
  )
}

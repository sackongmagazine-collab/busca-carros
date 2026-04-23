import axios from 'axios'
import type { SearchCriteria, SearchResponse } from '../types'

// Em produção VITE_API_URL aponta para o Render backend (ex: https://buscacarros-api.onrender.com)
// Em desenvolvimento usa proxy do Vite (/api → localhost:8000)
const baseURL = import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL}/api` : '/api'

const api = axios.create({ baseURL })

export default api

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export async function startSearch(criteria: SearchCriteria): Promise<{ search_id: number }> {
  const { data } = await api.post('/search', criteria)
  return data
}

export async function pollSearch(searchId: number): Promise<SearchResponse> {
  const { data } = await api.get(`/search/${searchId}`)
  return data
}

export async function waitForResults(
  searchId: number,
  onProgress?: (status: string) => void,
  maxWait = 90000,
): Promise<SearchResponse> {
  const interval = 2500
  const maxAttempts = maxWait / interval
  let attempts = 0

  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        const result = await pollSearch(searchId)
        onProgress?.(result.status)
        if (result.status === 'completed') { resolve(result); return }
        if (result.status === 'failed') { reject(new Error('A busca falhou. Tente novamente.')); return }
        if (++attempts >= maxAttempts) { reject(new Error('Tempo limite excedido.')); return }
        setTimeout(poll, interval)
      } catch (err) {
        reject(err)
      }
    }
    poll()
  })
}

export async function register(email: string, password: string, full_name?: string) {
  const { data } = await api.post('/auth/register', { email, password, full_name })
  return data
}

export async function login(email: string, password: string) {
  const { data } = await api.post('/auth/login', { email, password })
  return data
}

export async function getHistory() {
  const { data } = await api.get('/search/history/me')
  return data
}

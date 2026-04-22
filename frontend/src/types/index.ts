export interface SearchCriteria {
  model: string
  max_price: number
  location: string
  year_min?: number
  year_max?: number
  max_km?: number
  transmission: 'manual' | 'automatico' | 'indiferente'
  fuel: 'flex' | 'gasolina' | 'diesel' | 'eletrico' | 'indiferente'
}

export interface CarListing {
  source: string
  title: string
  model: string
  year?: number
  price: number
  km?: number
  transmission?: string
  fuel?: string
  location: string
  url: string
  image_url?: string
  seller_type?: string
}

export type Verdict = 'vale muito a pena' | 'vale a pena' | 'atenção' | 'evitar'

export interface RankedResult {
  position: number
  listing: CarListing
  fipe_value: number
  fipe_diff_pct: number
  verdict: Verdict
  strengths: string[]
  risks: string[]
  summary: string
}

export interface SearchResponse {
  search_id: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  fipe_value?: number
  total_found: number
  ranking: RankedResult[]
  best_choice?: string
  cheapest_choice?: string
  inspection_checklist: string[]
}

export interface User {
  id: number
  email: string
  full_name?: string
  is_premium: boolean
}

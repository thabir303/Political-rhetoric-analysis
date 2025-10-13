export interface Article {
  content: string
  distance: number
  metadata?: ArticleMetadata
}

export interface ArticleMetadata {
  title?: string
  date?: string
  category?: string
  source?: string
  persons?: string[]
  parties?: string[]
  themes?: string[]
  language?: string
  is_speech?: boolean
  is_stance?: boolean
  keywords?: string[]
}

export interface SearchResponse {
  results: Article[]
  total_results: number
  query: string
}

export interface SearchRequest {
  query: string
  top_k?: number
  filter_category?: string
  filter_parties?: string[]
  filter_people?: string[]
  filter_date_from?: string
  filter_date_to?: string
  filter_themes?: string[]
  filter_is_speech?: boolean
}

export interface PoliticalParty {
  name: string
  full_name?: string
  figures: string[]
  total_articles?: number
  article_count?: number
}

export interface PartiesListResponse {
  parties: PoliticalParty[]
  total_parties: number
}

export interface ArticleSummary {
  id: string
  title: string
  date: string
  source: string
  similarity: number
  summary?: string
  key_points: string[]
  stance_analysis?: string
  keywords: string[]
  key_phrases: string[]
  topics: string[]
  url?: string
}

export interface FigureProfileResponse {
  figure_name: string
  party_name: string
  total_articles: number
  articles: ArticleSummary[]
  summaries_by_date: Record<string, any[]>
}

// Legacy interface for backward compatibility
export interface FigureProfile {
  name: string
  party: string
  article_count: number
  speech_count: number
  recent_articles: Article[]
  top_keywords: string[]
  themes: string[]
  date_range?: {
    earliest: string
    latest: string
  }
}

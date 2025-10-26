import axios, { AxiosError } from 'axios'
import type { SearchRequest, SearchResponse, PartiesListResponse, FigureProfileResponse } from '../types'
import { getAuthHeader } from './auth'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

// Configure axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 0, // No timeout - scraping can take a while
})

// Add auth interceptor to include token in all requests
apiClient.interceptors.request.use(
  (config) => {
    const authHeaders = getAuthHeader()
    if (authHeaders.Authorization) {
      config.headers.Authorization = authHeaders.Authorization
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Add response interceptor to handle 401 errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login page
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Export apiClient for direct use (e.g., in test pages)
export { apiClient }

// Error handler
function handleApiError(error: unknown, context: string): never {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError
    console.error(`${context} failed:`, axiosError.response?.data || axiosError.message)
    throw new Error(
      `${context} failed: ${axiosError.response?.statusText || axiosError.message}`
    )
  }
  console.error(`${context} failed:`, error)
  throw new Error(`${context} failed: ${String(error)}`)
}

// ==================== Existing Functions ====================

export async function searchArticles(request: SearchRequest): Promise<SearchResponse> {
  try {
    const response = await apiClient.post<SearchResponse>('/query', request)
    return response.data
  } catch (error) {
    return handleApiError(error, 'Search')
  }
}

export async function getHealthStatus() {
  try {
    const response = await apiClient.get('/health')
    return response.data
  } catch (error) {
    return handleApiError(error, 'Health check')
  }
}

export async function getStats() {
  try {
    const response = await apiClient.get('/stats')
    return response.data
  } catch (error) {
    return handleApiError(error, 'Stats fetch')
  }
}

// ==================== New Political Functions ====================

/**
 * Fetches the list of political parties and their associated figures
 * 
 * @returns Promise with parties list data
 * @throws Error if the request fails
 * 
 * @example
 * ```typescript
 * const parties = await fetchPoliticalParties()
 * console.log(parties.parties) // Array of political parties
 * ```
 */
export async function fetchPoliticalParties(): Promise<PartiesListResponse> {
  try {
    const response = await apiClient.get<PartiesListResponse>('/parties/')
    return response.data
  } catch (error) {
    return handleApiError(error, 'Fetch political parties')
  }
}

/**
 * Fetches the profile data for a specific political figure
 * 
 * @param partyName - Name of the political party (e.g., "BNP", "NCP")
 * @param figureName - Name of the political figure (e.g., "Tareq Rahman")
 * @param dateFrom - Optional start date for filtering (YYYY-MM-DD format)
 * @param dateTo - Optional end date for filtering (YYYY-MM-DD format)
 * @param speechesOnly - Optional flag to filter only speeches
 * @returns Promise with figure profile data including speeches and keywords
 * @throws Error if the request fails
 * 
 * @example
 * ```typescript
 * const profile = await fetchFigureProfile("BNP", "Tareq Rahman")
 * const filtered = await fetchFigureProfile("BNP", "Tareq Rahman", "2024-01-01", "2024-12-31")
 * ```
 */
export async function fetchFigureProfile(
  partyName: string,
  figureName: string,
  dateFrom?: string,
  dateTo?: string,
  speechesOnly?: boolean
): Promise<FigureProfileResponse> {
  try {
    // URL encode the parameters to handle spaces and special characters
    const encodedParty = encodeURIComponent(partyName)
    const encodedFigure = encodeURIComponent(figureName)
    
    // Build request body
    const requestBody: {
      query: string
      date_from?: string
      date_to?: string
      speeches_only?: boolean
      top_k: number
    } = {
      query: "recent statements",
      top_k: 50
    }
    
    if (dateFrom) requestBody.date_from = dateFrom
    if (dateTo) requestBody.date_to = dateTo
    if (speechesOnly !== undefined) requestBody.speeches_only = speechesOnly
    
    const response = await apiClient.post<FigureProfileResponse>(
      `/party/${encodedParty}/figure/${encodedFigure}/`,
      requestBody
    )
    return response.data
  } catch (error) {
    return handleApiError(error, `Fetch figure profile for ${figureName}`)
  }
}

/**
 * Fetches party profile with statistics and recent articles
 * 
 * @param partyName - Name of the political party
 * @returns Promise with party profile data
 * @throws Error if the request fails
 * 
 * @example
 * ```typescript
 * const party = await fetchPartyProfile("BNP")
 * console.log(party.article_count)
 * ```
 */
export async function fetchPartyProfile(partyName: string) {
  try {
    const encodedParty = encodeURIComponent(partyName)
    const response = await apiClient.get(`/parties/${encodedParty}`)
    return response.data
  } catch (error) {
    return handleApiError(error, `Fetch party profile for ${partyName}`)
  }
}

/**
 * Fetches all political figures across all parties
 * 
 * @returns Promise with list of all figures
 * @throws Error if the request fails
 */
export async function fetchAllFigures() {
  try {
    const response = await apiClient.get('/figures/')
    return response.data
  } catch (error) {
    return handleApiError(error, 'Fetch all figures')
  }
}

// ==================== Scraping Functions ====================

export interface ScrapingRequest {
  start_date: string  // YYYY-MM-DD format
  end_date: string    // YYYY-MM-DD format
  newspapers?: string[]  // Optional, defaults to all newspapers
}

export interface ScrapingResponse {
  status: string
  total_articles_scraped: number
  total_articles_stored: number
  articles_by_source: Record<string, number>
  processing_time: number
  message: string
}

/**
 * Trigger newspaper scraping with date range (NO LLM Analysis)
 * 
 * This will:
 * 1. Scrape articles from newspapers (ProthomAlo, Jugantor, DailyStar, DhakaTribune)
 * 2. Filter only political articles
 * 3. Categorize and extract metadata
 * 4. Generate embeddings
 * 5. Store in ChromaDB
 * 
 * NOTE: NO LLM analysis is performed. Use triggerLLMAnalysis() separately for analysis.
 * 
 * @param startDate - Start date in YYYY-MM-DD format (e.g., "2024-08-05")
 * @param endDate - End date in YYYY-MM-DD format (e.g., "2024-09-05")
 * @param newspapers - Optional array of newspaper names to scrape
 * @returns Promise with scraping statistics
 * @throws Error if the request fails
 * 
 * @example
 * ```typescript
 * // Scrape all newspapers
 * const result = await triggerScraping("2024-08-05", "2024-09-05")
 * 
 * // Scrape specific newspapers only
 * const result = await triggerScraping("2024-08-05", "2024-09-05", ["ProthomAlo", "DailyStar"])
 * 
 * console.log(`Scraped: ${result.total_articles_scraped}`)
 * console.log(`Stored: ${result.total_articles_stored}`)
 * ```
 */
export async function triggerScraping(
  startDate: string,
  endDate: string,
  newspapers?: string[]
): Promise<ScrapingResponse> {
  try {
    const requestData: ScrapingRequest = {
      start_date: startDate,
      end_date: endDate,
      newspapers: newspapers || ["ProthomAlo", "Jugantor", "DailyStar", "DhakaTribune"]
    }
    
    const response = await apiClient.post<ScrapingResponse>('/scraping/newspapers', requestData)
    return response.data
  } catch (error) {
    return handleApiError(error, 'Trigger scraping')
  }
}

// ==================== LLM Analysis Functions ====================

export interface LLMAnalysisRequest {
  party?: string
  figure?: string
  date_from?: string
  date_to?: string
  limit?: number
  language?: string
  include_summary?: boolean
  include_keywords?: boolean
  include_stance?: boolean
}

export interface ArticleAnalysis {
  article_id: string
  title: string
  date?: string
  party?: string
  figures: string[]
  summary?: {
    summary: string
    key_points: string[]
    stance: string
  }
  keywords?: {
    keywords: string[]
    phrases: string[]
    topics: string[]
  }
  stance?: string
}

export interface LLMAnalysisResponse {
  status: string
  total_analyzed: number
  analyses: ArticleAnalysis[]
  processing_time: number
  message: string
}

/**
 * Trigger LLM analysis on stored articles with filters
 * 
 * This will:
 * 1. Query articles from database based on filters
 * 2. Run LLM analysis (summaries, keywords, stance)
 * 3. Return analysis results
 * 
 * @param request - LLM analysis request with filters
 * @returns Promise with analysis results
 * @throws Error if the request fails
 * 
 * @example
 * ```typescript
 * // Analyze BNP articles
 * const result = await triggerLLMAnalysis({
 *   party: "BNP",
 *   date_from: "2024-10-01",
 *   date_to: "2024-10-14",
 *   limit: 10,
 *   language: "Bangla"
 * })
 * 
 * // Analyze specific figure
 * const result = await triggerLLMAnalysis({
 *   figure: "Tareq Rahman",
 *   limit: 20
 * })
 * ```
 */
export async function triggerLLMAnalysis(
  request: LLMAnalysisRequest
): Promise<LLMAnalysisResponse> {
  try {
    const response = await apiClient.post<LLMAnalysisResponse>('/analysis/llm', request)
    return response.data
  } catch (error) {
    return handleApiError(error, 'LLM Analysis')
  }
}

/**
 * Generate comprehensive party report
 * 
 * @param party - Party ID (e.g., "bnp", "ji", "ncp")
 * @param limit - Maximum articles to analyze
 * @param language - Analysis language
 * @returns Promise with party report
 * @throws Error if the request fails
 * 
 * @example
 * ```typescript
 * const report = await generatePartyReport("bnp", 50, "Bangla")
 * console.log(report.top_topics)
 * console.log(report.top_keywords)
 * ```
 */
export async function generatePartyReport(
  party: string,
  limit: number = 50,
  language: string = "Bangla"
) {
  try {
    const response = await apiClient.post('/analysis/party-report', {
      party,
      limit,
      language
    })
    return response.data
  } catch (error) {
    return handleApiError(error, 'Generate party report')
  }
}

/**
 * Generate comprehensive figure report
 * 
 * @param figure - Political figure name
 * @param party - Optional party filter
 * @param limit - Maximum articles to analyze
 * @param language - Analysis language
 * @returns Promise with figure report
 * @throws Error if the request fails
 * 
 * @example
 * ```typescript
 * const report = await generateFigureReport("Tareq Rahman", "bnp", 30)
 * console.log(report.top_topics)
 * ```
 */
export async function generateFigureReport(
  figure: string,
  party?: string,
  limit: number = 50,
  language: string = "Bangla"
) {
  try {
    const params = new URLSearchParams({
      figure,
      limit: limit.toString(),
      language
    })
    if (party) {
      params.append('party', party)
    }
    
    const response = await apiClient.post(`/analysis/figure-report?${params.toString()}`)
    return response.data
  } catch (error) {
    return handleApiError(error, 'Generate figure report')
  }
}

/**
 * Analyze stored articles for a specific political party using Gemini LLM
 * 
 * @param party - Party name (e.g., "BNP", "NCP", "Interim Government")
 * @param startDate - Optional start date filter (YYYY-MM-DD)
 * @param endDate - Optional end date filter (YYYY-MM-DD)
 * @param maxArticles - Maximum articles to analyze (default: 50)
 * @returns Promise with comprehensive party analysis
 * @throws Error if the request fails
 * 
 * @example
 * ```typescript
 * const analysis = await analyzeStoredPartyArticles("BNP")
 * const filtered = await analyzeStoredPartyArticles("BNP", "2024-01-01", "2024-12-31", 30)
 * console.log(analysis.analysis.raw_analysis)
 * ```
 */
export async function analyzeStoredPartyArticles(
  party: string,
  startDate?: string,
  endDate?: string,
  maxArticles: number = 50
) {
  try {
    const response = await apiClient.post('/analysis/party', {
      party,
      start_date: startDate,
      end_date: endDate,
      max_articles: maxArticles
    })
    return response.data
  } catch (error) {
    return handleApiError(error, 'Analyze stored party articles')
  }
}

/**
 * Analyze stored articles for a specific political figure using Gemini LLM
 * 
 * @param figure - Figure name (e.g., "Tareq Rahman", "Dr Yunus")
 * @param party - Optional party filter
 * @param startDate - Optional start date filter (YYYY-MM-DD)
 * @param endDate - Optional end date filter (YYYY-MM-DD)
 * @param maxArticles - Maximum articles to analyze (default: 50)
 * @returns Promise with comprehensive figure analysis
 * @throws Error if the request fails
 * 
 * @example
 * ```typescript
 * const analysis = await analyzeStoredFigureArticles("Tareq Rahman")
 * const filtered = await analyzeStoredFigureArticles("Tareq Rahman", "BNP", "2024-01-01", "2024-12-31")
 * console.log(analysis.analysis.raw_analysis)
 * ```
 */
export async function analyzeStoredFigureArticles(
  figure: string,
  party?: string,
  startDate?: string,
  endDate?: string,
  maxArticles: number = 50
) {
  try {
    const response = await apiClient.post('/analysis/figure', {
      figure,
      party,
      start_date: startDate,
      end_date: endDate,
      max_articles: maxArticles
    })
    return response.data
  } catch (error) {
    return handleApiError(error, 'Analyze stored figure articles')
  }
}

/**
 * Fetch categorization test data to validate article-party-figure associations
 * 
 * @param limit - Number of articles to fetch (default: 50)
 * @returns Promise with articles, party breakdown, and validation data
 * @throws Error if the request fails
 * 
 * @example
 * ```typescript
 * const data = await fetchCategorizationTest(100)
 * console.log(`Total articles: ${data.total_articles}`)
 * console.log(`Issues found: ${data.issues_count}`)
 * ```
 */
export async function fetchCategorizationTest(limit: number = 50) {
  try {
    const response = await apiClient.get(`/parties/categorization-test?limit=${limit}`)
    return response.data
  } catch (error) {
    return handleApiError(error, 'Fetch categorization test data')
  }
}

/**
 * Generate period summary for a party or figure with date range
 * 
 * @param entityType - "party" or "figure"
 * @param entityName - Name of party or figure
 * @param startDate - Start date in YYYY-MM-DD format
 * @param endDate - End date in YYYY-MM-DD format
 * @param maxArticles - Maximum articles to analyze (default: 100)
 * @returns Promise with period summary including meta-summary and individual summaries
 * 
 * @example
 * ```typescript
 * const summary = await generatePeriodSummary("party", "BNP", "2025-10-01", "2025-10-21")
 * console.log(summary.period_summary)
 * console.log(`Analyzed ${summary.statistics.total_articles} articles`)
 * ```
 */
export async function generatePeriodSummary(
  entityType: 'party' | 'figure',
  entityName: string,
  startDate: string,
  endDate: string,
  maxArticles: number = 100
) {
  try {
    const response = await apiClient.post('/analysis/summary/period', {
      entity_type: entityType,
      entity_name: entityName,
      start_date: startDate,
      end_date: endDate,
      max_articles: maxArticles
    })
    return response.data
  } catch (error) {
    return handleApiError(error, `Generate period summary for ${entityName}`)
  }
}

/**
 * Get all stored period summaries for an entity
 * 
 * @param entityType - Type of entity ("party" or "figure")
 * @param entityName - Name of the party or figure
 * @returns Promise with all period summaries for the entity
 */
export async function getPeriodSummaries(
  entityType: 'party' | 'figure',
  entityName: string
) {
  try {
    const response = await apiClient.get(`/analysis/summary/period/${entityType}/${entityName}`)
    return response.data
  } catch (error) {
    return handleApiError(error, `Get period summaries for ${entityName}`)
  }
}


import axios, { AxiosError } from 'axios'
import type { SearchRequest, SearchResponse, PartiesListResponse, FigureProfileResponse } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

// Configure axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 0, // No timeout - scraping can take a while
})

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
  enable_llm_analysis?: boolean  // Optional, defaults to false (LLM is slow!)
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
 * Trigger newspaper scraping with date range
 * 
 * This will:
 * 1. Scrape articles from newspapers (ProthomAlo, Jugantor, DailyStar, DhakaTribune)
 * 2. Filter only political articles
 * 3. Categorize and extract metadata
 * 4. Generate embeddings
 * 5. Perform LLM analysis (summaries, keywords, stance)
 * 6. Automatically store in ChromaDB
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
  newspapers?: string[],
  enableLlmAnalysis: boolean = true
): Promise<ScrapingResponse> {
  try {
    const requestData: ScrapingRequest = {
      start_date: startDate,
      end_date: endDate,
      newspapers: newspapers || ["ProthomAlo", "Jugantor", "DailyStar", "DhakaTribune"],
      enable_llm_analysis: enableLlmAnalysis
    }
    
    const response = await apiClient.post<ScrapingResponse>('/scrape', requestData)
    return response.data
  } catch (error) {
    return handleApiError(error, 'Trigger scraping')
  }
}

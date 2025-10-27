import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { triggerScraping, type ScrapingResponse } from '../utils/api'
import { LogOut } from 'lucide-react'
import { logout, getEmail } from '../utils/auth'

export default function NewspaperScraper() {
  const navigate = useNavigate()
  const email = getEmail()
  
  const handleLogout = () => {
    logout()
    navigate('/login')
  }
  
  // Calculate default date range: last 30 days
  const today = new Date()
  const thirtyDaysAgo = new Date(today)
  thirtyDaysAgo.setDate(today.getDate() - 30)
  
  const formatDate = (date: Date) => {
    return date.toISOString().split('T')[0]
  }
  
  const [startDate, setStartDate] = useState(formatDate(thirtyDaysAgo))
  const [endDate, setEndDate] = useState(formatDate(today))
  const [selectedNewspapers, setSelectedNewspapers] = useState<string[]>([
    'ProthomAlo',
    'Jugantor',
    'DailyStar',
    'DhakaTribune'
  ])
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<ScrapingResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const newspapers = [
    { id: 'ProthomAlo', name: 'Prothom Alo', lang: 'Bangla', color: 'bg-blue-100 text-blue-800' },
    { id: 'Jugantor', name: 'Jugantor', lang: 'Bangla', color: 'bg-green-100 text-green-800' },
    { id: 'DailyStar', name: 'Daily Star', lang: 'English', color: 'bg-purple-100 text-purple-800' },
    { id: 'DhakaTribune', name: 'Dhaka Tribune', lang: 'English', color: 'bg-orange-100 text-orange-800' }
  ]

  const handleToggleNewspaper = (newspaperId: string) => {
    setSelectedNewspapers(prev =>
      prev.includes(newspaperId)
        ? prev.filter(id => id !== newspaperId)
        : [...prev, newspaperId]
    )
  }

  const handleScrape = async () => {
    if (!startDate || !endDate) {
      setError('Please provide both start and end dates')
      return
    }

    if (new Date(startDate) > new Date(endDate)) {
      setError('Start date must be before end date')
      return
    }

    if (selectedNewspapers.length === 0) {
      setError('Please select at least one newspaper')
      return
    }

    setIsLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await triggerScraping(startDate, endDate, selectedNewspapers)
      setResult(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Scraping failed')
    } finally {
      setIsLoading(false)
    }
  }

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = (seconds % 60).toFixed(0)
    return `${minutes}m ${remainingSeconds}s`
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="bg-white rounded-lg shadow-lg p-6">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              📰 Newspaper Scraper
            </h2>
            <p className="text-gray-600">
              Scrape political articles from Bangladeshi newspapers
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-600 font-medium">
              {email}
            </span>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition duration-200 font-medium"
            >
              <LogOut size={18} />
              Logout
            </button>
          </div>
        </div>

        {/* Date Range Selection */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Date Range</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Start Date
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                disabled={isLoading}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                End Date
              </label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                disabled={isLoading}
              />
            </div>
          </div>
        </div>

        {/* Newspaper Selection */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-3">
            Select Newspapers
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {newspapers.map((newspaper) => (
              <label
                key={newspaper.id}
                className={`flex items-center p-4 border-2 rounded-lg cursor-pointer transition-all ${
                  selectedNewspapers.includes(newspaper.id)
                    ? 'border-indigo-500 bg-indigo-50'
                    : 'border-gray-200 hover:border-gray-300'
                } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <input
                  type="checkbox"
                  checked={selectedNewspapers.includes(newspaper.id)}
                  onChange={() => handleToggleNewspaper(newspaper.id)}
                  disabled={isLoading}
                  className="w-5 h-5 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                />
                <div className="ml-3 flex-1">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-gray-900">
                      {newspaper.name}
                    </span>
                    <span className={`text-xs px-2 py-1 rounded-full ${newspaper.color}`}>
                      {newspaper.lang}
                    </span>
                  </div>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Action Button */}
        <div className="mb-6">
          <button
            onClick={handleScrape}
            disabled={isLoading || selectedNewspapers.length === 0}
            className={`w-full py-3 px-6 rounded-lg font-semibold text-white transition-all ${
              isLoading || selectedNewspapers.length === 0
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-indigo-600 hover:bg-indigo-700 active:scale-95'
            }`}
          >
            {isLoading ? (
              <span className="flex items-center justify-center cursor-pointer">
                <svg
                  className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Scraping in progress...
              </span>
            ) : (
              <div className='cursor-pointer'>
                🚀 Start Scraping
              </div>
            )}
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 rounded">
            <div className="flex items-start">
              <span className="text-red-600 mr-2">❌</span>
              <p className="text-red-700">{error}</p>
            </div>
          </div>
        )}

        {/* Result Display */}
        {result && (
          <div className="space-y-4">
            {/* Success Message */}
            <div className="p-4 bg-green-50 border-l-4 border-green-500 rounded">
              <div className="flex items-start">
                <span className="text-green-600 mr-2 text-xl">✅</span>
                <div className="flex-1">
                  <p className="font-semibold text-green-900">
                    {result.status === 'completed' ? 'Scraping Completed!' : result.status}
                  </p>
                  <p className="text-sm text-green-700 mt-1">{result.message}</p>
                </div>
              </div>
            </div>

            {/* Statistics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                <div className="text-blue-600 text-sm font-medium mb-1">
                  Articles Scraped
                </div>
                <div className="text-3xl font-bold text-blue-900">
                  {result.total_articles_scraped}
                </div>
              </div>

              <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                <div className="text-green-600 text-sm font-medium mb-1">
                  Articles Stored
                </div>
                <div className="text-3xl font-bold text-green-900">
                  {result.total_articles_stored}
                </div>
              </div>

              <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
                <div className="text-purple-600 text-sm font-medium mb-1">
                  Processing Time
                </div>
                <div className="text-3xl font-bold text-purple-900">
                  {formatTime(result.processing_time)}
                </div>
              </div>
            </div>

            {/* Breakdown by Source */}
            {Object.keys(result.articles_by_source).length > 0 && (
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-900 mb-3">
                  Articles by Newspaper
                </h4>
                <div className="space-y-2">
                  {Object.entries(result.articles_by_source).map(([source, count]) => {
                    const newspaper = newspapers.find(n => n.id === source)
                    return (
                      <div
                        key={source}
                        className="flex items-center justify-between py-2 px-3 bg-white rounded border border-gray-200"
                      >
                        <div className="flex items-center">
                          <span className="font-medium text-gray-900">
                            {newspaper?.name || source}
                          </span>
                          {newspaper && (
                            <span className={`ml-2 text-xs px-2 py-1 rounded-full ${newspaper.color}`}>
                              {newspaper.lang}
                            </span>
                          )}
                        </div>
                        <span className="text-lg font-bold text-indigo-600">
                          {count}
                        </span>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {/* Info Note */}
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-sm text-blue-900">
                <span className="font-semibold">ℹ️ Note:</span> All scraped articles have been
                categorized, embedded, analyzed with LLM, and stored in the vector database.
                You can now browse them in the Political Party List.
              </p>
            </div>
          </div>
        )}

        {/* Pipeline Info */}
        <div className="mt-8 pt-6 border-t border-gray-200">
          <h4 className="font-semibold text-gray-900 mb-3">
            🔄 Automated Pipeline
          </h4>
          <div className="space-y-2 text-sm text-gray-600">
            <div className="flex items-start">
              <span className="mr-2">1️⃣</span>
              <span>Scrape articles from selected newspapers</span>
            </div>
            <div className="flex items-start">
              <span className="mr-2">2️⃣</span>
              <span>Categorize themes & extract keywords (TF-IDF)</span>
            </div>
            <div className="flex items-start">
              <span className="mr-2">3️⃣</span>
              <span>Generate 384-dim embeddings (Sentence-BERT)</span>
            </div>
            <div className="flex items-start">
              <span className="mr-2">4️⃣</span>
              <span>LLM analysis (speech summaries, keywords, stance)</span>
            </div>
            <div className="flex items-start">
              <span className="mr-2">5️⃣</span>
              <span>Store in ChromaDB with full metadata</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

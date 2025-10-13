import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { fetchFigureProfile } from '../utils/api'
import type { FigureProfileResponse } from '../types'

export default function FigureProfile() {
  const { partyName, figureName } = useParams<{ partyName: string; figureName: string }>()
  const navigate = useNavigate()
  
  const [profile, setProfile] = useState<FigureProfileResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Date filter state
  const [dateFrom, setDateFrom] = useState<string>('')
  const [dateTo, setDateTo] = useState<string>('')
  const [speechesOnly, setSpeechesOnly] = useState<boolean>(false)
  const [isFiltering, setIsFiltering] = useState(false)

  const loadProfile = async (from?: string, to?: string, speechOnly?: boolean) => {
    if (!partyName || !figureName) {
      setError('Missing party or figure name')
      setLoading(false)
      return
    }

    setIsFiltering(true)
    setError(null)

    try {
      const response = await fetchFigureProfile(partyName, figureName, from, to, speechOnly)
      setProfile(response)
    } catch (err) {
      setError(`Failed to load profile: ${err}`)
      console.error('Error loading figure profile:', err)
    } finally {
      setLoading(false)
      setIsFiltering(false)
    }
  }

  useEffect(() => {
    setLoading(true)
    loadProfile()
  }, [partyName, figureName])

  const handleApplyFilter = () => {
    loadProfile(dateFrom || undefined, dateTo || undefined, speechesOnly)
  }

  const handleResetFilter = () => {
    setDateFrom('')
    setDateTo('')
    setSpeechesOnly(false)
    loadProfile()
  }

  // Get speech count
  const speechCount = profile ? profile.articles.filter(a => a.keywords.some(k => k.toLowerCase().includes('speech'))).length : 0
  
  // Get unique keywords
  const allKeywords = profile ? Array.from(new Set(profile.articles.flatMap(a => a.keywords))).slice(0, 20) : []
  
  // Get unique topics
  const allTopics = profile ? Array.from(new Set(profile.articles.flatMap(a => a.topics))).slice(0, 10) : []

  // Get date range
  const dateRange = profile && profile.articles.length > 0 ? {
    earliest: profile.articles[profile.articles.length - 1].date,
    latest: profile.articles[0].date
  } : null

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 py-12 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col items-center justify-center py-20">
            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mb-4"></div>
            <p className="text-xl text-gray-600">Loading profile data...</p>
            <p className="text-sm text-gray-500 mt-2">
              Fetching information for {figureName}
            </p>
          </div>
        </div>
      </div>
    )
  }

  // Error state
  if (error || !profile) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 py-12 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="bg-red-50 border-2 border-red-200 rounded-xl p-8 text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-4">
              <svg className="h-8 w-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-red-800 mb-2">Failed to Load Profile</h3>
            <p className="text-red-600 mb-6">{error || 'Profile data not available'}</p>
            <div className="flex gap-4 justify-center">
              <button
                onClick={() => window.location.reload()}
                className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Try Again
              </button>
              <button
                onClick={() => navigate('/')}
                className="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                Go Back
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Success state - Display profile
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 py-12 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Back Button */}
        <button
          onClick={() => navigate(-1)}
          className="mb-6 flex items-center gap-2 text-gray-600 hover:text-blue-600 transition-colors"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          <span className="font-medium">Back to Parties</span>
        </button>

        {/* Profile Header */}
        <div className="bg-white rounded-xl shadow-lg overflow-hidden mb-8">
          <div className="bg-gradient-to-r from-blue-600 to-blue-800 px-8 py-12">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-6">
                {/* Avatar */}
                <div className="w-24 h-24 bg-white rounded-full flex items-center justify-center shadow-xl">
                  <span className="text-4xl font-bold text-blue-600">
                    {profile.figure_name.charAt(0)}
                  </span>
                </div>
                
                {/* Name and Party */}
                <div className="text-white">
                  <h1 className="text-4xl font-bold mb-2">{profile.figure_name}</h1>
                  <div className="flex items-center gap-2">
                    <span className="px-3 py-1 bg-white/20 backdrop-blur-sm rounded-full text-sm font-medium">
                      {profile.party_name}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-6 bg-gray-50">
            <div className="bg-white p-4 rounded-lg text-center shadow-sm">
              <div className="text-3xl font-bold text-blue-600">{profile.total_articles}</div>
              <div className="text-sm text-gray-600 mt-1">Total Articles</div>
            </div>
            <div className="bg-white p-4 rounded-lg text-center shadow-sm">
              <div className="text-3xl font-bold text-green-600">{speechCount}</div>
              <div className="text-sm text-gray-600 mt-1">Speeches</div>
            </div>
            <div className="bg-white p-4 rounded-lg text-center shadow-sm">
              <div className="text-3xl font-bold text-purple-600">{allTopics.length}</div>
              <div className="text-sm text-gray-600 mt-1">Topics</div>
            </div>
            <div className="bg-white p-4 rounded-lg text-center shadow-sm">
              <div className="text-3xl font-bold text-orange-600">{allKeywords.length}</div>
              <div className="text-sm text-gray-600 mt-1">Keywords</div>
            </div>
          </div>
        </div>

        {/* Date Range Filter */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
            <svg className="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
            </svg>
            Filter Articles by Date
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                From Date
              </label>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                To Date
              </label>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            
            <div className="flex items-end">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={speechesOnly}
                  onChange={(e) => setSpeechesOnly(e.target.checked)}
                  className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-gray-700">Speeches Only</span>
              </label>
            </div>
          </div>
          
          <div className="flex gap-3">
            <button
              onClick={handleApplyFilter}
              disabled={isFiltering}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isFiltering ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Filtering...</span>
                </>
              ) : (
                <>
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                  </svg>
                  <span>Apply Filter</span>
                </>
              )}
            </button>
            
            <button
              onClick={handleResetFilter}
              disabled={isFiltering}
              className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              Reset
            </button>
          </div>
          
          {(dateFrom || dateTo || speechesOnly) && !isFiltering && (
            <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-800">
                <strong>Active Filters:</strong>
                {dateFrom && ` From ${new Date(dateFrom).toLocaleDateString()}`}
                {dateTo && ` To ${new Date(dateTo).toLocaleDateString()}`}
                {speechesOnly && ` • Speeches Only`}
              </p>
            </div>
          )}
        </div>

        {/* Date Range Display */}
        {dateRange && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
            <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
              <svg className="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              Coverage Period
            </h2>
            <div className="flex items-center gap-6 text-gray-700">
              <div>
                <span className="text-sm text-gray-500">From:</span>
                <span className="ml-2 font-semibold">{new Date(dateRange.earliest).toLocaleDateString()}</span>
              </div>
              <div className="text-gray-300">→</div>
              <div>
                <span className="text-sm text-gray-500">To:</span>
                <span className="ml-2 font-semibold">{new Date(dateRange.latest).toLocaleDateString()}</span>
              </div>
            </div>
          </div>
        )}

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Keywords and Topics */}
          <div className="lg:col-span-1 space-y-6">
            {/* Top Keywords */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                <svg className="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                </svg>
                Top Keywords
              </h2>
              {allKeywords.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {allKeywords.map((keyword, index) => (
                    <span
                      key={index}
                      className="px-3 py-1.5 bg-blue-50 text-blue-700 rounded-full text-sm font-medium border border-blue-200 hover:bg-blue-100 transition-colors"
                    >
                      {keyword}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-sm">No keywords available</p>
              )}
            </div>

            {/* Topics */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                <svg className="h-6 w-6 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
                Topics Covered
              </h2>
              {allTopics.length > 0 ? (
                <div className="space-y-2">
                  {allTopics.map((topic, index) => (
                    <div
                      key={index}
                      className="flex items-center gap-3 p-3 bg-purple-50 rounded-lg border border-purple-100 hover:bg-purple-100 transition-colors"
                    >
                      <div className="w-2 h-2 bg-purple-600 rounded-full"></div>
                      <span className="text-gray-800 font-medium">{topic}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-sm">No topics available</p>
              )}
            </div>
          </div>

          {/* Right Column - Articles */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-xl font-bold text-gray-800 mb-6 flex items-center gap-2">
                <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
                </svg>
                Articles & Speeches
                <span className="ml-auto text-sm font-normal text-gray-500">
                  {profile.articles.length} items
                </span>
              </h2>

              {profile.articles.length > 0 ? (
                <div className="space-y-4 max-h-[800px] overflow-y-auto pr-2">
                  {profile.articles.map((article, index) => (
                    <div
                      key={article.id || index}
                      className="border border-gray-200 rounded-lg p-5 hover:shadow-md hover:border-blue-300 transition-all"
                    >
                      {/* Article Header */}
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <h3 className="font-bold text-gray-900 text-lg mb-2 line-clamp-2">
                            {article.title}
                          </h3>
                          <div className="flex flex-wrap gap-3 text-sm text-gray-600">
                            <span className="flex items-center gap-1">
                              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                              </svg>
                              {new Date(article.date).toLocaleDateString()}
                            </span>
                            <span className="flex items-center gap-1">
                              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
                              </svg>
                              {article.source}
                            </span>
                            <span className="flex items-center gap-1 text-blue-600">
                              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                              </svg>
                              {(article.similarity * 100).toFixed(1)}% match
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Article Summary */}
                      {article.summary && (
                        <div className="mb-3 p-3 bg-gray-50 rounded-lg">
                          <p className="text-gray-700 leading-relaxed text-sm">
                            {article.summary}
                          </p>
                        </div>
                      )}

                      {/* Key Points */}
                      {article.key_points && article.key_points.length > 0 && (
                        <div className="mb-3">
                          <h4 className="text-sm font-semibold text-gray-700 mb-2">Key Points:</h4>
                          <ul className="list-disc list-inside space-y-1">
                            {article.key_points.map((point, idx) => (
                              <li key={idx} className="text-sm text-gray-600">{point}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Stance Analysis */}
                      {article.stance_analysis && (
                        <div className="mb-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                          <h4 className="text-sm font-semibold text-yellow-800 mb-1">Stance Analysis:</h4>
                          <p className="text-sm text-yellow-700">{article.stance_analysis}</p>
                        </div>
                      )}

                      {/* Tags */}
                      <div className="flex flex-wrap gap-2 mt-3">
                        {article.topics.map((topic, idx) => (
                          <span key={idx} className="px-2 py-1 bg-purple-50 text-purple-700 rounded text-xs">
                            {topic}
                          </span>
                        ))}
                        {article.keywords.slice(0, 5).map((keyword, idx) => (
                          <span key={idx} className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs">
                            {keyword}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <svg className="h-16 w-16 text-gray-300 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <p className="text-gray-500 text-lg">No articles found</p>
                  <p className="text-gray-400 text-sm mt-2">Try adjusting your filters</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

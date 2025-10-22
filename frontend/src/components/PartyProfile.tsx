import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import type { FigureProfileResponse } from '../types'
import { AnalysisButton } from './AnalysisButton'

export default function PartyProfile() {
  const { partyName } = useParams<{ partyName: string }>()
  const navigate = useNavigate()
  
  const [profile, setProfile] = useState<FigureProfileResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Date filter state
  const [dateFrom, setDateFrom] = useState<string>('')
  const [dateTo, setDateTo] = useState<string>('')
  const [isFiltering, setIsFiltering] = useState(false)
  
  // Expanded articles state
  const [expandedArticles, setExpandedArticles] = useState<Set<string>>(new Set())
  const [loadingFullArticle, setLoadingFullArticle] = useState<string | null>(null)
  const [fullArticles, setFullArticles] = useState<Map<string, string>>(new Map())
  
  // Summarization state
  const [summarizingArticles, setSummarizingArticles] = useState<Set<string>>(new Set())

  const loadProfile = async (from?: string, to?: string) => {
    if (!partyName) {
      setError('Missing party name')
      setLoading(false)
      return
    }

    setIsFiltering(true)
    setError(null)

    try {
      const response = await fetch(`http://localhost:8000/api/v1/parties/${encodeURIComponent(partyName)}/profile`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          date_from: from,
          date_to: to
        })
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      setProfile(data)
    } catch (err) {
      setError(`Failed to load profile: ${err}`)
      console.error('Error loading party profile:', err)
    } finally {
      setLoading(false)
      setIsFiltering(false)
    }
  }

  useEffect(() => {
    setLoading(true)
    loadProfile()
  }, [partyName])

  const handleApplyFilter = () => {
    loadProfile(dateFrom || undefined, dateTo || undefined)
  }

  const handleResetFilter = () => {
    setDateFrom('')
    setDateTo('')
    loadProfile()
  }
  
  // Toggle article expansion and fetch full content if needed
  const toggleArticle = async (articleId: string) => {
    if (expandedArticles.has(articleId)) {
      // Collapse
      const newExpanded = new Set(expandedArticles)
      newExpanded.delete(articleId)
      setExpandedArticles(newExpanded)
    } else {
      // Expand - fetch full content if not already loaded
      const newExpanded = new Set(expandedArticles)
      newExpanded.add(articleId)
      setExpandedArticles(newExpanded)
      
      if (!fullArticles.has(articleId)) {
        setLoadingFullArticle(articleId)
        try {
          const response = await fetch(`http://localhost:8000/api/v1/article/${articleId}/full`)
          if (response.ok) {
            const data = await response.json()
            const newFullArticles = new Map(fullArticles)
            newFullArticles.set(articleId, data.content)
            setFullArticles(newFullArticles)
          }
        } catch (err) {
          console.error('Failed to load full article:', err)
        } finally {
          setLoadingFullArticle(null)
        }
      }
    }
  }
  
  // Generate summary for an article using LLM
  const handleGenerateSummary = async (articleId: string) => {
    setSummarizingArticles(prev => new Set(prev).add(articleId))
    
    try {
      const response = await fetch(`http://localhost:8000/api/v1/articles/${articleId}/summarize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error('Failed to generate summary')
      }

      const data = await response.json()
      
      // Store the full generated summary in fullArticles so "See More" shows it
      const newFullArticles = new Map(fullArticles)
      newFullArticles.set(articleId, data.summary)
      setFullArticles(newFullArticles)
      
      // Update the profile articles with the generated summary
      if (profile) {
        const updatedArticles = profile.articles.map(article =>
          article.id === articleId
            ? { ...article, summary: data.summary }
            : article
        )
        setProfile({ ...profile, articles: updatedArticles })
      }
    } catch (err) {
      console.error('Error generating summary:', err)
      alert('Failed to generate summary. Please try again.')
    } finally {
      setSummarizingArticles(prev => {
        const newSet = new Set(prev)
        newSet.delete(articleId)
        return newSet
      })
    }
  }
  
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
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-50 py-12 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col items-center justify-center py-20">
            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-green-600 mb-4"></div>
            <p className="text-xl text-gray-600">Loading party profile...</p>
            <p className="text-sm text-gray-500 mt-2">
              Fetching information for {partyName}
            </p>
          </div>
        </div>
      </div>
    )
  }

  // Error state
  if (error || !profile) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-50 py-12 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="bg-red-50 border-2 border-red-200 rounded-xl p-8 text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-4">
              <svg className="h-8 w-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-red-800 mb-2">Failed to Load Profile</h2>
            <p className="text-red-600 mb-6">{error}</p>
            <div className="flex gap-3 justify-center">
              <button
                onClick={() => loadProfile()}
                className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Try Again
              </button>
              <Link
                to="/parties"
                className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Back to Parties
              </Link>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-50">
      {/* Header with Navigation */}
      <div className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/parties')}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <svg className="h-6 w-6 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{profile.figure_name}</h1>
                <p className="text-sm text-gray-500">Party Profile</p>
              </div>
            </div>
            
            <AnalysisButton type="party" name={partyName || ''} />
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
                </svg>
              </div>
              <div>
                <p className="text-3xl font-bold text-gray-900">{profile.total_articles}</p>
                <p className="text-sm text-gray-500">Total Articles</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                </svg>
              </div>
              <div>
                <p className="text-3xl font-bold text-gray-900">{allKeywords.length}</p>
                <p className="text-sm text-gray-500">Keywords</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                <svg className="h-6 w-6 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <div>
                <p className="text-3xl font-bold text-gray-900">{Object.keys(profile.summaries_by_date).length}</p>
                <p className="text-sm text-gray-500">Days Covered</p>
              </div>
            </div>
          </div>
        </div>

        {/* Key Figures Section */}
        {profile.figures && profile.figures.length > 0 && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
            <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
              <svg className="h-6 w-6 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              Key Figures ({profile.figures.length})
            </h2>
            
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 max-h-64 overflow-y-auto">
              {profile.figures.map((figure, index) => (
                <button
                  key={index}
                  onClick={() => navigate(`/figure/${encodeURIComponent(partyName || '')}/${encodeURIComponent(figure)}`)}
                  className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:border-blue-400 hover:bg-blue-50 transition-all group text-left"
                >
                  <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-gray-700 font-semibold group-hover:bg-blue-100 group-hover:text-blue-600 transition-colors flex-shrink-0">
                    {figure.charAt(0).toUpperCase()}
                  </div>
                  <span className="font-medium text-gray-800 group-hover:text-blue-600 transition-colors text-sm truncate">
                    {figure}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* AI Summary Section */}
        {profile.ai_summary && (
          <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl shadow-lg p-6 mb-8 border border-indigo-100">
            <div className="flex items-start justify-between mb-4">
              <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                <svg className="h-7 w-7 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                AI-Generated Summary
              </h2>
              {profile.last_analyzed && (
                <span className="text-xs text-gray-500 bg-white px-3 py-1 rounded-full shadow-sm">
                  Last updated: {new Date(profile.last_analyzed).toLocaleDateString()}
                </span>
              )}
            </div>

            {/* AI Summary Text */}
            <div className="mb-6 prose prose-sm max-w-none">
              <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                {profile.ai_summary}
              </p>
            </div>

            {/* AI Keywords */}
            {profile.ai_keywords && profile.ai_keywords.length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                  <svg className="h-4 w-4 text-indigo-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M17.707 9.293a1 1 0 010 1.414l-7 7a1 1 0 01-1.414 0l-7-7A.997.997 0 012 10V5a3 3 0 013-3h5c.256 0 .512.098.707.293l7 7zM5 6a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                  </svg>
                  Top Keywords
                </h3>
                <div className="flex flex-wrap gap-2">
                  {profile.ai_keywords.map((keyword, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-indigo-100 text-indigo-800 border border-indigo-200 shadow-sm"
                    >
                      {keyword}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* AI Topics */}
            {profile.ai_topics && profile.ai_topics.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                  <svg className="h-4 w-4 text-purple-500" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M2 6a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zM14.553 7.106A1 1 0 0014 8v4a1 1 0 00.553.894l2 1A1 1 0 0018 13V7a1 1 0 00-1.447-.894l-2 1z" />
                  </svg>
                  Topics Covered
                </h3>
                <div className="flex flex-wrap gap-2">
                  {profile.ai_topics.map((topic, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800 border border-purple-200 shadow-sm"
                    >
                      {topic}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Date Filter */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
            <svg className="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
            </svg>
            Filter Articles by Date
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
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
          </div>
          
          <div className="flex gap-3">
            <button
              onClick={handleApplyFilter}
              disabled={isFiltering}
              className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
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
          
          {(dateFrom || dateTo) && !isFiltering && (
            <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-800">
                <strong>Active Filters:</strong>
                {dateFrom && ` From ${new Date(dateFrom).toLocaleDateString()}`}
                {dateTo && ` To ${new Date(dateTo).toLocaleDateString()}`}
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
                Articles & News
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
                          {article.url ? (
                            <a 
                              href={article.url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="font-bold text-gray-900 text-lg mb-2 line-clamp-2 hover:text-green-600 transition-colors cursor-pointer block"
                            >
                              {article.title}
                              <svg className="inline-block w-4 h-4 ml-1 mb-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                              </svg>
                            </a>
                          ) : (
                            <h3 className="font-bold text-gray-900 text-lg mb-2 line-clamp-2">
                              {article.title}
                            </h3>
                          )}
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
                          </div>
                        </div>
                      </div>

                      {/* Article Summary */}
                      {article.summary && (
                        <div className="mb-3">
                          <div className="p-3 bg-gray-50 rounded-lg">
                            <p className="text-gray-700 leading-relaxed text-sm">
                              {expandedArticles.has(article.id)
                                ? (fullArticles.get(article.id) || article.summary)
                                : article.summary}
                            </p>
                          </div>
                          
                          {/* See More / See Less Button */}
                          {article.summary.length >= 280 && (
                            <button
                              onClick={() => toggleArticle(article.id)}
                              disabled={loadingFullArticle === article.id}
                              className="mt-2 text-sm text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1 transition-colors disabled:text-gray-400"
                            >
                              {loadingFullArticle === article.id ? (
                                <>
                                  <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-600"></div>
                                  <span>Loading...</span>
                                </>
                              ) : expandedArticles.has(article.id) ? (
                                <>
                                  <span>See Less</span>
                                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                                  </svg>
                                </>
                              ) : (
                                <>
                                  <span>See More</span>
                                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                  </svg>
                                </>
                              )}
                            </button>
                          )}
                        </div>
                      )}
                      
                      {/* Generate Summary Button */}
                      <div className="flex justify-end pt-3 mt-3 border-t border-gray-100">
                        <button
                          onClick={() => handleGenerateSummary(article.id)}
                          disabled={summarizingArticles.has(article.id)}
                          className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-green-600 hover:text-green-700 hover:bg-green-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {summarizingArticles.has(article.id) ? (
                            <>
                              <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-green-600"></div>
                              <span>Generating...</span>
                            </>
                          ) : (
                            <>
                              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                              </svg>
                              <span>Generate Summary</span>
                            </>
                          )}
                        </button>
                      </div>

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

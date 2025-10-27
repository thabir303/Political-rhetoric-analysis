import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { fetchFigureProfile, getPeriodSummaries } from '../utils/api'
import type { FigureProfileResponse } from '../types'
import { AnalysisButton } from './AnalysisButton'
import { formatDateToDDMMYYYY } from '../utils/dateFormat'
import { getAuthHeader } from '../utils/auth'

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
  
  // Expanded articles state
  const [expandedArticles, setExpandedArticles] = useState<Set<string>>(new Set())
  const [loadingFullArticle, setLoadingFullArticle] = useState<string | null>(null)
  const [fullArticles, setFullArticles] = useState<Map<string, string>>(new Map())
  
  // Summarization state
  const [summarizingArticles, setSummarizingArticles] = useState<Set<string>>(new Set())
  
  // Period summary state (for newly generated summary from AnalysisButton)
  const [_periodSummary, setPeriodSummary] = useState<{
    summary: string
    key_points: string[]
    keywords: string[]
    topics: string[]
    date_range: { start: string, end: string }
  } | null>(null)
  
  // All period summaries state (loaded from storage)
  const [allPeriodSummaries, setAllPeriodSummaries] = useState<Array<{
    summary: string
    key_points: string[]
    keywords: string[]
    topics: string[]
    date_range: { start: string, end: string }
    last_updated?: string
  }>>([])
  const [_loadingPeriodSummaries, setLoadingPeriodSummaries] = useState(false)

  // Load all period summaries for this figure
  const loadPeriodSummaries = async () => {
    if (!figureName) return
    
    setLoadingPeriodSummaries(true)
    try {
      const response = await getPeriodSummaries('figure', figureName)
      if (response.success && response.period_summaries) {
        setAllPeriodSummaries(response.period_summaries)
      }
    } catch (error) {
      console.error('Failed to load period summaries:', error)
    } finally {
      setLoadingPeriodSummaries(false)
    }
  }

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
    loadPeriodSummaries()
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
          const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
          const authHeaders = getAuthHeader()
          const response = await fetch(`${API_BASE_URL}/article/${articleId}/full`, {
            headers: authHeaders,
          })
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
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
      const authHeaders = getAuthHeader()
      const response = await fetch(`${API_BASE_URL}/articles/${articleId}/summarize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to generate summary')
      }

      const data = await response.json()
      
      // Store the full generated summary and LLM data
      const newFullArticles = new Map(fullArticles)
      newFullArticles.set(articleId, data.summary)
      setFullArticles(newFullArticles)
      
      // Update the profile articles with ALL LLM-generated data
      if (profile) {
        const updatedArticles = profile.articles.map(article =>
          article.id === articleId
            ? { 
                ...article, 
                summary: data.summary,
                key_points: data.key_points || [],
                keywords: data.keywords || [],
                topics: data.topics || [],
                stance_analysis: data.stance_analysis || ''
              }
            : article
        )
        setProfile({ ...profile, articles: updatedArticles })
      }
      
      console.log('Summary generated with keywords:', data.keywords)
      console.log('Topics:', data.topics)
      console.log('Stance analysis:', data.stance_analysis)
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
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-violet-50 py-12 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col items-center justify-center py-20">
            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-purple-600 mb-4"></div>
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
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-violet-50 py-12 px-4">
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
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-violet-50 py-12 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Back Button */}
        <button
          onClick={() => navigate(-1)}
          className="mb-6 flex items-center gap-2 text-gray-600 hover:text-purple-600 transition-colors"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          <span className="font-medium">Back to Parties</span>
        </button>

        {/* Profile Header */}
        <div className="bg-white rounded-xl shadow-lg overflow-hidden mb-8">
          <div className="bg-gradient-to-r from-purple-600 to-violet-700 px-8 py-12">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-6">
                {/* Avatar */}
                <div className="w-24 h-24 bg-white rounded-full flex items-center justify-center shadow-xl">
                  <span className="text-4xl font-bold text-purple-600">
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
              
              {/* Analysis Button */}
              <div className="mt-2">
                <AnalysisButton
                  type="figure"
                  name={profile.figure_name}
                  party={profile.party_name}
                  className="bg-white/10 hover:bg-white/20 border-white/30"
                  onAnalysisComplete={(result) => {
                    // Store period summary data
                    if (result.success) {
                      setPeriodSummary({
                        summary: result.analysis.raw_analysis,
                        key_points: result.key_points || [],
                        keywords: result.keywords || [],
                        topics: result.topics || [],
                        date_range: {
                          start: result.date_range.earliest,
                          end: result.date_range.latest
                        }
                      })
                      
                      // Reload profile to get updated article summaries
                      console.log('Analysis complete - reloading profile to show updated summaries...')
                      loadProfile(dateFrom, dateTo, speechesOnly)
                      
                      // Reload period summaries to include the new one
                      loadPeriodSummaries()
                    }
                  }}
                />
              </div>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-6 bg-gray-50">
            <div className="bg-white p-4 rounded-lg text-center shadow-sm">
              <div className="text-3xl font-bold text-purple-600">{profile.total_articles}</div>
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

        {/* All Period Summaries Section */}
        {allPeriodSummaries.length > 0 && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
            <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2 mb-6">
              <svg className="h-7 w-7 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Period Summaries
              <span className="text-sm text-gray-500 font-normal">({allPeriodSummaries.length})</span>
            </h2>
            
            <div className="space-y-6">
              {allPeriodSummaries.map((summary, index) => (
                <div key={index} className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-100">
                  <div className="flex items-start justify-between mb-4">
                    <h3 className="text-lg font-bold text-gray-800">Period Analysis</h3>
                    <span className="text-xs text-gray-600 bg-white px-3 py-1 rounded-full shadow-sm">
                      {formatDateToDDMMYYYY(summary.date_range.start)} to {formatDateToDDMMYYYY(summary.date_range.end)}
                    </span>
                  </div>

                  {/* Summary Text */}
                  <div className="mb-4 prose prose-sm max-w-none">
                    <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                      {summary.summary}
                    </p>
                  </div>

                  {/* Key Points */}
                  {summary.key_points && summary.key_points.length > 0 && (
                    <div className="mb-4">
                      <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                        <svg className="h-4 w-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        Key Points
                      </h4>
                      <ul className="space-y-1">
                        {summary.key_points.map((point, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <span className="text-blue-600 mt-1">•</span>
                            <span className="text-gray-700 text-sm">{point}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Keywords and Topics */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {summary.keywords && summary.keywords.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-gray-700 mb-2">Keywords</h4>
                        <div className="flex flex-wrap gap-2">
                          {summary.keywords.map((keyword, idx) => (
                            <span key={idx} className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800">
                              {keyword}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {summary.topics && summary.topics.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-gray-700 mb-2">Topics</h4>
                        <div className="flex flex-wrap gap-2">
                          {summary.topics.map((topic, idx) => (
                            <span key={idx} className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-indigo-100 text-indigo-800">
                              {topic}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Period Summary Section (newly generated, will be moved to storage) */}
        {/* {periodSummary && (
          <div className="bg-gradient-to-br from-green-50 to-teal-50 rounded-xl shadow-lg p-6 mb-8 border border-green-100">
            <div className="flex items-start justify-between mb-4">
              <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                <svg className="h-7 w-7 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Period Summary
              </h2>
              <span className="text-xs text-gray-600 bg-white px-3 py-1 rounded-full shadow-sm">
                {periodSummary.date_range.start} to {periodSummary.date_range.end}
              </span>
            </div>

            <div className="mb-6 prose prose-sm max-w-none">
              <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                {periodSummary.summary}
              </p>
            </div>

            {periodSummary.key_points && periodSummary.key_points.length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                  <svg className="h-4 w-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  Key Points
                </h3>
                <ul className="space-y-2">
                  {periodSummary.key_points.map((point, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-green-600 mt-1">•</span>
                      <span className="text-gray-700 text-sm">{point}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {periodSummary.keywords && periodSummary.keywords.length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                  <svg className="h-4 w-4 text-teal-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M17.707 9.293a1 1 0 010 1.414l-7 7a1 1 0 01-1.414 0l-7-7A.997.997 0 012 10V5a3 3 0 013-3h5c.256 0 .512.098.707.293l7 7zM5 6a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                  </svg>
                  Keywords
                </h3>
                <div className="flex flex-wrap gap-2">
                  {periodSummary.keywords.map((keyword, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-teal-100 text-teal-800 border border-teal-200 shadow-sm"
                    >
                      {keyword}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {periodSummary.topics && periodSummary.topics.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                  <svg className="h-4 w-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M2 6a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zM14.553 7.106A1 1 0 0014 8v4a1 1 0 00.553.894l2 1A1 1 0 0018 13V7a1 1 0 00-1.447-.894l-2 1z" />
                  </svg>
                  Topics
                </h3>
                <div className="flex flex-wrap gap-2">
                  {periodSummary.topics.map((topic, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800 border border-green-200 shadow-sm"
                    >
                      {topic}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )} */}

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
                  className="w-5 h-5 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                />
                <span className="text-sm font-medium text-gray-700">Speeches Only</span>
              </label>
            </div>
          </div>
          
          <div className="flex gap-3">
            <button
              onClick={handleApplyFilter}
              disabled={isFiltering}
              className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
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
                          {article.url ? (
                            <a 
                              href={article.url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="font-bold text-gray-900 text-lg mb-2 line-clamp-2 hover:text-purple-600 transition-colors cursor-pointer block"
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
                            <span className="flex items-center gap-1 text-blue-600">
                              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                              </svg>
                        <button
                          onClick={() => handleGenerateSummary(article.id)}
                          disabled={summarizingArticles.has(article.id)}
                          className="flex items-center gap-2 py-1.5 text-xs font-medium text-blue-600 hover:text-purple-700 cursor-pointer hover:bg-purple-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {summarizingArticles.has(article.id) ? (
                            <>
                              <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-purple-600"></div>
                              <span>Generating...</span>
                            </>
                          ) : (
                            <>
                              <span>Generate Summary</span>
                            </>
                          )}
                        </button>
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

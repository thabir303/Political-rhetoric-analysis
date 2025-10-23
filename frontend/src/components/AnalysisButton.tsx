import { useState } from 'react'
import { Brain, Loader2 } from 'lucide-react'
import { generatePeriodSummary } from '../utils/api'

interface AnalysisButtonProps {
  type: 'party' | 'figure'
  name: string
  party?: string  // For figure analysis, specify the party
  className?: string
  onAnalysisComplete?: (result: AnalysisResult) => void  // Callback when analysis completes
}

interface AnalysisResult {
  success: boolean
  party_or_figure: string
  total_articles_analyzed: number
  date_range: {
    earliest: string
    latest: string
  }
  analysis: {
    raw_analysis: string
    articles_count: number
    date_range: {
      earliest: string
      latest: string
    }
    sources: string[]
    sample_titles: Array<{ title: string; summary: string }>
    associated_parties?: string[]
  }
  key_points?: string[]
  keywords?: string[]
  topics?: string[]
  processing_time: number
}

export function AnalysisButton({ type, name, party, className = '', onAnalysisComplete }: AnalysisButtonProps) {
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [showModal, setShowModal] = useState(false)
  const [showPrompt, setShowPrompt] = useState(false)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleAnalyze = async () => {
    // Set default date range (last 30 days)
    const today = new Date()
    const thirtyDaysAgo = new Date(today)
    thirtyDaysAgo.setDate(today.getDate() - 30)
    
    setEndDate(today.toISOString().split('T')[0])
    setStartDate(thirtyDaysAgo.toISOString().split('T')[0])
    
    // Show prompt to ask for date range
    setShowPrompt(true)
  }
  
  const startAnalysis = async () => {
    setShowPrompt(false)
    setIsAnalyzing(true)
    setError(null)
    
    try {
      // Use new period summary API
      const result = await generatePeriodSummary(
        type,
        name,
        startDate,
        endDate,
        100
      )
      
      // Clean function to remove ### markers
      const cleanText = (text: string) => text.replace(/^###\s*/gm, '').trim()
      
      // Debug: Log the response
      console.log('=== PERIOD SUMMARY RESPONSE ===')
      console.log('Individual Summaries Count:', result.individual_summaries?.length)
      console.log('Sample Individual Summary:', result.individual_summaries?.[0])
      console.log('Period Summary:', result.period_summary?.substring(0, 100))
      
      // Transform response to match expected AnalysisResult format
      const transformedResult: AnalysisResult = {
        success: result.success,
        party_or_figure: result.entity_name,
        total_articles_analyzed: result.statistics.total_articles,
        date_range: {
          earliest: result.earliest_date || startDate,
          latest: result.latest_date || endDate
        },
        analysis: {
          raw_analysis: cleanText(result.period_summary),
          articles_count: result.statistics.total_articles,
          date_range: {
            earliest: result.earliest_date || startDate,
            latest: result.latest_date || endDate
          },
          sources: [], // Will be populated from individual summaries if needed
          sample_titles: result.individual_summaries.map((s: any) => ({
            title: s.title,
            summary: s.summary
          }))
        },
        key_points: (result.key_points || []).map(cleanText),
        keywords: (result.keywords || []).map(cleanText),
        topics: (result.topics || []).map(cleanText),
        processing_time: 0
      }
      
      setAnalysisResult(transformedResult)
      setShowModal(true)
      
      // Call the callback if provided
      if (onAnalysisComplete) {
        onAnalysisComplete(transformedResult)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed')
      console.error('Analysis error:', err)
    } finally {
      setIsAnalyzing(false)
    }
  }

  const closeModal = () => {
    setShowModal(false)
    setAnalysisResult(null)
    setError(null)
  }

  return (
    <>
      {/* Analysis Button */}
      <button
        onClick={handleAnalyze}
        disabled={isAnalyzing}
        className={`inline-flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 
                   disabled:bg-gray-400 text-white rounded-lg transition-colors ${className}`}
        title={`Analyze stored ${type} articles using AI`}
      >
        {isAnalyzing ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            <span>Analyzing...</span>
          </>
        ) : (
          <>
            <Brain className="w-5 h-5" />
            <span>AI Analysis</span>
          </>
        )}
      </button>

      {/* Date Range Prompt Modal */}
      {showPrompt && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4">
              Select Date Range for Analysis
            </h3>
            <p className="text-gray-600 mb-4">
              Choose the time period you want to analyze
            </p>
            
            <div className="mb-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Start Date
                </label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
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
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
              
              <p className="text-xs text-gray-500">
                All articles in this date range will be analyzed and summarized if not already done
              </p>
            </div>
            
            <div className="flex gap-3">
              <button
                onClick={() => setShowPrompt(false)}
                className="flex-1 px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={startAnalysis}
                disabled={!startDate || !endDate}
                className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white rounded-lg transition-colors"
              >
                Start Analysis
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mt-2 p-3 bg-red-100 border border-red-300 text-red-700 rounded-lg">
          <p className="font-semibold">Analysis Failed</p>
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* Analysis Modal */}
      {showModal && analysisResult && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-purple-600 to-indigo-600 text-white">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Brain className="w-6 h-6" />
                  <div>
                    <h2 className="text-xl font-bold">
                      AI Analysis: {analysisResult.party_or_figure}
                    </h2>
                    <p className="text-sm text-purple-100">
                      {analysisResult.total_articles_analyzed} articles analyzed
                      {analysisResult.processing_time && (
                        <span> • {analysisResult.processing_time.toFixed(1)}s</span>
                      )}
                    </p>
                  </div>
                </div>
                <button
                  onClick={closeModal}
                  className="text-white hover:text-gray-200 transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Modal Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {/* Metadata */}
              <div className="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">Date Range</p>
                  <p className="font-semibold text-gray-800">
                    {analysisResult.analysis.date_range.earliest} → {analysisResult.analysis.date_range.latest}
                  </p>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">Articles Analyzed</p>
                  <p className="font-semibold text-gray-800">
                    {analysisResult.total_articles_analyzed} articles
                  </p>
                </div>
              </div>

              {/* Individual Article Summaries */}
              {analysisResult.analysis.sample_titles && analysisResult.analysis.sample_titles.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
                    <span className="text-blue-600">📰</span>
                    Individual Article Summaries
                  </h3>
                  <div className="space-y-3 max-h-80 overflow-y-auto">
                    {analysisResult.analysis.sample_titles.map((item, index) => (
                      <div key={index} className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                        <h4 className="text-sm font-semibold text-gray-900 mb-2">{item.title}</h4>
                        <p className="text-sm text-gray-700 leading-relaxed">{item.summary}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Period Summary */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
                  <span className="text-purple-600">📊</span>
                  Period Summary
                </h3>
                <div className="bg-gradient-to-br from-purple-50 to-indigo-50 p-4 rounded-lg border border-purple-200">
                  <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap">
                    {analysisResult.analysis.raw_analysis}
                  </div>
                </div>
              </div>

              {/* Key Points */}
              {analysisResult.key_points && analysisResult.key_points.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
                    <span className="text-green-600">✓</span>
                    Key Points
                  </h3>
                  <div className="bg-green-50 p-4 rounded-lg">
                    <ul className="space-y-2">
                      {analysisResult.key_points.map((point, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-sm text-gray-700">
                          <span className="text-green-600 mt-1">•</span>
                          <span>{point}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {/* Keywords */}
              {analysisResult.keywords && analysisResult.keywords.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
                    <span className="text-teal-600">🏷️</span>
                    Keywords
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {analysisResult.keywords.map((keyword, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1 bg-teal-100 text-teal-800 rounded-full text-sm font-medium border border-teal-200"
                      >
                        {keyword}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Topics */}
              {analysisResult.topics && analysisResult.topics.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
                    <span className="text-indigo-600">📑</span>
                    Topics Covered
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {analysisResult.topics.map((topic, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1 bg-indigo-100 text-indigo-800 rounded-full text-sm font-medium border border-indigo-200"
                      >
                        {topic}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Associated Parties (for figure analysis) */}
              {type === 'figure' && analysisResult.analysis.associated_parties && 
               analysisResult.analysis.associated_parties.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-800 mb-3">Associated Parties</h3>
                  <div className="flex flex-wrap gap-2">
                    {analysisResult.analysis.associated_parties.map((party, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm font-medium"
                      >
                        {party}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
              <div className="flex justify-end gap-3">
                <button
                  onClick={closeModal}
                  className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg transition-colors"
                >
                  Close
                </button>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(analysisResult.analysis.raw_analysis)
                    alert('Analysis copied to clipboard!')
                  }}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
                >
                  Copy Analysis
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

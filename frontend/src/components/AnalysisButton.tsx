import { useState } from 'react'
import { Brain, Loader2 } from 'lucide-react'
import { analyzeStoredPartyArticles, analyzeStoredFigureArticles } from '../utils/api'

interface AnalysisButtonProps {
  type: 'party' | 'figure'
  name: string
  party?: string  // For figure analysis, specify the party
  className?: string
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
    sample_titles: string[]
    associated_parties?: string[]
    comprehensive_summary?: string  // NEW: Summary of all article summaries
    article_summaries?: Array<{
      title: string
      date: string
      source: string
      summary: string
      url: string
    }>
  }
  processing_time: number
}

export function AnalysisButton({ type, name, party, className = '' }: AnalysisButtonProps) {
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [showModal, setShowModal] = useState(false)
  const [showPrompt, setShowPrompt] = useState(false)
  const [articleCount, setArticleCount] = useState('50')
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleAnalyze = async () => {
    // Show prompt to ask for article count
    setShowPrompt(true)
  }
  
  const startAnalysis = async () => {
    setShowPrompt(false)
    setIsAnalyzing(true)
    setError(null)
    
    const count = parseInt(articleCount) || 50
    
    try {
      let result
      
      if (type === 'party') {
        result = await analyzeStoredPartyArticles(name, undefined, undefined, count)
      } else {
        result = await analyzeStoredFigureArticles(name, party, undefined, undefined, count)
      }
      
      setAnalysisResult(result)
      setShowModal(true)
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

      {/* Article Count Prompt Modal */}
      {showPrompt && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4">
              Select Articles to Analyze
            </h3>
            <p className="text-gray-600 mb-4">
              How many recent articles would you like to analyze?
            </p>
            
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Number of Articles
              </label>
              <input
                type="number"
                min="10"
                max="100"
                value={articleCount}
                onChange={(e) => setArticleCount(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="e.g., 50"
              />
              <p className="text-xs text-gray-500 mt-1">
                Recommended: 20-50 articles for balanced analysis
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
                className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
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
                  <p className="text-sm text-gray-600 mb-1">Sources</p>
                  <p className="font-semibold text-gray-800">
                    {analysisResult.analysis.sources.join(', ')}
                  </p>
                </div>
              </div>

              {/* Sample Titles */}
              {analysisResult.analysis.sample_titles && analysisResult.analysis.sample_titles.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
                    <span className="text-blue-600">📰</span>
                    Article Summary
                  </h3>
                  <div className="bg-blue-50 p-4 rounded-lg mb-3">
                    <p className="text-sm text-gray-700 mb-2">
                      Analyzed <strong>{analysisResult.total_articles_analyzed} articles</strong> from{' '}
                      <strong>{analysisResult.analysis.sources.join(', ')}</strong> spanning{' '}
                      <strong>{analysisResult.analysis.date_range.earliest}</strong> to{' '}
                      <strong>{analysisResult.analysis.date_range.latest}</strong>
                    </p>
                  </div>
                  <p className="text-sm text-gray-600 mb-3 font-medium">Sample Titles:</p>
                  <ul className="space-y-2">
                    {analysisResult.analysis.sample_titles.map((title, index) => (
                      <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                        <span className="text-gray-400 mt-0.5">•</span>
                        <span>{title}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Article Summaries - NEW SECTION */}
              {analysisResult.analysis.article_summaries && analysisResult.analysis.article_summaries.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
                    <span className="text-green-600">📋</span>
                    Article Summaries ({analysisResult.analysis.article_summaries.length} articles)
                  </h3>
                  <div className="space-y-4 max-h-96 overflow-y-auto pr-2">
                    {analysisResult.analysis.article_summaries.map((article, index) => (
                      <div key={index} className="bg-gradient-to-r from-green-50 to-blue-50 p-4 rounded-lg border border-green-200 hover:shadow-md transition-shadow">
                        <div className="flex items-start justify-between mb-2">
                          <h4 className="font-semibold text-gray-800 flex-1 pr-2">
                            {index + 1}. {article.title}
                          </h4>
                          <span className="text-xs text-gray-500 whitespace-nowrap">{article.date}</span>
                        </div>
                        <p className="text-xs text-gray-600 mb-2 flex items-center gap-1">
                          <span className="font-medium">Source:</span> {article.source}
                        </p>
                        <div className="bg-white bg-opacity-70 p-3 rounded border border-green-100">
                          <p className="text-sm text-gray-700 leading-relaxed">
                            {article.summary}
                          </p>
                        </div>
                        {article.url && (
                          <a
                            href={article.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-blue-600 hover:text-blue-800 mt-2 inline-flex items-center gap-1"
                          >
                            <span>Read full article</span>
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                            </svg>
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Comprehensive Summary of All Articles - NEW SECTION */}
              {analysisResult.analysis.comprehensive_summary && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
                    <span className="text-orange-600">📊</span>
                    Comprehensive Summary (Summary of All Article Summaries)
                  </h3>
                  <div className="bg-gradient-to-br from-orange-50 via-yellow-50 to-orange-50 p-5 rounded-lg border-2 border-orange-200 shadow-sm">
                    <div className="prose prose-sm max-w-none text-gray-800">
                      <p className="text-sm text-gray-600 mb-3 italic">
                        This is a comprehensive summary combining insights from all {analysisResult.analysis.article_summaries?.length || 0} individual article summaries.
                      </p>
                      <div className="bg-white bg-opacity-80 p-4 rounded border border-orange-100">
                        <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                          {analysisResult.analysis.comprehensive_summary}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* AI Analysis */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
                  <span className="text-purple-600">🤖</span>
                  AI-Generated Analysis
                </h3>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap">
                    {analysisResult.analysis.raw_analysis}
                  </div>
                </div>
              </div>

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

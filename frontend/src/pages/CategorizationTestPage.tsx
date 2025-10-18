import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { FileSearch, RefreshCw, AlertTriangle, CheckCircle } from 'lucide-react'
import { fetchCategorizationTest } from '../utils/api'

interface Article {
  index: number
  title: string
  date: string
  source: string
  parties: string[]
  people: string[]
  people_affiliations?: Record<string, string>
  primary_parties: string
  mentioned_figures: string
  political_entities: string
  keywords: string
  content_preview: string
}

interface CategorizationData {
  total_articles: number
  articles: Article[]
  party_figure_breakdown: Record<string, string[]>
  correct_mapping_from_db?: Record<string, string[]>  // Optional with new name
  correct_mapping?: Record<string, string[]>  // Keep old name for backward compatibility
}

export default function CategorizationTestPage() {
  const [data, setData] = useState<CategorizationData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [limit, setLimit] = useState(50)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await fetchCategorizationTest(limit);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const checkIncorrectAssociations = () => {
    if (!data || !data.party_figure_breakdown) return []
    
    // Use correct_mapping_from_db if available, otherwise fallback to correct_mapping
    const correctMapping = data.correct_mapping_from_db || data.correct_mapping || {}
    
    const issues: Array<{ party: string; incorrect: string[]; correct: string[] }> = []
    
    Object.entries(data.party_figure_breakdown).forEach(([party, actualFigures]) => {
      const correctFigures = correctMapping[party] || []
      
      // Ensure correctFigures is an array and filter safely
      const correctList = Array.isArray(correctFigures) ? correctFigures : []
      const actualList = Array.isArray(actualFigures) ? actualFigures : []
      
      const incorrect = actualList.filter(fig => !correctList.includes(fig))
      
      if (incorrect.length > 0) {
        issues.push({ party, incorrect, correct: correctList })
      }
    })
    
    return issues
  }

  const issues = data ? checkIncorrectAssociations() : []

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow-md px-6 py-4">
          <div className="max-w-7xl mx-auto flex items-center gap-6">
            <Link to="/" className="text-xl font-bold text-blue-600 hover:text-blue-700">
              Speech Analysis System
            </Link>
            <span className="text-gray-700 font-medium">Categorization Test</span>
          </div>
        </nav>
        
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading categorization data...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow-md px-6 py-4">
          <div className="max-w-7xl mx-auto flex items-center gap-6">
            <Link to="/" className="text-xl font-bold text-blue-600 hover:text-blue-700">
              Speech Analysis System
            </Link>
            <span className="text-gray-700 font-medium">Categorization Test</span>
          </div>
        </nav>
        
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <div className="flex items-center">
              <AlertTriangle className="h-6 w-6 text-red-600 mr-3" />
              <div>
                <h3 className="text-lg font-semibold text-red-800">Error Loading Data</h3>
                <p className="text-red-700 mt-1">{error || 'Unknown error'}</p>
              </div>
            </div>
            <button
              onClick={loadData}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors inline-flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Try Again
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-md px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link to="/" className="text-xl font-bold text-blue-600 hover:text-blue-700">
              Speech Analysis System
            </Link>
            <span className="text-gray-700 font-medium">Categorization Test</span>
          </div>
          <div className="flex items-center gap-4">
            <select
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value={25}>25 articles</option>
              <option value={50}>50 articles</option>
              <option value={100}>100 articles</option>
              <option value={200}>200 articles</option>
            </select>
            <button
              onClick={loadData}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors inline-flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Reload
            </button>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <FileSearch className="w-8 h-8 text-blue-600" />
            <h1 className="text-4xl font-bold text-gray-800">
              Categorization Test
            </h1>
          </div>
          <p className="text-gray-600">
            View how articles are categorized and verify party-figure associations
          </p>
        </div>

        {/* Status Card */}
        <div className="mb-6 bg-white rounded-lg shadow-md p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <div className="text-3xl font-bold text-blue-600">{data.total_articles}</div>
              <div className="text-sm text-gray-600">Total Articles Loaded</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-green-600">
                {Object.keys(data.party_figure_breakdown).length}
              </div>
              <div className="text-sm text-gray-600">Parties Found</div>
            </div>
            <div>
              <div className={`text-3xl font-bold ${issues.length === 0 ? 'text-green-600' : 'text-red-600'}`}>
                {issues.length === 0 ? (
                  <span className="flex items-center gap-2">
                    <CheckCircle className="w-8 h-8" />
                    All Good
                  </span>
                ) : (
                  <span>{issues.length} Issues</span>
                )}
              </div>
              <div className="text-sm text-gray-600">Association Status</div>
            </div>
          </div>
        </div>

        {/* Issues Section */}
        {issues.length > 0 && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-xl font-bold text-red-800 mb-4 flex items-center gap-2">
              <AlertTriangle className="w-6 h-6" />
              Incorrect Party-Figure Associations Found
            </h2>
            <div className="space-y-4">
              {issues.map((issue, idx) => (
                <div key={idx} className="bg-white rounded-lg p-4">
                  <h3 className="font-bold text-gray-800 mb-2">{issue.party}</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm font-semibold text-red-700 mb-1">❌ Incorrect Figures Found:</p>
                      <div className="flex flex-wrap gap-2">
                        {issue.incorrect.map((fig, i) => (
                          <span key={i} className="px-2 py-1 bg-red-100 text-red-700 rounded text-sm">
                            {fig}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-green-700 mb-1">✅ Correct Figures Should Be:</p>
                      <div className="flex flex-wrap gap-2">
                        {issue.correct.map((fig, i) => (
                          <span key={i} className="px-2 py-1 bg-green-100 text-green-700 rounded text-sm">
                            {fig}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded">
              <p className="text-sm text-yellow-800">
                <strong>Fix:</strong> Run <code className="px-2 py-1 bg-yellow-100 rounded">python fix_party_associations.py</code> to correct these associations.
              </p>
            </div>
          </div>
        )}

        {/* Party-Figure Breakdown */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Party-Figure Breakdown</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.party_figure_breakdown && Object.entries(data.party_figure_breakdown).map(([party, figures]) => {
              // Use correct_mapping_from_db if available, otherwise fallback to correct_mapping
              const correctMapping = data.correct_mapping_from_db || data.correct_mapping || {}
              const correctFigures = correctMapping[party] 
                ? (Array.isArray(correctMapping[party]) ? correctMapping[party] : [])
                : []
              const hasIssues = Array.isArray(figures) && figures.some(fig => !correctFigures.includes(fig))
              
              return (
                <div
                  key={party}
                  className={`bg-white rounded-lg shadow-md p-4 ${
                    hasIssues ? 'border-2 border-red-300' : 'border-2 border-green-300'
                  }`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-lg font-bold text-gray-800">{party}</h3>
                    {hasIssues ? (
                      <AlertTriangle className="w-5 h-5 text-red-600" />
                    ) : (
                      <CheckCircle className="w-5 h-5 text-green-600" />
                    )}
                  </div>
                  <div className="space-y-1">
                    {Array.isArray(figures) && figures.map((figure, idx) => {
                      const isCorrect = correctFigures.includes(figure)
                      return (
                        <div
                          key={idx}
                          className={`text-sm px-2 py-1 rounded ${
                            isCorrect ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
                          }`}
                        >
                          {isCorrect ? '✓' : '✗'} {figure}
                        </div>
                      )
                    })}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Articles Table */}
        <div>
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Articles Detail</h2>
          <div className="bg-white rounded-lg shadow-md overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">#</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Title</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Source</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Parties</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">People</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {data.articles.map((article) => (
                    <tr key={article.index} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm text-gray-900">{article.index}</td>
                      <td className="px-4 py-3 text-sm text-gray-900 max-w-xs">
                        <div className="font-medium">{article.title}</div>
                        <div className="text-xs text-gray-500 mt-1">{article.content_preview}</div>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 whitespace-nowrap">{article.date}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">{article.source}</td>
                      <td className="px-4 py-3 text-sm">
                        <div className="flex flex-wrap gap-1">
                          {(Array.isArray(article.parties) ? article.parties : String(article.parties).split(',')).filter(Boolean).map((party: string, idx: number) => (
                            <span
                              key={idx}
                              className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs"
                            >
                              {party.trim()}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <div className="flex flex-wrap gap-1">
                          {(Array.isArray(article.people) ? article.people : String(article.people).split(',')).filter(Boolean).map((person: string, idx: number) => {
                            const canonical = person.trim()
                            const affiliation = (article.people_affiliations && article.people_affiliations[canonical]) || ''
                            return (
                              <span
                                key={idx}
                                title={affiliation ? `Affiliation: ${affiliation}` : undefined}
                                className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs"
                              >
                                {canonical}{affiliation ? ` • ${affiliation}` : ''}
                              </span>
                            )
                          })}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

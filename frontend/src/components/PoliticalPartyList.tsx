import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { fetchPoliticalParties } from '../utils/api'
import type { PoliticalParty } from '../types'

/**
 * PoliticalPartyList Component
 * 
 * Displays a list of all political parties with their associated figures.
 * Clicking on a figure redirects to their profile page.
 */
export default function PoliticalPartyList() {
  const navigate = useNavigate()
  const [parties, setParties] = useState<PoliticalParty[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedParty, setExpandedParty] = useState<string | null>(null)

  useEffect(() => {
    loadParties()
  }, [])

  const loadParties = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetchPoliticalParties()
      setParties(response.parties)
    } catch (err) {
      setError(`Failed to load political parties: ${err}`)
      console.error('Error loading parties:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleFigureClick = (partyName: string, figureName: string) => {
    // Navigate to figure profile page using React Router
    const encodedParty = encodeURIComponent(partyName)
    const encodedFigure = encodeURIComponent(figureName)
    navigate(`/figure/${encodedParty}/${encodedFigure}`)
  }

  const toggleParty = (partyName: string) => {
    setExpandedParty(expandedParty === partyName ? null : partyName)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Navigation Bar */}
        <nav className="bg-white shadow-md px-6 py-4">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-6">
              <Link to="/" className="text-xl font-bold text-blue-600 hover:text-blue-700">
                Speech Analysis System
              </Link>
              <span className="text-gray-700 font-medium">Political Parties</span>
            </div>
            <Link
              to="/scraper"
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium flex items-center gap-2"
            >
              <span>📰</span>
              <span>Scrape Newspapers</span>
            </Link>
          </div>
        </nav>
        
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading political parties...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Navigation Bar */}
        <nav className="bg-white shadow-md px-6 py-4">
          <div className="max-w-7xl mx-auto flex items-center gap-6">
            <Link to="/" className="text-xl font-bold text-blue-600 hover:text-blue-700">
              Speech Analysis System
            </Link>
            <span className="text-gray-700 font-medium">Political Parties</span>
          </div>
        </nav>
        
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <div className="flex items-center">
              <svg className="h-6 w-6 text-red-600 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <h3 className="text-lg font-semibold text-red-800">Error Loading Data</h3>
                <p className="text-red-700 mt-1">{error}</p>
              </div>
            </div>
            <button
              onClick={loadParties}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Bar */}
      <nav className="bg-white shadow-md px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center gap-6">
          <Link to="/" className="text-xl font-bold text-blue-600 hover:text-blue-700">
            Speech Analysis System
          </Link>
          <span className="text-gray-700 font-medium">Political Parties</span>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            Political Parties
          </h1>
          <p className="text-gray-600">
            Explore {parties.length} political organizations and their key figures
          </p>
        </div>

        {/* Parties Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {parties.map((party) => (
          <div
            key={party.name}
            className="bg-white rounded-lg shadow-md hover:shadow-xl transition-shadow duration-300 overflow-hidden"
          >
            {/* Party Header */}
            <div 
              className="bg-gradient-to-r from-blue-500 to-blue-600 text-white p-6 cursor-pointer"
              onClick={() => toggleParty(party.name)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h2 className="text-2xl font-bold mb-1">
                    {party.name}
                  </h2>
                  <p className="text-blue-100 text-sm mb-3">
                    {party.full_name}
                  </p>
                  <div className="flex items-center space-x-4 text-sm">
                    <span className="flex items-center">
                      <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
                      </svg>
                      {party?.figures?.length} figures
                    </span>
                    {party?.article_count !== undefined && (
                      <span className="flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M9 2a2 2 0 00-2 2v8a2 2 0 002 2h6a2 2 0 002-2V6.414A2 2 0 0016.414 5L14 2.586A2 2 0 0012.586 2H9z" />
                          <path d="M3 8a2 2 0 012-2v10h8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z" />
                        </svg>
                        {party?.article_count} articles
                      </span>
                    )}
                  </div>
                </div>
                <button className="text-white">
                  <svg 
                    className={`w-6 h-6 transform transition-transform ${expandedParty === party.name ? 'rotate-180' : ''}`}
                    fill="none" 
                    viewBox="0 0 24 24" 
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Figures List - Collapsible */}
            <div 
              className={`transition-all duration-300 ease-in-out ${
                expandedParty === party.name ? 'max-h-[500px] opacity-100' : 'max-h-0 opacity-0'
              } overflow-hidden`}
            >
              <div className="p-6">
                <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
                  Key Figures ({party?.figures?.length || 0})
                </h3>
                <div className="space-y-2">
                  {party?.figures?.map((figure, index) => (
                    <button
                      key={index}
                      onClick={() => handleFigureClick(party.name, figure)}
                      className="w-full text-left px-4 py-3 rounded-lg border border-gray-200 hover:border-blue-400 hover:bg-blue-50 transition-all duration-200 group"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white font-semibold">
                            {figure.charAt(0).toUpperCase()}
                          </div>
                          <span className="font-medium text-gray-800 group-hover:text-blue-600">
                            {figure}
                          </span>
                        </div>
                        <svg 
                          className="w-5 h-5 text-gray-400 group-hover:text-blue-600 transform group-hover:translate-x-1 transition-transform" 
                          fill="none" 
                          viewBox="0 0 24 24" 
                          stroke="currentColor"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Quick View Button (when collapsed) */}
            {expandedParty !== party.name && (
              <div className="px-6 pb-6">
                <button
                  onClick={() => toggleParty(party.name)}
                  className="w-full py-2 text-sm text-blue-600 hover:text-blue-700 font-medium"
                >
                  View {party?.figures?.length} figures →
                </button>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Empty State */}
      {parties.length === 0 && !loading && (
        <div className="text-center py-12">
          <svg className="mx-auto h-16 w-16 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
          </svg>
          <h3 className="mt-4 text-lg font-medium text-gray-900">No parties found</h3>
          <p className="mt-2 text-gray-500">Try refreshing the page or check back later.</p>
        </div>
      )}

      {/* Footer Stats */}
      {parties.length > 0 && (
        <div className="mt-8 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <div className="text-3xl font-bold text-blue-600">
                {parties.length}
              </div>
              <div className="text-sm text-gray-600 mt-1">Political Parties</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-blue-600">
                {parties.reduce((sum, party) => sum + (party?.figures?.length || 0), 0)}
              </div>
              <div className="text-sm text-gray-600 mt-1">Key Figures</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-blue-600">
                {parties.reduce((sum, party) => sum + (party.article_count || 0), 0).toLocaleString()}
              </div>
              <div className="text-sm text-gray-600 mt-1">Total Articles</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-blue-600">
                {parties.length > 0 ? Math.round(parties.reduce((sum, party) => sum + (party.article_count || 0), 0) / parties.length).toLocaleString() : 0}
              </div>
              <div className="text-sm text-gray-600 mt-1">Avg. per Party</div>
            </div>
          </div>
        </div>
      )}
      </div>
    </div>
  )
}

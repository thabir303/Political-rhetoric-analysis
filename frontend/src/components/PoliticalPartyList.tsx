import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { fetchPoliticalParties } from '../utils/api'
import { AnalysisButton } from './AnalysisButton'
import { LogOut } from 'lucide-react'
import { logout, getEmail } from '../utils/auth'
import type { PoliticalParty } from '../types'

/**
 * PoliticalPartyList Component
 * 
 * Displays a list of all political parties with their associated figures.
 * Clicking on a figure redirects to their profile page.
 */
export default function PoliticalPartyList() {
  const navigate = useNavigate()
  const email = getEmail()
  const [parties, setParties] = useState<PoliticalParty[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedParty, setExpandedParty] = useState<string | null>(null)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

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
  
  const handlePartyClick = (partyName: string) => {
    // Navigate to party profile page
    const encodedParty = encodeURIComponent(partyName)
    navigate(`/party/${encodedParty}`)
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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-indigo-50">
      {/* Navigation Bar */}
      <nav className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link to="/" className="text-2xl font-bold text-gray-900 hover:text-blue-600 transition-colors">
              Speech Analysis System
            </Link>
            <span className="text-gray-500 text-sm">Political Parties</span>
          </div>
          <div className="flex items-center gap-4">
            <Link
              to="/scraper"
              className="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors font-medium"
            >
              Scrape Newspapers
            </Link>
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
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-12">
        {/* Header */}
        <div className="mb-12 text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            Political Parties & Interim Government
          </h1>
          <p className="text-xl text-gray-600">
            Explore {parties.length} political organizations and their key figures
          </p>
        </div>

        {/* Parties Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {parties.map((party) => (
          <div
            key={party.name}
            className="bg-white rounded-2xl border-2 border-gray-100 hover:border-blue-300 hover:shadow-xl transition-all duration-300 overflow-hidden group"
          >
            {/* Party Header */}
            <div className="p-8 border-b border-gray-100">
              <div className="flex items-start justify-between mb-4">
                <div 
                  className="flex-1 cursor-pointer"
                  onClick={() => handlePartyClick(party.name)}
                >
                  <h2 className="text-2xl font-bold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
                    {party.name}
                  </h2>
                  <p className="text-gray-500 text-sm mb-4">
                    {party.full_name}
                  </p>
                  
                  {/* Stats */}
                  <div className="flex items-center gap-6 text-sm text-gray-600">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      <span>{party?.figures?.length} figures</span>
                    </div>
                    {party?.article_count !== undefined && (
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        <span>{party?.article_count} articles</span>
                      </div>
                    )}
                  </div>
                </div>
                
                <button 
                  onClick={() => toggleParty(party.name)}
                  className="text-gray-400 hover:text-gray-600 transition-colors p-2 rounded-lg hover:bg-gray-100"
                  title="Toggle figures list"
                >
                  <svg 
                    className={`w-5 h-5 transform transition-transform duration-300 ${expandedParty === party.name ? 'rotate-180' : ''}`}
                    fill="none" 
                    viewBox="0 0 24 24" 
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
              </div>
              
              {/* AI Analysis Button */}
              <AnalysisButton 
                type="party" 
                name={party.name}
                className="w-full justify-center"
              />
            </div>

            {/* Figures List - Collapsible with Scrolling */}
            <div 
              className={`transition-all duration-300 ease-in-out ${
                expandedParty === party.name ? 'max-h-[500px] opacity-100' : 'max-h-0 opacity-0'
              } overflow-hidden`}
            >
              <div className="p-6">
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">
                  Key Figures ({party?.figures?.length || 0})
                </h3>
                <div className="space-y-2 max-h-96 overflow-y-auto pr-2">
                  {party?.figures?.map((figure, index) => (
                    <button
                      key={index}
                      onClick={() => handleFigureClick(party.name, figure)}
                      className="w-full text-left px-4 py-3 rounded-xl border border-gray-200 hover:border-blue-400 hover:bg-blue-50 transition-all duration-200 group/figure"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-gray-700 font-semibold group-hover/figure:bg-blue-100 group-hover/figure:text-blue-600 transition-colors flex-shrink-0">
                            {figure.charAt(0).toUpperCase()}
                          </div>
                          <span className="font-medium text-gray-800 group-hover/figure:text-blue-600 transition-colors">
                            {figure}
                          </span>
                        </div>
                        <svg 
                          className="w-4 h-4 text-gray-400 group-hover/figure:text-blue-600 transform group-hover/figure:translate-x-1 transition-all flex-shrink-0" 
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
                  className="w-full py-3 text-sm text-gray-600 hover:text-blue-600 font-medium rounded-lg hover:bg-gray-50 transition-colors"
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
      </div>
    </div>
  )
}

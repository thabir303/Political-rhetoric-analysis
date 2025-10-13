import { useState, useEffect } from 'react'
import { fetchPoliticalParties, fetchFigureProfile } from '../utils/api'
import type { PoliticalParty, FigureProfile } from '../types'

/**
 * Example component demonstrating the usage of new API functions
 * 
 * This component shows how to:
 * 1. Fetch and display political parties
 * 2. Fetch and display figure profiles
 * 3. Handle loading and error states
 */
export default function PoliticalExplorer() {
  const [parties, setParties] = useState<PoliticalParty[]>([])
  const [selectedParty, setSelectedParty] = useState<string>('')
  const [selectedFigure, setSelectedFigure] = useState<string>('')
  const [figureProfile, setFigureProfile] = useState<FigureProfile | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch parties on mount
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
      setError(`Failed to load parties: ${err}`)
    } finally {
      setLoading(false)
    }
  }

  const loadFigureProfile = async (party: string, figure: string) => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetchFigureProfile(party, figure)
      // Convert FigureProfileResponse to FigureProfile
      const profile: FigureProfile = {
        name: response.figure_name,
        party: response.party_name,
        article_count: response.total_articles,
        speech_count: response.articles.filter(a => a.summary).length,
        recent_articles: response.articles.map(a => ({
          content: a.summary || '',
          distance: 1 - a.similarity,
          metadata: {
            title: a.title,
            date: a.date,
            source: a.source,
            keywords: a.keywords,
          }
        })),
        top_keywords: [...new Set(response.articles.flatMap(a => a.keywords))].slice(0, 10),
        themes: [...new Set(response.articles.flatMap(a => a.topics))],
        date_range: response.articles.length > 0 ? {
          earliest: response.articles[response.articles.length - 1]?.date || '',
          latest: response.articles[0]?.date || ''
        } : undefined
      }
      setFigureProfile(profile)
    } catch (err) {
      setError(`Failed to load figure profile: ${err}`)
    } finally {
      setLoading(false)
    }
  }

  const handlePartySelect = (partyName: string) => {
    setSelectedParty(partyName)
    setSelectedFigure('')
    setFigureProfile(null)
  }

  const handleFigureSelect = (figureName: string) => {
    setSelectedFigure(figureName)
    if (selectedParty && figureName) {
      loadFigureProfile(selectedParty, figureName)
    }
  }

  const selectedPartyData = parties.find(p => p.name === selectedParty)

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <h2 className="text-3xl font-bold text-gray-800 mb-6">
        Political Explorer
      </h2>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Parties Grid */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-semibold text-gray-800 mb-4">
          Political Parties ({parties.length})
        </h3>
        
        {loading && parties.length === 0 ? (
          <div className="text-center py-8 text-gray-500">Loading parties...</div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {parties.map((party) => (
              <button
                key={party.name}
                onClick={() => handlePartySelect(party.name)}
                className={`p-4 rounded-lg border-2 transition-all ${
                  selectedParty === party.name
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
                }`}
              >
                <div className="font-semibold text-gray-800">{party.name}</div>
                <div className="text-sm text-gray-600">{party.full_name}</div>
                <div className="text-xs text-gray-500 mt-2">
                  {party.figures.length} figures
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Figures List */}
      {selectedPartyData && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">
            {selectedPartyData.name} Figures
          </h3>
          
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {selectedPartyData.figures.map((figure) => (
              <button
                key={figure}
                onClick={() => handleFigureSelect(figure)}
                className={`p-3 rounded-lg border transition-all ${
                  selectedFigure === figure
                    ? 'border-green-500 bg-green-50'
                    : 'border-gray-200 hover:border-green-300 hover:bg-gray-50'
                }`}
              >
                <div className="font-medium text-gray-800">{figure}</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Figure Profile */}
      {loading && figureProfile === null && selectedFigure ? (
        <div className="bg-white rounded-lg shadow-md p-6 text-center text-gray-500">
          Loading profile...
        </div>
      ) : figureProfile ? (
        <div className="bg-white rounded-lg shadow-md p-6 space-y-4">
          <div className="border-b pb-4">
            <h3 className="text-2xl font-bold text-gray-800">{figureProfile.name}</h3>
            <p className="text-gray-600">{figureProfile.party}</p>
          </div>

          {/* Statistics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Total Articles</div>
              <div className="text-2xl font-bold text-blue-600">
                {figureProfile.article_count}
              </div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Speeches</div>
              <div className="text-2xl font-bold text-green-600">
                {figureProfile.speech_count}
              </div>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Keywords</div>
              <div className="text-2xl font-bold text-purple-600">
                {figureProfile.top_keywords.length}
              </div>
            </div>
            <div className="bg-orange-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Themes</div>
              <div className="text-2xl font-bold text-orange-600">
                {figureProfile.themes.length}
              </div>
            </div>
          </div>

          {/* Top Keywords */}
          <div>
            <h4 className="font-semibold text-gray-800 mb-2">Top Keywords</h4>
            <div className="flex flex-wrap gap-2">
              {figureProfile.top_keywords.map((keyword, idx) => (
                <span
                  key={idx}
                  className="bg-gray-100 px-3 py-1 rounded-full text-sm text-gray-700"
                >
                  {keyword}
                </span>
              ))}
            </div>
          </div>

          {/* Themes */}
          <div>
            <h4 className="font-semibold text-gray-800 mb-2">Main Themes</h4>
            <div className="flex flex-wrap gap-2">
              {figureProfile.themes.map((theme, idx) => (
                <span
                  key={idx}
                  className="bg-blue-100 px-3 py-1 rounded-full text-sm text-blue-700"
                >
                  {theme}
                </span>
              ))}
            </div>
          </div>

          {/* Date Range */}
          {figureProfile.date_range && (
            <div className="text-sm text-gray-600">
              <strong>Activity Period:</strong> {figureProfile.date_range.earliest} → {figureProfile.date_range.latest}
            </div>
          )}

          {/* Recent Articles */}
          <div>
            <h4 className="font-semibold text-gray-800 mb-3">Recent Articles</h4>
            <div className="space-y-3">
              {figureProfile.recent_articles.slice(0, 5).map((article, idx) => (
                <div key={idx} className="border-l-4 border-blue-500 pl-4 py-2">
                  <div className="font-medium text-gray-800">
                    {article.metadata?.title || 'Untitled'}
                  </div>
                  <div className="text-sm text-gray-600 line-clamp-2">
                    {article.content}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {article.metadata?.date} • {article.metadata?.source}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}

import { useState } from 'react'
import { Link } from 'react-router-dom'
import Header from '../components/Header'
import SearchBar from '../components/SearchBar'
import ResultCard from '../components/ResultCard'
import StatsPanel from '../components/StatsPanel'
import { searchArticles } from '../utils/api'
import type { Article } from '../types'
import logo from '../assets/logo.png'

export default function HomePage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Article[]>([])
  const [loading, setLoading] = useState(false)

  const handleSearch = async () => {
    if (!query.trim()) return

    setLoading(true)
    try {
      const data = await searchArticles({
        query: query,
        top_k: 5,
      })
      setResults(data.results || [])
    } catch (error) {
      console.error('Search error:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Navigation Bar */}
        <nav className="mb-8 bg-white rounded-lg shadow-md px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              <Link to="/" className="flex items-center">
                <img src={logo} alt="Speech Analysis" className="h-8 w-auto" />
              </Link>
              <Link 
                to="/parties" 
                className="px-4 py-2 text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors font-medium"
              >
                Political Parties
              </Link>
            </div>
          </div>
        </nav>

        <Header />
        
        <SearchBar
          query={query}
          setQuery={setQuery}
          onSearch={handleSearch}
          loading={loading}
        />

        {/* Results */}
        {results.length > 0 && (
          <div className="max-w-4xl mx-auto space-y-4">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">
              Results ({results.length})
            </h2>
            {results.map((result, index) => (
              <ResultCard key={index} result={result} index={index} />
            ))}
          </div>
        )}

        {/* Empty State */}
        {!loading && results.length === 0 && query && (
          <div className="max-w-4xl mx-auto text-center py-12">
            <p className="text-gray-500 text-lg">
              No results found for "{query}"
            </p>
          </div>
        )}
      </div>
      
      <StatsPanel />
    </div>
  )
}

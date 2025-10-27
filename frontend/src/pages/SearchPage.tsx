import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, ArrowLeft, Loader2, Sparkles } from 'lucide-react';
import { getAuthHeader } from '../utils/auth';

interface SearchResult {
  id: string;
  content: string;
  metadata: {
    title?: string;
    date?: string;
    source?: string;
    category?: string;
    persons?: string;
  };
  score: number;
  summary?: string;
}

const SearchPage = () => {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [summarizingId, setSummarizingId] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!query.trim()) {
      setError('Please enter a search query');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
      const authHeaders = getAuthHeader()
      const response = await fetch(`${API_BASE_URL}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders,
        },
        body: JSON.stringify({
          query: query,
          top_k: 10
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch search results');
      }

      const data = await response.json();
      setResults(data.results || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateSummary = async (articleId: string) => {
    setSummarizingId(articleId);
    
    try {
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
      const authHeaders = getAuthHeader()
      const response = await fetch(`${API_BASE_URL}/articles/${articleId}/summarize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to generate summary');
      }

      const data = await response.json();
      
      // Update the search results with ALL LLM-generated data
      setResults(prevResults =>
        prevResults.map(result =>
          result.id === articleId
            ? { 
                ...result, 
                summary: data.summary,
                key_points: data.key_points || [],
                keywords: data.keywords || [],
                topics: data.topics || [],
                stance_analysis: data.stance_analysis || ''
              }
            : result
        )
      );
      
      console.log('Summary generated with keywords:', data.keywords);
      console.log('Topics:', data.topics);
      console.log('Stance analysis:', data.stance_analysis);
    } catch (err) {
      console.error('Error generating summary:', err);
      alert('Failed to generate summary. Please try again.');
    } finally {
      setSummarizingId(null);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <button
              onClick={() => navigate('/')}
              className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              Back to Home
            </button>
            <h1 className="text-2xl font-bold text-gray-900">
              Article Search
            </h1>
            <div className="w-24"></div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {/* Search Box */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <div className="flex gap-4">
            <div className="flex-1">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Search for political articles, figures, or topics..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <button
              onClick={handleSearch}
              disabled={loading}
              className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Searching...
                </>
              ) : (
                <>
                  <Search className="w-5 h-5 mr-2" />
                  Search
                </>
              )}
            </button>
          </div>
          {error && (
            <p className="mt-4 text-red-600">{error}</p>
          )}
        </div>

        {/* Results */}
        {results.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              Found {results.length} results
            </h2>
            {results.map((result) => (
              <div
                key={result.id}
                className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
              >
                <div className="flex items-start justify-between mb-3">
                  <h3 className="text-lg font-semibold text-gray-900 flex-1">
                    {result.metadata.title || 'Untitled Article'}
                  </h3>
                  <span className="ml-4 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                    {(result.score * 100).toFixed(1)}% match
                  </span>
                </div>
                <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
                  {result.metadata.source && (
                    <span className="font-medium">{result.metadata.source}</span>
                  )}
                  {result.metadata.date && (
                    <span>{result.metadata.date}</span>
                  )}
                  {result.metadata.category && (
                    <span className="px-2 py-1 bg-gray-100 rounded">
                      {result.metadata.category}
                    </span>
                  )}
                </div>
                {result.metadata.persons && (
                  <div className="mb-3">
                    <span className="text-sm text-gray-600">Mentioned: </span>
                    <span className="text-sm font-medium text-gray-900">
                      {result.metadata.persons}
                    </span>
                  </div>
                )}
                <p className="text-gray-700 mb-4">
                  {result.content}
                </p>
                
                {/* Generate Summary Button */}
                <div className="flex justify-end pt-3 border-t border-gray-100">
                  <button
                    onClick={() => handleGenerateSummary(result.id)}
                    disabled={summarizingId === result.id}
                    className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {summarizingId === result.id ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Generating...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4" />
                        <span>Generate Summary</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* No Results */}
        {!loading && results.length === 0 && query && (
          <div className="text-center py-12">
            <Search className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              No results found
            </h3>
            <p className="text-gray-600">
              Try different keywords or search terms
            </p>
          </div>
        )}

        {/* Initial State */}
        {!loading && results.length === 0 && !query && (
          <div className="text-center py-12">
            <Search className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Start searching
            </h3>
            <p className="text-gray-600">
              Enter a query to search through political articles
            </p>
          </div>
        )}
      </main>
    </div>
  );
};

export default SearchPage;

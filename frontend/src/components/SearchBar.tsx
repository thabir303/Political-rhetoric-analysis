interface SearchBarProps {
  query: string
  setQuery: (query: string) => void
  onSearch: () => void
  loading: boolean
}

export default function SearchBar({ query, setQuery, onSearch, loading }: SearchBarProps) {
  return (
    <div className="max-w-4xl mx-auto mb-8">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex gap-4">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && onSearch()}
            placeholder="Search articles using semantic search..."
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-800"
          />
          <button
            onClick={onSearch}
            disabled={loading}
            className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-semibold"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </div>
    </div>
  )
}

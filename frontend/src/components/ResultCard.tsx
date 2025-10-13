interface ResultCardProps {
  result: {
    content: string
    distance: number
    metadata?: {
      title?: string
      date?: string
      category?: string
      source?: string
      persons?: string[]
      parties?: string[]
      themes?: string[]
    }
  }
  index: number
}

export default function ResultCard({ result }: ResultCardProps) {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start mb-3">
        <h3 className="text-xl font-semibold text-gray-800">
          {result.metadata?.title || 'Untitled'}
        </h3>
        <span className="text-sm text-gray-500 bg-blue-100 px-3 py-1 rounded-full">
          {(result.distance * 100).toFixed(1)}% match
        </span>
      </div>
      
      <p className="text-gray-600 mb-4 line-clamp-3">
        {result.content}
      </p>
      
      <div className="flex flex-wrap gap-2 text-sm text-gray-500">
        {result.metadata?.date && (
          <span className="bg-gray-100 px-2 py-1 rounded">
            📅 {result.metadata.date}
          </span>
        )}
        {result.metadata?.category && (
          <span className="bg-gray-100 px-2 py-1 rounded">
            🏷️ {result.metadata.category}
          </span>
        )}
        {result.metadata?.source && (
          <span className="bg-gray-100 px-2 py-1 rounded truncate max-w-xs">
            🔗 {result.metadata.source}
          </span>
        )}
        {result.metadata?.parties && result.metadata.parties.length > 0 && (
          <span className="bg-purple-100 px-2 py-1 rounded">
            🏛️ {result.metadata.parties.join(', ')}
          </span>
        )}
        {result.metadata?.persons && result.metadata.persons.length > 0 && (
          <span className="bg-green-100 px-2 py-1 rounded">
            👤 {result.metadata.persons.slice(0, 2).join(', ')}
            {result.metadata.persons.length > 2 && ` +${result.metadata.persons.length - 2}`}
          </span>
        )}
        {result.metadata?.themes && result.metadata.themes.length > 0 && (
          <span className="bg-yellow-100 px-2 py-1 rounded">
            🎯 {result.metadata.themes.slice(0, 2).join(', ')}
          </span>
        )}
      </div>
    </div>
  )
}

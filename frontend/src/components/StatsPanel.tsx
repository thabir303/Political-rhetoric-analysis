import { useState, useEffect } from 'react'
import { getStats } from '../utils/api'
import { formatDateToDDMMYYYY } from '../utils/dateFormat'

interface Stats {
  total_articles: number
  sources: string[]
  date_range: {
    earliest: string
    latest: string
  }
  categories: Record<string, number>
}

export default function StatsPanel() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [isOpen, setIsOpen] = useState(false)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const data = await getStats()
      setStats(data)
    } catch (error) {
      console.error('Failed to load stats:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return null

  if (!stats) return null

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {!isOpen ? (
        <button
          onClick={() => setIsOpen(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg shadow-lg hover:bg-blue-700 transition-colors"
        >
          📊 Stats
        </button>
      ) : (
        <div className="bg-white rounded-lg shadow-xl p-6 w-80">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-bold text-gray-800">Database Stats</h3>
            <button
              onClick={() => setIsOpen(false)}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>
          
          <div className="space-y-3">
            <div className="bg-blue-50 p-3 rounded">
              <div className="text-sm text-gray-600">Total Articles</div>
              <div className="text-2xl font-bold text-blue-600">
                {stats.total_articles.toLocaleString()}
              </div>
            </div>

            {stats.sources && stats.sources.length > 0 && (
              <div>
                <div className="text-sm text-gray-600 mb-2">Sources</div>
                <div className="flex flex-wrap gap-1">
                  {stats.sources.map((source, i) => (
                    <span key={i} className="bg-gray-100 px-2 py-1 rounded text-xs">
                      {source}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {stats.date_range && (
              <div>
                <div className="text-sm text-gray-600 mb-2">Date Range</div>
                <div className="text-xs text-gray-700">
                  {formatDateToDDMMYYYY(stats.date_range.earliest)} → {formatDateToDDMMYYYY(stats.date_range.latest)}
                </div>
              </div>
            )}

            <button
              onClick={loadStats}
              className="w-full text-sm text-blue-600 hover:text-blue-700"
            >
              🔄 Refresh
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

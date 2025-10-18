import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Loader2, Vote, TrendingUp, BarChart3, ArrowLeft } from 'lucide-react';
import { EnhancedArticleCard } from '../components/EnhancedArticleCard';

interface Article {
  id: string;
  title: string;
  summary: string;
  date: string;
  source: string;
  url: string;
  keywords: string[];
  topics: string[];
  has_election_impact: boolean;
  election_2026_impact: string;
  persons: string;
  language: string;
}

interface ElectionStats {
  total_articles: number;
  articles_with_impact: number;
  articles_without_impact: number;
  impact_percentage: number;
  impact_by_source: Record<string, any>;
  impact_by_party: Record<string, number>;
}

export function ElectionImpact() {
  const navigate = useNavigate();
  const [articles, setArticles] = useState<Article[]>([]);
  const [stats, setStats] = useState<ElectionStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Load articles and stats in parallel
      const [articlesRes, statsRes] = await Promise.all([
        axios.get('http://localhost:8000/api/v1/election-impact'),
        axios.get('http://localhost:8000/api/v1/election-impact/stats')
      ]);
      
      // Parse keywords and topics from comma-separated strings
      const processedArticles = articlesRes.data.articles.map((article: any) => ({
        ...article,
        keywords: typeof article.keywords === 'string' 
          ? article.keywords.split(',').map((k: string) => k.trim()).filter(Boolean)
          : article.keywords || [],
        topics: typeof article.topics === 'string'
          ? article.topics.split(',').map((t: string) => t.trim()).filter(Boolean)
          : article.topics || [],
      }));
      
      setArticles(processedArticles);
      setTotalCount(articlesRes.data.total_count);
      setStats(statsRes.data);
    } catch (err: any) {
      console.error('Error loading data:', err);
      setError(err.response?.data?.detail || 'Failed to load election impact data');
    } finally {
      setLoading(false);
    }
  };

  const handleTopicClick = (topic: string) => {
    navigate(`/topics/${encodeURIComponent(topic)}`);
  };

  const handleKeywordClick = (keyword: string) => {
    navigate(`/keywords/${encodeURIComponent(keyword)}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50 py-8">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-12 h-12 animate-spin text-purple-600" />
            <span className="ml-4 text-xl text-gray-600">Loading election impact analysis...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50 py-8">
        <div className="container mx-auto px-4">
          <div className="bg-red-50 border border-red-200 rounded-lg p-8 max-w-2xl mx-auto">
            <div className="flex items-center gap-3 text-red-800 mb-4">
              <span className="text-3xl">⚠️</span>
              <div>
                <h2 className="text-xl font-semibold">Error Loading Data</h2>
                <p className="text-sm mt-1">{error}</p>
              </div>
            </div>
            <button
              onClick={loadData}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50 py-8">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-800 mb-4 transition"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>Back to Home</span>
          </button>

          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center gap-3 mb-2">
              <Vote className="w-10 h-10 text-purple-600" />
              <h1 className="text-4xl font-bold text-gray-800">
                2026 বাংলাদেশ নির্বাচন প্রভাব বিশ্লেষণ
              </h1>
            </div>
            <p className="text-gray-600 text-lg">
              Articles with potential impact on Bangladesh's 2026 election
            </p>
          </div>
        </div>

        {/* Statistics Dashboard */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {/* Total Articles */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex items-center justify-between mb-2">
                <BarChart3 className="w-8 h-8 text-blue-600" />
                <span className="text-3xl font-bold text-blue-600">
                  {stats.total_articles}
                </span>
              </div>
              <div className="text-gray-600 font-semibold">Total Articles</div>
            </div>

            {/* With Impact */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex items-center justify-between mb-2">
                <TrendingUp className="w-8 h-8 text-green-600" />
                <span className="text-3xl font-bold text-green-600">
                  {stats.articles_with_impact}
                </span>
              </div>
              <div className="text-gray-600 font-semibold">With Impact</div>
            </div>

            {/* Without Impact */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-3xl">📊</span>
                <span className="text-3xl font-bold text-gray-600">
                  {stats.articles_without_impact}
                </span>
              </div>
              <div className="text-gray-600 font-semibold">Without Impact</div>
            </div>

            {/* Impact Percentage */}
            <div className="bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg shadow-lg p-6 text-white">
              <div className="flex items-center justify-between mb-2">
                <Vote className="w-8 h-8" />
                <span className="text-3xl font-bold">
                  {stats.impact_percentage}%
                </span>
              </div>
              <div className="font-semibold">Impact Rate</div>
            </div>
          </div>
        )}

        {/* Impact by Party */}
        {stats && Object.keys(stats.impact_by_party).length > 0 && (
          <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
              <span>🏛️</span>
              <span>Impact by Political Party</span>
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {Object.entries(stats.impact_by_party).map(([party, count]) => (
                <div key={party} className="border rounded-lg p-4 hover:shadow-md transition">
                  <div className="text-2xl font-bold text-purple-600">{count}</div>
                  <div className="text-gray-700 font-semibold">{party}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Articles List */}
        <div className="mb-4">
          <h2 className="text-2xl font-bold text-gray-800">
            Articles with Election Impact ({totalCount})
          </h2>
        </div>

        {articles.length === 0 ? (
          <div className="bg-white rounded-lg shadow-lg p-12 text-center">
            <div className="text-6xl mb-4">🗳️</div>
            <h2 className="text-2xl font-semibold text-gray-800 mb-2">
              No Election Impact Articles
            </h2>
            <p className="text-gray-600">
              No articles with 2026 election impact found. Articles need to be analyzed first.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {articles.map((article) => (
              <EnhancedArticleCard
                key={article.id}
                article={article}
                onTopicClick={handleTopicClick}
                onKeywordClick={handleKeywordClick}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

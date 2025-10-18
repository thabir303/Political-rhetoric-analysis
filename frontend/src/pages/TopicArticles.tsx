import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, Loader2, Tag } from 'lucide-react';
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

export function TopicArticles() {
  const { topic } = useParams<{ topic: string }>();
  const navigate = useNavigate();
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    if (topic) {
      loadArticles();
    }
  }, [topic]);

  const loadArticles = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(
        `http://localhost:8000/api/v1/topics/${encodeURIComponent(topic!)}/articles`
      );
      
      // Parse keywords and topics from comma-separated strings
      const processedArticles = response.data.articles.map((article: any) => ({
        ...article,
        keywords: typeof article.keywords === 'string' 
          ? article.keywords.split(',').map((k: string) => k.trim()).filter(Boolean)
          : article.keywords || [],
        topics: typeof article.topics === 'string'
          ? article.topics.split(',').map((t: string) => t.trim()).filter(Boolean)
          : article.topics || [],
      }));
      
      setArticles(processedArticles);
      setTotalCount(response.data.total_count);
    } catch (err: any) {
      console.error('Error loading articles:', err);
      setError(err.response?.data?.detail || 'Failed to load articles');
    } finally {
      setLoading(false);
    }
  };

  const handleTopicClick = (clickedTopic: string) => {
    navigate(`/topics/${encodeURIComponent(clickedTopic)}`);
  };

  const handleKeywordClick = (keyword: string) => {
    navigate(`/keywords/${encodeURIComponent(keyword)}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 py-8">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-12 h-12 animate-spin text-blue-600" />
            <span className="ml-4 text-xl text-gray-600">Loading articles...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 py-8">
        <div className="container mx-auto px-4">
          <div className="bg-red-50 border border-red-200 rounded-lg p-8 max-w-2xl mx-auto">
            <div className="flex items-center gap-3 text-red-800 mb-4">
              <span className="text-3xl">⚠️</span>
              <div>
                <h2 className="text-xl font-semibold">Error Loading Articles</h2>
                <p className="text-sm mt-1">{error}</p>
              </div>
            </div>
            <div className="flex gap-3">
              <button
                onClick={loadArticles}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition"
              >
                Retry
              </button>
              <button
                onClick={() => navigate(-1)}
                className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition"
              >
                Go Back
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 py-8">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-800 mb-4 transition"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>Back</span>
          </button>

          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center gap-3 mb-2">
              <Tag className="w-8 h-8 text-blue-600" />
              <h1 className="text-3xl font-bold text-gray-800">
                Articles about "{topic}"
              </h1>
            </div>
            <p className="text-gray-600 text-lg">
              {totalCount} {totalCount === 1 ? 'article' : 'articles'} found
            </p>
          </div>
        </div>

        {/* Articles List */}
        {articles.length === 0 ? (
          <div className="bg-white rounded-lg shadow-lg p-12 text-center">
            <div className="text-6xl mb-4">📭</div>
            <h2 className="text-2xl font-semibold text-gray-800 mb-2">
              No Articles Found
            </h2>
            <p className="text-gray-600">
              No articles found for this topic. Try a different topic or check back later.
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

import React from 'react';
import { ExternalLink } from 'lucide-react';

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

interface EnhancedArticleCardProps {
  article: Article;
  onTopicClick?: (topic: string) => void;
  onKeywordClick?: (keyword: string) => void;
}

export function EnhancedArticleCard({ article, onTopicClick, onKeywordClick }: EnhancedArticleCardProps) {
  const handleTopicClick = (topic: string, e: React.MouseEvent) => {
    e.preventDefault();
    if (onTopicClick) {
      onTopicClick(topic);
    }
  };

  const handleKeywordClick = (keyword: string, e: React.MouseEvent) => {
    e.preventDefault();
    if (onKeywordClick) {
      onKeywordClick(keyword);
    }
  };

  return (
    <div className="border border-gray-200 rounded-lg p-6 bg-white shadow-sm hover:shadow-md transition-shadow duration-200">
      {/* Title */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xl font-bold text-blue-600 hover:text-blue-800 transition-colors flex items-center gap-2 flex-1"
        >
          <span className="line-clamp-2">{article.title}</span>
          <ExternalLink className="w-4 h-4 flex-shrink-0" />
        </a>
      </div>

      {/* Metadata */}
      <div className="flex flex-wrap gap-3 text-sm text-gray-600 mb-4">
        <span className="flex items-center gap-1">
          📅 {article.date}
        </span>
        <span className="flex items-center gap-1">
          📰 {article.source}
        </span>
        {article.persons && (
          <span className="flex items-center gap-1">
            👤 {article.persons}
          </span>
        )}
        <span className="flex items-center gap-1 px-2 py-0.5 bg-gray-100 rounded">
          {article.language === 'bangla' ? '🇧🇩 বাংলা' : '🇬🇧 English'}
        </span>
      </div>

      {/* Summary */}
      <p className="text-gray-700 leading-relaxed mb-4">
        {article.summary}
      </p>

      {/* Keywords */}
      {article.keywords && article.keywords.length > 0 && (
        <div className="mb-3">
          <div className="text-xs font-semibold text-gray-500 mb-2">KEYWORDS:</div>
          <div className="flex flex-wrap gap-2">
            {article.keywords.map((keyword, idx) => (
              <button
                key={idx}
                onClick={(e) => handleKeywordClick(keyword, e)}
                className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm hover:bg-blue-100 transition-colors cursor-pointer border border-blue-200"
              >
                #{keyword}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Topics */}
      {article.topics && article.topics.length > 0 && (
        <div className="mb-4">
          <div className="text-xs font-semibold text-gray-500 mb-2">TOPICS:</div>
          <div className="flex flex-wrap gap-2">
            {article.topics.map((topic, idx) => (
              <button
                key={idx}
                onClick={(e) => handleTopicClick(topic, e)}
                className="px-3 py-1.5 bg-green-50 text-green-700 rounded-lg text-sm hover:bg-green-100 transition-colors cursor-pointer border border-green-200 flex items-center gap-1"
              >
                🏷️ {topic}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Election Impact */}
      {article.has_election_impact && article.election_2026_impact && (
        <div className="mt-4 p-4 bg-gradient-to-r from-purple-50 to-pink-50 border-l-4 border-purple-500 rounded-r-lg">
          <div className="flex items-center gap-2 font-semibold text-purple-900 mb-2">
            <span className="text-lg">🗳️</span>
            <span>2026 বাংলাদেশ নির্বাচনে প্রভাব</span>
          </div>
          <p className="text-sm text-purple-800 leading-relaxed">
            {article.election_2026_impact}
          </p>
        </div>
      )}
    </div>
  );
}

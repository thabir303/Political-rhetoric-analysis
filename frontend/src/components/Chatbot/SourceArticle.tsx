import React from 'react';
import { ExternalLink, Calendar, FileText } from 'lucide-react';

interface SourceArticleProps {
  title: string;
  date: string;
  source: string;
  url?: string;
  relevance_score?: number;
}

const SourceArticle: React.FC<SourceArticleProps> = ({
  title,
  date,
  source,
  url,
  relevance_score,
}) => {
  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-1">
            {title}
          </h4>
          
          <div className="flex items-center gap-3 text-xs text-gray-600 dark:text-gray-400">
            <span className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              {new Date(date).toLocaleDateString()}
            </span>
            <span className="flex items-center gap-1">
              <FileText className="w-3 h-3" />
              {source}
            </span>
          </div>
        </div>

        {relevance_score && (
          <div className="flex-shrink-0">
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
              {(relevance_score * 100).toFixed(0)}%
            </span>
          </div>
        )}
      </div>

      {url && (
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 mt-2"
        >
          Read full article
          <ExternalLink className="w-3 h-3" />
        </a>
      )}
    </div>
  );
};

export default SourceArticle;

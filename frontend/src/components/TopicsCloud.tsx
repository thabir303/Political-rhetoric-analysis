import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { TrendingUp, Loader2 } from 'lucide-react';

interface Topic {
  topic: string;
  article_count: number;
  percentage: number;
}

interface TopicsCloudProps {
  onTopicClick?: (topic: string) => void;
}

export function TopicsCloud({ onTopicClick }: TopicsCloudProps) {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadTopics();
  }, []);

  const loadTopics = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get('http://localhost:8000/api/v1/topics');
      setTopics(response.data.topics);
    } catch (err: any) {
      console.error('Error loading topics:', err);
      setError(err.response?.data?.detail || 'Failed to load topics');
    } finally {
      setLoading(false);
    }
  };

  const handleTopicClick = (topic: string) => {
    if (onTopicClick) {
      onTopicClick(topic);
    }
  };

  const getTopicColor = (index: number) => {
    const colors = [
      'from-blue-500 to-blue-600',
      'from-green-500 to-green-600',
      'from-purple-500 to-purple-600',
      'from-pink-500 to-pink-600',
      'from-indigo-500 to-indigo-600',
      'from-orange-500 to-orange-600',
      'from-teal-500 to-teal-600',
      'from-red-500 to-red-600',
    ];
    return colors[index % colors.length];
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-8">
        <div className="flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          <span className="ml-3 text-gray-600">Loading topics...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center gap-2 text-red-800">
          <span className="text-xl">⚠️</span>
          <span className="font-semibold">Error: {error}</span>
        </div>
        <button
          onClick={loadTopics}
          className="mt-3 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center gap-3 mb-6">
        <TrendingUp className="w-6 h-6 text-blue-600" />
        <h2 className="text-2xl font-bold text-gray-800">Topics Dashboard</h2>
        <span className="ml-auto px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-semibold">
          {topics.length} Topics
        </span>
      </div>

      {topics.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <p className="text-lg">No topics found</p>
          <p className="text-sm mt-2">Articles need to be analyzed first</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {topics.map((topic, index) => (
            <button
              key={topic.topic}
              onClick={() => handleTopicClick(topic.topic)}
              className="group relative overflow-hidden rounded-lg shadow-md hover:shadow-xl transition-all duration-300 transform hover:scale-105"
            >
              <div className={`absolute inset-0 bg-gradient-to-br ${getTopicColor(index)} opacity-90 group-hover:opacity-100 transition-opacity`} />
              
              <div className="relative p-5 text-white">
                <div className="flex items-start justify-between mb-2">
                  <span className="text-2xl">🏷️</span>
                  <span className="px-2 py-1 bg-white bg-opacity-30 rounded text-xs font-semibold">
                    {topic.percentage}%
                  </span>
                </div>
                
                <div className="font-bold text-lg mb-2 line-clamp-2">
                  {topic.topic}
                </div>
                
                <div className="flex items-center gap-2 text-sm opacity-90">
                  <span className="font-semibold">{topic.article_count}</span>
                  <span>articles</span>
                </div>
              </div>

              <div className="absolute bottom-0 left-0 right-0 h-1 bg-white opacity-0 group-hover:opacity-100 transition-opacity" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

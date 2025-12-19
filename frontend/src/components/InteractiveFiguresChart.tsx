import React, { useState } from 'react';
import { Users, TrendingUp, Award, FileText } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';

interface FigureData {
  fullName: string;
  articles: number;
}

interface InteractiveFiguresChartProps {
  figuresData: FigureData[];
  categoryColor: string;
  categoryName?: string;
  onFigureClick?: (figureName: string) => void;
}

const InteractiveFiguresChart: React.FC<InteractiveFiguresChartProps> = ({
  figuresData,
  categoryColor,
  categoryName,
  onFigureClick
}) => {
  const [viewMode, setViewMode] = useState<'top10' | 'all'>('top10');
  const [sortBy, setSortBy] = useState<'articles' | 'name'>('articles');
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const [selectedFigure, setSelectedFigure] = useState<string | null>(null);
  const [showArticles, setShowArticles] = useState(false);
  const [loadingArticles, setLoadingArticles] = useState(false);
  const [articles, setArticles] = useState<any[]>([]);

  if (!figuresData || figuresData.length === 0) {
    return (
      <div className="bg-white rounded-2xl shadow-xl shadow-gray-300/60 p-6 border-2 border-blue-300">
        <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
          <Users className="w-5 h-5 mr-2" style={{ color: categoryColor }} />
          All Political Figures
        </h3>
        <p className="text-gray-500 text-center py-8">No political figures data available</p>
      </div>
    );
  }

  // Sort data
  const sortedData = [...figuresData].sort((a, b) => {
    if (sortBy === 'articles') {
      return b.articles - a.articles;
    }
    return a.fullName.localeCompare(b.fullName);
  });

  // Filter data based on view mode
  const displayData = viewMode === 'top10' ? sortedData.slice(0, 10) : sortedData;

  // Calculate statistics
  const totalArticles = figuresData.reduce((sum, fig) => sum + fig.articles, 0);
  const avgArticles = Math.round(totalArticles / figuresData.length);
  const topFigure = sortedData[0];

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const percentage = ((data.articles / totalArticles) * 100).toFixed(1);

      return (
        <div className="bg-white p-4 rounded-lg shadow-lg border border-gray-200">
          <p className="font-bold text-gray-900 mb-2">{data.fullName}</p>
          <div className="space-y-1 text-sm">
            <p className="text-gray-700">
              <span className="font-medium">Articles:</span> {data.articles}
            </p>
            <p className="text-gray-600">
              <span className="font-medium">Share:</span> {percentage}%
            </p>
            <p className="text-gray-600">
              <span className="font-medium">Rank:</span> #{sortedData.findIndex(f => f.fullName === data.fullName) + 1}
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  // Fetch articles for a figure
  const fetchArticlesForFigure = async (figureName: string) => {
    if (!categoryName) return;

    setLoadingArticles(true);
    setShowArticles(true);

    try {
      // Search for articles mentioning this figure in this category
      const response = await fetch(
        `http://localhost:8000/categories/${encodeURIComponent(categoryName)}/articles?limit=50`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        // Filter articles that mention this figure
        const filtered = data.articles.filter((article: any) =>
          article.people.some((person: string) =>
            person.toLowerCase().includes(figureName.toLowerCase()) ||
            figureName.toLowerCase().includes(person.toLowerCase())
          )
        );
        setArticles(filtered);
      }
    } catch (error) {
      console.error('Error fetching articles:', error);
      setArticles([]);
    } finally {
      setLoadingArticles(false);
    }
  };

  // Handle figure click
  const handleFigureClick = (data: any) => {
    setSelectedFigure(data.fullName);
    fetchArticlesForFigure(data.fullName);
    if (onFigureClick) {
      onFigureClick(data.fullName);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-xl shadow-gray-300/60 p-6 border-2 border-blue-300 hover:shadow-2xl hover:border-blue-500 hover:scale-[1.02] transition-all duration-500">
      {/* Header with Stats */}
      <div className="mb-4">
        <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center justify-between">
          <span className="flex items-center">
            <Users className="w-5 h-5 mr-2" style={{ color: categoryColor }} />
            All Political Figures ({figuresData.length})
          </span>
        </h3>

        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-3 mb-3">
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-2">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-blue-600 font-medium mb-1">Total Figures</p>
                <p className="text-xl font-bold text-blue-900">{figuresData.length}</p>
              </div>
              <Users className="w-6 h-6 text-blue-400 opacity-50" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-2">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-green-600 font-medium mb-1">Avg Articles</p>
                <p className="text-xl font-bold text-green-900">{avgArticles}</p>
              </div>
              <TrendingUp className="w-6 h-6 text-green-400 opacity-50" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-2">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-purple-600 font-medium mb-1">Top Figure</p>
                <p className="text-lg font-bold text-purple-900 truncate" title={topFigure?.fullName}>
                  {topFigure?.fullName?.split(' ')[0]}
                </p>
              </div>
              <Award className="w-6 h-6 text-purple-400 opacity-50" />
            </div>
          </div>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap gap-2 items-center justify-between">
          <div className="flex gap-2">
            <button
              onClick={() => setViewMode('top10')}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${viewMode === 'top10'
                  ? 'bg-blue-500 text-white shadow-md'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
            >
              Top 10
            </button>
            <button
              onClick={() => setViewMode('all')}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${viewMode === 'all'
                  ? 'bg-blue-500 text-white shadow-md'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
            >
              All
            </button>
          </div>

          <div className="flex gap-2 items-center flex-wrap">
            <span className="text-xs text-gray-500">Sort:</span>
            <div className="flex gap-1">
              <button
                onClick={() => setSortBy('articles')}
                className={`px-2 py-1 rounded text-xs font-medium transition-all ${sortBy === 'articles'
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
              >
                Count {sortBy === 'articles' && '▼'}
              </button>
              <button
                onClick={() => setSortBy('name')}
                className={`px-2 py-1 rounded text-xs font-medium transition-all ${sortBy === 'name'
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
              >
                Name {sortBy === 'name' && '▲'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Interactive Bar Chart */}
      <div className="mb-3">
        <ResponsiveContainer width="100%" height={350}>
          <BarChart
            data={displayData}
            margin={{ top: 10, right: 30, left: 0, bottom: 60 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="fullName"
              stroke="#6b7280"
              angle={-45}
              textAnchor="end"
              height={80}
              tick={{ fontSize: 10 }}
            />
            <YAxis
              stroke="#6b7280"
              tick={{ fontSize: 12 }}
              label={{ value: 'Articles', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar
              dataKey="articles"
              fill={categoryColor}
              radius={[8, 8, 0, 0]}
              cursor="pointer"
              onClick={(_data: any, index: number) => handleFigureClick(displayData[index])}
              onMouseEnter={(_data: any, index: number) => setHoveredIndex(index)}
              onMouseLeave={() => setHoveredIndex(null)}
            >
              {displayData.map((entry, index) => {
                const isSelected = selectedFigure === entry.fullName;
                const isHovered = hoveredIndex === index;
                return (
                  <Cell
                    key={`cell-${index}`}
                    fill={isSelected ? '#1e40af' : isHovered ? '#3b82f6' : categoryColor}
                    opacity={isSelected ? 1 : isHovered ? 0.8 : 0.7}
                  />
                );
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        {/* <p className="text-xs text-gray-500 text-center mt-2">
          💡 Click on any point to see articles mentioning that figure
        </p> */}
      </div>

      {/* Selected Figure Info with Articles */}
      {selectedFigure && (
        <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center justify-between mb-3">
            <div>
              <p className="text-sm text-blue-600 font-medium mb-1">Selected Figure</p>
              <p className="text-lg font-bold text-blue-900">{selectedFigure}</p>
              <p className="text-sm text-blue-700 mt-1">
                {displayData.find(f => f.fullName === selectedFigure)?.articles} articles found
              </p>
            </div>
            <button
              onClick={() => {
                setSelectedFigure(null);
                setShowArticles(false);
                setArticles([]);
              }}
              className="px-3 py-1.5 bg-white hover:bg-blue-100 text-blue-700 rounded-lg text-sm font-medium transition-colors"
            >
              Clear
            </button>
          </div>

          {/* Articles List */}
          {showArticles && (
            <div className="mt-3 pt-3 border-t border-blue-200">
              {loadingArticles ? (
                <div className="text-center py-4">
                  <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                  <p className="text-sm text-gray-600 mt-2">Loading articles...</p>
                </div>
              ) : articles.length > 0 ? (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  <p className="text-xs font-medium text-gray-700 mb-2 flex items-center">
                    <FileText className="w-4 h-4 mr-1" />
                    Articles mentioning {selectedFigure}:
                  </p>
                  {articles.map((article: any, idx: number) => (
                    <div
                      key={idx}
                      className="p-2 bg-white rounded border border-gray-200 hover:border-blue-300 transition-colors cursor-pointer"
                      onClick={() => window.open(article.url, '_blank')}
                    >
                      <p className="text-sm font-medium text-gray-900 line-clamp-2 mb-1">
                        {article.title}
                      </p>
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        <span>{article.source}</span>
                        <span>•</span>
                        <span>{article.date}</span>
                        {article.parties.length > 0 && (
                          <>
                            <span>•</span>
                            <span className="text-blue-600">{article.parties[0]}</span>
                          </>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500 text-center py-4">
                  No articles found for this figure
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Footer Stats */}
      <div className="mt-3 pt-3 border-t border-gray-200">
        <div className="flex justify-between items-center text-xs text-gray-600">
          <span>
            Showing {displayData.length} of {figuresData.length} figures
          </span>
          <span>
            Total: {totalArticles} articles
          </span>
        </div>
      </div>
    </div>
  );
};

export default InteractiveFiguresChart;

import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Filter, Search, Loader2, TrendingUp, Users, Calendar, Newspaper, Quote, PieChart as PieChartIcon } from 'lucide-react';
import {
  LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import {
  getCategoryDetailedStats,
  getCategoryPartyBreakdown,
  getArticlesByCategory
} from '../utils/api';
import { getCategoryColor, getPartyColor } from '../utils/partyColors';
import InteractiveFiguresChart from '../components/InteractiveFiguresChart';
import HighlightedText from '../components/HighlightedText';
import Pagination from '../components/Pagination';

interface Article {
  id: string;
  title: string;
  content: string;
  date: string;
  source: string;
  url: string;
  parties: string[];
  people: string[];
  primary_category: string;
  all_categories: string[];
  is_primary: boolean;
  relevant_excerpt?: string; // Speech excerpt for this category
  category_reasoning?: string; // Why this was categorized
}

const CategoryDetailPage = () => {
  const { categoryName } = useParams<{ categoryName: string }>();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<any>(null);
  const [partyBreakdown, setPartyBreakdown] = useState<any>(null);
  const [articles, setArticles] = useState<Article[]>([]);
  const [totalArticles, setTotalArticles] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  // Filters
  const [selectedParty, setSelectedParty] = useState<string>('');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [source, setSource] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Expanded articles state for "See more" feature
  const [expandedArticles, setExpandedArticles] = useState<Set<string>>(new Set());

  const toggleArticleExpand = (articleId: string) => {
    setExpandedArticles(prev => {
      const newSet = new Set(prev);
      if (newSet.has(articleId)) {
        newSet.delete(articleId);
      } else {
        newSet.add(articleId);
      }
      return newSet;
    });
  };

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(20);

  const decodedCategoryName = decodeURIComponent(categoryName || '');
  const categoryColor = getCategoryColor(decodedCategoryName);

  useEffect(() => {
    if (categoryName) {
      loadData();
    }
  }, [categoryName]);

  const loadData = async () => {
    try {
      setLoading(true);

      const [statsRes, breakdownRes, articlesRes] = await Promise.all([
        getCategoryDetailedStats(decodedCategoryName),
        getCategoryPartyBreakdown(decodedCategoryName),
        getArticlesByCategory(decodedCategoryName, undefined, undefined, undefined, undefined, 1, 20)
      ]);

      if (statsRes.success) {
        setStats(statsRes);
      }

      if (breakdownRes.success) {
        setPartyBreakdown(breakdownRes);
      }

      if (articlesRes.success) {
        setArticles(articlesRes.articles);
        setTotalArticles(articlesRes.total_articles || 0);
        setTotalPages(articlesRes.total_pages || 1);
      }

    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = async () => {
    try {
      setLoading(true);
      setCurrentPage(1);

      const articlesRes = await getArticlesByCategory(
        decodedCategoryName,
        selectedParty || undefined,
        startDate || undefined,
        endDate || undefined,
        source || undefined,
        1,
        itemsPerPage
      );

      if (articlesRes.success) {
        setArticles(articlesRes.articles);
        setTotalArticles(articlesRes.total_articles || 0);
        setTotalPages(articlesRes.total_pages || 1);
      }

      // Also update party breakdown with date filters
      const breakdownRes = await getCategoryPartyBreakdown(
        decodedCategoryName,
        startDate || undefined,
        endDate || undefined
      );

      if (breakdownRes.success) {
        setPartyBreakdown(breakdownRes);
      }

    } catch (error) {
      console.error('Error applying filters:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = async (page: number) => {
    setCurrentPage(page);
    try {
      setLoading(true);
      const articlesRes = await getArticlesByCategory(
        decodedCategoryName,
        selectedParty || undefined,
        startDate || undefined,
        endDate || undefined,
        source || undefined,
        page,
        itemsPerPage
      );

      if (articlesRes.success) {
        setArticles(articlesRes.articles);
        setTotalArticles(articlesRes.total_articles || 0);
        setTotalPages(articlesRes.total_pages || 1);
      }
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (error) {
      console.error('Error changing page:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleItemsPerPageChange = async (items: number) => {
    setItemsPerPage(items);
    setCurrentPage(1);
    try {
      setLoading(true);
      const articlesRes = await getArticlesByCategory(
        decodedCategoryName,
        selectedParty || undefined,
        startDate || undefined,
        endDate || undefined,
        source || undefined,
        1,
        items
      );

      if (articlesRes.success) {
        setArticles(articlesRes.articles);
        setTotalArticles(articlesRes.total_articles || 0);
        setTotalPages(articlesRes.total_pages || 1);
      }
    } catch (error) {
      console.error('Error changing items per page:', error);
    } finally {
      setLoading(false);
    }
  };

  const clearFilters = () => {
    setSelectedParty('');
    setStartDate('');
    setEndDate('');
    setSource('');
    setSearchQuery('');
    loadData();
  };

  if (loading && !stats) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/20 flex items-center justify-center relative overflow-hidden">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-1/2 -right-1/4 w-96 h-96 bg-blue-200/20 rounded-full blur-3xl animate-pulse"></div>
          <div className="absolute top-1/3 -left-1/4 w-96 h-96 bg-indigo-200/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
        </div>
        <div className="backdrop-blur-xl bg-white/60 rounded-3xl shadow-2xl p-12 border-2 border-gray-200/80 z-10">
          <Loader2 className="w-16 h-16 animate-spin text-blue-600 mx-auto mb-6" />
          <p className="text-gray-800 font-semibold text-lg">Loading category data...</p>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/20 flex items-center justify-center relative overflow-hidden">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-1/2 -right-1/4 w-96 h-96 bg-blue-200/20 rounded-full blur-3xl animate-pulse"></div>
        </div>
        <div className="backdrop-blur-xl bg-white/60 rounded-3xl shadow-2xl p-12 border-2 border-gray-200/80 text-center z-10">
          <p className="text-gray-800 font-semibold text-xl mb-6">Category not found</p>
          <button
            onClick={() => navigate('/categories')}
            className="px-8 py-3 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 cursor-pointer"
          >
            Back to Categories
          </button>
        </div>
      </div>
    );
  }

  // Prepare chart data
  const pieChartData = partyBreakdown?.top_parties?.map((item: any) => ({
    name: item.party,
    value: item.count,
    color: getPartyColor(item.party)
  })) || [];

  // Show ALL figures, not just top 10
  const allFiguresData = stats?.top_people?.map((item: any) => ({
    name: item.name.length > 25 ? item.name.substring(0, 25) + '...' : item.name,
    fullName: item.name,
    articles: item.count
  })) || [];

  const timeSeriesData = stats?.monthly_trend || [];

  // Custom Tooltip with Glassmorphism
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="backdrop-blur-xl bg-white/90 p-4 border-2 border-gray-200/80 rounded-2xl shadow-2xl">
          <p className="font-bold text-gray-900 mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }} className="text-sm font-medium">
              {entry.name}: <span className="font-bold">{entry.value}</span>
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  // Filter articles by search
  const filteredArticles = articles.filter(article =>
    article.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    article.content.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/20 relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-1/2 -right-1/4 w-96 h-96 bg-blue-200/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute top-1/3 -left-1/4 w-96 h-96 bg-indigo-200/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-200/20 rounded-full blur-3xl animate-pulse delay-2000"></div>
      </div>

      {/* Header with Enhanced Glassmorphism */}
      <header className="sticky top-0 z-50 backdrop-blur-md bg-white/40 border-b border-white/30 shadow-lg shadow-gray-200/30">
        <div className="max-w-7xl mx-auto px-4 py-5 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <button
              onClick={() => navigate('/categories')}
              className="group flex items-center px-4 py-2.5 text-gray-800 hover:text-gray-900 transition-all duration-300 rounded-xl hover:bg-white/60 backdrop-blur-sm border-2 border-gray-200/80 shadow-md hover:shadow-xl cursor-pointer"
            >
              <ArrowLeft className="w-5 h-5 mr-2 group-hover:-translate-x-1 transition-transform" />
              <span className="font-semibold">Back to Categories</span>
            </button>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-gray-900 via-gray-800 to-gray-700 bg-clip-text text-transparent drop-shadow-sm">
              {decodedCategoryName}
            </h1>
            <div className="w-32"></div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8 z-10">
        {/* Category Info with Glassmorphism */}
        <div
          className="backdrop-blur-xl bg-white/60 rounded-2xl shadow-2xl shadow-gray-300/60 p-8 mb-8 border-2 border-gray-200/80 hover:shadow-2xl hover:border-blue-300/80 transition-all duration-300"
          style={{ borderLeft: `6px solid ${categoryColor}` }}
        >
          <h2 className="text-2xl font-bold text-gray-900 mb-3 flex items-center gap-3">
            <div className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: categoryColor }}></div>
            {decodedCategoryName}
          </h2>
          <p className="text-gray-700 leading-relaxed">{stats.description}</p>
        </div>

        {/* Stats Overview with Glass Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="group backdrop-blur-lg bg-gradient-to-br from-white/70 to-white/40 rounded-2xl shadow-lg shadow-blue-100/40 p-6 border-2 border-blue-300 hover:shadow-xl hover:scale-105 hover:border-blue-500 transition-all duration-300">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 font-semibold uppercase tracking-wide mb-2">Total Articles</p>
                <p className="text-4xl font-bold bg-gradient-to-br from-blue-600 to-blue-400 bg-clip-text text-transparent">{stats.total_articles}</p>
              </div>
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500/20 to-blue-400/10 flex items-center justify-center group-hover:scale-110 transition-transform">
                <TrendingUp className="w-8 h-8 text-blue-600" />
              </div>
            </div>
          </div>

          <div className="group backdrop-blur-lg bg-gradient-to-br from-white/70 to-white/40 rounded-2xl shadow-lg shadow-green-100/40 p-6 border-2 border-green-300 hover:shadow-xl hover:scale-105 hover:border-green-500 transition-all duration-300">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 font-semibold uppercase tracking-wide mb-2">As Primary</p>
                <p className="text-4xl font-bold bg-gradient-to-br from-green-600 to-green-400 bg-clip-text text-transparent">{stats.as_primary_category}</p>
              </div>
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-green-500/20 to-green-400/10 flex items-center justify-center group-hover:scale-110 transition-transform">
                <Users className="w-8 h-8 text-green-600" />
              </div>
            </div>
          </div>

          <div className="group backdrop-blur-lg bg-gradient-to-br from-white/70 to-white/40 rounded-2xl shadow-lg shadow-orange-100/20 p-6 border-2 border-orange-300 hover:shadow-xl hover:scale-105 hover:border-orange-500 transition-all duration-300">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 font-semibold uppercase tracking-wide mb-2">As Secondary</p>
                <p className="text-4xl font-bold bg-gradient-to-br from-orange-600 to-orange-400 bg-clip-text text-transparent">{stats.as_secondary_category}</p>
              </div>
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-orange-500/20 to-orange-400/10 flex items-center justify-center group-hover:scale-110 transition-transform">
                <Calendar className="w-8 h-8 text-orange-600" />
              </div>
            </div>
          </div>

          <div className="group backdrop-blur-lg bg-gradient-to-br from-white/70 to-white/40 rounded-2xl shadow-lg shadow-purple-100/40 p-6 border-2 border-purple-300 hover:shadow-xl hover:scale-105 hover:border-purple-500 transition-all duration-300">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 font-semibold uppercase tracking-wide mb-2">Parties</p>
                <p className="text-4xl font-bold bg-gradient-to-br from-purple-600 to-purple-400 bg-clip-text text-transparent">
                  {stats.top_parties?.length || 0}
                </p>
              </div>
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-500/20 to-purple-400/10 flex items-center justify-center group-hover:scale-110 transition-transform">
                <Users className="w-8 h-8 text-purple-600" />
              </div>
            </div>
          </div>
        </div>

        {/* Charts Row 1: Party Breakdown (Pie) + Top People (Bar) */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8 items-start">
          {/* Pie Chart - Party Breakdown */}
          <div className="group backdrop-blur-xl bg-gradient-to-br from-white/70 via-white/60 to-white/50 rounded-2xl shadow-2xl shadow-purple-200/40 p-8 border-2 border-purple-300 hover:shadow-2xl hover:border-purple-500 hover:scale-[1.02] transition-all duration-500">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500/20 to-pink-500/20 flex items-center justify-center shadow-md group-hover:scale-110 transition-transform">
                  <PieChartIcon className="w-5 h-5 text-purple-600" />
                </div>
                <span className="bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">Party-wise Distribution</span>
              </h3>
              {selectedParty && (
                <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-semibold animate-pulse">
                  Filtered: {selectedParty}
                </span>
              )}
            </div>

            {/* Stats Summary */}
            <div className="grid grid-cols-3 gap-2 mb-4">
              <div className="bg-gradient-to-br from-blue-50 to-blue-100/50 rounded-lg p-2 text-center">
                <p className="text-xs text-blue-600 font-medium">Total Parties</p>
                <p className="text-lg font-bold text-blue-900">{pieChartData.length}</p>
              </div>
              <div className="bg-gradient-to-br from-green-50 to-green-100/50 rounded-lg p-2 text-center">
                <p className="text-xs text-green-600 font-medium">Top Party</p>
                <p className="text-sm font-bold text-green-900 truncate" title={pieChartData[0]?.name}>
                  {pieChartData[0]?.name?.split(' ')[0]}
                </p>
              </div>
              <div className="bg-gradient-to-br from-orange-50 to-orange-100/50 rounded-lg p-2 text-center">
                <p className="text-xs text-orange-600 font-medium">Articles</p>
                <p className="text-lg font-bold text-orange-900">
                  {pieChartData.reduce((sum: number, item: any) => sum + item.value, 0)}
                </p>
              </div>
            </div>

            <ResponsiveContainer width="100%" height={400}>
              <PieChart>
                <Pie
                  data={pieChartData}
                  cx="50%"
                  cy="50%"
                  labelLine={true}
                  outerRadius={120}
                  innerRadius={0}
                  fill="#8884d8"
                  dataKey="value"
                  label={(entry: any) => {
                    const percent = ((entry.value / pieChartData.reduce((sum: number, item: any) => sum + item.value, 0)) * 100).toFixed(1);
                    return `${entry.name}\n${entry.value} (${percent}%)`;
                  }}
                  animationBegin={0}
                  animationDuration={800}
                  animationEasing="ease-out"
                >
                  {pieChartData.map((entry: any, index: number) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.color}
                      stroke="#fff"
                      strokeWidth={3}
                    />
                  ))}
                </Pie>
                <Tooltip
                  content={<CustomTooltip />}
                  cursor={{ fill: 'rgba(0,0,0,0.05)' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Political Figures - Interactive Chart */}
          <InteractiveFiguresChart
            figuresData={allFiguresData}
            categoryColor={categoryColor}
            categoryName={decodedCategoryName}
            onFigureClick={(figureName) => {
              console.log('Figure clicked:', figureName);
            }}
          />
        </div>

        {/* Line Chart - Time Trend */}
        <div className="group backdrop-blur-xl bg-gradient-to-br from-white/70 via-white/60 to-white/50 rounded-2xl shadow-2xl shadow-blue-200/40 p-8 mb-8 border-2 border-blue-300 hover:shadow-2xl hover:border-blue-500 hover:scale-[1.01] transition-all duration-500">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/20 to-cyan-500/20 flex items-center justify-center shadow-md group-hover:scale-110 transition-transform">
                <TrendingUp className="w-5 h-5 text-blue-600" />
              </div>
              <span className="bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">Monthly Trend Analysis</span>
            </h3>
          </div>

          {/* Trend Stats Summary */}
          <div className="grid grid-cols-4 gap-2 mb-4">
            <div className="bg-gradient-to-br from-blue-50 to-blue-100/50 rounded-lg p-2 text-center">
              <p className="text-xs text-blue-600 font-medium">Total Months</p>
              <p className="text-lg font-bold text-blue-900">{timeSeriesData.length}</p>
            </div>
            <div className="bg-gradient-to-br from-green-50 to-green-100/50 rounded-lg p-2 text-center">
              <p className="text-xs text-green-600 font-medium">Peak Month</p>
              <p className="text-xs font-bold text-green-900 truncate" title={timeSeriesData.reduce((max: any, item: any) => item.count > (max?.count || 0) ? item : max, {})?.month}>
                {timeSeriesData.reduce((max: any, item: any) => item.count > (max?.count || 0) ? item : max, {})?.month?.substring(0, 7)}
              </p>
            </div>
            <div className="bg-gradient-to-br from-orange-50 to-orange-100/50 rounded-lg p-2 text-center">
              <p className="text-xs text-orange-600 font-medium">Peak Count</p>
              <p className="text-lg font-bold text-orange-900">
                {Math.max(...timeSeriesData.map((item: any) => item.count || 0))}
              </p>
            </div>
            <div className="bg-gradient-to-br from-purple-50 to-purple-100/50 rounded-lg p-2 text-center">
              <p className="text-xs text-purple-600 font-medium">Avg/Month</p>
              <p className="text-lg font-bold text-purple-900">
                {Math.round(timeSeriesData.reduce((sum: number, item: any) => sum + (item.count || 0), 0) / (timeSeriesData.length || 1))}
              </p>
            </div>
          </div>

          <ResponsiveContainer width="100%" height={400}>
            <LineChart
              data={timeSeriesData}
              margin={{ top: 10, right: 30, left: 0, bottom: 20 }}
            >
              <defs>
                <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={categoryColor} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={categoryColor} stopOpacity={0.05} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" opacity={0.5} />
              <XAxis
                dataKey="month"
                stroke="#6b7280"
                tick={{ fontSize: 11, fill: '#6b7280' }}
                tickLine={{ stroke: '#9ca3af' }}
              />
              <YAxis
                stroke="#6b7280"
                tick={{ fontSize: 12, fill: '#6b7280' }}
                tickLine={{ stroke: '#9ca3af' }}
              />
              <Tooltip
                content={<CustomTooltip />}
                cursor={{ stroke: categoryColor, strokeWidth: 2, strokeDasharray: '5 5' }}
              />
              <Legend
                wrapperStyle={{ paddingTop: '20px' }}
                iconType="line"
              />
              <Line
                type="monotone"
                dataKey="count"
                stroke={categoryColor}
                strokeWidth={4}
                dot={{
                  r: 5,
                  fill: categoryColor,
                  strokeWidth: 3,
                  stroke: '#fff',
                  className: 'hover:r-8 transition-all'
                }}
                activeDot={{
                  r: 9,
                  fill: categoryColor,
                  stroke: '#fff',
                  strokeWidth: 3
                }}
                name="Articles"
                animationDuration={1500}
                animationEasing="ease-in-out"
              />
            </LineChart>
          </ResponsiveContainer>
          <div className="mt-4 p-3 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-xl border border-blue-200">
            <p className="text-xs text-blue-700 text-center font-medium">
              📈 Track article trends over time • Hover to see exact monthly counts
            </p>
          </div>
        </div>

        {/* Filters Section */}
        <div className="backdrop-blur-xl bg-white/60 rounded-2xl shadow-2xl shadow-purple-100/50 p-8 mb-8 border-2 border-purple-200/60 hover:border-purple-300/80 hover:shadow-purple-200/60 transition-all duration-300">
          <h3 className="text-lg font-bold text-gray-900 mb-6 flex items-center gap-2">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center shadow-md" style={{ backgroundColor: categoryColor + '20' }}>
              <Filter className="w-5 h-5" style={{ color: categoryColor }} />
            </div>
            <span>Filter Articles</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-3">Party</label>
              <select
                value={selectedParty}
                onChange={(e) => setSelectedParty(e.target.value)}
                className="w-full px-4 py-3 backdrop-blur-sm bg-white/70 border-2 border-gray-200/80 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400 shadow-md hover:bg-white/90 hover:border-blue-300 transition-all"
              >
                <option value="">All Parties</option>
                {stats.top_parties?.map((party: any) => (
                  <option key={party.name} value={party.name}>
                    {party.name} ({party.count})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-3">Start Date</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-4 py-3 backdrop-blur-sm bg-white/70 border-2 border-gray-200/80 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400 shadow-md hover:bg-white/90 hover:border-blue-300 transition-all"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-3">End Date</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-4 py-3 backdrop-blur-sm bg-white/70 border-2 border-gray-200/80 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400 shadow-md hover:bg-white/90 hover:border-blue-300 transition-all"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-3">Source</label>
              <select
                value={source}
                onChange={(e) => setSource(e.target.value)}
                className="w-full px-4 py-3 backdrop-blur-sm bg-white/70 border-2 border-gray-200/80 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400 shadow-md hover:bg-white/90 hover:border-blue-300 transition-all"
              >
                <option value="">All Sources</option>
                {Object.keys(stats.sources || {}).map((src) => (
                  <option key={src} value={src}>
                    {src} ({stats.sources[src]})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex gap-4">
            <button
              onClick={applyFilters}
              className="px-8 py-3 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 backdrop-blur-sm cursor-pointer"
              style={{
                background: `linear-gradient(135deg, ${categoryColor} 0%, ${categoryColor}dd 100%)`,
              }}
            >
              Apply Filters
            </button>
            <button
              onClick={clearFilters}
              className="px-8 py-3 backdrop-blur-sm bg-white/70 hover:bg-white/90 text-gray-700 rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 border-2 border-gray-200/80 hover:border-blue-300 cursor-pointer"
            >
              Clear Filters
            </button>
          </div>
        </div>

        {/* Search Bar */}
        <div className="backdrop-blur-xl bg-white/60 rounded-2xl shadow-2xl shadow-blue-100/50 p-6 mb-8 border-2 border-blue-200/60 hover:border-blue-300/80 hover:shadow-blue-200/60 transition-all duration-300">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/20 to-blue-400/10 flex items-center justify-center flex-shrink-0 shadow-md">
              <Search className="w-5 h-5 text-blue-600" />
            </div>
            <input
              type="text"
              placeholder="Search articles by title or content..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex-1 px-6 py-3 backdrop-blur-sm bg-white/70 border-2 border-gray-200/80 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400 shadow-inner placeholder:text-gray-500 hover:bg-white/90 hover:border-blue-300 transition-all"
            />
          </div>
        </div>

        {/* Articles List */}
        <div className="backdrop-blur-xl bg-white/60 rounded-2xl shadow-2xl shadow-indigo-100/50 p-8 border-2 border-indigo-200/60 hover:border-indigo-300/80 transition-all duration-300">
          <h3 className="text-lg font-bold text-gray-900 mb-6 flex items-center gap-2">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ backgroundColor: categoryColor + '20' }}>
              <Newspaper className="w-5 h-5" style={{ color: categoryColor }} />
            </div>
            <span>Articles ({filteredArticles.length})</span>
          </h3>

          {loading ? (
            <div className="text-center py-8">
              <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-2" />
              <p className="text-gray-600">Loading articles...</p>
            </div>
          ) : filteredArticles.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-600">No articles found</p>
            </div>
          ) : (
            <div className="space-y-6">
              {filteredArticles.map((article) => (
                <div
                  key={article.id}
                  className="group backdrop-blur-lg bg-white/70 border-2 border-gray-200/80 rounded-2xl p-6 hover:bg-white/90 hover:shadow-2xl hover:scale-[1.01] hover:border-blue-300/80 transition-all duration-300 shadow-lg shadow-gray-200/50"
                >
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="text-lg font-semibold text-gray-900 flex-1">
                      {article.title}
                    </h4>
                    {article.is_primary && (
                      <span className="px-2 py-1 text-xs font-medium text-white rounded-full ml-2 shadow-sm" style={{ backgroundColor: categoryColor }}>
                        Primary
                      </span>
                    )}
                  </div>

                  {/* Show category reasoning if available */}
                  {article.category_reasoning && article.category_reasoning.trim() && (
                    <div className="mb-3 p-3 backdrop-blur-sm bg-gradient-to-r from-blue-50/80 to-indigo-50/80 rounded-xl shadow-md border-2 border-blue-300/80">
                      <p className="text-xs font-bold text-blue-800 mb-1 uppercase tracking-wide">📋 কেন এই ক্যাটাগরিতে (Why this Category)</p>
                      <p className="text-sm text-gray-700 leading-relaxed">{article.category_reasoning}</p>
                    </div>
                  )}

                  {/* Show relevant excerpt if available */}
                  {article.relevant_excerpt && typeof article.relevant_excerpt === 'string' && article.relevant_excerpt.trim() && (
                    <div className="mb-4 p-4 backdrop-blur-sm bg-gradient-to-r from-yellow-50/80 to-amber-50/80 rounded-xl shadow-md border-2 border-yellow-300/80">
                      <div className="flex items-start gap-3">
                        <div className="w-8 h-8 rounded-lg bg-yellow-400/20 flex items-center justify-center flex-shrink-0">
                          <Quote className="w-4 h-4 text-yellow-700" />
                        </div>
                        <div className="flex-1">
                          <p className="text-xs font-bold text-yellow-800 mb-2 uppercase tracking-wide">💬 প্রাসঙ্গিক বক্তব্য (Relevant Speech/Statement)</p>
                          <p className="text-sm text-gray-800 italic leading-relaxed">
                            "{article.relevant_excerpt}"
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Article content with See more feature */}
                  <div className="mb-3">
                    <div className={`text-sm text-gray-600 leading-relaxed ${expandedArticles.has(article.id) ? '' : 'line-clamp-3'}`}>
                      {expandedArticles.has(article.id) ? (
                        <span>{article.content}</span>
                      ) : (
                        <HighlightedText
                          text={article.content}
                          highlight={(typeof article.relevant_excerpt === 'string' ? article.relevant_excerpt : '') || ''}
                        />
                      )}
                    </div>
                    {article.content && article.content.length > 150 && (
                      <button
                        onClick={() => toggleArticleExpand(article.id)}
                        className="mt-2 text-sm font-semibold text-blue-600 hover:text-blue-700 hover:underline transition-colors flex items-center gap-1 cursor-pointer"
                      >
                        {expandedArticles.has(article.id) ? (
                          <>Show less <span className="text-xs">▲</span></>
                        ) : (
                          <>See more... <span className="text-xs">▼</span></>
                        )}
                      </button>
                    )}
                  </div>

                  <div className="flex flex-wrap items-center gap-4 text-xs text-gray-500">
                    <span className="flex items-center">
                      <Calendar className="w-4 h-4 mr-1" />
                      {article.date}
                    </span>
                    <span className="flex items-center">
                      <Newspaper className="w-4 h-4 mr-1" />
                      {article.source}
                    </span>
                    {article.parties.length > 0 && (
                      <div className="flex items-center gap-1">
                        <Users className="w-4 h-4" />
                        {article.parties.slice(0, 2).map((party) => (
                          <span
                            key={party}
                            className="px-2 py-0.5 rounded-full text-xs shadow-sm"
                            style={{ backgroundColor: getPartyColor(party) + '20', color: getPartyColor(party) }}
                          >
                            {party}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {article.url && (
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-3 inline-flex items-center gap-2 text-sm font-semibold text-blue-600 hover:text-blue-700 group-hover:translate-x-1 transition-transform"
                    >
                      <span>Read full article</span>
                      <span className="text-lg">→</span>
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Pagination - Bottom */}
        {!loading && articles.length > 0 && (
          <div className="mt-6">
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              totalItems={totalArticles}
              itemsPerPage={itemsPerPage}
              onPageChange={handlePageChange}
              onItemsPerPageChange={handleItemsPerPageChange}
            />
          </div>
        )}
      </main>
    </div>
  );
};

export default CategoryDetailPage;

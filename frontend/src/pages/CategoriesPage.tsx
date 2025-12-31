import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, BarChart3, TrendingUp, Users, FileText, Loader2, Calendar, Trash2, X } from 'lucide-react';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { fetchCategories, getCategoryStats, analyzeCategories, clearCategoryMetadata } from '../utils/api';
import { getCategoryColor, getLightColor } from '../utils/partyColors';

interface CategoryInfo {
  name: string;
  description: string;
  keywords: string[];
}

interface CategoryStats {
  total_articles: number;
  as_primary: number;
  party_breakdown: Record<string, number>;
  monthly_distribution: Record<string, number>;
}

const CategoriesPage = () => {
  const navigate = useNavigate();
  
  const [categories, setCategories] = useState<CategoryInfo[]>([]);
  const [stats, setStats] = useState<Record<string, CategoryStats>>({});
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [totalArticles, setTotalArticles] = useState(0);
  const [categorizedArticles, setCategorizedArticles] = useState(0);
  const [clearing, setClearing] = useState(false);
  const [showClearModal, setShowClearModal] = useState(false);
  const [clearPeopleData, setClearPeopleData] = useState(true);
  
  // Date range for analysis
  const [startDate, setStartDate] = useState('2024-10-01');
  const [endDate, setEndDate] = useState('2024-10-31');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Load categories and stats in parallel
      const [categoriesRes, statsRes] = await Promise.all([
        fetchCategories(),
        getCategoryStats()
      ]);
      
      if (categoriesRes.success) {
        setCategories(categoriesRes.categories);
      }
      
      if (statsRes.success) {
        setStats(statsRes.category_stats);
        setTotalArticles(statsRes.total_articles);
        setCategorizedArticles(statsRes.categorized_articles);
      }
      
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeCategories = async () => {
    try {
      setAnalyzing(true);
      
      const result = await analyzeCategories(startDate, endDate, undefined, false);
      
      if (result.success) {
        const message = false 
          ? `✅ Successfully re-analyzed ${result.analyzed_count} articles (replaced old categories)!`
          : `✅ Successfully analyzed ${result.analyzed_count} new articles!`;
        
        toast.success(message, {
          position: "top-right",
          autoClose: 5000,
          hideProgressBar: false,
          closeOnClick: true,
          pauseOnHover: true,
          draggable: true,
        });
        // Reload stats
        await loadData();
      }
      
    } catch (error: any) {
      console.error('Error analyzing:', error);
      toast.error('❌ Failed to analyze categories: ' + (error.message || 'Unknown error'), {
        position: "top-right",
        autoClose: 5000,
      });
    } finally {
      setAnalyzing(false);
    }
  };

  const handleClearMetadata = async () => {
    try {
      setClearing(true);
      setShowClearModal(false);
      
      const result = await clearCategoryMetadata(clearPeopleData);
      
      if (result.success) {
        const message = clearPeopleData 
          ? `🗑️ Successfully cleared ${result.cleared_count} articles (categories + people/parties data)!`
          : `🗑️ Successfully cleared category metadata from ${result.cleared_count} articles!`;
        toast.success(message, {
          position: "top-right",
          autoClose: 5000,
          hideProgressBar: false,
          closeOnClick: true,
          pauseOnHover: true,
          draggable: true,
        });
        // Reload stats
        await loadData();
      }
      
    } catch (error: any) {
      console.error('Error clearing metadata:', error);
      toast.error('❌ Failed to clear metadata: ' + (error.message || 'Unknown error'), {
        position: "top-right",
        autoClose: 5000,
      });
    } finally {
      setClearing(false);
    }
  };

  const getCategoryIcon = (categoryName: string) => {
    const icons: Record<string, React.ReactElement> = {
      'Reform': <TrendingUp className="w-8 h-8" />,
      'Elections': <Users className="w-8 h-8" />,
      'Trial of The Fascist Government': <FileText className="w-8 h-8" />,
      'National Security': <FileText className="w-8 h-8" />,
      'Conspiracy': <FileText className="w-8 h-8" />,
      'External Actors': <Users className="w-8 h-8" />,
      'Proportional Representation (PR) system': <BarChart3 className="w-8 h-8" />,
      'Legal Basis of July Charter': <FileText className="w-8 h-8" />,
      'Others': <FileText className="w-8 h-8" />
    };
    return icons[categoryName] || <FileText className="w-8 h-8" />;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/20 flex items-center justify-center relative overflow-hidden">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-1/2 -right-1/4 w-96 h-96 bg-blue-200/20 rounded-full blur-3xl animate-pulse"></div>
          <div className="absolute top-1/3 -left-1/4 w-96 h-96 bg-indigo-200/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
        </div>
        <div className="backdrop-blur-xl bg-white/60 rounded-3xl shadow-2xl p-12 border-2 border-gray-200/80 z-10">
          <Loader2 className="w-16 h-16 animate-spin text-blue-600 mx-auto mb-6" />
          <p className="text-gray-800 font-semibold text-lg">Loading categories...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/20 relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-1/2 -right-1/4 w-96 h-96 bg-blue-200/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute top-1/3 -left-1/4 w-96 h-96 bg-indigo-200/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-200/20 rounded-full blur-3xl animate-pulse delay-2000"></div>
      </div>

      {/* Toast Container */}
      <ToastContainer />

      {/* Confirmation Modal with Advanced Glassmorphism */}
      {showClearModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-md flex items-center justify-center z-50 p-4 animate-in fade-in duration-300">
          <div className="backdrop-blur-2xl bg-white/95 rounded-3xl shadow-2xl p-10 max-w-md w-full mx-4 border-2 border-white/50 animate-in zoom-in duration-300">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-red-500/20 to-red-600/20 flex items-center justify-center">
                  <Trash2 className="w-6 h-6 text-red-600" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900">Reset Category Data</h3>
              </div>
              <button
                onClick={() => setShowClearModal(false)}
                className="w-10 h-10 rounded-xl backdrop-blur-sm bg-white/50 hover:bg-white/80 flex items-center justify-center transition-all duration-200 border border-white/60 hover:scale-110 cursor-pointer"
              >
                <X className="w-5 h-5 text-gray-700" />
              </button>
            </div>
            
            <div className="mb-6">
              <p className="text-gray-800 mb-4 text-base leading-relaxed">
                This will clear all existing category analysis data so you can run fresh categorization.
              </p>
              
              <label className="flex items-center gap-3 cursor-pointer group mb-4 p-3 rounded-xl bg-blue-50/80 border border-blue-200/50">
                <input
                  type="checkbox"
                  checked={clearPeopleData}
                  onChange={(e) => setClearPeopleData(e.target.checked)}
                  className="w-5 h-5 text-blue-500 border-gray-300 rounded focus:ring-2 focus:ring-blue-500 cursor-pointer"
                />
                <div className="flex-1">
                  <span className="text-sm font-medium text-gray-700 group-hover:text-gray-900">
                    Also clear People & Parties data
                  </span>
                  <p className="text-xs text-gray-500 mt-1">
                    Recommended to fix name inconsistencies (e.g., "Tareq Rahman" vs "তারেক রহমান")
                  </p>
                </div>
              </label>
              
              <div className="backdrop-blur-sm bg-red-50/80 rounded-2xl p-4 border border-red-200/50">
                <p className="text-sm text-red-700 font-bold flex items-center gap-2">
                  <span className="text-lg">⚠️</span>
                  This action cannot be undone!
                </p>
              </div>
            </div>
            
            <div className="flex gap-4">
              <button
                onClick={() => setShowClearModal(false)}
                className="flex-1 px-6 py-3 backdrop-blur-sm bg-white/70 hover:bg-white/90 text-gray-800 rounded-xl font-semibold transition-all duration-300 border border-white/60 hover:scale-105 hover:shadow-lg cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={handleClearMetadata}
                className="flex-1 px-6 py-3 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white rounded-xl font-semibold transition-all duration-300 flex items-center justify-center gap-2 hover:scale-105 hover:shadow-xl shadow-lg cursor-pointer"
              >
                <Trash2 className="w-5 h-5" />
                Reset Data
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Header with Enhanced Glassmorphism */}
      <header className="sticky top-0 z-40 backdrop-blur-md bg-white/40 border-b border-white/30 shadow-lg shadow-gray-200/30">
        <div className="max-w-7xl mx-auto px-4 py-5 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <button
              onClick={() => navigate('/')}
              className="group flex items-center px-4 py-2.5 text-gray-800 hover:text-gray-900 transition-all duration-300 rounded-xl hover:bg-white/60 backdrop-blur-sm border border-white/40 shadow-sm hover:shadow-md"
            >
              <ArrowLeft className="w-5 h-5 mr-2 group-hover:-translate-x-1 transition-transform" />
              <span className="font-semibold">Back to Home</span>
            </button>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-gray-900 via-gray-800 to-gray-700 bg-clip-text text-transparent drop-shadow-sm">
              Category Analytics
            </h1>
            <div className="w-24"></div> {/* Spacer for centering */}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8 z-10">
        {/* Stats Overview with Glass Effect */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="group backdrop-blur-lg bg-gradient-to-br from-white/70 to-white/40 rounded-2xl shadow-lg shadow-blue-100/50 p-6 border-2 border-blue-200/80 hover:shadow-xl hover:scale-105 hover:border-blue-400/80 transition-all duration-300 cursor-pointer">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 font-semibold uppercase tracking-wide mb-2">Total Articles</p>
                <p className="text-4xl font-bold bg-gradient-to-br from-gray-800 to-gray-600 bg-clip-text text-transparent">{totalArticles}</p>
              </div>
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500/20 to-blue-400/10 flex items-center justify-center group-hover:scale-110 transition-transform">
                <FileText className="w-8 h-8 text-blue-600" />
              </div>
            </div>
          </div>
          
          <div className="group backdrop-blur-lg bg-gradient-to-br from-white/70 to-white/40 rounded-2xl shadow-lg shadow-green-100/50 p-6 border-2 border-green-200/80 hover:shadow-xl hover:scale-105 hover:border-green-400/80 transition-all duration-300 cursor-pointer">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 font-semibold uppercase tracking-wide mb-2">Categorized</p>
                <p className="text-4xl font-bold bg-gradient-to-br from-green-600 to-green-400 bg-clip-text text-transparent">{categorizedArticles}</p>
              </div>
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-green-500/20 to-green-400/10 flex items-center justify-center group-hover:scale-110 transition-transform">
                <BarChart3 className="w-8 h-8 text-green-600" />
              </div>
            </div>
          </div>
          
          <div className="group backdrop-blur-lg bg-gradient-to-br from-white/70 to-white/40 rounded-2xl shadow-lg shadow-purple-100/50 p-6 border-2 border-orange-200/80 hover:shadow-xl hover:scale-105 hover:border-orange-400/80 transition-all duration-300 cursor-pointer">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 font-semibold uppercase tracking-wide mb-2">Uncategorized</p>
                <p className="text-4xl font-bold bg-gradient-to-br from-orange-600 to-orange-400 bg-clip-text text-transparent">
                  {totalArticles - categorizedArticles}
                </p>
              </div>
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-orange-500/20 to-orange-400/10 flex items-center justify-center group-hover:scale-110 transition-transform">
                <TrendingUp className="w-8 h-8 text-orange-600" />
              </div>
            </div>
          </div>
        </div>

        {/* Analysis Section */}
        <div className="backdrop-blur-xl bg-white/60 rounded-2xl shadow-xl shadow-gray-300/60 p-8 mb-8 border-2 border-gray-200/80 hover:shadow-2xl hover:border-blue-300/80 transition-all duration-300">
          <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
            <Calendar className="w-6 h-6 mr-2 text-blue-500" />
            Analyze Articles by Date Range
          </h2>
          
          <div className="flex flex-wrap items-end gap-4 mb-4">
            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Start Date
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                End Date
              </label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <button
              onClick={handleAnalyzeCategories}
              disabled={analyzing}
              className="px-6 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              {analyzing ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <div className="flex items-center gap-2 cursor-pointer">
                  <BarChart3 className="w-5 h-5" />
                  Analyze Categories
                </div>
              )}
            </button>
          </div>
          
          {/* Force Re-classify Option */}
          {/* <div className="pt-4 border-t border-gray-200">
            <label className="flex items-center gap-3 cursor-pointer group">
              <input
                type="checkbox"
                checked={forceReclassify}
                onChange={(e) => setForceReclassify(e.target.checked)}
                className="w-5 h-5 text-blue-500 border-gray-300 rounded focus:ring-2 focus:ring-blue-500 cursor-pointer"
              />
              <div className="flex-1">
                <span className="text-sm font-medium text-gray-700 group-hover:text-gray-900">
                  Force Re-classify Already Categorized Articles
                </span>
                <p className="text-xs text-gray-500 mt-1">
                  {forceReclassify ? (
                    <span className="text-orange-600 font-medium">
                      ⚠️ This will replace existing categories for all articles in the date range with new AI analysis
                    </span>
                  ) : (
                    "Only categorize articles that don't have categories yet (recommended for new articles)"
                  )}
                </p>
              </div>
            </label>
          </div> */}

          {/* Clear Metadata Button */}
          <div className="pt-4 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-700">Reset Category Data</p>
                <p className="text-xs text-gray-500 mt-1">
                  Clear all existing category and people data to fix inconsistencies and start fresh
                </p>
              </div>
              <button
                onClick={() => setShowClearModal(true)}
                disabled={clearing}
                className="px-6 py-2 bg-red-500 hover:bg-red-600 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors flex items-center gap-2 cursor-pointer"
              >
                {clearing ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Clearing...
                  </>
                ) : (
                  <>
                    <Trash2 className="w-5 h-5" />
                    Reset All Data
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Categories Grid */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            9 Political Categories
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {categories.map((category) => {
              const categoryStats = stats[category.name] || {
                total_articles: 0,
                as_primary: 0,
                party_breakdown: {},
                monthly_distribution: {}
              };
              
              const color = getCategoryColor(category.name);
              const lightColor = getLightColor(color, 0.1);
              
              return (
                <div
                  key={category.name}
                  onClick={() => navigate(`/categories/${encodeURIComponent(category.name)}`)}
                  className="bg-white rounded-xl shadow-lg p-6 hover:shadow-2xl transition-all duration-300 cursor-pointer transform hover:-translate-y-2 border-2 border-gray-200/80 hover:border-blue-300/80"
                  style={{ borderLeft: `4px solid ${color}` }}
                >
                  {/* Icon */}
                  <div
                    className="w-16 h-16 rounded-full flex items-center justify-center mb-4"
                    style={{ backgroundColor: lightColor, color: color }}
                  >
                    {getCategoryIcon(category.name)}
                  </div>
                  
                  {/* Title */}
                  <h3 className="text-lg font-bold text-gray-900 mb-2">
                    {category.name}
                  </h3>
                  
                  {/* Description */}
                  <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                    {category.description}
                  </p>
                  
                  {/* Stats */}
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                      <p className="text-xs text-gray-500">Total Articles</p>
                      <p className="text-2xl font-bold" style={{ color: color }}>
                        {categoryStats.total_articles}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">As Primary</p>
                      <p className="text-2xl font-bold text-gray-700">
                        {categoryStats.as_primary}
                      </p>
                    </div>
                  </div>
                  
                  {/* Parties */}
                  {Object.keys(categoryStats.party_breakdown).length > 0 && (
                    <div className="pt-4 border-t border-gray-200">
                      <p className="text-xs text-gray-500 mb-2">Top Parties</p>
                      <div className="flex flex-wrap gap-1">
                        {Object.entries(categoryStats.party_breakdown)
                          .slice(0, 3)
                          .map(([party, count]) => (
                            <span
                              key={party}
                              className="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-700"
                            >
                              {party} ({count})
                            </span>
                          ))}
                      </div>
                    </div>
                  )}
                  
                  {/* View Details Button */}
                  <button
                    className="mt-4 w-full py-2 rounded-lg cursor-pointer font-medium text-white transition-colors"
                    style={{ backgroundColor: color }}
                  >
                    View Details →
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      </main>
    </div>
  );
};

export default CategoriesPage;

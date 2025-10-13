import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Database, ArrowLeft, Loader2 } from 'lucide-react';

const DatabasePage = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/health');
      const data = await response.json();
      setStats(data);
    } catch (err) {
      setError('Failed to fetch database stats');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <button
              onClick={() => navigate('/')}
              className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              Back to Home
            </button>
            <h1 className="text-2xl font-bold text-gray-900">
              Vector Database
            </h1>
            <div className="w-24"></div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <p className="text-red-600">{error}</p>
          </div>
        ) : (
          <>
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Database Status</p>
                    <p className="text-2xl font-bold text-green-600">
                      {stats?.status === 'healthy' ? 'Healthy' : 'Unhealthy'}
                    </p>
                  </div>
                  <Database className="w-12 h-12 text-green-600" />
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Total Articles</p>
                    <p className="text-2xl font-bold text-blue-600">
                      {stats?.total_articles || 0}
                    </p>
                  </div>
                  <Database className="w-12 h-12 text-blue-600" />
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Database Connected</p>
                    <p className="text-2xl font-bold text-purple-600">
                      {stats?.database_connected ? 'Yes' : 'No'}
                    </p>
                  </div>
                  <Database className="w-12 h-12 text-purple-600" />
                </div>
              </div>
            </div>

            {/* Info Section */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                Database Information
              </h2>
              <div className="space-y-3">
                <div className="flex justify-between py-2 border-b border-gray-200">
                  <span className="text-gray-600">Version:</span>
                  <span className="font-semibold">{stats?.version || 'N/A'}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-gray-200">
                  <span className="text-gray-600">Collection Name:</span>
                  <span className="font-semibold">political_articles</span>
                </div>
                <div className="flex justify-between py-2 border-b border-gray-200">
                  <span className="text-gray-600">Embedding Model:</span>
                  <span className="font-semibold">all-MiniLM-L6-v2</span>
                </div>
                <div className="flex justify-between py-2">
                  <span className="text-gray-600">Vector Dimension:</span>
                  <span className="font-semibold">384</span>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="mt-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg shadow-lg p-8 text-white">
              <h3 className="text-2xl font-bold mb-4">
                Database Operations
              </h3>
              <p className="mb-6 text-blue-100">
                Manage your vector database with the following operations:
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <button
                  onClick={() => navigate('/scraper')}
                  className="bg-white text-blue-600 font-semibold py-3 px-6 rounded-lg hover:bg-blue-50 transition-colors"
                >
                  Add Articles
                </button>
                <button
                  onClick={() => navigate('/search')}
                  className="bg-white text-purple-600 font-semibold py-3 px-6 rounded-lg hover:bg-purple-50 transition-colors"
                >
                  Search Articles
                </button>
                <button
                  onClick={() => window.location.reload()}
                  className="bg-white text-green-600 font-semibold py-3 px-6 rounded-lg hover:bg-green-50 transition-colors"
                >
                  Refresh Stats
                </button>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
};

export default DatabasePage;

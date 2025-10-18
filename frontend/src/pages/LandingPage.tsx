import { useNavigate } from 'react-router-dom';
import { Newspaper, Users, Search, Database, FileSearch, Vote } from 'lucide-react';
import { TopicsCloud } from '../components/TopicsCloud';

const LandingPage = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: <Users className=" " />,
      title: 'Political Parties',
      description: 'Explore political parties and their key figures in Bangladesh',
      path: '/parties',
      color: 'from-blue-500 to-blue-600'
    },
    {
      icon: <Newspaper className=" " />,
      title: 'News Scraper',
      description: 'Scrape and analyze news articles from major Bangladeshi newspapers',
      path: '/scraper',
      color: 'from-green-500 to-green-600'
    },
    {
      icon: <Search className=" " />,
      title: 'Search Articles',
      description: 'Search and query political articles using semantic search',
      path: '/search',
      color: 'from-purple-500 to-purple-600'
    },
    {
      icon: <Database className=" " />,
      title: 'Vector Database',
      description: 'View and manage articles stored in the vector database',
      path: '/database',
      color: 'from-orange-500 to-orange-600'
    },
    {
      icon: <Vote className=" " />,
      title: '2026 Election Impact',
      description: 'Articles with potential impact on Bangladesh\'s 2026 election',
      path: '/election-impact',
      color: 'from-purple-500 to-pink-600'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              Speech Analysis System
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              Analyzing Bangladesh Political News & Speeches
            </p>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-12 sm:px-6 lg:px-8">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Welcome to Political News Analysis Platform
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Comprehensive tools for scraping, analyzing, and retrieving political news articles 
            from leading Bangladeshi newspapers with AI-powered insights.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-12">
          {features.map((feature, index) => (
            <div
              key={index}
              onClick={() => navigate(feature.path)}
              className="bg-white rounded-xl shadow-lg p-8 hover:shadow-2xl transition-all duration-300 cursor-pointer transform hover:-translate-y-2"
            >
              <div className={`w-16 h-16 rounded-full bg-gradient-to-r ${feature.color} flex items-center justify-center mb-6`}>
                {feature.icon}
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-3">
                {feature.title}
              </h3>
              <p className="text-gray-600 mb-4">
                {feature.description}
              </p>
              <button className={`px-6 py-2 cursor-pointer bg-gradient-to-r ${feature.color} text-white font-semibold rounded-lg hover:opacity-90 transition-opacity`}>
                Get Started →
              </button>
            </div>
          ))}
        </div>

        {/* Topics Cloud Section */}
        <div className="mb-12">
          <TopicsCloud onTopicClick={(topic) => navigate(`/topics/${encodeURIComponent(topic)}`)} />
        </div>

        {/* Stats Section */}
        <div className="bg-white rounded-xl shadow-lg p-8 mb-12">
          <h3 className="text-2xl font-bold text-gray-900 mb-6 text-center">
            System Capabilities
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="text-4xl font-bold text-blue-600 mb-2">4</div>
              <div className="text-gray-600">News Sources</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-green-600 mb-2">7+</div>
              <div className="text-gray-600">Political Parties</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-purple-600 mb-2">AI</div>
              <div className="text-gray-600">Powered Analysis</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-orange-600 mb-2">∞</div>
              <div className="text-gray-600">Articles Capacity</div>
            </div>
          </div>
        </div>

        {/* Features List */}
        <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl shadow-lg p-8 text-white">
          <h3 className="text-2xl font-bold mb-6 text-center">
            Key Features
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-white text-blue-600 flex items-center justify-center font-bold text-sm">
                ✓
              </div>
              <div>
                <h4 className="font-semibold mb-1">Real-time Scraping</h4>
                <p className="text-sm text-blue-100">
                  Scrape articles from Prothom Alo, Jugantor, Daily Star, and Dhaka Tribune
                </p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-white text-blue-600 flex items-center justify-center font-bold text-sm">
                ✓
              </div>
              <div>
                <h4 className="font-semibold mb-1">Political Entity Detection</h4>
                <p className="text-sm text-blue-100">
                  Automatically identify mentions of political figures and parties
                </p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-white text-blue-600 flex items-center justify-center font-bold text-sm">
                ✓
              </div>
              <div>
                <h4 className="font-semibold mb-1">Semantic Search</h4>
                <p className="text-sm text-blue-100">
                  Find relevant articles using AI-powered similarity search
                </p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-white text-blue-600 flex items-center justify-center font-bold text-sm">
                ✓
              </div>
              <div>
                <h4 className="font-semibold mb-1">Speech Analysis</h4>
                <p className="text-sm text-blue-100">
                  Generate summaries and extract key points from political speeches
                </p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-white text-blue-600 flex items-center justify-center font-bold text-sm">
                ✓
              </div>
              <div>
                <h4 className="font-semibold mb-1">Vector Database</h4>
                <p className="text-sm text-blue-100">
                  Efficient storage and retrieval using ChromaDB embeddings
                </p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-white text-blue-600 flex items-center justify-center font-bold text-sm">
                ✓
              </div>
              <div>
                <h4 className="font-semibold mb-1">Multi-language Support</h4>
                <p className="text-sm text-blue-100">
                  Handle both English and Bangla content seamlessly
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Developer Tools Section */}
        <div className="bg-gradient-to-r from-gray-700 to-gray-800 rounded-xl shadow-lg p-8 mb-12">
          <h3 className="text-2xl font-bold text-white mb-6 text-center">
            Developer Tools
          </h3>
          <div className="grid grid-cols-1 gap-4">
            <div
              onClick={() => navigate('/categorization-test')}
              className="bg-white/10 backdrop-blur-sm rounded-lg p-6 hover:bg-white/20 transition-all cursor-pointer border border-white/20"
            >
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 rounded-full bg-gradient-to-r from-yellow-400 to-yellow-500 flex items-center justify-center">
                  <FileSearch className="text-white" />
                </div>
                <div className="flex-1">
                  <h4 className="font-semibold text-white text-lg mb-1">Categorization Test</h4>
                  <p className="text-gray-300 text-sm">
                    Validate article categorization and party-figure associations in the database
                  </p>
                </div>
                <div className="text-white opacity-50 text-2xl">→</div>
              </div>
            </div>
          </div>
        </div>

      </main>

      {/* Footer */}
      <footer className="bg-white shadow-sm mt-12">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <p className="text-center text-gray-500 text-sm">
            © 2025 Speech Analysis System. 
          </p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;

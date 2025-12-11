import { useNavigate } from 'react-router-dom';
import { Newspaper, Users, Search, Database, LogOut, BarChart3 } from 'lucide-react';
import ChatbotIcon from '../assets/chatbot.svg';
import { logout, getEmail } from '../utils/auth';
import logo from '../assets/logo.png'
import { Link } from 'react-router-dom'

const LandingPage = () => {
  const navigate = useNavigate();
  const email = getEmail();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

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
      icon: <img src={ChatbotIcon} alt="Chatbot" style={{ width: '24px', height: '24px' }} />,
      title: 'AI Chatbot',
      description: 'Ask questions about Bangladesh politics and get AI-powered answers',
      path: '/chatbot',
      color: 'from-pink-500 to-pink-600'
    },
    {
      icon: <BarChart3 className=" " />,
      title: 'Category Analytics',
      description: 'Explore 9 political categories with interactive graphs and insights',
      path: '/categories',
      color: 'from-indigo-500 to-indigo-600'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/20 relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-1/2 -right-1/4 w-96 h-96 bg-blue-200/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute top-1/3 -left-1/4 w-96 h-96 bg-indigo-200/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-200/20 rounded-full blur-3xl animate-pulse delay-2000"></div>
      </div>

      {/* Header with Enhanced Glassmorphism */}
      <header className="relative z-10 backdrop-blur-md bg-white/40 border-b border-white/30 shadow-lg shadow-gray-200/30">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="text-center flex-1">
              <Link to="/" className="flex items-center ">
                <img src={logo} alt="Speech Analysis" className="h-20 w-640px" />
              </Link>
              
            </div>
            
            {/* Logout Button */}
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-800 font-semibold backdrop-blur-sm bg-white/50 px-3 py-1.5 rounded-lg border border-white/40">
                {email}
              </span>
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white rounded-xl transition-all duration-300 font-semibold shadow-lg hover:shadow-xl hover:scale-105"
              >
                <LogOut size={18} />
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative max-w-7xl mx-auto px-4 py-12 sm:px-6 lg:px-8 z-10">
        {/* Hero Section */}
        <div className="text-center mb-16 backdrop-blur-xl bg-white/50 rounded-2xl p-8 border border-white/40 shadow-xl">
          <h2 className="text-3xl font-bold bg-gradient-to-r from-gray-900 via-gray-800 to-gray-700 bg-clip-text text-transparent mb-4">
            Welcome to Political News Analysis Platform
          </h2>
          <p className="text-xl text-gray-700 max-w-3xl mx-auto font-medium">
            Comprehensive tools for scraping, analyzing, and retrieving political news articles 
            from leading Bangladeshi newspapers with AI-powered insights.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
          {features.map((feature, index) => (
            <div
              key={index}
              onClick={() => navigate(feature.path)}
              className="group backdrop-blur-xl bg-white/60 rounded-2xl shadow-xl p-8 hover:shadow-2xl transition-all duration-300 cursor-pointer hover:scale-105 border border-white/40 hover:bg-white/70"
            >
              <div className={`w-16 h-16 rounded-2xl bg-gradient-to-r ${feature.color} flex items-center justify-center mb-6 shadow-lg group-hover:scale-110 transition-transform`}>
                {feature.icon}
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-3">
                {feature.title}
              </h3>
              <p className="text-gray-700 mb-6 leading-relaxed">
                {feature.description}
              </p>
              <button className={`px-6 py-3 cursor-pointer bg-gradient-to-r ${feature.color} text-white font-semibold rounded-xl hover:shadow-xl transition-all duration-300 hover:scale-105 inline-flex items-center gap-2`}>
                <span>Get Started</span>
                <span className="text-lg">→</span>
              </button>
            </div>
          ))}
        </div>
        {/* Features List */}
        {/* <div className="backdrop-blur-xl bg-gradient-to-r from-blue-500/90 to-purple-600/90 rounded-2xl shadow-2xl p-8 text-white border border-white/20">
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
        </div> */}

        {/* Developer Tools Section */}
        {/* <div className="backdrop-blur-2xl bg-gradient-to-r from-gray-800/50 to-gray-900/50 rounded-3xl shadow-2xl p-10 mb-12 border border-white/10">
          <h3 className="text-2xl font-bold text-white mb-8 text-center flex items-center justify-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-yellow-400/30 to-yellow-500/30 backdrop-blur-sm flex items-center justify-center">
              <span className="text-2xl">⚙️</span>
            </div>
            Developer Tools
          </h3>
          <div className="grid grid-cols-1 gap-6">
            <div
              onClick={() => navigate('/categorization-test')}
              className="group backdrop-blur-xl bg-white/10 hover:bg-white/20 rounded-2xl p-8 transition-all duration-500 cursor-pointer border border-white/20 hover:border-white/40 hover:shadow-2xl hover:scale-[1.02]"
            >
              <div className="flex items-center space-x-6">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-yellow-400 to-yellow-600 flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300">
                  <FileSearch className="text-white w-8 h-8" />
                </div>
                <div className="flex-1">
                  <h4 className="font-bold text-white text-xl mb-2 group-hover:text-yellow-200 transition-colors">Categorization Test</h4>
                  <p className="text-gray-300 text-sm leading-relaxed">
                    Validate article categorization and party-figure associations in the database
                  </p>
                </div>
                <div className="text-white/50 group-hover:text-white/90 text-3xl group-hover:translate-x-2 transition-all duration-300">→</div>
              </div>
            </div>
          </div>
        </div> */}

      </main>

      {/* Footer with Glass Effect */}
      <footer className="relative backdrop-blur-md bg-white/40 shadow-lg shadow-gray-200/30 mt-12 border-t border-white/30 z-10">
        <div className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
          <p className="text-center text-gray-700 text-sm font-medium">
            © {new Date().getFullYear()} Speech Analysis System
          </p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;

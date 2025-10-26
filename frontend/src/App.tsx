import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import SearchPage from './pages/SearchPage'
import DatabasePage from './pages/DatabasePage'
import ScrapingAnalysisPage from './pages/ScrapingAnalysisPage'
import CategorizationTestPage from './pages/CategorizationTestPage'
import ChatbotPage from './pages/ChatbotPage'
import FigureProfile from './components/FigureProfile'
import PartyProfile from './components/PartyProfile'
import PoliticalPartyList from './components/PoliticalPartyList'
import NewspaperScraper from './components/NewspaperScraper'
import ProtectedRoute from './components/ProtectedRoute'
import { Chatbot } from './components/Chatbot'

function AppContent() {
  const location = useLocation();
  const showFloatingChatbot = location.pathname !== '/chatbot' && location.pathname !== '/login';

  return (
    <>
      <Routes>
        {/* Public Route - Login */}
        <Route path="/login" element={<LoginPage />} />
        
        {/* Protected Routes */}
        <Route path="/" element={<ProtectedRoute><LandingPage /></ProtectedRoute>} />
        <Route path="/parties" element={<ProtectedRoute><PoliticalPartyList /></ProtectedRoute>} />
        <Route path="/party/:partyName" element={<ProtectedRoute><PartyProfile /></ProtectedRoute>} />
        <Route path="/figure/:partyName/:figureName" element={<ProtectedRoute><FigureProfile /></ProtectedRoute>} />
        <Route path="/scraper" element={<ProtectedRoute><NewspaperScraper /></ProtectedRoute>} />
        <Route path="/search" element={<ProtectedRoute><SearchPage /></ProtectedRoute>} />
        <Route path="/database" element={<ProtectedRoute><DatabasePage /></ProtectedRoute>} />
        <Route path="/scraping-analysis" element={<ProtectedRoute><ScrapingAnalysisPage /></ProtectedRoute>} />
        <Route path="/categorization-test" element={<ProtectedRoute><CategorizationTestPage /></ProtectedRoute>} />
        <Route path="/chatbot" element={<ProtectedRoute><ChatbotPage /></ProtectedRoute>} />
      </Routes>
      
      {/* Floating Chatbot - shows on all pages except /chatbot and /login */}
      {showFloatingChatbot && (
        <Chatbot apiUrl={import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'} />
      )}
    </>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  )
}

export default App

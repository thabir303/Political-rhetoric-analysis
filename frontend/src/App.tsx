import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import SearchPage from './pages/SearchPage'
import DatabasePage from './pages/DatabasePage'
import ScrapingAnalysisPage from './pages/ScrapingAnalysisPage'
import CategorizationTestPage from './pages/CategorizationTestPage'
import ChatbotPage from './pages/ChatbotPage'
import FigureProfile from './components/FigureProfile'
import PartyProfile from './components/PartyProfile'
import PoliticalPartyList from './components/PoliticalPartyList'
import NewspaperScraper from './components/NewspaperScraper'
import { Chatbot } from './components/Chatbot'

function AppContent() {
  const location = useLocation();
  const showFloatingChatbot = location.pathname !== '/chatbot';

  return (
    <>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/parties" element={<PoliticalPartyList />} />
        <Route path="/party/:partyName" element={<PartyProfile />} />
        <Route path="/figure/:partyName/:figureName" element={<FigureProfile />} />
        <Route path="/scraper" element={<NewspaperScraper />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/database" element={<DatabasePage />} />
        <Route path="/scraping-analysis" element={<ScrapingAnalysisPage />} />
        <Route path="/categorization-test" element={<CategorizationTestPage />} />
        <Route path="/chatbot" element={<ChatbotPage />} />
      </Routes>
      
      {/* Floating Chatbot - shows on all pages except /chatbot */}
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

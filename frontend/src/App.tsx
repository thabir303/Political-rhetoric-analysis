import { BrowserRouter, Routes, Route } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import SearchPage from './pages/SearchPage'
import DatabasePage from './pages/DatabasePage'
import ScrapingAnalysisPage from './pages/ScrapingAnalysisPage'
import CategorizationTestPage from './pages/CategorizationTestPage'
import FigureProfile from './components/FigureProfile'
import PartyProfile from './components/PartyProfile'
import PoliticalPartyList from './components/PoliticalPartyList'
import NewspaperScraper from './components/NewspaperScraper'

function App() {
  return (
    <BrowserRouter>
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
      </Routes>
    </BrowserRouter>
  )
}

export default App

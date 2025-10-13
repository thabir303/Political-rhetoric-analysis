import { BrowserRouter, Routes, Route } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import SearchPage from './pages/SearchPage'
import DatabasePage from './pages/DatabasePage'
import FigureProfile from './components/FigureProfile'
import PoliticalPartyList from './components/PoliticalPartyList'
import NewspaperScraper from './components/NewspaperScraper'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/parties" element={<PoliticalPartyList />} />
        <Route path="/figure/:partyName/:figureName" element={<FigureProfile />} />
        <Route path="/scraper" element={<NewspaperScraper />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/database" element={<DatabasePage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App

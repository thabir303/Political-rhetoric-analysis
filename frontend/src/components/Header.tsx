import { useNavigate } from 'react-router-dom'
import { logout, getEmail, isAuthenticated } from '../utils/auth'

export default function Header() {
  const navigate = useNavigate()
  const email = getEmail()
  const authenticated = isAuthenticated()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="text-center mb-12 relative">
      {/* Logout Button */}
      {authenticated && (
        <div className="absolute top-0 right-0 flex items-center gap-4">
          <span className="text-sm text-gray-600">
            {email}
          </span>
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition duration-200 text-sm font-medium"
          >
            Logout
          </button>
        </div>
      )}

      <h1 className="text-5xl font-bold text-gray-800 mb-4">
        Speech Analysis
      </h1>
      <p className="text-xl text-gray-600 mb-2">
        RAG-based Information Retrieval System
      </p>
      <p className="text-sm text-gray-500">
        Semantic search powered by ChromaDB and Sentence Transformers
      </p>
    </header>
  )
}

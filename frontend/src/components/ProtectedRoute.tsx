import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { isAuthenticated, verifyToken } from '../utils/auth'

interface ProtectedRouteProps {
  children: React.ReactNode
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const [isVerifying, setIsVerifying] = useState(true)
  const [isValid, setIsValid] = useState(false)

  useEffect(() => {
    const checkAuth = async () => {
      // First check if token exists
      if (!isAuthenticated()) {
        setIsVerifying(false)
        setIsValid(false)
        return
      }

      // Verify token with backend
      const valid = await verifyToken()
      setIsValid(valid)
      setIsVerifying(false)
    }

    checkAuth()
  }, [])

  // Show loading while verifying
  if (isVerifying) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Verifying authentication...</p>
        </div>
      </div>
    )
  }

  // Redirect to login if not authenticated
  if (!isValid) {
    return <Navigate to="/login" replace />
  }

  // Render children if authenticated
  return <>{children}</>
}

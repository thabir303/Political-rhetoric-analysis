/**
 * Authentication utility functions for JWT-based authentication
 */

import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

// Local storage keys
const TOKEN_KEY = 'auth_token'
const EMAIL_KEY = 'admin_email'

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

export interface VerifyResponse {
  valid: boolean
  email: string
}

/**
 * Login with email and password
 */
export async function login(email: string, password: string): Promise<LoginResponse> {
  try {
    const response = await axios.post<LoginResponse>(
      `${API_BASE_URL}/auth/login`,
      { email, password },
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    )

    // Store token and email
    localStorage.setItem(TOKEN_KEY, response.data.access_token)
    localStorage.setItem(EMAIL_KEY, email)

    return response.data
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.detail || 'Login failed')
    }
    throw new Error('Login failed')
  }
}

/**
 * Logout - clear stored credentials
 */
export function logout(): void {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(EMAIL_KEY)
}

/**
 * Get stored auth token
 */
export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

/**
 * Get stored admin email
 */
export function getEmail(): string | null {
  return localStorage.getItem(EMAIL_KEY)
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  return getToken() !== null
}

/**
 * Verify token with backend
 */
export async function verifyToken(): Promise<boolean> {
  const token = getToken()
  if (!token) return false

  try {
    const response = await axios.get<VerifyResponse>(
      `${API_BASE_URL}/auth/verify`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    )
    return response.data.valid
  } catch (error) {
    // Token invalid or expired
    logout()
    return false
  }
}

/**
 * Get authorization header for API requests
 */
export function getAuthHeader(): Record<string, string> {
  const token = getToken()
  if (!token) return {}
  
  return {
    Authorization: `Bearer ${token}`,
  }
}

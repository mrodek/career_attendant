import { useLayoutEffect } from 'react'
import { useAuth } from '@clerk/clerk-react'
import { setAuthTokenGetter } from '../lib/api-client'

/**
 * Connects Clerk authentication to the API client.
 * Must be rendered inside ClerkProvider.
 */
export default function AuthProvider({ children }: { children: React.ReactNode }) {
  const { getToken } = useAuth()

  // Use useLayoutEffect to set token getter BEFORE children render
  // This prevents race conditions where API calls happen before token is available
  useLayoutEffect(() => {
    // Set the token getter for the API client
    setAuthTokenGetter(async () => {
      try {
        return await getToken()
      } catch {
        return null
      }
    })
  }, [getToken])

  return <>{children}</>
}

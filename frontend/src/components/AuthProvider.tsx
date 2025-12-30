import { useEffect } from 'react'
import { useAuth } from '@clerk/clerk-react'
import { setAuthTokenGetter } from '../lib/api-client'

/**
 * Connects Clerk authentication to the API client.
 * Must be rendered inside ClerkProvider.
 */
export default function AuthProvider({ children }: { children: React.ReactNode }) {
  const { getToken } = useAuth()

  useEffect(() => {
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

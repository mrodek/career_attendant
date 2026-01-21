import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ClerkProvider } from '@clerk/clerk-react'
import AuthProvider from './components/AuthProvider'
import App from './App'
import './index.css'

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY
console.log('All env vars:', import.meta.env)
console.log('Clerk key:', PUBLISHABLE_KEY)

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
})

// Render with or without Clerk based on key availability
const AppWithProviders = ({ withAuth = false }: { withAuth?: boolean }) => (
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {withAuth ? (
          <AuthProvider>
            <App />
          </AuthProvider>
        ) : (
          <App />
        )}
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>
)

if (PUBLISHABLE_KEY) {
  createRoot(document.getElementById('root')!).render(
    <ClerkProvider 
      publishableKey={PUBLISHABLE_KEY}
      signInUrl="/sign-in"
      signUpUrl="/sign-up"
      fallbackRedirectUrl="/"
    >
      <AppWithProviders withAuth />
    </ClerkProvider>,
  )
} else {
  console.warn('Clerk publishable key not found. Running without authentication.')
  createRoot(document.getElementById('root')!).render(<AppWithProviders />)
}

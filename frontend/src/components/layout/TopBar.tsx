import { Star } from 'lucide-react'
import {
  SignInButton,
  SignedIn,
  SignedOut,
  UserButton,
} from '@clerk/clerk-react'

const CLERK_ENABLED = !!import.meta.env.VITE_CLERK_PUBLISHABLE_KEY

export default function TopBar() {
  return (
    <div className="bg-slate-900 text-slate-100 px-8 py-4 border-b border-slate-800">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
            <Star className="text-white" size={24} />
          </div>
          <div>
            <h1 className="text-xl font-bold">Career Attendant</h1>
            <p className="text-xs text-slate-400">Your AI-Powered Job Search Assistant</p>
          </div>
        </div>

        {CLERK_ENABLED ? (
          <>
            <SignedOut>
              <SignInButton mode="modal">
                <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">
                  Sign In
                </button>
              </SignInButton>
            </SignedOut>
            <SignedIn>
              <UserButton 
                appearance={{
                  elements: {
                    avatarBox: 'w-10 h-10',
                  },
                }}
              />
            </SignedIn>
          </>
        ) : (
          <span className="text-sm text-slate-400">Dev Mode</span>
        )}
      </div>
    </div>
  )
}

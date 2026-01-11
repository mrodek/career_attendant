import { Link } from 'react-router-dom'
import { Star, TrendingUp, Edit3, Calendar, Bookmark } from 'lucide-react'
import { SignInButton, SignedIn, SignedOut } from '@clerk/clerk-react'

export default function HomePage() {

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Top Bar */}
      <header className="bg-slate-900 text-slate-100 px-8 py-4 border-b border-slate-800">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <Star className="text-white" size={24} />
            </div>
            <div>
              <h1 className="text-xl font-bold">Career Attendant</h1>
              <p className="text-xs text-slate-400">Your AI-Powered Job Search Assistant</p>
            </div>
          </div>
          <SignedIn>
            <Link 
              to="/jobs"
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium text-sm"
            >
              View Your Jobs
            </Link>
          </SignedIn>
          <SignedOut>
            <SignInButton mode="modal" forceRedirectUrl="/jobs">
              <button className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium text-sm">
                Login / Sign Up
              </button>
            </SignInButton>
          </SignedOut>
        </div>
      </header>

      {/* Hero Section */}
      <div className="relative bg-gradient-to-br from-slate-900 via-slate-800 to-blue-900 text-white overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-20 left-20 w-72 h-72 bg-blue-500 rounded-full blur-3xl"></div>
          <div className="absolute bottom-20 right-20 w-96 h-96 bg-purple-500 rounded-full blur-3xl"></div>
        </div>
        
        <div className="relative max-w-7xl mx-auto px-8 py-20">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div>
              <h2 className="text-5xl lg:text-6xl font-bold mb-6 leading-tight">
                Transform Your Job Search with AI
              </h2>
              <p className="text-xl text-slate-300 mb-8 leading-relaxed">
                Career Attendant streamlines your job hunt with intelligent tracking, AI-powered resume generation, and personalized job fit analysis.
              </p>
              <div className="flex gap-4">
                <Link 
                  to="/jobs"
                  className="px-8 py-4 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition font-semibold text-lg shadow-lg hover:shadow-xl"
                >
                  Get Started
                </Link>
                <button className="px-8 py-4 bg-white/10 backdrop-blur-sm text-white rounded-xl hover:bg-white/20 transition font-semibold text-lg border border-white/20">
                  Learn More
                </button>
              </div>
            </div>

            <div className="hidden lg:block relative">
              <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8 border border-white/20 shadow-2xl">
                <div className="space-y-4">
                  <FeatureCard 
                    icon={<TrendingUp size={24} />}
                    title="Smart Job Matching"
                    description="AI analyzes your fit for each role"
                    color="bg-blue-600"
                  />
                  <FeatureCard 
                    icon={<Edit3 size={24} />}
                    title="Tailored Documents"
                    description="Auto-generate targeted resumes"
                    color="bg-purple-600"
                  />
                  <FeatureCard 
                    icon={<Calendar size={24} />}
                    title="Track Everything"
                    description="Never miss a follow-up or deadline"
                    color="bg-emerald-600"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Features Grid */}
      <div className="max-w-7xl mx-auto px-8 py-20">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-slate-900 mb-4">Everything You Need to Land Your Next Role</h2>
          <p className="text-xl text-slate-600">Powerful features designed to streamline your job search</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          <FeatureBlock 
            icon={<Star className="text-blue-600" size={28} />}
            title="AI Job Fit Analysis"
            description="Our AI evaluates how well each position matches your skills, experience, and career goals."
            bgColor="bg-blue-100"
          />
          <FeatureBlock 
            icon={<Edit3 className="text-purple-600" size={28} />}
            title="Targeted Resume Generator"
            description="Automatically create customized resumes and cover letters tailored to each job posting."
            bgColor="bg-purple-100"
          />
          <FeatureBlock 
            icon={<Calendar className="text-emerald-600" size={28} />}
            title="Application Tracking"
            description="Keep all your applications organized in one place. Track status, set reminders, and never miss a deadline."
            bgColor="bg-emerald-100"
          />
          <FeatureBlock 
            icon={<TrendingUp className="text-blue-600" size={28} />}
            title="Progress Dashboard"
            description="Visualize your job search journey with comprehensive analytics and success tracking."
            bgColor="bg-blue-100"
          />
          <FeatureBlock 
            icon={<Bookmark className="text-indigo-600" size={28} />}
            title="Smart Organization"
            description="Sort, filter, and prioritize jobs based on fit score, interest level, and application status."
            bgColor="bg-indigo-100"
          />
          <FeatureBlock 
            icon={<Star className="text-amber-600" size={28} />}
            title="Browser Extension"
            description="Save jobs from any job board with one click using our Chrome extension."
            bgColor="bg-amber-100"
          />
        </div>
      </div>
    </div>
  )
}

function FeatureCard({ icon, title, description, color }: { 
  icon: React.ReactNode
  title: string
  description: string
  color: string 
}) {
  return (
    <div className="flex items-center gap-4 p-4 bg-white/10 rounded-xl">
      <div className={`w-12 h-12 ${color} rounded-lg flex items-center justify-center flex-shrink-0`}>
        {icon}
      </div>
      <div className="flex-1">
        <p className="font-semibold text-lg">{title}</p>
        <p className="text-sm text-slate-300">{description}</p>
      </div>
    </div>
  )
}

function FeatureBlock({ icon, title, description, bgColor }: { 
  icon: React.ReactNode
  title: string
  description: string
  bgColor: string 
}) {
  return (
    <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200 hover:shadow-lg transition">
      <div className={`w-14 h-14 ${bgColor} rounded-xl flex items-center justify-center mb-6`}>
        {icon}
      </div>
      <h3 className="text-2xl font-bold text-slate-900 mb-4">{title}</h3>
      <p className="text-slate-600 leading-relaxed">{description}</p>
    </div>
  )
}

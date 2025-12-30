import { Link, useLocation } from 'react-router-dom'
import { Home, LayoutDashboard, Bookmark, ChevronLeft, ChevronRight } from 'lucide-react'
import { useUIStore } from '../../stores/ui-store'

const navItems = [
  { path: '/', icon: Home, label: 'Home' },
  { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/jobs', icon: Bookmark, label: 'Saved Jobs' },
]

export default function Sidebar() {
  const location = useLocation()
  const { isNavExpanded, toggleNav } = useUIStore()

  return (
    <div
      className={`${
        isNavExpanded ? 'w-72' : 'w-20'
      } bg-slate-900 text-slate-100 transition-all duration-300 flex flex-col shadow-xl`}
    >
      {/* Logo */}
      <div className="p-6 border-b border-slate-700">
        {isNavExpanded && (
          <div>
            <h1 className="text-2xl font-bold text-blue-400">Career Hub</h1>
            <p className="text-sm text-slate-400 mt-1">Track your applications</p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {navItems.map(({ path, icon: Icon, label }) => {
          const isActive = location.pathname === path
          return (
            <Link
              key={path}
              to={path}
              className={`w-full flex items-center gap-4 p-4 rounded-lg transition ${
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'hover:bg-slate-800'
              }`}
            >
              <Icon size={22} />
              {isNavExpanded && <span className="font-medium">{label}</span>}
            </Link>
          )
        })}
      </nav>

      {/* Toggle Button */}
      <button
        onClick={toggleNav}
        className="p-4 border-t border-slate-700 hover:bg-slate-800 flex items-center justify-center"
      >
        {isNavExpanded ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
      </button>
    </div>
  )
}

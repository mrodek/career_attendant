import { Routes, Route } from 'react-router-dom'
import AppLayout from './components/layout/AppLayout'
import HomePage from './pages/HomePage'
import SavedJobsPage from './pages/SavedJobsPage'
import DashboardPage from './pages/DashboardPage'

function App() {
  return (
    <Routes>
      {/* Pages with sidebar layout */}
      <Route element={<AppLayout />}>
        <Route path="/jobs" element={<SavedJobsPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
      </Route>
      
      {/* Landing page without sidebar */}
      <Route path="/" element={<HomePage />} />
    </Routes>
  )
}

export default App

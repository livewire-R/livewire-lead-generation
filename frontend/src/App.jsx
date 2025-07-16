import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from '@/components/theme-provider'
import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import AdminPage from './pages/AdminPage'
import OnboardingPage from './pages/OnboardingPage'
import './App.css'

function App() {
  return (
    <ThemeProvider defaultTheme="light" storageKey="livewire-ui-theme">
      <Router>
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/onboarding" element={<OnboardingPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/admin" element={<AdminPage />} />
          </Routes>
        </div>
      </Router>
    </ThemeProvider>
  )
}

export default App


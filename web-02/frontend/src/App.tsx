import { Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import AppLayout from './components/layout/AppLayout'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import ClassesPage from './pages/ClassesPage'
import ClassDetailPage from './pages/ClassDetailPage'
import AssignmentPage from './pages/AssignmentPage'
import GalleryPage from './pages/GalleryPage'

function AppRoutes() {
  const { user, loading } = useAuth()

  if (loading) {
    return <div className="boot-screen"><div className="brand-mark">D</div><span>Đang mở không gian học tập…</span></div>
  }
  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    )
  }
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/classes" element={<ClassesPage />} />
        <Route path="/classes/:id" element={<ClassDetailPage />} />
        <Route path="/assignments/:id" element={<AssignmentPage />} />
        <Route path="/gallery" element={<GalleryPage />} />
        <Route path="/discussion" element={<GalleryPage key="discussion" />} />
        <Route path="/comparison" element={<GalleryPage key="comparison" mode="comparison" />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}

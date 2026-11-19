import { Outlet } from 'react-router-dom'
import { CheckCircle2 } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import AppSidebar from './AppSidebar'

export default function AppLayout() {
  const { toast } = useAuth()
  return (
    <div className="app-shell community-shell">
      <AppSidebar />
      <main className="main-area"><Outlet /></main>
      {toast && <div className="toast"><CheckCircle2 size={17} />{toast}</div>}
    </div>
  )
}

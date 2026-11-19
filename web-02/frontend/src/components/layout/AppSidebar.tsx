import { NavLink } from 'react-router-dom'
import { BookOpen, CircleHelp, LayoutDashboard, LogOut, MessageSquare, Sparkles } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import Brand from './Brand'

export default function AppSidebar() {
  const { user, logout } = useAuth()
  if (!user) return null
  return (
    <aside className="sidebar">
      <Brand />
      <div className="side-label">KHÔNG GIAN HỌC TẬP</div>
      <nav className="side-nav">
        <NavLink to="/" end><LayoutDashboard size={18} />Tổng quan</NavLink>
        <NavLink to="/classes"><BookOpen size={18} />Lớp học</NavLink>
        <NavLink to="/comparison"><Sparkles size={18} />AI so sánh bài</NavLink>
        <NavLink to="/discussion"><MessageSquare size={18} />Thảo luận</NavLink>
      </nav>
      <div className="sidebar-bottom">
        <div className="help-card">
          <div className="help-icon"><CircleHelp size={17} /></div>
          <strong>Cần trợ giúp?</strong>
          <span>Hãy bắt đầu bằng một câu hỏi hay.</span>
        </div>
        <button className="profile-button" onClick={logout}>
          <span className="avatar">{user.full_name.slice(0, 1).toUpperCase()}</span>
          <span className="profile-copy">
            <strong>{user.full_name}</strong>
            <small>{user.role === 'teacher' ? 'Giáo viên' : 'Sinh viên'}</small>
          </span>
          <LogOut size={17} className="logout-icon" />
        </button>
      </div>
    </aside>
  )
}

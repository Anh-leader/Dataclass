import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Activity, ArrowRight, BarChart3, BookOpen, CheckCircle2, Sparkles } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { classApi, dashboardApi } from '../services/api'
import type { ClassItem, DashboardStats } from '../types'
import { todayLong } from '../utils/format'
import ClassCard from '../components/classes/ClassCard'
import EmptyState from '../components/ui/EmptyState'
import LoadingState from '../components/ui/LoadingState'
import PageContainer from '../components/layout/PageContainer'

export default function DashboardPage() {
  const { user, notify } = useAuth()
  const [classes, setClasses] = useState<ClassItem[]>([])
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    classApi.list()
      .then(setClasses)
      .catch(e => notify(e.message))
      .finally(() => setLoading(false))
    dashboardApi.get().then(setStats).catch(() => {})
  }, [notify])

  if (!user) return null
  const total = classes.reduce((sum, item) => sum + item.assignment_count, 0)

  return (
    <PageContainer>
      <div className="welcome-strip">
        <div className="welcome-copy">
          <div className="welcome-date">{todayLong()}</div>
          <h2>Mỗi dữ liệu đều kể một câu chuyện<span>.</span></h2>
          <p>Chào {user.full_name.split(' ').slice(-1)[0]}, hôm nay bạn muốn khám phá điều gì?</p>
        </div>
        <div className="welcome-illustration">
          <div className="orbit orbit-one" /><div className="orbit orbit-two" />
          <div className="orbit-core"><BarChart3 size={27} /></div>
          <i className="orbit-node node-a" /><i className="orbit-node node-b" /><i className="orbit-node node-c" />
        </div>
        <div className="welcome-spark"><Sparkles size={16} /></div>
      </div>

      <div className="metric-grid">
        <div className="metric-card">
          <div className="metric-icon mint"><BookOpen size={19} /></div>
          <div><span>Lớp học của bạn</span><strong>{classes.length.toString().padStart(2, '0')}</strong></div>
          <small>đang tham gia</small>
        </div>
        <div className="metric-card">
          <div className="metric-icon peach"><Activity size={19} /></div>
          <div><span>{user.role === 'teacher' ? 'Bài tập đang mở' : 'Bài tập đang mở'}</span><strong>{String(stats?.open_assignments ?? total).padStart(2, '0')}</strong></div>
          <small>trong các lớp</small>
        </div>
        <div className="metric-card">
          <div className="metric-icon lavender"><CheckCircle2 size={19} /></div>
          <div><span>{user.role === 'teacher' ? 'Bài chờ chấm' : 'Bài đã nộp'}</span><strong>{String(user.role === 'teacher' ? (stats?.pending_grades ?? 0) : (stats?.my_submissions ?? 0)).padStart(2, '0')}</strong></div>
          <small>{user.role === 'teacher' ? 'cần chấm điểm' : 'của bạn'}</small>
        </div>
      </div>

      <div className="section-heading">
        <div><div className="page-eyebrow">KHÔNG GIAN CỦA BẠN</div><h2>Lớp học gần đây</h2></div>
        <Link to="/classes" className="text-link">Xem tất cả <ArrowRight size={15} /></Link>
      </div>

      {loading ? (
        <LoadingState text="Đang tải lớp học…" />
      ) : classes.length ? (
        <div className="class-grid">{classes.slice(0, 3).map((item, i) => <ClassCard key={item.id} item={item} index={i} />)}</div>
      ) : (
        <EmptyState
          icon={<BookOpen />}
          title="Chưa có lớp học nào"
          text={user.role === 'teacher' ? 'Tạo lớp đầu tiên để bắt đầu giao bài phân tích.' : 'Tham gia lớp bằng mã do giáo viên cung cấp.'}
          action={<Link to="/classes" className="button button-primary">{user.role === 'teacher' ? 'Tạo lớp học' : 'Tham gia lớp'}<ArrowRight size={16} /></Link>}
        />
      )}

      <div className="bottom-note">
        <div className="bottom-note-icon"><Sparkles size={17} /></div>
        <div><strong>Học cách đặt câu hỏi hay.</strong><span>AI ở đây để gợi mở cách nghĩ, giúp bạn tự tin với kết quả của mình.</span></div>
        <Link to="/classes">Khám phá lớp học <ArrowRight size={15} /></Link>
      </div>
    </PageContainer>
  )
}

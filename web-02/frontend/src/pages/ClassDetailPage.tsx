import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, ArrowRight, BookOpen, FileSpreadsheet, Plus } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { classApi } from '../services/api'
import type { Assignment } from '../types'
import { fmtDate, remaining } from '../utils/format'
import EmptyState from '../components/ui/EmptyState'
import LoadingState from '../components/ui/LoadingState'
import PageContainer from '../components/layout/PageContainer'
import AssignmentCreatePage from './AssignmentCreatePage'

export default function ClassDetailPage() {
  const { id = '' } = useParams()
  const { user, notify } = useAuth()
  const [data, setData] = useState<{ id: number; name: string; join_code?: string; assignments: Assignment[] } | null>(null)
  const [error, setError] = useState('')
  const [creating, setCreating] = useState(false)

  const load = () => classApi.get(id).then(setData).catch(e => setError(e.message))
  useEffect(() => { load() }, [id])

  if (creating) {
    return <AssignmentCreatePage classId={Number(id)} onDone={() => { setCreating(false); load(); notify('Bài tập đã được tạo.') }} onCancel={() => setCreating(false)} />
  }
  if (error) return <PageContainer><div className="form-error">{error}</div></PageContainer>
  if (!data) return <PageContainer><LoadingState text="Đang tải lớp học…" /></PageContainer>

  const assignments = data.assignments || []

  return (
    <PageContainer>
      <Link to="/classes" className="back-link"><ArrowLeft size={15} />Tất cả lớp học</Link>
      <div className="class-hero">
        <div className="class-hero-icon"><BookOpen size={24} /></div>
        <div>
          <div className="page-eyebrow">LỚP HỌC</div>
          <h1>{data.name}</h1>
          <p>{user?.role === 'teacher' ? 'Quản lý bài tập và xem tiến độ sinh viên.' : 'Khám phá bài tập và cùng lớp phân tích dữ liệu.'}</p>
        </div>
        {data.join_code && (
          <div className="join-code-card"><span>MÃ THAM GIA</span><strong>{data.join_code}</strong></div>
        )}
      </div>

      <div className="section-heading">
        <div><div className="page-eyebrow">HỌC QUA THỰC HÀNH</div><h2>Bài tập</h2></div>
        {user?.role === 'teacher' && <button className="button button-primary" onClick={() => setCreating(true)}><Plus size={17} />Tạo bài tập</button>}
      </div>

      {assignments.length ? (
        <div className="assignment-list">
          {assignments.map(a => (
            <Link key={a.id} className="assignment-row" to={`/assignments/${a.id}`}>
              <div className="assignment-row-icon"><FileSpreadsheet size={19} /></div>
              <div className="assignment-row-main">
                <div className="assignment-row-title">{a.title}<span className={`status-pill ${a.status}`}>{a.status === 'published' ? 'Đã giao' : 'Bản nháp'}</span></div>
                <span>{a.datasets.length} dataset · {a.questions.length} câu hỏi</span>
              </div>
              <div className="assignment-due">
                <small>{user?.role === 'teacher' ? 'HẠN NỘP' : remaining(a.due_at)}</small>
                <strong>{fmtDate(a.due_at)}</strong>
              </div>
              <span className="row-arrow"><ArrowRight size={18} /></span>
            </Link>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={<FileSpreadsheet />}
          title="Chưa có bài tập"
          text={user?.role === 'teacher' ? 'Tạo bài đầu tiên với đề bài, dataset và rubric.' : 'Giáo viên sẽ đăng bài tập tại đây.'}
          action={user?.role === 'teacher' ? <button className="button button-primary" onClick={() => setCreating(true)}>Tạo bài tập<Plus size={16} /></button> : undefined}
        />
      )}
    </PageContainer>
  )
}

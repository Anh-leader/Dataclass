import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { ArrowUpDown, BookOpen, ChevronRight, MessageCircle, RefreshCw, Share2, Sparkles } from 'lucide-react'
import { classApi, galleryApi } from '../services/api'
import type { Assignment, ClassItem, GalleryItem } from '../types'
import { useAuth } from '../context/AuthContext'
import { fmtDate } from '../utils/format'
import PageContainer from '../components/layout/PageContainer'
import EmptyState from '../components/ui/EmptyState'
import LoadingState from '../components/ui/LoadingState'
import DiscussionBoard from '../components/assignments/DiscussionBoard'
import AIComparison from '../components/assignments/AIComparison'

export default function GalleryPage({ mode = 'discussion' }: { mode?: 'discussion' | 'comparison' }) {
  const { user, notify } = useAuth()
  const [params] = useSearchParams()
  const [classes, setClasses] = useState<ClassItem[]>([])
  const [classId, setClassId] = useState(params.get('class') || '')
  const [assignmentId, setAssignmentId] = useState(params.get('assignment') || '')
  const [assignments, setAssignments] = useState<Assignment[]>([])
  const [items, setItems] = useState<GalleryItem[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [sort, setSort] = useState('votes')
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    classApi.list().then(result => {
      setClasses(result)
      setClassId(previous => result.some(c => String(c.id) === previous) ? previous : String(result[0]?.id || ''))
      if (!result.length) setLoading(false)
    }).catch(e => { setError(e.message); setLoading(false) })
  }, [])

  useEffect(() => {
    if (!classId) return
    let cancelled = false
    setLoading(true)
    setItems([])
    setAssignments([])
    setError('')
    Promise.all([classApi.get(classId), mode === 'discussion' ? galleryApi.list(classId) : Promise.resolve([])]).then(([group, data]) => {
      if (cancelled) return
      setAssignments(group.assignments.filter(a => a.status === 'published'))
      setAssignmentId(previous => group.assignments.some(a => String(a.id) === previous) ? previous : '')
      setItems(data)
    }).catch(e => { if (!cancelled) setError(e.message) }).finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [classId, mode])

  async function reload() {
    const [group, data] = await Promise.all([classApi.get(classId), mode === 'discussion' ? galleryApi.list(classId) : Promise.resolve([])])
    setAssignments(group.assignments.filter(a => a.status === 'published'))
    setItems(data)
    setRefreshKey(previous => previous + 1)
  }
  useEffect(() => {
    const delay = assignments.map(a => new Date(a.sharing_open_at).getTime() - Date.now()).filter(value => value > 0).sort((a, b) => a - b)[0]
    if (delay === undefined || delay > 2147480000) return
    const timer = window.setTimeout(() => { reload().catch(e => setError(e.message)) }, delay + 200)
    return () => window.clearTimeout(timer)
  }, [assignments, classId])
  if (!user) return null
  const displayed = items.filter(item => !assignmentId || String(item.assignment_id) === assignmentId).sort((a, b) => {
    if (sort === 'votes') return b.vote_count - a.vote_count || a.student.localeCompare(b.student, 'vi')
    if (sort === 'comments') return b.comments.length - a.comments.length
    if (sort === 'recent') return new Date(b.versions[0].submitted_at).getTime() - new Date(a.versions[0].submitted_at).getTime()
    return a.student.localeCompare(b.student, 'vi')
  })
  const scheduled = assignments.filter(a => (!assignmentId || String(a.id) === assignmentId) && !a.sharing_open)

  return (
    <PageContainer className="community-page">
      <div className="community-breadcrumb"><Link to="/classes"><BookOpen size={14} />Lớp học</Link><ChevronRight size={13} /><span>{mode === 'comparison' ? 'AI so sánh bài' : 'Thảo luận'}</span></div>
      <header className="community-header"><div><span className="community-eyebrow">CÙNG NHAU TIẾN BỘ</span><h1>{mode === 'comparison' ? 'AI so sánh bài' : 'Thảo luận'}<span className="community-title-icon">{mode === 'comparison' ? <Sparkles size={23} /> : <MessageCircle size={23} />}</span></h1><p>{mode === 'comparison' ? 'Khám phá điều khác biệt. Học từ bạn bè. Hoàn thiện bài của mình.' : 'Xem bài làm của mọi người, chia sẻ góc nhìn và cùng nhau học tốt hơn.'}</p></div><div className="community-header-actions"><Link className="community-switch" to={`/${mode === 'comparison' ? 'discussion' : 'comparison'}?class=${classId}&assignment=${assignmentId}`}>{mode === 'comparison' ? <MessageCircle size={16} /> : <Sparkles size={16} />}{mode === 'comparison' ? 'Thảo luận' : 'AI so sánh bài'}<ChevronRight size={14} /></Link><button className="community-refresh" aria-label="Cập nhật bài nộp" title="Cập nhật bài nộp" disabled={!classId || loading} onClick={() => { reload().catch(e => setError(e.message)) }}><RefreshCw size={17} className={loading ? 'comparison-spin' : ''} /></button></div></header>
      <div className="community-toolbar">
        <div className="community-filters"><label><BookOpen size={15} /><span className="sr-only">Lớp học</span><select aria-label="Lớp học" value={classId} onChange={e => { setClassId(e.target.value); setAssignmentId('') }}>{!classes.length && <option value="">Chưa có lớp học</option>}{classes.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></label>
        <label><span className="sr-only">Bài tập</span><select aria-label="Bài tập" value={assignmentId} onChange={e => setAssignmentId(e.target.value)}><option value="">Tất cả bài tập</option>{assignments.map(a => <option key={a.id} value={a.id}>{a.title}</option>)}</select></label></div>
        {mode === 'discussion' ? <label className="community-sort"><ArrowUpDown size={15} /><select aria-label="Sắp xếp bài nộp" value={sort} onChange={e => setSort(e.target.value)}><option value="votes">Nhiều bình chọn nhất</option><option value="recent">Mới nhất</option><option value="comments">Nhiều bình luận nhất</option><option value="name">Tên sinh viên</option></select></label> : <span className="community-toolbar-note"><Sparkles size={14} />Học hỏi từ mỗi lần so sánh</span>}
      </div>
      {error && <div className="form-error">{error}</div>}
      {mode === 'comparison' && !loading && assignments.length > 0 && <AIComparison key={`${classId}:${assignmentId}:${refreshKey}`} assignments={assignments.filter(a => !assignmentId || String(a.id) === assignmentId)} />}
      {scheduled.map(a => <div className="learning-notice" key={a.id}><strong>{a.title}</strong><span>Mở xem bài từ {fmtDate(a.sharing_open_at)}. Các bài nộp được giữ riêng trước thời điểm này.</span><Link className="text-link" to={`/assignments/${a.id}`}>Mở bài tập →</Link></div>)}
      {loading ? <LoadingState text="Đang tải bài nộp…" /> : mode === 'discussion' && displayed.length ? <DiscussionBoard items={displayed} user={user} reload={reload} notify={notify} /> : !error && ((mode === 'discussion' && !displayed.length) || !assignments.length) && <EmptyState icon={<Share2 />} title="Chưa có bài chia sẻ" text="Bài đã nộp sẽ xuất hiện theo lịch và cách chia sẻ giáo viên đặt. Bản nháp luôn được giữ riêng." />}
    </PageContainer>
  )
}

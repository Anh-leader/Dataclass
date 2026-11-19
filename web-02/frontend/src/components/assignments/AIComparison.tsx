import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, Check, Clock3, Files, History, Loader2, Search, ShieldCheck, Sparkles, TrendingUp, Users } from 'lucide-react'
import { api, post } from '../../api'
import type { Assignment } from '../../types'
import StudentAvatar from './StudentAvatar'
import ComparisonResult from './ComparisonResult'
import type { ComparisonFeedback } from './ComparisonResult'
import { fmtDate } from '../../utils/format'

interface Source {
  submission_id: number; student_id: number; student: string; is_mine: boolean; can_be_base: boolean
  baseline_version_id: number | null
  versions: { id: number; version_number: number; is_improvement: boolean; submitted_at: string }[]
}
interface Entry {
  id: number; status: string; created_at: string; base_version_id: number; peer_version_ids: number[]; mode: string
  result: ComparisonFeedback | null; error: string | null
}
interface ComparisonData { sources: Source[]; history: Entry[] }

export default function AIComparison({ assignments }: { assignments: Assignment[] }) {
  const [assignmentId, setAssignmentId] = useState(String(assignments.find(a => a.sharing_open)?.id || assignments[0]?.id || ''))
  const [data, setData] = useState<ComparisonData>({ sources: [], history: [] })
  const [base, setBase] = useState(0)
  const [peers, setPeers] = useState<number[]>([])
  const [selectedJob, setSelectedJob] = useState(0)
  const [loading, setLoading] = useState(false)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const [now, setNow] = useState(Date.now())
  const [mode, setMode] = useState<'peers' | 'self'>('peers')
  const [query, setQuery] = useState('')
  const assignment = assignments.find(a => String(a.id) === assignmentId)
  const entry = data.history.find(j => j.id === selectedJob)
  const pending = entry?.status === 'queued' || entry?.status === 'running'
  const baseSource = data.sources.find(s => s.versions.some(v => v.id === base))
  const bases = data.sources.filter(s => s.can_be_base && (mode === 'peers' || s.is_mine))
  const candidates = data.sources.filter(s => s.student_id !== baseSource?.student_id && s.baseline_version_id)
  const visibleCandidates = candidates.filter(s => s.student.toLocaleLowerCase('vi').includes(query.toLocaleLowerCase('vi')))
  const improvements = baseSource?.versions.filter(v => assignment && new Date(v.submitted_at) >= new Date(assignment.due_at) && v.id !== base) || []
  const history = data.history.filter(j => (j.mode || 'peers') === mode)

  function changeMode(next: 'peers' | 'self') {
    setMode(next); setSelectedJob(0); setPeers([]); setQuery(''); setError('')
    const source = data.sources.find(s => s.is_mine) || data.sources.find(s => s.can_be_base && next === 'peers')
    setBase(source?.baseline_version_id || 0)
  }
  function openEntry(job: Entry) { setSelectedJob(job.id); setBase(job.base_version_id); setPeers(job.peer_version_ids) }

  useEffect(() => {
    let cancelled = false
    setError(''); setData({ sources: [], history: [] }); setBase(0); setPeers([]); setSelectedJob(0); setQuery('')
    if (!assignment?.sharing_open) { setLoading(false); return }
    setLoading(true)
    api<ComparisonData>(`/assignments/${assignmentId}/ai/comparisons`).then(result => {
      if (cancelled) return
      setData(result)
      const initial = result.sources.find(s => s.is_mine) || result.sources.find(s => s.can_be_base)
      setBase(initial?.baseline_version_id || 0); setMode('peers')
    }).catch(e => { if (!cancelled) setError(e.message) }).finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [assignmentId, assignment?.sharing_open])

  useEffect(() => {
    if (!pending || !selectedJob) return
    let cancelled = false
    let timer: number
    async function refresh() {
      try {
        const job = await api<{ status: string; result: ComparisonFeedback | null; error: string | null }>(`/jobs/${selectedJob}`)
        if (cancelled) return
        setNow(Date.now())
        setData(previous => ({ ...previous, history: previous.history.map(j => j.id === selectedJob ? { ...j, ...job } : j) }))
        if (job.status === 'queued' || job.status === 'running') timer = window.setTimeout(refresh, 2500)
      } catch (e) { if (!cancelled) { setError((e as Error).message); setSelectedJob(0) } }
    }
    timer = window.setTimeout(refresh, 1000)
    return () => { cancelled = true; window.clearTimeout(timer) }
  }, [selectedJob, pending])

  async function compare() {
    setSending(true); setError('')
    try {
      const job = await post<{ job_id: number }>(`/assignments/${assignmentId}/ai/compare-submissions`, { mode, base_version_id: base, peer_version_ids: peers })
      const result = await api<ComparisonData>(`/assignments/${assignmentId}/ai/comparisons`)
      setData(result)
      const created = result.history.find(j => j.id === job.job_id)
      if (created) openEntry(created)
    } catch (e) { setError((e as Error).message) } finally { setSending(false) }
  }
  function choosePeer(source: Source, checked: boolean) {
    setSelectedJob(0)
    setPeers(previous => checked ? [...new Set([...previous, source.baseline_version_id!])] : previous.filter(id => id !== source.baseline_version_id))
  }
  function chooseAll() {
    setSelectedJob(0)
    const ids = visibleCandidates.map(s => s.baseline_version_id!)
    const all = ids.length > 0 && ids.every(id => peers.includes(id))
    setPeers(previous => all ? previous.filter(id => !ids.includes(id)) : [...new Set([...previous, ...ids])])
  }
  const allVisibleSelected = visibleCandidates.length > 0 && visibleCandidates.every(s => peers.includes(s.baseline_version_id!))

  return <section className="ai-comparison comparison-studio" aria-label="AI so sánh bài">
    <div className="comparison-mode-cards" role="group" aria-label="Chế độ so sánh">
      <button aria-label="So sánh bài với người khác" className={`comparison-mode-card ${mode === 'peers' ? 'is-active' : ''}`} aria-pressed={mode === 'peers'} disabled={sending} onClick={() => changeMode('peers')}><span className="mode-card-icon"><Users size={24} /></span><span><strong>So sánh bài với người khác</strong><small>Khám phá những góc nhìn mới từ bài làm của các bạn cùng lớp.</small></span><span className="mode-card-check">{mode === 'peers' && <Check size={13} />}</span></button>
      <button aria-label="So sánh 2 phiên bản của mình" className={`comparison-mode-card ${mode === 'self' ? 'is-active' : ''}`} aria-pressed={mode === 'self'} disabled={sending} onClick={() => changeMode('self')}><span className="mode-card-icon"><Files size={24} /></span><span><strong>So sánh 2 phiên bản của mình</strong><small>Nhìn lại thay đổi và theo dõi sự tiến bộ qua mỗi lần hoàn thiện bài.</small></span><span className="mode-card-check">{mode === 'self' && <Check size={13} />}</span></button>
    </div>
    {assignments.length > 1 && <label className="comparison-assignment">Bài tập để so sánh<select value={assignmentId} disabled={sending} onChange={e => setAssignmentId(e.target.value)}>{assignments.map(a => <option key={a.id} value={a.id}>{a.title}</option>)}</select></label>}
    {!assignment?.sharing_open ? <div className="comparison-locked"><Clock3 size={25} /><h3>Chờ đến giờ chia sẻ bài</h3><p>Chức năng mở cùng thời điểm chia sẻ{assignment ? `: ${fmtDate(assignment.sharing_open_at)}` : '.'}</p></div> : loading ? <div className="comparison-locked" role="status"><Loader2 size={25} className="comparison-spin" /><p>Đang chuẩn bị các bài nộp…</p></div> : <>
      <section className="comparison-workspace">
        <header className="comparison-module-heading"><div><h2>{mode === 'peers' ? 'So sánh bài với người khác' : 'Nhìn lại hành trình tiến bộ'}</h2><p>{mode === 'peers' ? 'Đối chiếu cách phân tích của bạn với bạn cùng lớp, tìm ý tưởng để tự hoàn thiện.' : 'So sánh bản cuối trước hạn với một bản mới nộp lại để nhận ra những thay đổi.'}</p></div><span className="comparison-step">{mode === 'peers' ? <Users size={16} /> : <TrendingUp size={16} />}{mode === 'peers' ? 'Học từ bạn bè' : 'Học từ chính mình'}</span></header>
        <div className="comparison-base-label">{mode === 'peers' ? 'Bài của bạn' : 'Phiên bản gốc'}</div>
        <div className="comparison-baseline-card"><StudentAvatar name={baseSource?.student || 'Bạn'} seed={baseSource?.student_id} /><div className="baseline-author"><strong>{baseSource?.student || 'Chưa có bài nộp trước hạn'}{baseSource?.is_mine && <span className="mine-label">Bạn</span>}</strong><select aria-label="Bài làm gốc" value={base} disabled={sending} onChange={e => { setBase(Number(e.target.value)); setPeers([]); setSelectedJob(0) }}>{!base && <option value={0}>Cần nộp bài trước hạn</option>}{bases.flatMap(s => s.versions.filter(v => v.id === s.baseline_version_id).map(v => <option key={v.id} value={v.id}>{bases.length > 1 ? `${s.student} · ` : ''}Phiên bản {v.version_number} · {fmtDate(v.submitted_at)}</option>))}</select></div><span className={`deadline-label ${!base ? 'is-missing' : ''}`}><ShieldCheck size={13} />{base ? 'Bản cuối trước hạn' : 'Chưa có bản hợp lệ'}</span></div>
        {mode === 'self' ? <div className="comparison-self-picker"><span className="self-version-connector"><ArrowRight size={20} /></span><div><label>Phiên bản mới nộp lại<select aria-label="Phiên bản mới nộp lại" value={peers[0] || 0} disabled={sending} onChange={e => { setPeers(e.target.value === '0' ? [] : [Number(e.target.value)]); setSelectedJob(0) }}><option value={0}>Chọn bản nộp cải thiện</option>{improvements.map(v => <option key={v.id} value={v.id}>Phiên bản {v.version_number} · {fmtDate(v.submitted_at)}</option>)}</select></label><p>AI giúp nhận ra phần đã tốt hơn và điều bạn có thể tiếp tục phát triển.</p>{!improvements.length && <Link className="text-link" to={`/assignments/${assignmentId}`}>Làm lại và nộp bản cải thiện <ArrowRight size={14} /></Link>}</div></div> : <>
          <div className="comparison-table-toolbar"><div><h3>Chọn bài bạn muốn so sánh</h3><span>{candidates.length} bài nộp được chia sẻ</span></div><label className="community-search"><Search size={16} /><input aria-label="Tìm sinh viên để so sánh" placeholder="Tìm tên sinh viên…" value={query} onChange={e => setQuery(e.target.value)} /></label></div>
          <div className="comparison-table-wrap"><table className="comparison-student-table"><thead><tr><th><input type="checkbox" aria-label="Chọn tất cả bài đang hiển thị" checked={allVisibleSelected} disabled={!base || !visibleCandidates.length || sending} onChange={chooseAll} /></th><th>Sinh viên</th><th>Phiên bản</th><th>Thời gian nộp</th></tr></thead><tbody>{visibleCandidates.map(source => { const version = source.versions.find(v => v.id === source.baseline_version_id)!; const selected = peers.includes(version.id); return <tr key={source.submission_id} className={selected ? 'is-selected' : ''}><td><input type="checkbox" aria-label={`Chọn bài của ${source.student}`} checked={selected} disabled={!base || sending} onChange={e => choosePeer(source, e.target.checked)} /></td><td><span className="comparison-student-name"><StudentAvatar name={source.student} seed={source.student_id} small /><strong>{source.student}</strong></span></td><td><span className="version-pill">Phiên bản {version.version_number}</span></td><td>{fmtDate(version.submitted_at)}</td></tr> })}</tbody></table></div>
          {!visibleCandidates.length && <div className="comparison-table-empty"><Search size={20} /><span>{query ? 'Không tìm thấy sinh viên phù hợp.' : 'Chưa có bài trước hạn của bạn khác được chia sẻ.'}</span></div>}
        </>}
        <footer className="comparison-submit-bar"><div>{mode === 'peers' ? <><button className="text-link" disabled={!base || !visibleCandidates.length || sending} onClick={chooseAll}>{allVisibleSelected ? 'Bỏ chọn tất cả' : 'Chọn tất cả'}</button><span>Đã chọn <strong>{peers.length}</strong> bài</span></> : <span><Files size={15} />So sánh đúng hai phiên bản đã nộp</span>}</div><button className="button button-primary" disabled={sending || pending || !base || !peers.length} onClick={compare}>{sending || pending ? <Loader2 size={16} className="comparison-spin" /> : <Sparkles size={16} />}{sending ? 'Đang gửi yêu cầu…' : pending ? 'AI đang so sánh…' : 'Bắt đầu so sánh'}{!sending && !pending && <ArrowRight size={15} />}</button></footer>
        <div className="comparison-footnote"><ShieldCheck size={14} /><span>Luôn dùng bản cuối trước hạn. Bản nháp và điểm số không được đưa vào so sánh.</span></div>
      </section>
      {!!history.length && <div className="comparison-history-bar"><History size={16} /><label>Lịch sử so sánh<select aria-label="Lịch sử so sánh" value={selectedJob} disabled={sending} onChange={e => { const job = history.find(j => j.id === Number(e.target.value)); if (job) openEntry(job); else setSelectedJob(0) }}><option value={0}>Chọn lần so sánh đã lưu</option>{history.map(j => <option key={j.id} value={j.id}>{fmtDate(j.created_at)} · {j.status === 'done' ? 'Đã có nhận xét' : j.status === 'failed' ? 'Chưa thành công' : 'Đang xử lý'}</option>)}</select></label></div>}
      {pending && <div className="comparison-status" role="status"><Loader2 size={22} className="comparison-spin" /><div><strong>{entry?.status === 'queued' ? 'Đã nhận yêu cầu của bạn' : 'AI đang đọc và đối chiếu các bài'}</strong><p>Đã chờ {Math.max(0, Math.floor((now - new Date(entry!.created_at).getTime()) / 1000))} giây. Kết quả sẽ được lưu để bạn xem lại bất cứ lúc nào.</p></div></div>}
      {entry?.status === 'failed' && <div className="form-error" role="alert">{entry.error || 'AI chưa hoàn thành. Bấm Bắt đầu so sánh để thử lại.'}</div>}
      {entry?.status === 'done' && entry.result ? <ComparisonResult key={entry.id} result={entry.result} assignmentId={Number(assignmentId)} /> : !pending && <div className="comparison-result-placeholder"><span><Sparkles size={24} /></span><div><h3>Một góc nhìn mới cho bài làm của bạn</h3><p>Chọn bài và bắt đầu so sánh. Nhận xét sẽ xuất hiện ở đây theo từng câu hỏi.</p></div></div>}
    </>}
    {error && <div className="form-error" role="alert">{error}</div>}
  </section>
}

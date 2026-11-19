import { useEffect, useState, type FormEvent } from 'react'
import { assignmentApi } from '../../services/api'
import type { Assignment } from '../../types'
import { fmtDate } from '../../utils/format'

export function localDateInput(value: string) {
  const date = new Date(value)
  return new Date(date.getTime() + 7 * 60 * 60 * 1000).toISOString().slice(0, 16)
}

export default function SharingSettings({ assignment, onRefresh, notify }: { assignment: Assignment; onRefresh: () => void; notify: (message: string) => void }) {
  const [dueAt, setDueAt] = useState('')
  const [opensAt, setOpensAt] = useState('')
  const [mode, setMode] = useState<'all' | 'opt_in'>('all')
  const [improvements, setImprovements] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  useEffect(() => {
    setDueAt(localDateInput(assignment.due_at))
    setOpensAt(localDateInput(assignment.sharing_open_at))
    setMode(assignment.share_mode)
    setImprovements(assignment.allow_improvements)
  }, [assignment.id, assignment.due_at, assignment.sharing_open_at, assignment.share_mode, assignment.allow_improvements])

  async function save(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      await assignmentApi.updateSettings(assignment.id, { ...(dueAt !== localDateInput(assignment.due_at) ? { due_at: `${dueAt}:00+07:00` } : {}), sharing_open_at: `${opensAt}:00+07:00`, share_mode: mode, allow_improvements: improvements })
      notify('Đã lưu lịch chia sẻ và cải thiện bài.')
      onRefresh()
    } catch (e) { setError((e as Error).message) } finally { setBusy(false) }
  }

  return (
    <section className="panel sharing-settings">
      <div className="panel-heading"><div><span className="page-eyebrow">HỌC TỪ BẠN CÙNG LỚP</span><h2>Lịch chia sẻ và cải thiện</h2></div></div>
      <p className="muted">{assignment.sharing_open ? 'Đã mở xem bài và đánh giá chéo.' : `Mở xem bài từ ${fmtDate(assignment.sharing_open_at)}.`} Thời gian theo giờ Việt Nam (UTC+7).</p>
      <form onSubmit={save} className="stack-form">
        <div className="schedule-fields">
          <label>Hạn nộp lần đầu<input type="datetime-local" value={dueAt} onChange={e => setDueAt(e.target.value)} required /></label>
          <label>Mở xem bài của bạn cùng lớp<input type="datetime-local" value={opensAt} onChange={e => setOpensAt(e.target.value)} required /></label>
        </div>
        <label>Bài xuất hiện trong lớp<select value={mode} onChange={e => setMode(e.target.value as 'all' | 'opt_in')}><option value="all">Tất cả bài đã nộp</option><option value="opt_in">Bài sinh viên chủ động chia sẻ</option></select></label>
        <label className="checkbox-field"><input type="checkbox" checked={improvements} onChange={e => setImprovements(e.target.checked)} />Cho sinh viên đã nộp gửi phiên bản cải thiện sau hạn, khi chia sẻ đã mở</label>
        <p className="muted">Bài nháp được giữ riêng. Mỗi bản nộp, nhận xét và điểm của phiên bản trước vẫn được lưu.</p>
        {error && <div className="form-error">{error}</div>}
        <div className="modal-actions"><button className="button button-primary" disabled={busy}>{busy ? 'Đang lưu…' : 'Lưu lịch bài tập'}</button></div>
      </form>
    </section>
  )
}

import { useEffect, useState } from 'react'
import { Send } from 'lucide-react'
import { assignmentApi } from '../../services/api'
import type { Assignment } from '../../types'
import Badge from '../ui/Badge'

interface ReferenceEditorProps {
  assignment: Assignment
  notify: (s: string) => void
  onRefresh: () => void
}

export default function ReferenceEditor({ assignment, notify, onRefresh }: ReferenceEditorProps) {
  const ref = assignment.reference
  const questions = assignment.questions || []
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [note, setNote] = useState(ref?.note || '')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    setAnswers(Object.fromEntries(questions.map(q => [String(q.id), ref?.answers?.find(a => a.question_id === q.id)?.answer_markdown || ''])))
    setNote(ref?.note || '')
  }, [assignment.id, assignment.reference?.published, questions.length])

  async function save(publish: boolean | null) {
    setBusy(true)
    setError('')
    const missing = questions.filter(q => !(answers[String(q.id)] || '').trim()).map(q => q.question_order)
    if (missing.length) { setError(`Bài tham khảo đang thiếu nội dung Câu hỏi ${missing.join(', ')}.`); setBusy(false); return }
    try {
      await assignmentApi.saveReference(assignment.id, questions.map(q => ({ question_id: q.id, answer_markdown: answers[String(q.id)] })), note)
      if (publish !== null) {
        await assignmentApi.publishReference(assignment.id, publish)
        notify(publish ? 'Đã công bố bài tham khảo.' : 'Đã tắt công bố bài tham khảo.')
      } else {
        notify('Đã lưu bản nháp bài tham khảo.')
      }
      onRefresh()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="panel reference-editor">
      <div className="panel-heading">
        <div><span className="page-eyebrow">BÀI THAM KHẢO</span><h2>Bài tham khảo của giảng viên</h2></div>
        <Badge status={ref?.published ? 'published' : 'draft'} label={ref?.published ? 'Đã công bố' : 'Chưa công bố'} />
      </div>
      <p className="muted">Nội dung sinh viên đọc sau khi nộp bài lần đầu. Không phải đáp án chấm nội bộ.</p>
      {!questions.length && <div className="form-error compact-error">Cần có câu hỏi bài tập trước khi soạn và công bố bài tham khảo.</div>}
      {questions.map(q => (
        <label className="reference-answer" key={q.id}>
          <span className="question-form-label">Câu hỏi {q.question_order}</span>
          <span className="question-read-text">{q.question_text}</span>
          <textarea value={answers[String(q.id)] || ''} onChange={e => setAnswers({ ...answers, [String(q.id)]: e.target.value })} rows={3} placeholder={`Câu trả lời tham khảo cho Câu hỏi ${q.question_order}…`} />
        </label>
      ))}
      <label>Ghi chú chung<span className="optional"> (không bắt buộc)</span><textarea value={note} onChange={e => setNote(e.target.value)} rows={2} placeholder="Lưu ý cho sinh viên khi đọc bài tham khảo…" /></label>
      {error && <div className="form-error">{error}</div>}
      <div className="modal-actions">
        <button className="button button-ghost" onClick={() => save(null)} disabled={busy || !questions.length}>Lưu bản nháp</button>
        {ref?.published
          ? <button className="button button-ghost" onClick={() => save(false)} disabled={busy}>Tắt công bố</button>
          : <button className="button button-primary" onClick={() => save(true)} disabled={busy || !questions.length}>{busy ? 'Đang xử lý…' : 'Công bố bài tham khảo'}<Send size={16} /></button>}
      </div>
    </section>
  )
}

import { useEffect, useState } from 'react'
import { Check, Plus, X } from 'lucide-react'
import { assignmentApi } from '../../services/api'
import type { Assignment } from '../../types'
import Badge from '../ui/Badge'

interface QuestionEditorProps {
  assignment: Assignment
  notify: (s: string) => void
  onRefresh: () => void
}

export default function QuestionEditor({ assignment, notify, onRefresh }: QuestionEditorProps) {
  const questions = assignment.questions || []
  const [texts, setTexts] = useState<Record<string, string>>({})
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [orders, setOrders] = useState<number[]>([])
  const [scores, setScores] = useState<Record<string, number>>({})

  useEffect(() => {
    const current = questions.length ? questions.map(q => q.question_order) : [1]
    setOrders(current)
    setTexts(Object.fromEntries(current.map(n => [String(n), questions.find(q => q.question_order === n)?.question_text || ''])))
    setScores(Object.fromEntries(current.map(n => [String(n), questions.find(q => q.question_order === n)?.max_score ?? 10])))
  }, [assignment.id])

  async function save() {
    setBusy(true)
    setError('')
    const missing = orders.filter(n => !(texts[String(n)] || '').trim())
    if (missing.length) { setError(`Chưa nhập đủ câu hỏi. Câu hỏi ${missing.join(', ')} đang trống.`); setBusy(false); return }
    try {
      await assignmentApi.updateQuestions(assignment.id, orders.map((n, i) => ({ question_order: i + 1, question_text: texts[String(n)], max_score: scores[String(n)] ?? 10 })))
      notify('Đã lưu câu hỏi.')
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
        <div><span className="page-eyebrow">CÂU HỎI BÀI TẬP</span><h2>Thiết kế câu hỏi phân tích</h2></div>
        <Badge status={assignment.status} label={assignment.status === 'published' ? 'Đã công bố' : 'Bản nháp'} />
      </div>
      <p className="muted">Bài tập có từ 1 đến 20 câu hỏi. Câu hỏi được giữ cố định sau khi công bố để các phiên bản nộp cùng một yêu cầu.</p>
      {orders.map((n, i) => (
        <label className="reference-answer" key={n}>
          <span className="question-form-label">Câu hỏi {i + 1}</span>
          <textarea value={texts[String(n)] || ''} onChange={e => setTexts({ ...texts, [String(n)]: e.target.value })} rows={2} placeholder={`Nội dung Câu hỏi ${n}…`} />
          <span className="score-input">Điểm tối đa <input type="number" min="0.5" max="100" step="0.5" value={scores[String(n)] ?? 10} onChange={e => setScores({ ...scores, [String(n)]: Number(e.target.value) })} /></span>
          {orders.length > 1 && <button type="button" className="button button-ghost" onClick={() => setOrders(prev => prev.filter(order => order !== n))}><X size={13} />Bỏ câu hỏi</button>}
        </label>
      ))}
      <button className="button button-ghost" disabled={orders.length >= 20} onClick={() => setOrders(prev => [...prev, Math.max(0, ...prev) + 1])}><Plus size={15} />Thêm câu hỏi</button>
      {error && <div className="form-error">{error}</div>}
      <div className="modal-actions">
        <button className="button button-primary" onClick={save} disabled={busy}>{busy ? 'Đang lưu…' : 'Lưu câu hỏi'}<Check size={16} /></button>
      </div>
    </section>
  )
}

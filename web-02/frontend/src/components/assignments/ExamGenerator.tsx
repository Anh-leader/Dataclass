import { useEffect, useState } from 'react'
import { Sparkles, Check, ChevronDown, Eye, Pencil, LockKeyhole } from 'lucide-react'
import MarkdownContent from '../ui/MarkdownContent'
import { api } from '../../api'
import { assignmentApi } from '../../services/api'
import type { Assignment, GeneratedExam } from '../../types'

interface Props {
  assignment: Assignment
  onApplied: (assignment: Assignment) => void
}

export default function ExamGenerator({ assignment, onApplied }: Props) {
  const [count, setCount] = useState(3)
  const [difficulty, setDifficulty] = useState('medium')
  const [instructions, setInstructions] = useState('')
  const [jobId, setJobId] = useState<number | null>(assignment.generation_job?.id ?? null)
  const [status, setStatus] = useState('')
  const [draft, setDraft] = useState<GeneratedExam | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)
  const [savedDraft, setSavedDraft] = useState<GeneratedExam | null>(null)
  const [expanded, setExpanded] = useState<number[]>([1])
  const [editing, setEditing] = useState<number[]>([])
  const [changed, setChanged] = useState<number[]>([])

  useEffect(() => { setExpanded([1]); setEditing([]); setChanged([]) }, [jobId])

  useEffect(() => {
    if (!jobId) return
    let stopped = false
    let timer: number | undefined
    async function check() {
      try {
        const job = await api<{ status: string; error?: string; result: GeneratedExam; settings?: { count: number; difficulty: string; instructions: string } }>(`/jobs/${jobId}`)
        if (stopped) return
        if (job.settings) { setCount(job.settings.count); setDifficulty(job.settings.difficulty); setInstructions(job.settings.instructions) }
        setStatus(job.status)
        if (job.status === 'done') {
          if (!job.result.applied_at) setDraft(job.result)
          else { setSaved(true); setSavedDraft(job.result) }
        } else if (job.status === 'failed') {
          setError(job.error || 'AI chưa tạo được đề. Bạn có thể thử lại.')
        } else timer = window.setTimeout(check, 2500)
      } catch (e) { if (!stopped) setError((e as Error).message) }
    }
    check()
    return () => { stopped = true; window.clearTimeout(timer) }
  }, [jobId])

  async function generate() {
    setBusy(true); setError('')
    try {
      const job = await assignmentApi.generateExam(assignment.id, { count, difficulty, instructions })
      setDraft(null); setSaved(false); setStatus(job.status); setJobId(job.job_id)
    } catch (e) { setError((e as Error).message) } finally { setBusy(false) }
  }

  async function apply() {
    if (!draft) return
    setBusy(true); setError('')
    try {
      const updated = await assignmentApi.applyExam(assignment.id, { job_id: jobId, questions: draft.questions, note: draft.note })
      setSaved(true); setSavedDraft(draft); setDraft(null); onApplied(updated)
    } catch (e) { setError((e as Error).message) } finally { setBusy(false) }
  }

  const running = status === 'queued' || status === 'running'
  const updateQuestion = (index: number, field: string, value: string | number) => {
    setDraft(prev => prev && ({ ...prev, questions: prev.questions.map((q, i) => i === index ? { ...q, [field]: value } : q) }))
    setChanged(prev => prev.includes(index + 1) ? prev : [...prev, index + 1])
  }
  const toggleExpanded = (order: number) => setExpanded(prev => prev.includes(order) ? prev.filter(n => n !== order) : [...prev, order])
  const toggleEditing = (order: number) => setEditing(prev => prev.includes(order) ? prev.filter(n => n !== order) : [...prev, order])
  const allExpanded = draft && expanded.length === draft.questions.length

  return <section className="panel reference-editor exam-generator stack-form">
    <div className="panel-heading"><div><span className="page-eyebrow">SOẠN ĐỀ VỚI AI</span><h2>Câu hỏi và đáp án từ dataset</h2></div><Sparkles size={21} /></div>
    <p className="muted">AI phân tích dataset để đề xuất đề kiểm tra. Giáo viên kiểm tra số liệu, chỉnh sửa và lưu đề trước khi công bố. Đáp án được giữ riêng tư.</p>
    <div className="exam-generation-settings"><div className="schedule-fields">
      <label>Số câu hỏi<input type="number" min="1" max="20" value={count} disabled={busy || running} onChange={e => setCount(Number(e.target.value))} /></label>
      <label>Độ khó<select aria-label="Độ khó" value={difficulty} disabled={busy || running} onChange={e => setDifficulty(e.target.value)}><option value="easy">Cơ bản</option><option value="medium">Trung bình</option><option value="hard">Nâng cao</option></select></label>
    </div>
    <label>Yêu cầu cho AI <span className="optional">(không bắt buộc)</span><textarea aria-label="Yêu cầu cho AI (không bắt buộc)" maxLength={4000} value={instructions} disabled={busy || running} rows={2} onChange={e => setInstructions(e.target.value)} placeholder="Ví dụ: so sánh doanh thu theo vùng, có một câu yêu cầu biểu đồ…" /></label></div>
    {!assignment.datasets.length && <p className="muted">Tải dataset để bắt đầu tạo đề.</p>}
    <button type="button" className="button button-ghost" onClick={generate} disabled={busy || running || !assignment.datasets.length || !(count >= 1 && count <= 20 && Number.isInteger(count))}><Sparkles size={16} />{running ? 'AI đang phân tích dataset và soạn đề…' : 'Tạo câu hỏi và đáp án bằng AI'}</button>
    {running && <p role="status" className="muted">Quá trình có thể mất vài phút. Bạn có thể quay lại bài nháp để xem kết quả.</p>}
    {error && <div className="form-error" role="alert">{error}</div>}
    {saved && <p role="status">Đã lưu đề và đáp án riêng tư. Bạn có thể công bố bài tập khi đã kiểm tra xong.</p>}
    {saved && savedDraft && <button type="button" className="button button-ghost" onClick={() => { setDraft(savedDraft); setSaved(false) }}>Chỉnh sửa đề và đáp án đã lưu</button>}
    {draft && <>
      <div className="exam-review-heading">
        <div><span className="page-eyebrow">KIỂM TRA TRƯỚC KHI GIAO BÀI</span><h3>Duyệt đề AI</h3><p>{draft.questions.length} câu hỏi <span>·</span> {draft.questions.reduce((sum, q) => sum + q.max_score, 0)} điểm tối đa</p></div>
        <button type="button" className="button button-ghost" onClick={() => setExpanded(allExpanded ? [] : draft.questions.map(q => q.question_order))}>{allExpanded ? 'Thu gọn tất cả' : 'Mở tất cả câu hỏi'}</button>
      </div>
      <nav className="exam-question-nav" aria-label="Đi tới câu hỏi">
        {draft.questions.map(q => <button type="button" key={q.question_order} aria-label={`Đi tới câu ${q.question_order}`} onClick={() => {
          setExpanded(prev => prev.includes(q.question_order) ? prev : [...prev, q.question_order])
          window.requestAnimationFrame(() => document.getElementById(`exam-${assignment.id}-question-${q.question_order}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' }))
        }}>Câu {q.question_order}{changed.includes(q.question_order) && <span aria-label="Đã chỉnh sửa">·</span>}</button>)}
      </nav>
      {draft.questions.map((q, i) => {
        const open = expanded.includes(q.question_order)
        const edit = editing.includes(q.question_order)
        const sectionId = `exam-${assignment.id}-question-${q.question_order}`
        return <article className={`exam-question-card ${open ? 'is-open' : ''}`} id={sectionId} key={q.question_order}>
          <button type="button" className="exam-question-toggle" aria-expanded={open} aria-controls={`${sectionId}-body`} aria-label={`${open ? 'Thu gọn' : 'Mở'} câu hỏi ${i + 1}`} onClick={() => toggleExpanded(q.question_order)}>
            <span className="exam-question-number">{String(i + 1).padStart(2, '0')}</span>
            <span className="exam-question-title"><strong>Câu hỏi {i + 1}</strong><span>{q.question_text.replace(/\s+/g, ' ').slice(0, 150)}</span></span>
            <span className="exam-points">{q.max_score} điểm</span><ChevronDown size={18} />
          </button>
          {open && <div className="exam-question-body" id={`${sectionId}-body`}>
            <div className="exam-question-tools"><span className="exam-private-badge"><LockKeyhole size={13} />Đáp án riêng tư</span>{changed.includes(q.question_order) && <span className="exam-changed-badge">Đã chỉnh sửa</span>}<button type="button" className="button button-ghost" onClick={() => toggleEditing(q.question_order)} aria-label={`${edit ? 'Xem trình bày' : 'Chỉnh sửa'} câu ${i + 1}`}>{edit ? <Eye size={14} /> : <Pencil size={14} />}{edit ? 'Xem trình bày' : 'Chỉnh sửa'}</button></div>
            {edit ? <div className="exam-question-edit-grid stack-form">
              <div className="stack-form">
                <label>Câu hỏi {i + 1}<textarea aria-label={`Câu hỏi ${i + 1}`} rows={5} maxLength={8000} value={q.question_text} onChange={e => updateQuestion(i, 'question_text', e.target.value)} /></label>
                <label className="exam-question-score">Điểm tối đa câu {i + 1}<input type="number" min="0.5" max="100" step="0.5" value={q.max_score} onChange={e => updateQuestion(i, 'max_score', Number(e.target.value))} /></label>
                <div className="exam-format-help"><strong>Trình bày với Markdown & LaTeX</strong><p>Dùng tiêu đề, danh sách và bảng Markdown. Công thức trong dòng: <code>{'$x = 1$'}</code>. Công thức riêng dòng: <code>{'$$\\bar{x} = \\frac{1}{n}\\sum_{i=1}^{n}x_i$$'}</code>.</p></div>
              </div>
              <label>Đáp án mẫu câu {i + 1} (riêng tư)<textarea aria-label={`Đáp án mẫu câu ${i + 1} (riêng tư)`} rows={14} maxLength={20000} value={q.answer_markdown} onChange={e => updateQuestion(i, 'answer_markdown', e.target.value)} /></label>
            </div> : <>
              <div className="exam-question-content"><span className="exam-content-label">YÊU CẦU PHÂN TÍCH</span><div className="prose math-content"><MarkdownContent>{q.question_text}</MarkdownContent></div></div>
              <div className="exam-answer-content"><span className="exam-content-label">ĐÁP ÁN THAM CHIẾU</span><div className="prose math-content"><MarkdownContent>{q.answer_markdown}</MarkdownContent></div></div>
            </>}
          </div>}
        </article>
      })}
      <details className="exam-extra-details"><summary>Ghi chú chung cho đáp án</summary><label>Ghi chú đáp án<textarea aria-label="Ghi chú đáp án" rows={3} maxLength={8000} value={draft.note} onChange={e => setDraft({ ...draft, note: e.target.value })} /></label></details>
      <details className="exam-extra-details"><summary>Xem kết quả phân tích để đối chiếu</summary><div className="prose math-content"><MarkdownContent>{draft.evidence}</MarkdownContent></div></details>
      <div className="exam-save-bar"><div><strong>Sẵn sàng giao bài?</strong><p>Lưu đề đã duyệt trước khi công bố. Đáp án vẫn được giữ riêng tư.</p></div><button type="button" className="button button-primary" disabled={busy} onClick={apply}><Check size={16} />{busy ? 'Đang lưu…' : 'Lưu đề và đáp án đã duyệt'}</button></div>
    </>}
  </section>
}

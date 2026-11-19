import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, FileSpreadsheet, Plus, Upload, X } from 'lucide-react'
import { assignmentApi } from '../services/api'
import type { Assignment } from '../types'
import PageContainer from '../components/layout/PageContainer'
import PageHeader from '../components/layout/PageHeader'
import ExamGenerator from '../components/assignments/ExamGenerator'

interface QuestionDraft {
  title: string
  prompt: string
  maxScore: number
}

interface AssignmentCreatePageProps {
  classId: number
  onDone: () => void
  onCancel: () => void
}

const DEFAULT_QUESTIONS: QuestionDraft[] = [
  { title: 'Khám phá dữ liệu', prompt: '', maxScore: 10 },
  { title: 'Phân tích trọng tâm', prompt: '', maxScore: 10 },
  { title: 'Kết luận và đề xuất', prompt: '', maxScore: 10 },
]

export default function AssignmentCreatePage({ classId, onDone, onCancel }: AssignmentCreatePageProps) {
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [step, setStep] = useState(1)
  const [assignment, setAssignment] = useState<Assignment | null>(null)
  const [files, setFiles] = useState<FileList | null>(null)
  const [questions, setQuestions] = useState<QuestionDraft[]>(DEFAULT_QUESTIONS)
  const [useRubric, setUseRubric] = useState(false)
  const [shareMode, setShareMode] = useState<'all' | 'opt_in'>('all')
  const [allowImprovements, setAllowImprovements] = useState(true)
  const [useAI, setUseAI] = useState(false)

  const setQuestion = (index: number, patch: Partial<QuestionDraft>) =>
    setQuestions(prev => prev.map((q, i) => (i === index ? { ...q, ...patch } : q)))

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setError('')
    const form = new FormData(event.currentTarget)
    const trimmed = questions.map(q => ({ ...q, prompt: q.prompt.trim() }))
    const missing = trimmed.map((q, i) => (!q.prompt ? i + 1 : 0)).filter(Boolean)
    if (!useAI && missing.length) { setError(`Chưa nhập đủ nội dung câu hỏi. Câu hỏi ${missing.join(', ')} đang trống.`); setBusy(false); return }
    const invalidScores = trimmed.filter(q => !(q.maxScore > 0 && q.maxScore <= 100))
    if (invalidScores.length) { setError('Điểm tối đa của mỗi câu phải lớn hơn 0 và không quá 100.'); setBusy(false); return }
    const payload = {
      title: form.get('title'),
      description: form.get('description'),
      due_at: `${form.get('due_at')}:00+07:00`,
      sharing_open_at: `${form.get('sharing_open_at') || form.get('due_at')}:00+07:00`,
      share_mode: shareMode,
      allow_improvements: allowImprovements,
      answer_key: form.get('answer_key') || '',
      ai_generate: useAI,
      questions: useAI ? [] : trimmed.map((q, i) => ({ question_order: i + 1, question_text: q.title.trim() ? `${q.title.trim()}\n\n${q.prompt}` : q.prompt, max_score: q.maxScore })),
      rubric: useRubric ? [
        { id: 'interpret', title: String(form.get('c1_title') || 'Diễn giải dữ liệu'), description: String(form.get('c1_desc') || ''), hint: String(form.get('c1_hint') || ''), max_points: 3 },
        { id: 'method', title: String(form.get('c2_title') || 'Phương pháp phân tích'), description: String(form.get('c2_desc') || ''), hint: String(form.get('c2_hint') || ''), max_points: 3 },
        { id: 'visual', title: String(form.get('c3_title') || 'Biểu đồ và trình bày'), description: String(form.get('c3_desc') || ''), hint: String(form.get('c3_hint') || ''), max_points: 4 },
      ] : [],
    }
    try {
      const result = await assignmentApi.create(classId, payload)
      setAssignment(result)
      setStep(2)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  async function uploadAndPublish() {
    setBusy(true)
    setError('')
    try {
      if (!assignment!.datasets.length) {
        if (!files?.length) throw new Error('Chọn ít nhất một file CSV hoặc XLSX.')
        await assignmentApi.uploadDatasets(assignment!.id, Array.from(files))
      }
      const updated = await assignmentApi.get(assignment!.id)
      setAssignment(updated)
      if (useAI) setStep(3)
      else { await assignmentApi.publish(assignment!.id); onDone() }
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <PageContainer>
      <button className="back-link" onClick={onCancel}><ArrowLeft size={15} />Quay lại lớp học</button>
      <PageHeader eyebrow="BÀI TẬP MỚI" title="Tạo bài tập mới" subtitle="Cả lớp phân tích cùng dataset, rồi học từ những góc nhìn khác nhau." />

      {step === 1 ? (
        <form onSubmit={create} className="stack-form panel create-form">
          <div className="form-section-title">Thông tin chung</div>
          <label>Tên bài tập<input name="title" placeholder="Ví dụ: Khám phá hành vi khách hàng" required /></label>
          <label>Mô tả chung<span className="optional"> (hướng dẫn cho toàn bài)</span><textarea name="description" rows={3} placeholder="Mục tiêu, yêu cầu biểu đồ…" required /></label>
          <div className="schedule-fields">
            <label>Hạn nộp lần đầu<input name="due_at" type="datetime-local" required /></label>
            <label>Mở xem bài của bạn cùng lớp<input name="sharing_open_at" type="datetime-local" /><small>Bỏ trống để mở ngay khi hết hạn nộp. Giờ Việt Nam (UTC+7).</small></label>
          </div>
          <label>Bài được chia sẻ<select value={shareMode} onChange={e => setShareMode(e.target.value as 'all' | 'opt_in')}><option value="all">Tất cả bài đã nộp</option><option value="opt_in">Sinh viên chủ động bật chia sẻ</option></select></label>
          <label className="checkbox-field"><input type="checkbox" checked={allowImprovements} onChange={e => setAllowImprovements(e.target.checked)} />Cho sinh viên đã nộp gửi bản cải thiện sau khi mở chia sẻ</label>

          <label className="checkbox-field"><input type="checkbox" checked={useAI} onChange={e => setUseAI(e.target.checked)} />Cho AI tạo câu hỏi và đáp án từ dataset</label>
          {useAI && <p className="muted">Sau khi tải dataset, chọn số câu và độ khó. Giáo viên duyệt câu hỏi và đáp án trước khi giao bài.</p>}
          {!useAI && <><div className="form-section-title">Câu hỏi phân tích <span className="optional">1–20 CÂU</span></div>
          <div className="questions-form">
            {questions.map((q, i) => (
              <div className="question-form-card" key={i}>
                <span className="question-form-num">0{i + 1}</span>
                <span className="question-form-label">Câu hỏi {i + 1}</span>
                {questions.length > 1 && <button type="button" className="icon-button question-remove" aria-label={`Xóa câu hỏi ${i + 1}`} onClick={() => setQuestions(prev => prev.filter((_, n) => n !== i))}><X size={16} /></button>}
                <input
                  value={q.title}
                  onChange={e => setQuestion(i, { title: e.target.value })}
                  placeholder={`Tiêu đề Câu hỏi ${i + 1}…`}
                />
                <textarea
                  value={q.prompt}
                  onChange={e => setQuestion(i, { prompt: e.target.value })}
                  rows={3}
                  placeholder={`Nội dung Câu hỏi ${i + 1}…`}
                />
                <label className="score-field">Điểm tối đa
                  <input type="number" min="0" max="100" step="0.5" value={q.maxScore}
                    onChange={e => setQuestion(i, { maxScore: Number(e.target.value) })} />
                </label>
              </div>
            ))}
          </div>
          <button type="button" className="button button-ghost" disabled={questions.length >= 20} onClick={() => setQuestions(prev => [...prev, { title: '', prompt: '', maxScore: 10 }])}><Plus size={16} />Thêm câu hỏi</button></>}

          <label className="checkbox-field"><input type="checkbox" checked={useRubric} onChange={e => setUseRubric(e.target.checked)} />Thiết lập tiêu chí đánh giá riêng (không bắt buộc)</label>
          {useRubric && <><div className="form-section-title">Tiêu chí đánh giá — tổng 10 điểm</div><div className="rubric-form-grid">
            {[['c1', '3', 'Diễn giải dữ liệu'], ['c2', '3', 'Phương pháp phân tích'], ['c3', '4', 'Biểu đồ và trình bày']].map(([key, points, title], i) => (
              <div className="rubric-form-card" key={key}>
                <span>0{i + 1} · {points} ĐIỂM</span>
                <input name={`${key}_title`} defaultValue={title} required />
                <textarea name={`${key}_desc`} rows={2} placeholder="Mô tả tiêu chí…" />
                <textarea name={`${key}_hint`} rows={2} placeholder="Gợi ý hiển thị cho sinh viên…" />
              </div>
            ))}
          </div></>}
          {!useRubric && <p className="muted">AI sẽ góp ý về tính chính xác, bằng chứng, phương pháp và insight. Giáo viên chấm theo điểm tối đa từng câu hỏi.</p>}

          {!useAI && <label>Đáp án mẫu <span className="optional">(chỉ AI và giáo viên sử dụng)</span><textarea name="answer_key" rows={3} placeholder="Kết quả kỳ vọng hoặc các kết luận chính…" /></label>}
          {error && <div className="form-error">{error}</div>}
          <div className="modal-actions">
            <button type="button" className="button button-ghost" onClick={onCancel}>Hủy</button>
            <button className="button button-primary" disabled={busy}>{busy ? 'Đang lưu…' : 'Tiếp tục'}<ArrowRight size={16} /></button>
          </div>
        </form>
      ) : step === 2 ? (
        <div className="stack-form panel create-form">
          <div className="form-section-title">Thêm dataset</div>
          <label className="upload-zone">
            <input type="file" accept=".csv,.xlsx" multiple onChange={event => setFiles(event.target.files)} />
            <span className="upload-icon"><Upload size={20} /></span>
            <strong>{files?.length ? `${files.length} tệp đã chọn` : 'Chọn hoặc thả file tại đây'}</strong>
            <small>CSV, XLSX · Tối đa 10 MB mỗi file</small>
            <span className="button button-ghost">Chọn file</span>
          </label>
          {files && Array.from(files).map(file => (
            <div className="selected-file" key={file.name}><FileSpreadsheet size={16} />{file.name}<span>{(file.size / 1024 / 1024).toFixed(1)} MB</span></div>
          ))}
          {error && <div className="form-error">{error}</div>}
          <div className="modal-actions">
            <button className="button button-ghost" onClick={onCancel}>Lưu nháp và về lớp</button>
            <button className="button button-primary" onClick={uploadAndPublish} disabled={busy}>{busy ? 'Đang tải…' : useAI ? 'Tải dataset và soạn đề AI' : 'Công bố bài tập'}<ArrowRight size={16} /></button>
          </div>
        </div>
      ) : assignment && <>
        <ExamGenerator assignment={assignment} onApplied={setAssignment} />
        {error && <div className="form-error">{error}</div>}
        <div className="modal-actions">
          <button className="button button-ghost" onClick={onCancel}>Lưu nháp và về lớp</button>
          <button className="button button-primary" disabled={busy || !assignment.questions.length} onClick={async () => {
            setBusy(true); setError('')
            try { await assignmentApi.publish(assignment.id); onDone() } catch (e) { setError((e as Error).message) } finally { setBusy(false) }
          }}>Công bố bài tập<ArrowRight size={16} /></button>
        </div>
      </>}
    </PageContainer>
  )
}

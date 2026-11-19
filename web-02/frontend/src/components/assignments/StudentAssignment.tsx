import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import MarkdownContent from '../ui/MarkdownContent'
import {
  ArrowDownToLine, ArrowLeft, ArrowRight, BarChart3, Check, CheckCircle2, ChevronDown,
  Clock3, FileSpreadsheet, Plus, Send, Share2, Sparkles, X,
} from 'lucide-react'
import { assignmentApi, submissionApi, pollJob } from '../../services/api'
import type { Assignment, ChatMessage, Reference, ReferenceState, ReviewView } from '../../types'
import { fmtDate, remaining } from '../../utils/format'
import PageContainer from '../layout/PageContainer'
import ReviewCard from './ReviewCard'
import ReferenceView from './ReferenceView'
import DataPreview from './DataPreview'
import SubmissionHistory from './SubmissionHistory'
import QuestionHints from './QuestionHints'

interface StudentAssignmentProps {
  assignment: Assignment
  notify: (s: string) => void
  onRefresh: () => void
}

export default function StudentAssignment({ assignment, notify, onRefresh }: StudentAssignmentProps) {
  const [chat, setChat] = useState<ChatMessage[]>([])
  const [question, setQuestion] = useState('')
  const [busy, setBusy] = useState('')
  const [review, setReview] = useState<ReviewView | null>(null)
  const [reflection, setReflection] = useState('')
  const [jobError, setJobError] = useState('')
  const [preview, setPreview] = useState<{ title: string; data: { columns: string[]; rows: Record<string, unknown>[] } } | null>(null)
  const [shared, setShared] = useState(Boolean(assignment.submission?.shared))
  const [showBrief, setShowBrief] = useState(false)
  const [activeQuestionId, setActiveQuestionId] = useState<number | null>(null)
  const [reference, setReference] = useState<Reference | null>(null)
  const [referenceState, setReferenceState] = useState<ReferenceState>('loading')

  const questions = assignment.questions || []
  const submission = assignment.submission
  const due = new Date(assignment.due_at).getTime() > Date.now()
  const canEdit = assignment.can_edit
  const isImprovement = !due && canEdit
  const latest = submission?.versions?.[0]

  const [answers, setAnswers] = useState<Record<string, { text: string; artifacts: { id: string; name: string; media_type: string; url: string }[] }>>({})

  useEffect(() => {
    setAnswers(Object.fromEntries(questions.map(q => [
      String(q.id),
      {
        text: submission?.answers?.find(a => a.question_id === q.id)?.answer_markdown || '',
        artifacts: submission?.answers?.find(a => a.question_id === q.id)?.artifacts || [],
      },
    ])))
    setShared(Boolean(assignment.submission?.shared))
    setChat([])
    setReview(null)
  }, [assignment.id])
  useEffect(() => { setShared(Boolean(assignment.submission?.shared)) }, [assignment.submission?.shared])

  useEffect(() => { if (questions[0]) setActiveQuestionId(prev => questions.some(q => q.id === prev) ? prev : questions[0].id) }, [assignment.id, questions.length])

  useEffect(() => {
    assignmentApi.aiHistory(assignment.id)
      .then(history => setChat(history.flatMap(item => [
        { role: 'student' as const, text: item.question, questionOrder: item.question_order ?? undefined },
        { role: 'ai' as const, text: item.answer },
      ])))
      .catch(() => {})
  }, [assignment.id])

  useEffect(() => {
    setReferenceState('loading')
    assignmentApi.getReference(assignment.id)
      .then(result => { setReference(result.reference as Reference); setReferenceState('ok') })
      .catch(e => {
        const status = (e as Error).message || ''
        if (status.includes('nộp bài lần đầu')) setReferenceState('not_submitted')
        else if (status.includes('chưa công bố')) setReferenceState('not_published')
        else setReferenceState('hidden')
      })
  }, [assignment.id, latest?.id])

  const setAnswerText = (qid: number, text: string) => setAnswers(prev => ({ ...prev, [String(qid)]: { ...(prev[String(qid)] || { text: '', artifacts: [] }), text } }))
  const attachArtifact = (qid: number, art: { id: string; name: string; media_type: string; url: string }) => setAnswers(prev => {
    const cur = prev[String(qid)] || { text: '', artifacts: [] }
    if (cur.artifacts.some(a => a.id === art.id)) return prev
    return { ...prev, [String(qid)]: { ...cur, artifacts: [...cur.artifacts, art] } }
  })
  const detachArtifact = (qid: number, artId: string) => setAnswers(prev => {
    const cur = prev[String(qid)] || { text: '', artifacts: [] }
    return { ...prev, [String(qid)]: { ...cur, artifacts: cur.artifacts.filter(a => a.id !== artId) } }
  })

  async function wait(jobId: number, kind: string) {
    setBusy(kind)
    setJobError('')
    try {
      return await pollJob<ReviewView & { answer?: string }>(jobId)
    } catch (e) {
      setJobError((e as Error).message)
      return null
    } finally {
      setBusy('')
    }
  }

  async function saveDraft(silent = false) {
    try {
      await assignmentApi.saveAnswers(assignment.id, questions.map(q => ({
        question_id: q.id,
        answer_markdown: answers[String(q.id)]?.text || '',
        artifact_ids: (answers[String(q.id)]?.artifacts || []).map(a => a.id),
      })))
      if (!silent) notify('Bản nháp đã được lưu.')
      return true
    } catch (e) {
      setJobError((e as Error).message)
      return false
    }
  }

  async function ask(event: FormEvent) {
    event.preventDefault()
    const text = question.trim()
    if (!text) return
    const target = activeQuestionId
    setChat(items => [...items, { role: 'student', text, questionOrder: questions.find(q => q.id === target)?.question_order }])
    setQuestion('')
    try {
      const result = await assignmentApi.aiChat(assignment.id, text, target)
      const answer = await wait(result.job_id, 'chat')
      if (answer?.answer) setChat(items => [...items, { role: 'ai', text: answer.answer! }])
    } catch (e) {
      setJobError((e as Error).message)
    }
  }

  async function reviewDraft() {
    if (!await saveDraft(true)) return
    try {
      const result = await assignmentApi.reviewDraft(assignment.id)
      const response = await wait(result.job_id, 'review')
      if (response) setReview({ checks: response.checks || [], overall: response.overall })
    } catch (e) {
      setJobError((e as Error).message)
    }
  }

  async function submitWork() {
    setBusy('saving')
    if (!await saveDraft(true)) { setBusy(''); return }
    if (!window.confirm('Lưu một phiên bản bài nộp cố định và gửi cho giáo viên, AI đánh giá?')) { setBusy(''); return }
    try {
      const result = await assignmentApi.submit(assignment.id, reflection)
      setReflection('')
      setReview(null)
      notify(`Đã nộp phiên bản ${result.version_number}. Đang kiểm tra với AI…`)
      onRefresh()
      void wait(result.job_id, 'submit').then(() => onRefresh())
    } catch (e) {
      setJobError((e as Error).message)
      setBusy('')
    }
  }

  async function toggleShare() {
    if (!submission) return
    try {
      const result = await submissionApi.share(submission.id, !shared)
      setShared(result.shared)
      notify(result.shared ? 'Bài đã được chia sẻ trong lớp.' : 'Đã thu hồi chia sẻ.')
    } catch (e) {
      setJobError((e as Error).message)
    }
  }

  async function previewFile(file: { id: string; name: string }) {
    try {
      setPreview({ title: file.name, data: await assignmentApi.previewDataset(assignment.id, file.id) })
    } catch (e) {
      setJobError((e as Error).message)
    }
  }

  const answeredAll = questions.every(q => (answers[String(q.id)]?.text || '').trim())
  const answeredCount = questions.filter(q => (answers[String(q.id)]?.text || '').trim()).length
  const activeQuestion = questions.find(q => q.id === activeQuestionId)

  return (
    <PageContainer>
      <div className="workspace-top">
        <div>
          <Link to={`/classes/${assignment.classroom_id}`} className="back-link"><ArrowLeft size={15} />{assignment.classroom_name}</Link>
          <div className="page-eyebrow">BÀI TẬP PHÂN TÍCH</div>
          <h1 className="workspace-title">{assignment.title}</h1>
          <div className="workspace-meta">
            <span><Clock3 size={14} />{remaining(assignment.due_at)} · {fmtDate(assignment.due_at)}</span>
            <span><FileSpreadsheet size={14} />{assignment.datasets.length} dataset</span>
          </div>
        </div>
        <div className="workspace-actions">
          <button className="button button-ghost" onClick={() => saveDraft()} disabled={!canEdit || Boolean(busy)}><Check size={16} />Lưu nháp</button>
          <button className="button button-primary" onClick={submitWork} disabled={!canEdit || !answeredAll || Boolean(busy)}><Send size={16} />{isImprovement ? 'Nộp bản cải thiện' : 'Nộp bài'}</button>
        </div>
      </div>
      <div className="learning-timeline">
        <span><strong>1. Làm bài riêng</strong>Hạn nộp lần đầu: {fmtDate(assignment.due_at)}</span>
        <span><strong>2. Học từ bạn cùng lớp</strong>Mở chia sẻ: {fmtDate(assignment.sharing_open_at)}</span>
        <span><strong>3. Cải thiện bài</strong>{assignment.allow_improvements ? 'Sinh viên đã nộp có thể gửi bản cải thiện sau khi mở chia sẻ.' : 'Giáo viên chưa mở nộp bản cải thiện sau hạn.'}</span>
      </div>
      {isImprovement && <div className="learning-notice">Bạn đang cải thiện bài sau hạn. Các phiên bản trước vẫn được lưu cùng phản hồi và điểm của từng bản.</div>}

      {submission?.grade_published && submission.grade && (
        <div className="published-grade">
          <div className="grade-big">{submission.grade.total}<small>/{submission.grade.max_score}</small></div>
          <div><strong>Điểm đã công bố</strong><span>{submission.teacher_comment || 'Giáo viên đã hoàn tất chấm bài.'}</span></div>
          <CheckCircle2 size={22} />
        </div>
      )}

      <div className="workspace-grid">
        <nav className="question-nav">
          <div className="question-nav-title">NỘI DUNG BÀI LÀM</div>
          {questions.map(q => {
            const answered = Boolean((answers[String(q.id)]?.text || '').trim())
            return (
              <button key={q.id} className={`question-nav-item ${activeQuestionId === q.id ? 'active' : ''}`} onClick={() => setActiveQuestionId(q.id)}>
                <span className="question-nav-num">0{q.question_order}</span>
                <span className="question-nav-copy">
                  <strong>{answered ? 'Đã trả lời' : q.question_order === 1 ? 'Chưa làm' : 'Chưa làm'}</strong>
                  <small>Câu hỏi {q.question_order}</small>
                </span>
                <span className={`nav-status ${answered ? 'done' : ''}`}>{answered ? <Check size={12} /> : ''}</span>
              </button>
            )
          })}
          <div className="question-nav-section">DỮ LIỆU</div>
          {assignment.datasets.map(file => (
            <button className="dataset-chip" key={file.id} onClick={() => previewFile(file)}>
              <FileSpreadsheet size={15} />{file.name}<ArrowDownToLine size={13} />
            </button>
          ))}
        </nav>

        <div className="workspace-main">
          <section className="panel brief-panel">
            <div className="panel-heading">
              <div><div className="page-eyebrow">ĐỀ BÀI</div><h2>Điều cần khám phá</h2></div>
              <button className="icon-button" aria-label="Thu gọn đề bài" onClick={() => setShowBrief(!showBrief)}><ChevronDown size={18} className={showBrief ? 'rotate' : ''} /></button>
            </div>
            {showBrief
              ? <div className="prose"><MarkdownContent>{assignment.description}</MarkdownContent></div>
              : <p className="brief-excerpt">{assignment.description.slice(0, 210)}{assignment.description.length > 210 ? '…' : ''} <button className="inline-link" onClick={() => setShowBrief(true)}>Xem đề bài</button></p>}
          </section>

          {activeQuestion ? (
            <section className="panel active-question-panel">
              <div className="panel-heading">
                <div>
                  <div className="page-eyebrow">CÂU HỎI {activeQuestion.question_order}</div>
                  <h2>Câu {activeQuestion.question_order} · {activeQuestion.max_score} điểm</h2>
                </div>
                <span className="answered-count">{answeredCount}/{questions.length} đã trả lời</span>
              </div>
              <div className="prose question-read-text active-question-text"><MarkdownContent>{activeQuestion.question_text}</MarkdownContent></div>
              <QuestionHints key={activeQuestion.id} assignmentId={assignment.id} questionId={activeQuestion.id} />
              <div className="question-form-label">Bài phân tích của bạn</div>
              <textarea
                className="answer-editor"
                value={answers[String(activeQuestion.id)]?.text || ''}
                onChange={e => setAnswerText(activeQuestion.id, e.target.value)}
                placeholder={`Viết câu trả lời cho Câu hỏi ${activeQuestion.question_order}…`}
                disabled={!canEdit}
              />
              <div className="answer-artifacts">
                {(answers[String(activeQuestion.id)]?.artifacts || []).map(art => (
                  <span className="artifact-chip" key={art.id}>
                    <img src={art.url} alt={art.name} />{art.name}
                    <button onClick={() => detachArtifact(activeQuestion.id, art.id)} disabled={!canEdit} aria-label="Bỏ biểu đồ"><X size={12} /></button>
                  </span>
                ))}
              </div>
              <button className="button button-ghost button-review" onClick={reviewDraft} disabled={!canEdit || !answeredCount || Boolean(busy)}>
                <Sparkles size={16} />{busy ? 'AI đang xem bài…' : 'Xin AI góp ý bản nháp'}
              </button>
              {review && <ReviewCard checks={review.checks} overall={review.overall} />}
              {isImprovement && <label className="reflection-field">Bạn đã học và cải thiện điều gì?<textarea value={reflection} onChange={e => setReflection(e.target.value)} rows={3} maxLength={4000} placeholder="Ví dụ: Sau khi xem bài của bạn, tôi bổ sung so sánh theo vùng và giải thích giới hạn dữ liệu…" /><small>Ghi chú này được lưu cùng phiên bản cải thiện.</small></label>}
              {latest && (
                <div className="last-submission">
                  <CheckCircle2 size={17} />
                  <span><strong>Đã nộp phiên bản {latest.version_number}</strong><small>{fmtDate(latest.submitted_at)}</small></span>
                </div>
              )}
              {jobError && <div className="form-error compact-error">{jobError}</div>}
            </section>
          ) : (
            <section className="panel"><div className="form-error">Bài tập đang thiếu câu hỏi. Vui lòng báo giáo viên bổ sung.</div></section>
          )}

          <section className="panel rubric-panel">
            <div className="panel-heading">
              <div><div className="page-eyebrow">ĐỊNH HƯỚNG</div><h2>Tiêu chí đánh giá</h2></div>
              <span className="total-points">{questions.reduce((sum, q) => sum + q.max_score, 0)} điểm tối đa</span>
            </div>
            <div className="student-rubric">
              {assignment.rubric.map((r, index) => (
                <div className="student-rubric-row" key={r.id}>
                  <span className="rubric-index">0{index + 1}</span>
                  <div><strong>{r.title}</strong><small>{r.description}</small></div>
                  <span className="rubric-point">{r.max_points}đ</span>
                </div>
              ))}
            </div>
            {!assignment.rubric.length && <p className="muted">Giáo viên không đặt rubric riêng. Hãy dùng bằng chứng từ dữ liệu, trình bày phương pháp và giải thích insight cho từng câu hỏi.</p>}
            <div className="share-after-deadline"><div><strong>{assignment.sharing_open ? 'Đã mở học từ bạn cùng lớp' : 'Chia sẻ theo lịch của lớp'}</strong><span>{assignment.share_mode === 'all' ? 'Các phiên bản đã nộp xuất hiện trong lớp khi đến giờ mở. Bản nháp được giữ riêng.' : 'Bạn chọn chia sẻ bản đã nộp khi lớp mở xem bài.'}</span></div></div>
            {assignment.sharing_open && <div className="learning-tabs"><Link className="button button-primary" to={`/comparison?class=${assignment.classroom_id}&assignment=${assignment.id}`}>AI so sánh bài<ArrowRight size={15} /></Link><Link className="button button-ghost" to={`/discussion?class=${assignment.classroom_id}&assignment=${assignment.id}`}>Thảo luận<ArrowRight size={15} /></Link></div>}
            {assignment.sharing_open && assignment.share_mode === 'opt_in' && submission && (
              <div className="share-after-deadline">
                <div><strong>Chia sẻ cùng lớp</strong><span>Chỉ báo cáo và biểu đồ được hiển thị.</span></div>
                <button className={`button ${shared ? 'button-shared' : 'button-primary'}`} onClick={toggleShare} disabled={!latest}><Share2 size={15} />{shared ? 'Đang chia sẻ' : 'Chia sẻ bài'}</button>
              </div>
            )}
          </section>
          <SubmissionHistory submission={submission} onRefresh={onRefresh} />

          {referenceState === 'ok' && reference && <ReferenceView reference={reference} questions={questions} />}
          {referenceState === 'not_submitted' && <section className="panel reference-gate"><div className="page-eyebrow">BÀI THAM KHẢO CỦA GIẢNG VIÊN</div><p className="muted">Bạn cần nộp bài lần đầu trước khi xem bài tham khảo.</p></section>}
          {referenceState === 'not_published' && <section className="panel reference-gate"><div className="page-eyebrow">BÀI THAM KHẢO CỦA GIẢNG VIÊN</div><p className="muted">Giảng viên chưa công bố bài tham khảo.</p></section>}
        </div>

        <aside className="workspace-aside">
          <section className="ai-panel">
            <div className="ai-panel-heading">
              <div className="ai-avatar"><Sparkles size={17} /></div>
              <div><strong>Trợ lý phân tích AI</strong><span><i />DA-Agent sẵn sàng</span></div>
              <span className="ai-beta">BETA</span>
            </div>
            <div className="ai-note"><Sparkles size={14} /><span>AI gợi mở ý tưởng theo câu hỏi đang chọn. Bạn tự phân tích dữ liệu và viết câu trả lời.</span></div>
            {questions.length > 0 && (
              <div className="question-selector">
                {questions.map(q => <button key={q.id} className={activeQuestionId === q.id ? 'active' : ''} onClick={() => setActiveQuestionId(q.id)}>Câu hỏi {q.question_order}</button>)}
              </div>
            )}
            <div className="chat-messages">
              {chat.length === 0 && (
                <div className="ai-welcome">
                  <div className="ai-welcome-icon"><BarChart3 size={22} /></div>
                  <strong>Bắt đầu từ một câu hỏi</strong>
                  <p>Hỏi về dataset, cách chọn phép phân tích hoặc cách đọc biểu đồ.</p>
                  <div className="suggestion-list">
                    {['Tôi nên bắt đầu khám phá dữ liệu từ đâu?', 'Giúp tôi hiểu câu hỏi đang chọn'].map(text => (
                      <button key={text} onClick={() => setQuestion(text)}>{text}<ArrowRight size={13} /></button>
                    ))}
                  </div>
                </div>
              )}
              {chat.map((item, i) => (
                <div className={`chat-message ${item.role}`} key={i}>
                  <div className="chat-bubble">
                    {item.role === 'student' && item.questionOrder && <span className="chat-question-tag">Câu hỏi {item.questionOrder}</span>}
                    {item.role === 'ai' ? <MarkdownContent>{item.text}</MarkdownContent> : item.text}
                  </div>
                  {item.role === 'ai' && activeQuestionId && [...item.text.matchAll(/!\[[^\]]*\]\((\/api\/assets\/[^)]+)\)/g)].map((match, n) => (
                    <button className="insert-chart" key={n} disabled={!canEdit} onClick={() => attachArtifact(activeQuestionId, { id: match[1].split('/').pop() || '', url: match[1], name: 'Biểu đồ', media_type: 'image/png' })}>
                      <Plus size={12} />Đưa vào câu trả lời
                    </button>
                  ))}
                </div>
              ))}
              {busy === 'chat' && <div className="chat-message ai"><div className="typing"><i /><i /><i /></div></div>}
            </div>
            <form className="chat-input-wrap" onSubmit={ask}>
              <textarea
                value={question}
                onChange={e => setQuestion(e.target.value)}
                placeholder="Hỏi trợ giảng…"
                rows={2}
                disabled={!canEdit}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); (e.currentTarget.form as HTMLFormElement)?.requestSubmit() } }}
              />
              <button className="send-button" disabled={!canEdit || !question.trim() || Boolean(busy)} aria-label="Gửi câu hỏi"><Send size={16} /></button>
            </form>
            <div className="chat-disclaimer">AI có thể sai. Hãy đối chiếu với dữ liệu và lập luận của bạn.</div>
            {jobError && <div className="form-error compact-error">{jobError}</div>}
          </section>
        </aside>
      </div>
      {preview && <DataPreview title={preview.title} data={preview.data} close={() => setPreview(null)} />}
    </PageContainer>
  )
}

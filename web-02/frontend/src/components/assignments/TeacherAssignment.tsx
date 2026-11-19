import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import MarkdownContent from '../ui/MarkdownContent'
import { ArrowLeft, ArrowRight, BookOpen, Check, ChevronDown, FileSpreadsheet, Users } from 'lucide-react'
import { assignmentApi, submissionApi } from '../../services/api'
import type { Assignment, Question, SubmissionView } from '../../types'
import { fmtDate } from '../../utils/format'
import PageContainer from '../layout/PageContainer'
import PageHeader from '../layout/PageHeader'
import Modal from '../ui/Modal'
import Badge from '../ui/Badge'
import ReviewCard from './ReviewCard'
import DataPreview from './DataPreview'
import ReferenceEditor from './ReferenceEditor'
import QuestionEditor from './QuestionEditor'
import SharingSettings from './SharingSettings'
import PeerFeedback from './PeerFeedback'
import ExamGenerator from './ExamGenerator'

interface TeacherAssignmentProps {
  assignment: Assignment
  notify: (s: string) => void
  onRefresh: () => void
}

export default function TeacherAssignment({ assignment, notify, onRefresh }: TeacherAssignmentProps) {
  const [submissions, setSubmissions] = useState<SubmissionView[]>([])
  const [selected, setSelected] = useState<SubmissionView | null>(null)
  const [preview, setPreview] = useState<{ title: string; data: { columns: string[]; rows: Record<string, unknown>[] } } | null>(null)
  const [scores, setScores] = useState<Record<string, string>>({})
  const [feedback, setFeedback] = useState<Record<string, string>>({})
  const [comment, setComment] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [versionId, setVersionId] = useState<number | null>(null)

  const load = () => assignmentApi.submissions(assignment.id).then(setSubmissions).catch(e => setError(e.message))
  useEffect(() => { load() }, [assignment.id])

  async function grade(publish: boolean) {
    if (!selected) return
    setBusy(true)
    try {
      await submissionApi.grade(selected.id, { scores, feedback, comment, publish, version_id: versionId })
      notify(publish ? 'Đã công bố điểm.' : 'Đã lưu bản chấm.')
      setSelected(null)
      load()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  async function showPreview(file: { id: string; name: string }) {
    try {
      setPreview({ title: file.name, data: await assignmentApi.previewDataset(assignment.id, file.id) })
    } catch (e) {
      setError((e as Error).message)
    }
  }

  function openGrading(item: SubmissionView, targetId = item.versions[0]?.id) {
    const version = item.versions.find(v => v.id === targetId)
    const grade = version?.grade
    if (grade?.per_question) {
      setScores(Object.fromEntries(grade.per_question.map(p => [String(p.question_id), String(p.score)])))
      setFeedback(Object.fromEntries(grade.per_question.map(p => [String(p.question_id), p.feedback || ''])))
    } else if (grade?.criteria) {
      setScores(Object.fromEntries(grade.criteria.map(c => [c.criterion_id, String(c.score)])))
      setFeedback({})
    } else {
      setScores({})
      setFeedback({})
    }
    setComment(version?.teacher_comment || '')
    setVersionId(version?.id ?? null)
    setSelected(item)
  }

  const questions = assignment.questions || []
  const answerFor = (item: SubmissionView, q: Question) => item.versions.find(v => v.id === versionId)?.answers_snapshot?.find(a => a.question_id === q.id)
  const totalMax = questions.reduce((sum, q) => sum + q.max_score, 0)

  return (
    <PageContainer>
      <Link to={`/classes/${assignment.classroom_id}`} className="back-link"><ArrowLeft size={15} />{assignment.classroom_name}</Link>
      <PageHeader
        eyebrow="BÀI TẬP · GIÁO VIÊN"
        title={assignment.title}
        subtitle={`Hạn nộp ${fmtDate(assignment.due_at)}`}
        action={<Badge status={assignment.status} label={assignment.status === 'published' ? 'Đã công bố' : 'Bản nháp'} />}
      />

      <div className="teacher-assignment-grid">
        <section className="panel assignment-info">
          <div className="panel-heading">
            <div><span className="page-eyebrow">ĐỀ BÀI</span><h2>Yêu cầu phân tích</h2></div>
            <span className="panel-icon"><BookOpen size={18} /></span>
          </div>
          <div className="prose"><MarkdownContent>{assignment.description}</MarkdownContent></div>
          {questions.length > 0 && (
            <>
              <div className="subsection-title">Câu hỏi bài tập</div>
              {questions.map(q => (
                <div className="question-read" key={q.id}>
                  <span className="question-form-num">0{q.question_order}</span>
                  <div>
                    <strong>Câu hỏi {q.question_order} <span className="optional">· {q.max_score} điểm</span></strong>
                    <div className="prose"><MarkdownContent>{q.question_text}</MarkdownContent></div>
                  </div>
                </div>
              ))}
            </>
          )}
          {!questions.length && <div className="form-error compact-error">Bổ sung câu hỏi để sinh viên bắt đầu làm bài.</div>}
          <div className="subsection-title">Dataset được giao</div>
          {assignment.datasets.map(file => (
            <button className="file-row file-row-button" key={file.id} onClick={() => showPreview(file)}>
              <span className="file-type-icon"><FileSpreadsheet size={17} /></span>
              <span><strong>{file.name}</strong><small>{(file.size / 1024 / 1024).toFixed(1)} MB · Xem trước dữ liệu</small></span>
              <ArrowRight size={16} />
            </button>
          ))}
          <div className="subsection-title">Rubric</div>
          {!assignment.rubric.length && <p className="muted">Không đặt tiêu chí riêng. Chấm theo điểm tối đa của từng câu hỏi.</p>}
          {assignment.rubric.map(r => (
            <div className="rubric-row" key={r.id}>
              <span className="rubric-point">{r.max_points}đ</span>
              <div><strong>{r.title}</strong><small>{r.description}</small></div>
            </div>
          ))}
          <details className="answer-key">
            <summary>Đáp án mẫu riêng tư <ChevronDown size={15} /></summary>
            <div className="prose"><MarkdownContent>{assignment.answer_key || 'Chưa có đáp án mẫu.'}</MarkdownContent></div>
          </details>
          {assignment.status === 'draft' && <div className="stack-form draft-publish">
            <label>Thêm dataset<input type="file" accept=".csv,.xlsx" multiple disabled={busy} onChange={async e => {
              const files = Array.from(e.target.files || [])
              if (!files.length) return
              setBusy(true)
              try { await assignmentApi.uploadDatasets(assignment.id, files); onRefresh() } catch (err) { setError((err as Error).message) } finally { setBusy(false) }
            }} /></label>
            <button className="button button-primary" disabled={busy || !assignment.datasets.length || !questions.length} onClick={async () => {
              setBusy(true)
              try { await assignmentApi.publish(assignment.id); notify('Đã công bố bài tập.'); onRefresh() } catch (err) { setError((err as Error).message) } finally { setBusy(false) }
            }}>Công bố bài tập</button>
          </div>}
        </section>

        <section className="panel submissions-panel">
          <div className="panel-heading">
            <div><span className="page-eyebrow">TIẾN ĐỘ LỚP</span><h2>Bài nộp <span className="count-badge">{submissions.length}</span></h2></div>
            <Users size={19} className="muted-icon" />
          </div>
          {error && <div className="form-error">{error}</div>}
          {submissions.length ? submissions.map(item => {
            const latest = item.versions[0]
            return (
              <button className="student-submission" key={item.id} onClick={() => openGrading(item)}>
                <span className="avatar avatar-small">{item.student?.slice(0, 1) ?? '?'}</span>
                <span className="student-submission-copy">
                  <strong>{item.student}</strong>
                  <small>{latest ? `Phiên bản ${latest.version_number} · ${fmtDate(latest.submitted_at)}` : 'Chưa nộp bài'}</small>
                </span>
                <span className={`review-dot ${latest?.review ? 'review-done' : ''}`} />
                {item.grade ? <span className="grade-chip">{item.grade.total}/{item.grade.max_score}</span> : <ArrowRight size={16} />}
              </button>
            )
          }) : (
            <div className="empty-mini"><Users size={22} /><span>Chưa có bài nộp.</span></div>
          )}
        </section>
      </div>

      {assignment.status === 'draft' && <ExamGenerator assignment={assignment} onApplied={() => { notify('Đã lưu đề AI và đáp án riêng tư.'); onRefresh() }} />}
      <SharingSettings assignment={assignment} notify={notify} onRefresh={onRefresh} />
      <ReferenceEditor key={JSON.stringify(assignment.reference)} assignment={assignment} notify={notify} onRefresh={onRefresh} />
      {(assignment.status === 'draft' || !questions.length) && <QuestionEditor key={JSON.stringify(questions)} assignment={assignment} notify={notify} onRefresh={onRefresh} />}

      {selected && (
        <Modal close={() => setSelected(null)} wide>
          <div className="modal-heading">
            <span className="modal-icon"><Users size={20} /></span>
            <div>
              <div className="page-eyebrow">BÀI NỘP CỦA SINH VIÊN</div>
              <h2>{selected.student}</h2>
              <p>{selected.versions.length ? `${selected.versions.length} phiên bản đã nộp` : 'Chưa có phiên bản nộp'}</p>
            </div>
          </div>
          <div className="grade-modal-body">
            {selected.versions.length > 0 && <label>Phiên bản được chấm<select value={versionId ?? ''} onChange={e => openGrading(selected, Number(e.target.value))}>{selected.versions.map(v => <option key={v.id} value={v.id}>Phiên bản {v.version_number}{v.is_improvement ? ' · Bản cải thiện sau hạn' : ''} · {fmtDate(v.submitted_at)}</option>)}</select></label>}
            <p className="muted">Nội dung dưới đây được lấy từ phiên bản nộp đã lưu. Thay đổi nháp không ảnh hưởng bài được chấm.</p>
            <div className="version-picker">
              {selected.versions.map(v => (
                <details key={v.id} className="version-detail">
                  <summary>Phiên bản {v.version_number}{v.is_improvement ? ' · Cải thiện sau hạn' : ''} · {fmtDate(v.submitted_at)}<ChevronDown size={15} /></summary>
                  <div className="prose"><MarkdownContent>{v.body_markdown}</MarkdownContent></div>
                  {v.review && <ReviewCard checks={v.review.checks} overall={v.review.overall} />}
                  {v.reflection && <p className="learned-note">Điều sinh viên đã cải thiện: {v.reflection}</p>}
                  <PeerFeedback reviews={v.peer_reviews} />
                </details>
              ))}
            </div>
            {questions.map(q => {
              const answer = answerFor(selected, q)
              return (
                <div className="question-answer-block" key={q.id}>
                  <div className="subsection-title">Câu hỏi {q.question_order} <span className="optional">· {q.max_score} điểm</span></div>
                  <p className="question-read-text">{q.question_text}</p>
                  <div className="prose answer-prose">
                    {answer?.answer_markdown ? <MarkdownContent>{answer.answer_markdown}</MarkdownContent> : <span className="muted">Chưa trả lời.</span>}
                  </div>
                  {answer?.artifacts?.length ? (
                    <div className="answer-artifacts">{answer.artifacts.map(art => <img key={art.id} src={art.url} alt={art.name} className="answer-artifact" />)}</div>
                  ) : null}
                  <div className="grade-row">
                    <label className="score-row">
                      <span><strong>Điểm câu {q.question_order}</strong></span>
                      <span className="score-input">
                        <input type="number" min="0" max={q.max_score} step="0.5"
                          value={scores[String(q.id)] ?? ''}
                          onChange={e => setScores({ ...scores, [String(q.id)]: e.target.value })} />
                        <small>/ {q.max_score}</small>
                      </span>
                    </label>
                    <textarea
                      value={feedback[String(q.id)] ?? ''}
                      onChange={e => setFeedback({ ...feedback, [String(q.id)]: e.target.value })}
                      rows={2}
                      placeholder={`Phản hồi cho Câu hỏi ${q.question_order}…`}
                    />
                  </div>
                </div>
              )
            })}
            <div className="grade-total">
              <strong>Tổng điểm</strong>
              <span>
                {questions.reduce((sum, q) => sum + (Number(scores[String(q.id)]) || 0), 0)} / {totalMax}
              </span>
            </div>
            <label>Nhận xét chung<textarea value={comment} onChange={e => setComment(e.target.value)} rows={3} placeholder="Ghi nhận xét cho sinh viên…" /></label>
            {error && <div className="form-error">{error}</div>}
          </div>
          <div className="modal-actions">
            <button className="button button-ghost" onClick={() => setSelected(null)}>Đóng</button>
            <button className="button button-ghost" onClick={() => grade(false)} disabled={busy || !versionId}>Lưu riêng</button>
            <button className="button button-primary" onClick={() => grade(true)} disabled={busy || !versionId}>Lưu và công bố điểm <Check size={16} /></button>
          </div>
        </Modal>
      )}
      {preview && <DataPreview title={preview.title} data={preview.data} close={() => setPreview(null)} />}
    </PageContainer>
  )
}

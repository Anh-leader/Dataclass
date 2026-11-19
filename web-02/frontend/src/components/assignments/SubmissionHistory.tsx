import { useState } from 'react'
import MarkdownContent from '../ui/MarkdownContent'
import { submissionApi, pollJob } from '../../services/api'
import type { SubmissionView } from '../../types'
import { fmtDate } from '../../utils/format'
import ReviewCard from './ReviewCard'
import PeerFeedback from './PeerFeedback'

export default function SubmissionHistory({ submission, onRefresh }: { submission?: SubmissionView; onRefresh: () => void }) {
  const [busy, setBusy] = useState<number | null>(null)
  const [error, setError] = useState('')
  async function retry(versionId: number) {
    if (!submission) return
    setBusy(versionId)
    setError('')
    try {
      const job = await submissionApi.retryAIReview(submission.id, versionId)
      onRefresh()
      await pollJob(job.job_id)
    } catch (e) { setError((e as Error).message) } finally { setBusy(null); onRefresh() }
  }
  if (!submission?.versions.length) return null
  return (
    <section className="panel submission-history">
      <div className="panel-heading"><div><span className="page-eyebrow">QUÁ TRÌNH HỌC TẬP</span><h2>Phiên bản và phản hồi</h2></div><span className="count-badge">{submission.versions.length}</span></div>
      <p className="muted">Mỗi bản nộp lưu cố định câu trả lời và bằng chứng. Mở từng bản để xem thay đổi, góp ý AI và đánh giá của bạn học.</p>
      {error && <div className="form-error">{error}</div>}
      {submission.versions.map((version, index) => (
        <details className="version-detail" key={version.id} open={index === 0}>
          <summary>Phiên bản {version.version_number} · {version.is_improvement ? 'Cải thiện sau hạn' : 'Bài nộp'} · {fmtDate(version.submitted_at)}</summary>
          <div className="prose"><MarkdownContent>{version.body_markdown}</MarkdownContent></div>
          {version.reflection && <p className="learned-note"><strong>Điều đã cải thiện: </strong>{version.reflection}</p>}
          {version.grade && <div className="published-grade"><div className="grade-big">{version.grade.total}<small>/{version.grade.max_score}</small></div><div><strong>Giáo viên đánh giá phiên bản {version.version_number}</strong><span>{version.teacher_comment || 'Đã công bố điểm.'}</span></div></div>}
          {version.review && <ReviewCard checks={version.review.checks} overall={version.review.overall} />}
          {['queued', 'running'].includes(version.review_status) && <p className="muted">{version.review_status === 'queued' ? 'Đánh giá AI đang chờ xử lý.' : 'AI đang đánh giá phiên bản này.'}</p>}
          {['failed', 'none', 'queued', 'running'].includes(version.review_status) && <button className="button button-ghost" disabled={busy !== null} onClick={() => retry(version.id)}>{busy === version.id ? 'Đang nhận đánh giá…' : ['queued', 'running'].includes(version.review_status) ? 'Theo dõi đánh giá AI' : 'Yêu cầu AI đánh giá lại'}</button>}
          <div className="subsection-title">Bạn cùng lớp đánh giá</div><PeerFeedback reviews={version.peer_reviews} />
        </details>
      ))}
    </section>
  )
}

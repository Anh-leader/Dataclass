import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import MarkdownContent from '../ui/MarkdownContent'
import { ArrowDown, ArrowUp, Check, ChevronRight, FileText, Flame, Heart, MessageCircle, Send, Star, X } from 'lucide-react'
import type { GalleryItem, User } from '../../types'
import { submissionApi, commentApi } from '../../services/api'
import { fmtDate } from '../../utils/format'
import PeerFeedback from './PeerFeedback'
import StudentAvatar from './StudentAvatar'

export default function GallerySubmission({ item, user, reload, notify, highlighted = false }: { item: GalleryItem; user: User; reload: () => Promise<void>; notify: (message: string) => void; highlighted?: boolean }) {
  const [versionId, setVersionId] = useState(item.version_id)
  const [rating, setRating] = useState(4)
  const [strengths, setStrengths] = useState('')
  const [suggestions, setSuggestions] = useState('')
  const [learned, setLearned] = useState('')
  const [comment, setComment] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [tab, setTab] = useState<'work' | 'discussion'>('work')
  const [expanded, setExpanded] = useState(false)
  const version = item.versions.find(v => v.id === versionId) || item.versions[0]
  const mine = version.peer_reviews.find(review => review.is_mine)
  const previewImage = version.body_markdown.match(/!\[[^\]]*\]\((\/api\/assets\/[a-zA-Z0-9_-]+)\)/)?.[1]
  const previewBody = previewImage && !expanded ? version.body_markdown.replace(/!\[[^\]]*\]\([^)]*\)/g, '') : version.body_markdown
  useEffect(() => {
    setRating(mine?.rating ?? 4)
    setStrengths(mine?.strengths || '')
    setSuggestions(mine?.suggestions || '')
    setLearned(mine?.learned || '')
    setError('')
  }, [version.id, mine?.id, mine?.updated_at])

  async function saveReview(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      await submissionApi.peerReview(item.submission_id, { version_id: version.id, rating, strengths, suggestions, learned })
      await reload()
      notify('Đã lưu đánh giá chéo và điều bạn học được.')
    } catch (e) { setError((e as Error).message) } finally { setBusy(false) }
  }
  async function sendComment() {
    if (!comment.trim()) return
    setBusy(true)
    setError('')
    try { await submissionApi.comments(item.submission_id, comment); setComment(''); await reload() }
    catch (e) { setError((e as Error).message) } finally { setBusy(false) }
  }
  async function removeComment(id: number) {
    setBusy(true); setError('')
    try { await commentApi.remove(id); await reload() } catch (e) { setError((e as Error).message) } finally { setBusy(false) }
  }
  async function vote() {
    setBusy(true); setError('')
    try { await submissionApi.vote(item.submission_id, !item.has_voted); await reload() }
    catch (e) { setError((e as Error).message) } finally { setBusy(false) }
  }
  const average = version.peer_reviews.length ? (version.peer_reviews.reduce((sum, review) => sum + review.rating, 0) / version.peer_reviews.length).toFixed(1) : null

  return (
    <article className="gallery-card discussion-detail">
      <div className="discussion-detail-tabs" role="group" aria-label="Nội dung bài nộp"><button aria-pressed={tab === 'work'} className={tab === 'work' ? 'active' : ''} onClick={() => setTab('work')}><FileText size={16} />Bài làm</button><button aria-pressed={tab === 'discussion'} className={tab === 'discussion' ? 'active' : ''} onClick={() => setTab('discussion')}><MessageCircle size={16} />Thảo luận <span>{item.comments.length}</span></button></div>
      <div className="discussion-detail-content">
      <header className="discussion-author-header"><StudentAvatar name={item.student} seed={item.student_id} /><div><strong>{item.student}{item.is_mine && <span className="mine-label">Bạn</span>}</strong><small>Phiên bản {version.version_number} · {fmtDate(version.submitted_at)}</small></div>{highlighted && <span className="featured-label"><Flame size={12} />Nổi bật</span>}<button className={`detail-heart ${item.has_voted ? 'has-voted' : ''}`} aria-label={`${item.has_voted ? 'Đã bình chọn' : 'Bài hay'} · ${item.vote_count}`} title={item.is_mine ? 'Bạn không thể bình chọn bài của mình' : item.has_voted ? 'Thu hồi bình chọn' : 'Bình chọn bài hay'} disabled={busy || item.is_mine} aria-pressed={item.has_voted} onClick={vote}><Heart size={19} fill={item.has_voted ? 'currentColor' : 'none'} /><span>{item.vote_count}</span></button></header>
      <div className="discussion-report-meta"><span><FileText size={13} />{item.assignment_title}</span><label><span className="sr-only">Phiên bản đang xem</span><select aria-label="Phiên bản đang xem" value={version.id} onChange={e => { setVersionId(Number(e.target.value)); setExpanded(false) }}>{item.versions.map(v => <option key={v.id} value={v.id}>Phiên bản {v.version_number}{v.is_improvement ? ' · Cải thiện' : ''}</option>)}</select></label></div>
      {tab === 'work' && <section className={`discussion-report ${previewImage ? 'has-chart-preview' : ''}`}><div className={`prose gallery-prose ${expanded ? 'is-expanded' : ''}`}><MarkdownContent>{previewBody}</MarkdownContent></div>{previewImage && !expanded && <figure className="discussion-chart-preview"><img src={previewImage} alt={`Biểu đồ trong bài của ${item.student}, phiên bản ${version.version_number}`} /><figcaption>Biểu đồ đính kèm · Phiên bản {version.version_number}</figcaption></figure>}<button className="report-expand" aria-expanded={expanded} onClick={() => setExpanded(value => !value)}>{expanded ? 'Thu gọn bài làm' : 'Xem toàn bộ bài làm'}{expanded ? <ArrowUp size={14} /> : <ArrowDown size={14} />}</button>{version.reflection && <p className="learned-note"><strong>Điều tác giả đã cải thiện: </strong>{version.reflection}</p>}</section>}
      <section className="discussion-conversation" aria-label="Bình luận về bài nộp"><div className="conversation-heading"><h3>Trao đổi về bài làm <span>{item.comments.length}</span></h3><span>Góp ý để cùng tiến bộ</span></div>
        <form className="discussion-compose" onSubmit={e => { e.preventDefault(); if (!busy) void sendComment() }}><StudentAvatar name={user.full_name} seed={user.id} small /><input aria-label={`Bình luận bài của ${item.student}`} value={comment} onChange={e => setComment(e.target.value)} placeholder="Chia sẻ góc nhìn của bạn…" maxLength={2000} /><button disabled={busy || !comment.trim()} aria-label="Gửi bình luận"><Send size={16} /><span>Gửi</span></button></form>
        <div className="discussion-comment-list">{item.comments.length ? item.comments.map(c => <div className="discussion-comment" key={c.id}><StudentAvatar name={c.author} seed={c.author_id} small /><div className="discussion-comment-copy"><div><strong>{c.author}</strong><time dateTime={c.created_at}>{fmtDate(c.created_at)}</time></div><p>{c.body}</p></div>{(c.author_id === user.id || user.role === 'teacher') && <button className="discussion-delete" aria-label="Xóa bình luận" title="Xóa bình luận" disabled={busy} onClick={() => removeComment(c.id)}><X size={14} /></button>}</div>) : <div className="conversation-empty"><MessageCircle size={20} /><p>Chưa có bình luận. Hãy mở đầu bằng một góp ý hữu ích nhé.</p></div>}</div>
      </section>
      <section className="discussion-reviews"><div className="discussion-rating"><span><Star size={16} /><strong>Đánh giá của lớp</strong></span>{average ? <span><strong>{average}</strong>/5 <small>· {version.peer_reviews.length} đánh giá</small></span> : <small>Chưa có đánh giá</small>}</div>
      {!!version.peer_reviews.length && <details className="discussion-saved-reviews" open={tab === 'discussion'}><summary>Xem {version.peer_reviews.length} đánh giá <ChevronRight size={14} /></summary><PeerFeedback reviews={version.peer_reviews} /></details>}
      {item.can_review && <details className="peer-review-editor"><summary><Star size={15} />{mine ? 'Sửa đánh giá của tôi' : `Đánh giá phiên bản ${version.version_number} và ghi điều học được`}</summary><form className="stack-form" onSubmit={saveReview}>
        <p className="muted">Nhận xét cụ thể về bằng chứng và cách phân tích. Mức 1–5 là đánh giá của bạn học.</p>
        <label>Mức đánh giá<select value={rating} onChange={e => setRating(Number(e.target.value))}><option value={1}>1 · Cần làm lại</option><option value={2}>2 · Cần cải thiện nhiều</option><option value={3}>3 · Có phần làm tốt</option><option value={4}>4 · Phân tích tốt</option><option value={5}>5 · Rất thuyết phục</option></select></label>
        <label>Điểm tốt trong bài<textarea value={strengths} onChange={e => setStrengths(e.target.value)} required maxLength={2000} rows={2} /></label>
        <label>Gợi ý để bài tốt hơn<textarea value={suggestions} onChange={e => setSuggestions(e.target.value)} required maxLength={2000} rows={2} /></label>
        <label>Tôi học được gì từ bài này?<textarea value={learned} onChange={e => setLearned(e.target.value)} required maxLength={2000} rows={2} /></label>
        <button className="button button-primary" disabled={busy}><Check size={15} />{busy ? 'Đang lưu…' : 'Lưu đánh giá chéo'}</button>
      </form></details>}
      </section>
      {item.is_mine && <Link className="text-link" to={`/assignments/${item.assignment_id}`}>Xem phản hồi và cải thiện bài của tôi →</Link>}
      {error && <div className="form-error">{error}</div>}
      </div>
    </article>
  )
}

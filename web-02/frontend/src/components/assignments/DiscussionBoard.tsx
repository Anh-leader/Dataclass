import { useState } from 'react'
import { Flame, Heart, MessageCircle, Search, Users } from 'lucide-react'
import type { GalleryItem, User } from '../../types'
import { fmtDate } from '../../utils/format'
import GallerySubmission from './GallerySubmission'
import StudentAvatar from './StudentAvatar'

function excerpt(body: string) {
  return body.replace(/!\[[^\]]*\]\([^)]*\)/g, '').replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/[#*`>_|]/g, '').replace(/\s+/g, ' ').trim().slice(0, 150)
}

export default function DiscussionBoard({ items, user, reload, notify }: {
  items: GalleryItem[]; user: User; reload: () => Promise<void>; notify: (message: string) => void
}) {
  const [selectedId, setSelectedId] = useState<number | null>(items[0]?.submission_id ?? null)
  const [query, setQuery] = useState('')
  const filtered = items.filter(item => `${item.student} ${item.assignment_title}`.toLocaleLowerCase('vi').includes(query.toLocaleLowerCase('vi')))
  const selected = filtered.find(item => item.submission_id === selectedId) || filtered[0]
  const topVotes = Math.max(0, ...items.map(item => item.vote_count))
  const highlighted = (item: GalleryItem) => topVotes > 0 && item.vote_count === topVotes

  return <div className="discussion-board">
    <section className="discussion-list-panel" aria-label="Danh sách bài nộp">
      <div className="discussion-list-heading"><div><Users size={17} /><h2>Bài nộp của lớp</h2><span className="count-badge">{items.length}</span></div><span>Cùng học từ những góc nhìn khác</span></div>
      <label className="community-search"><Search size={17} /><input aria-label="Tìm bài nộp" placeholder="Tìm tên sinh viên, bài tập…" value={query} onChange={e => setQuery(e.target.value)} /></label>
      <div className="discussion-list">
        {filtered.map(item => <button key={item.submission_id} className={`discussion-list-item ${item.submission_id === selected?.submission_id ? 'is-selected' : ''}`} aria-pressed={item.submission_id === selected?.submission_id} onClick={() => setSelectedId(item.submission_id)}>
          <div className="discussion-item-top"><StudentAvatar name={item.student} seed={item.student_id} /><div className="discussion-item-author"><strong>{item.student}{item.is_mine && <span className="mine-label">Bạn</span>}</strong><small>Phiên bản {item.version_number} · {fmtDate(item.versions.find(v => v.id === item.version_id)!.submitted_at)}</small></div></div>
          <p>{excerpt(item.body_markdown) || 'Mở bài để xem nội dung phân tích.'}</p>
          <div className="discussion-item-footer"><span className="discussion-item-assignment">{item.assignment_title}</span><span className={item.has_voted ? 'has-voted' : ''}><Heart size={14} fill={item.has_voted ? 'currentColor' : 'none'} />{item.vote_count}</span><span><MessageCircle size={14} />{item.comments.length}</span></div>
          {highlighted(item) && <span className="featured-label"><Flame size={12} />Nổi bật</span>}
        </button>)}
        {!filtered.length && <div className="community-empty"><Search size={26} /><strong>Không tìm thấy bài nộp</strong><p>Thử một tên hoặc từ khóa khác nhé.</p></div>}
      </div>
    </section>
    {selected ? <GallerySubmission key={selected.submission_id} item={selected} user={user} reload={reload} notify={notify} highlighted={highlighted(selected)} /> : <div className="discussion-no-selection"><MessageCircle size={32} /><h3>Mỗi bài làm, một góc nhìn mới</h3><p>Chọn một bài nộp để cùng đọc và trao đổi.</p></div>}
  </div>
}

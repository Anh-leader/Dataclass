import { Check, Sparkles } from 'lucide-react'
import type { ReviewView } from '../../types'

interface ReviewCardProps {
  checks: ReviewView['checks']
  overall?: ReviewView['overall']
}

export default function ReviewCard({ checks, overall }: ReviewCardProps) {
  const isQuestionReview = checks?.length > 0 && 'question_order' in checks[0]
  if (!checks?.length && !overall) return <div className="empty-mini">Chưa có nhận xét AI.</div>
  return (
    <div className="review-card">
      <div className="review-card-title"><Sparkles size={15} />Đánh giá AI
        {overall?.quality && <span className={`quality-label ${overall.quality}`}>{({ good: 'Đạt chất lượng', partial: 'Cần bổ sung', needs_work: 'Cần cải thiện', insufficient_evidence: 'Chưa đủ bằng chứng' })[overall.quality]}</span>}
      </div>
      <p className="muted">Góp ý tự động để cải thiện bài; điểm chính thức do giáo viên quyết định.</p>
      {isQuestionReview
        ? checks.map(item => (
            <div className="review-check" key={item.question_id}>
              <span className={`check-state ${item.status}`}>{item.status === 'met' ? <Check size={13} /> : item.status === 'partial' ? '…' : '!'}</span>
              <div>
                <strong>Câu hỏi {item.question_order}</strong>
                <small>{item.status === 'met' ? 'Đã thể hiện tốt' : item.status === 'partial' ? 'Có thể bổ sung thêm' : 'Nên xem lại câu hỏi này'}</small>
                <p>{item.feedback}</p>
                {item.suggestion && <p className="suggestion-line">{item.suggestion}</p>}
              </div>
            </div>
          ))
        : checks.map(item => (
            <div className="review-check" key={item.criterion_id}>
              <span className={`check-state ${item.status}`}>{item.status === 'met' ? <Check size={13} /> : item.status === 'partial' ? '…' : '!'}</span>
              <div>
                <strong>{item.title}</strong>
                <small>{item.status === 'met' ? 'Đã thể hiện tốt' : item.status === 'partial' ? 'Có thể bổ sung thêm' : 'Nên xem lại tiêu chí này'}</small>
                <p>{item.hint}</p>
              </div>
            </div>
          ))}
      {overall && (
        <div className="review-overall">
          <strong>Nhận xét tổng thể</strong>
          <p>{overall.feedback}</p>
          {overall.suggestion && <p className="suggestion-line">{overall.suggestion}</p>}
        </div>
      )}
    </div>
  )
}

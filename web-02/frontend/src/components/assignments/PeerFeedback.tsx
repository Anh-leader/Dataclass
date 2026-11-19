import type { PeerReviewView } from '../../types'

export default function PeerFeedback({ reviews }: { reviews: PeerReviewView[] }) {
  return (
    <div className="peer-feedback-list">
      {!reviews.length && <p className="muted">Chưa có đánh giá chéo cho phiên bản này.</p>}
      {reviews.map(review => (
        <article className="peer-feedback" key={review.id}>
          <div className="peer-feedback-heading"><strong>{review.reviewer}</strong><span>{review.rating}/5 · Đánh giá của bạn học</span></div>
          <p><strong>Điểm tốt: </strong>{review.strengths}</p>
          <p><strong>Gợi ý cải thiện: </strong>{review.suggestions}</p>
          <p className="learned-note"><strong>Điều học được: </strong>{review.learned}</p>
        </article>
      ))}
    </div>
  )
}

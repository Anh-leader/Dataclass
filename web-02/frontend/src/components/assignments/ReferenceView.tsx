import MarkdownContent from '../ui/MarkdownContent'
import type { Question, Reference } from '../../types'
import Badge from '../ui/Badge'

interface ReferenceViewProps {
  reference: Reference
  questions: Question[]
}

export default function ReferenceView({ reference, questions }: ReferenceViewProps) {
  return (
    <section className="panel reference-view">
      <div className="panel-heading">
        <div>
          <div className="page-eyebrow">BÀI THAM KHẢO CỦA GIẢNG VIÊN</div>
          <h2>Gợi ý từ giáo viên</h2>
        </div>
        <Badge status="published" label="Đã công bố" />
      </div>
      {questions.map(q => {
        const answer = reference.answers?.find(a => a.question_id === q.id)
        return (
          <div className="reference-answer-view" key={q.id}>
            <span className="question-form-label">Câu hỏi {q.question_order}</span>
            <div className="prose question-read-text"><MarkdownContent>{q.question_text}</MarkdownContent></div>
            <div className="prose"><MarkdownContent>{answer?.answer_markdown || 'Chưa có nội dung.'}</MarkdownContent></div>
          </div>
        )
      })}
      {reference.note && (
        <div className="reference-note">
          <strong>Ghi chú của giảng viên</strong>
          <div className="prose"><MarkdownContent>{reference.note}</MarkdownContent></div>
        </div>
      )}
    </section>
  )
}

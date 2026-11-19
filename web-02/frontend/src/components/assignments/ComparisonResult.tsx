import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, CheckCircle2, CircleHelp, FileCheck2, Lightbulb, Sparkles, TrendingUp } from 'lucide-react'
import MarkdownContent from '../ui/MarkdownContent'
import StudentAvatar from './StudentAvatar'

export interface ComparisonFeedback {
  summary: string; note: string; demo?: boolean; next_steps: string[]; mode?: string
  sources: { base: { student: string; version_id: number; version_number: number }; peers: { student: string; version_id: number; version_number: number }[] }
  question_labels: { id: number; order: number; text: string }[]
  questions: { question_id: number; base_strengths: string; base_gaps: string; peers: { version_id: number; similarities: string; differences: string; learn_from_peer: string }[] }[]
}

export default function ComparisonResult({ result, assignmentId }: { result: ComparisonFeedback; assignmentId: number }) {
  const [activeQuestion, setActiveQuestion] = useState<number | null>(null)
  const question = result.questions.find(q => q.question_id === activeQuestion)
  const label = result.question_labels.find(q => q.id === activeQuestion)
  return <section className="comparison-result">
    <header className="result-heading"><div><span className="result-spark"><Sparkles size={18} /></span><h2>Kết quả so sánh</h2><span className="result-saved"><CheckCircle2 size={13} />{result.demo ? 'Nhận xét mẫu' : 'Đã lưu'}</span></div><span>Nhận xét hỗ trợ học tập</span></header>
    <nav className="result-question-tabs" aria-label="Kết quả theo câu hỏi"><button aria-pressed={activeQuestion === null} className={activeQuestion === null ? 'active' : ''} onClick={() => setActiveQuestion(null)}>Tổng quan</button>{result.questions.map((q, index) => <button key={q.question_id} className={activeQuestion === q.question_id ? 'active' : ''} aria-pressed={activeQuestion === q.question_id} onClick={() => setActiveQuestion(q.question_id)}>Câu hỏi {result.question_labels.find(l => l.id === q.question_id)?.order || index + 1}</button>)}</nav>
    <div className="result-content">
      {!question ? <><div className="result-overview-summary"><MarkdownContent>{result.summary}</MarkdownContent></div><div className="result-insight-grid">
        <article className="result-insight insight-strength"><h3><CheckCircle2 size={17} />Điểm mạnh của bạn</h3>{result.questions.map(q => <div key={q.question_id}><span>Câu {result.question_labels.find(l => l.id === q.question_id)?.order}</span><MarkdownContent>{q.base_strengths}</MarkdownContent></div>)}</article>
        <article className="result-insight insight-improve"><h3><TrendingUp size={17} />Những điểm có thể cải thiện</h3>{result.questions.map(q => <div key={q.question_id}><span>Câu {result.question_labels.find(l => l.id === q.question_id)?.order}</span><MarkdownContent>{q.base_gaps}</MarkdownContent></div>)}</article>
        <article className="result-insight insight-ideas"><h3><Lightbulb size={17} />Gợi ý cho bước tiếp theo</h3><ol>{result.next_steps.map((step, index) => <li key={index}><MarkdownContent>{step}</MarkdownContent></li>)}</ol></article>
      </div></> : <><header className="result-question-title"><span>CÂU HỎI {label?.order}</span><MarkdownContent>{label?.text || 'Nhận xét câu trả lời'}</MarkdownContent></header><div className="result-question-insights"><article className="result-insight insight-strength"><h3><CheckCircle2 size={17} />Điểm mạnh bài gốc</h3><MarkdownContent>{question.base_strengths}</MarkdownContent></article><article className="result-insight insight-improve"><h3><TrendingUp size={17} />Phần cần bổ sung</h3><MarkdownContent>{question.base_gaps}</MarkdownContent></article></div>
      {question.peers.map(peer => { const source = result.sources.peers.find(s => s.version_id === peer.version_id); return <article className="result-peer-card" key={peer.version_id}><header><StudentAvatar name={source?.student || 'Sinh viên'} seed={peer.version_id} small /><strong>{result.mode === 'self' ? 'Bản mới nộp lại của tôi' : source?.student}</strong><span className="version-pill">Phiên bản {source?.version_number}</span></header><div className="result-peer-columns"><div><h4>Điểm tương đồng</h4><MarkdownContent>{peer.similarities}</MarkdownContent></div><div><h4>{result.mode === 'self' ? 'Thay đổi và tiến bộ' : 'Cách làm khác nhau'}</h4><MarkdownContent>{peer.differences}</MarkdownContent></div></div><div className="result-peer-learning"><Lightbulb size={17} /><div><strong>{result.mode === 'self' ? 'Định hướng cải thiện' : 'Điều bạn có thể học hỏi'}</strong><MarkdownContent>{peer.learn_from_peer}</MarkdownContent></div></div></article> })}</>}
      <div className="result-continue"><div><FileCheck2 size={20} /><span><strong>Biến điều học được thành bài làm tốt hơn</strong><small>Bạn tự lựa chọn, kiểm chứng và phát triển cách phân tích của mình.</small></span></div><Link className="button button-primary" to={`/assignments/${assignmentId}`}>Cải thiện bài của tôi<ArrowRight size={15} /></Link></div>
      <p className="result-disclaimer"><CircleHelp size={14} />{result.note}</p>
    </div>
  </section>
}

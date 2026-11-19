import { useEffect, useState } from 'react'
import { Lightbulb, Loader2 } from 'lucide-react'
import { assignmentApi, pollJob } from '../../services/api'

interface HintResult { question_id: number; ideas: { id: string; title: string; hint: string }[] }

export default function QuestionHints({ assignmentId, questionId }: { assignmentId: number; questionId: number }) {
  const [result, setResult] = useState<HintResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  useEffect(() => { setResult(null); setError('') }, [assignmentId, questionId])

  async function load() {
    setBusy(true); setError('')
    try {
      const job = await assignmentApi.questionHints(assignmentId, questionId)
      setResult(await pollJob<HintResult>(job.job_id))
    } catch (e) { setError((e as Error).message) } finally { setBusy(false) }
  }

  return <aside className="question-hints" aria-label="Gợi ý tư duy cho câu hỏi">
    <div className="question-hints-heading"><div><strong><Lightbulb size={17} />Ý tưởng cho câu hỏi này</strong><p>Gợi mở hướng tiếp cận để bạn tự làm, không cung cấp đáp án.</p></div><button className="button button-ghost" disabled={busy} onClick={load}>{busy ? <Loader2 size={16} className="comparison-spin" /> : <Lightbulb size={16} />}{busy ? 'Đang chọn gợi ý…' : result ? 'Xem lại gợi ý' : 'Gợi ý ý tưởng'}</button></div>
    {result?.question_id === questionId && <ul>{result.ideas.map(idea => <li key={idea.id}><strong>{idea.title}</strong><p>{idea.hint}</p></li>)}</ul>}
    {error && <p className="form-error" role="alert">{error}</p>}
  </aside>
}

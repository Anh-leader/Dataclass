import { useCallback, useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { assignmentApi } from '../services/api'
import type { Assignment } from '../types'
import PageContainer from '../components/layout/PageContainer'
import LoadingState from '../components/ui/LoadingState'
import TeacherAssignment from '../components/assignments/TeacherAssignment'
import StudentAssignment from '../components/assignments/StudentAssignment'
import { useAuth } from '../context/AuthContext'

export default function AssignmentPage() {
  const { id = '' } = useParams()
  const { notify } = useAuth()
  const [assignment, setAssignment] = useState<Assignment | null>(null)
  const [error, setError] = useState('')

  const load = useCallback(() => assignmentApi.get(id).then(data => { setAssignment(data); setError('') }).catch(e => setError(e.message)), [id])
  useEffect(() => { setError(''); load() }, [load])
  useEffect(() => {
    if (!assignment) return
    const delay = [assignment.due_at, assignment.sharing_open_at].map(value => new Date(value).getTime() - Date.now()).filter(value => value > 0).sort((a, b) => a - b)[0]
    if (delay === undefined || delay > 2147480000) return
    const timer = window.setTimeout(load, delay + 200)
    return () => window.clearTimeout(timer)
  }, [assignment?.due_at, assignment?.sharing_open_at, load])

  if (error) return <PageContainer><div className="form-error">{error}</div></PageContainer>
  if (!assignment || String(assignment.id) !== id) return <PageContainer><LoadingState text="Đang mở bài tập…" /></PageContainer>

  return assignment.is_teacher
    ? <TeacherAssignment assignment={assignment} notify={notify} onRefresh={load} />
    : <StudentAssignment assignment={assignment} notify={notify} onRefresh={load} />
}

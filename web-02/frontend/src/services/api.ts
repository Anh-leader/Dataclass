import { api, post, put, del, initializeCsrf, setCsrf, pollJob } from '../api'
import type { Assignment, ClassItem, DashboardStats, GalleryItem, SubmissionView, User } from '../types'

export const authApi = {
  csrf: initializeCsrf,
  me: () => api<{ user: User }>('/auth/me'),
  login: (payload: Record<string, string>) => post<{ user: User; csrf_token: string }>('/auth/login', payload),
  register: (payload: Record<string, string>) => post<{ user: User; csrf_token: string }>('/auth/register', payload),
  logout: () => post('/auth/logout'),
}

export const classApi = {
  list: () => api<ClassItem[]>('/classes'),
  create: (name: string) => post<ClassItem>('/classes', { name }),
  join: (code: string) => post<ClassItem>('/classes/join', { code }),
  get: (id: string | number) => api<{ id: number; name: string; join_code?: string; assignments: Assignment[] }>(`/classes/${id}`),
}

export const dashboardApi = {
  get: () => api<DashboardStats>('/dashboard'),
}

export const assignmentApi = {
  get: (id: string | number) => api<Assignment>(`/assignments/${id}`),
  create: (classId: number, payload: unknown) => post<Assignment>(`/classes/${classId}/assignments`, payload),
  updateQuestions: (id: number, questions: unknown[]) => put(`/assignments/${id}/questions`, { questions }),
  updateSettings: (id: number, payload: unknown) => put(`/assignments/${id}/settings`, payload),
  publish: (id: number) => post(`/assignments/${id}/publish`),
  generateExam: (id: number, payload: unknown) => post<{ job_id: number; status: string }>(`/assignments/${id}/ai/generate-exam`, payload),
  applyExam: (id: number, payload: unknown) => post<Assignment>(`/assignments/${id}/ai/apply-exam`, payload),
  uploadDatasets: (id: number, files: File[]) => {
    const form = new FormData()
    files.forEach(file => form.append('files', file))
    return post(`/assignments/${id}/datasets`, form)
  },
  previewDataset: (assignmentId: number, datasetId: string) => api<{ columns: string[]; rows: Record<string, unknown>[] }>(`/assignments/${assignmentId}/datasets/${datasetId}/preview`),
  saveAnswers: (id: number, answers: unknown[]) => put(`/assignments/${id}/answers`, { answers }),
  submit: (id: number, reflection = '') => post<{ version_number: number; job_id: number; is_improvement: boolean }>(`/assignments/${id}/submit`, { reflection }),
  reviewDraft: (id: number) => post<{ job_id: number }>(`/assignments/${id}/ai/review`),
  aiChat: (id: number, question: string, questionId: number | null) => post<{ job_id: number }>(`/assignments/${id}/ai/chat`, { question, question_id: questionId }),
  questionHints: (id: number, questionId: number) => post<{ job_id: number }>(`/assignments/${id}/questions/${questionId}/hints`),
  aiHistory: (id: number) => api<{ question: string; answer: string; question_id: number | null; question_order: number | null }[]>(`/assignments/${id}/ai/history`),
  submissions: (id: number) => api<SubmissionView[]>(`/assignments/${id}/submissions`),
  saveReference: (id: number, answers: unknown[], note: string) => put(`/assignments/${id}/reference`, { answers, note }),
  publishReference: (id: number, published: boolean) => post(`/assignments/${id}/reference/publish`, { published }),
  getReference: (id: number) => api<{ reference: unknown; can_view: boolean }>(`/assignments/${id}/reference`),
}

export const submissionApi = {
  grade: (id: number, payload: unknown) => post<{ grade: unknown; published: boolean }>(`/submissions/${id}/grade`, payload),
  share: (id: number, shared: boolean) => post<{ shared: boolean }>(`/submissions/${id}/share`, { shared }),
  comments: (id: number, body: string) => post(`/submissions/${id}/comments`, { body }),
  vote: (id: number, voted: boolean) => put<{ voted: boolean; vote_count: number }>(`/submissions/${id}/vote`, { voted }),
  peerReview: (id: number, payload: unknown) => put(`/submissions/${id}/peer-reviews`, payload),
  retryAIReview: (id: number, versionId: number) => post<{ job_id: number; status: string }>(`/submissions/${id}/ai/review`, { version_id: versionId }),
}

export const galleryApi = {
  list: (classId: string | number) => api<GalleryItem[]>(`/classes/${classId}/gallery`),
}

export const commentApi = {
  remove: (commentId: number) => del(`/comments/${commentId}`),
}

export { pollJob, setCsrf }

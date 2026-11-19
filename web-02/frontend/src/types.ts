export type UserRole = 'teacher' | 'student'

export interface User {
  id: number
  email: string
  full_name: string
  role: UserRole
}

export interface ClassItem {
  id: number
  name: string
  join_code?: string
  assignment_count: number
  teacher_name: string
  student_count?: number
}

export interface Question {
  id: number
  assignment_id: number
  question_order: number
  question_text: string
  max_score: number
}

export interface Answer {
  question_id: number
  answer_markdown: string
  artifacts: { id: string; name: string; media_type: string; url: string }[]
  updated_at: string
}

export interface Reference {
  published: boolean
  answers: { question_id: number; question_order: number; answer_markdown: string; artifact_ids: string[] }[]
  artifacts: unknown[]
  note: string
}

export interface DatasetItem {
  id: string
  name: string
  size: number
}

export interface SubmissionAnswerView {
  question_id: number
  answer_markdown: string
  artifacts: { id: string; name: string; media_type: string; url: string }[]
  updated_at: string
}

export interface ReviewView {
  checks: {
    question_id?: number
    question_order?: number
    criterion_id?: string
    title?: string
    status: string
    feedback?: string
    hint?: string
    suggestion?: string
  }[]
  overall?: { feedback?: string; suggestion?: string; quality?: 'good' | 'partial' | 'needs_work' | 'insufficient_evidence' }
}

export interface SubmissionVersionView {
  id: number
  version_number: number
  body_markdown: string
  submitted_at: string
  review: ReviewView | null
  answers_snapshot: SubmissionAnswerView[]
  is_improvement: boolean
  reflection: string
  review_status: 'none' | 'queued' | 'running' | 'done' | 'failed'
  review_job_id: number | null
  grade: GradeView | null
  grade_published: boolean
  teacher_comment: string | null
  peer_reviews: PeerReviewView[]
}

export interface GradeView {
  total: number
  max_score: number
  criteria?: { criterion_id: string; title: string; score: number; max_points: number }[]
  per_question?: { question_id: number; question_order: number; score: number; max_score: number; feedback: string }[]
}

export interface SubmissionView {
  id: number
  student?: string
  email?: string
  student_id?: number
  draft_markdown: string
  shared: boolean
  grade: GradeView | null
  grade_published: boolean
  teacher_comment: string | null
  answers: SubmissionAnswerView[]
  versions: SubmissionVersionView[]
}

export interface Assignment {
  id: number
  classroom_id: number
  classroom_name: string
  title: string
  description: string
  due_at: string
  sharing_open_at: string
  sharing_open: boolean
  share_mode: 'all' | 'opt_in'
  allow_improvements: boolean
  can_edit: boolean
  status: string
  rubric: { id: string; title: string; description: string; hint?: string; max_points: number }[]
  datasets: DatasetItem[]
  is_teacher: boolean
  questions: Question[]
  answer_key?: string
  generation_job?: { id: number; status: string } | null
  reference?: Reference
  submission?: SubmissionView
}

export interface GeneratedExam {
  questions: { question_order: number; question_text: string; max_score: number; answer_markdown: string }[]
  note: string
  evidence: string
  applied_at?: string
}

export interface DashboardStats {
  role: UserRole
  class_count: number
  open_assignments: number
  pending_grades?: number
  my_submissions?: number
  total_students: number
  recent_classes: ClassItem[]
}

export interface ChatMessage {
  role: 'student' | 'ai'
  text: string
  questionOrder?: number
}

export type ReferenceState = 'loading' | 'ok' | 'hidden' | 'not_published' | 'not_submitted'

export interface PeerReviewView {
  id: number
  version_id?: number
  reviewer_id?: number
  reviewer: string
  rating: number
  strengths: string
  suggestions: string
  learned: string
  is_mine?: boolean
  updated_at?: string
}

export interface GalleryVersion {
  id: number
  version_number: number
  body_markdown: string
  submitted_at: string
  is_improvement: boolean
  reflection: string
  peer_reviews: PeerReviewView[]
}

export interface GalleryItem {
  vote_count: number
  has_voted: boolean
  submission_id: number
  assignment_id: number
  assignment_title: string
  student_id: number
  student: string
  is_mine: boolean
  can_review: boolean
  body_markdown: string
  version_number: number
  version_id: number
  versions: GalleryVersion[]
  my_body_markdown: string | null
  my_version_number: number | null
  comments: { id: number; author: string; author_id: number; body: string; created_at: string }[]
}

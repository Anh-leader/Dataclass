import type { ReactNode } from 'react'

interface BadgeProps {
  status: string
  label?: string
  children?: ReactNode
}

const LABELS: Record<string, string> = {
  published: 'Đã công bố',
  draft: 'Bản nháp',
  active: 'Đang hoạt động',
}

export default function Badge({ status, label, children }: BadgeProps) {
  return <span className={`status-pill ${status}`}>{label ?? LABELS[status] ?? children}</span>
}

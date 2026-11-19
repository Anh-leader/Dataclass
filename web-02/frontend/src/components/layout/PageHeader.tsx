import type { ReactNode } from 'react'

interface PageHeaderProps {
  eyebrow?: string
  title: ReactNode
  subtitle?: string
  action?: ReactNode
}

export default function PageHeader({ eyebrow, title, subtitle, action }: PageHeaderProps) {
  return (
    <div className="page-header">
      <div>
        {eyebrow && <div className="page-eyebrow">{eyebrow}</div>}
        <h1>{title}</h1>
        {subtitle && <p>{subtitle}</p>}
      </div>
      {action}
    </div>
  )
}

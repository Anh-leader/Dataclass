import type { ReactNode } from 'react'

interface CardProps {
  className?: string
  children: ReactNode
}

export default function Card({ className = '', children }: CardProps) {
  return <section className={`panel ${className}`.trim()}>{children}</section>
}

export function PanelHeading({ eyebrow, title, action }: { eyebrow?: string; title: ReactNode; action?: ReactNode }) {
  return (
    <div className="panel-heading">
      <div>
        {eyebrow && <span className="page-eyebrow">{eyebrow}</span>}
        <h2>{title}</h2>
      </div>
      {action}
    </div>
  )
}

import type { ReactNode } from 'react'

export default function PageContainer({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <div className={`content-page ${className}`}>{children}</div>
}

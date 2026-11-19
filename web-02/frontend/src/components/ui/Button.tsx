import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Variant = 'primary' | 'ghost' | 'danger' | 'shared'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  wide?: boolean
  children: ReactNode
}

export default function Button({ variant = 'primary', wide = false, className = '', children, ...rest }: ButtonProps) {
  const variantClass = variant === 'primary' ? 'button-primary' : variant === 'ghost' ? 'button-ghost' : variant === 'danger' ? 'button-danger' : 'button-shared'
  return <button className={`button ${variantClass} ${wide ? 'button-wide' : ''} ${className}`.trim()} {...rest}>{children}</button>
}

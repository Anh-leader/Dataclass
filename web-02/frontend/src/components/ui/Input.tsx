import type { InputHTMLAttributes, TextareaHTMLAttributes, ReactNode } from 'react'

interface FieldProps {
  label: string
  children: ReactNode
  optional?: string
}

export function Field({ label, optional, children }: FieldProps) {
  return (
    <label className="stack-field">
      <span className="stack-label">{label}{optional && <span className="optional">{optional}</span>}</span>
      {children}
    </label>
  )
}

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {}

export function Input({ className = '', ...rest }: InputProps) {
  return <input className={`input-control ${className}`.trim()} {...rest} />
}

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {}

export function Textarea({ className = '', ...rest }: TextareaProps) {
  return <textarea className={`input-control textarea-control ${className}`.trim()} {...rest} />
}

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  children: ReactNode
}

export function Select({ className = '', children, ...rest }: SelectProps) {
  return <select className={`select-control ${className}`.trim()} {...rest}>{children}</select>
}

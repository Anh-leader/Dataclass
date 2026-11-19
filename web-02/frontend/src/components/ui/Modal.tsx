import type { ReactNode } from 'react'
import { X } from 'lucide-react'

interface ModalProps {
  children: ReactNode
  close: () => void
  wide?: boolean
}

export default function Modal({ children, close, wide = false }: ModalProps) {
  return (
    <div className="modal-backdrop" onMouseDown={e => e.target === e.currentTarget && close()}>
      <div className={`modal-card ${wide ? 'modal-wide' : ''}`}>
        <button className="modal-close" onClick={close} aria-label="Đóng"><X size={19} /></button>
        {children}
      </div>
    </div>
  )
}

import { useState, type FormEvent } from 'react'
import { ArrowRight, Check, Users } from 'lucide-react'
import { classApi } from '../../services/api'
import Modal from '../ui/Modal'

interface ClassModalProps {
  mode: 'create' | 'join'
  close: () => void
  done: () => void
}

export default function ClassModal({ mode, close, done }: ClassModalProps) {
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [created, setCreated] = useState<{ id: number; name: string; join_code?: string } | null>(null)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setError('')
    const data = new FormData(event.currentTarget)
    try {
      if (mode === 'create') {
        const result = await classApi.create(String(data.get('name') || ''))
        setCreated(result)
      } else {
        await classApi.join(String(data.get('code') || ''))
        done()
      }
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal close={close}>
      <div className="modal-heading">
        <span className="modal-icon"><Users size={20} /></span>
        <div>
          <h2>{created ? 'Lớp học đã sẵn sàng' : mode === 'create' ? 'Tạo lớp học' : 'Tham gia lớp học'}</h2>
          <p>{created ? 'Chia sẻ mã này với sinh viên của bạn.' : mode === 'create' ? 'Tạo một không gian cho lớp của bạn.' : 'Nhập mã tham gia do giáo viên cung cấp.'}</p>
        </div>
      </div>
      {created ? (
        <>
          <div className="join-code-large">{created.join_code}</div>
          <div className="modal-actions"><button className="button button-primary" onClick={done}>Hoàn tất <Check size={16} /></button></div>
        </>
      ) : (
        <form onSubmit={submit} className="stack-form">
          {mode === 'create'
            ? <label>Tên lớp<input name="name" placeholder="Ví dụ: Phân tích dữ liệu — Kỳ 1" required /></label>
            : <label>Mã tham gia<input name="code" placeholder="Nhập mã 10 ký tự" required autoCapitalize="characters" /></label>}
          {error && <div className="form-error">{error}</div>}
          <div className="modal-actions">
            <button type="button" className="button button-ghost" onClick={close}>Hủy</button>
            <button disabled={busy} className="button button-primary">{busy ? 'Đang xử lý…' : mode === 'create' ? 'Tạo lớp' : 'Tham gia'}<ArrowRight size={16} /></button>
          </div>
        </form>
      )}
    </Modal>
  )
}

import { FileSpreadsheet } from 'lucide-react'
import Modal from '../ui/Modal'

interface DataPreviewProps {
  title: string
  data: { columns: string[]; rows: Record<string, unknown>[] }
  close: () => void
}

export default function DataPreview({ title, data, close }: DataPreviewProps) {
  const columns = data?.columns || []
  const rows = data?.rows || []
  return (
    <Modal close={close} wide>
      <div className="modal-heading">
        <span className="modal-icon"><FileSpreadsheet size={20} /></span>
        <div>
          <div className="page-eyebrow">XEM TRƯỚC DATASET</div>
          <h2>{title}</h2>
          <p>{columns.length} cột · Hiển thị {rows.length} dòng đầu</p>
        </div>
      </div>
      <div className="table-scroll">
        <table>
          <thead><tr>{columns.map(c => <th key={c}>{c}</th>)}</tr></thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i}>{columns.map(c => <td key={c}>{String(row[c] ?? '—')}</td>)}</tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="modal-actions"><button className="button button-primary" onClick={close}>Đóng</button></div>
    </Modal>
  )
}

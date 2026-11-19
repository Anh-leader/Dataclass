import { Link } from 'react-router-dom'
import { ArrowRight, BarChart3, BookOpen, FileSpreadsheet } from 'lucide-react'
import type { ClassItem } from '../../types'

export default function ClassCard({ item, index }: { item: ClassItem; index: number }) {
  return (
    <Link to={`/classes/${item.id}`} className={`class-card class-tone-${index % 3}`}>
      <div className="class-card-top">
        <div className="class-icon"><BookOpen size={19} /></div>
        <span className="class-live"><i />ĐANG HỌC</span>
      </div>
      <h3>{item.name}</h3>
      <p>{item.teacher_name}</p>
      <div className="class-card-foot">
        <span><FileSpreadsheet size={15} />{item.assignment_count} bài tập</span>
        <span className="round-arrow"><ArrowRight size={16} /></span>
      </div>
      <div className="card-watermark"><BarChart3 size={75} /></div>
    </Link>
  )
}

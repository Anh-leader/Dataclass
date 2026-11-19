import { useEffect, useMemo, useState } from 'react'
import { ArrowRight, BookOpen, Plus, Users } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { classApi } from '../services/api'
import type { ClassItem } from '../types'
import ClassCard from '../components/classes/ClassCard'
import ClassModal from '../components/classes/ClassModal'
import EmptyState from '../components/ui/EmptyState'
import LoadingState from '../components/ui/LoadingState'
import PageContainer from '../components/layout/PageContainer'
import PageHeader from '../components/layout/PageHeader'

export default function ClassesPage() {
  const { user, notify } = useAuth()
  const [items, setItems] = useState<ClassItem[]>([])
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState<'create' | 'join' | null>(null)
  const [query, setQuery] = useState('')

  const load = () => classApi.list().then(setItems).catch(e => notify(e.message))
  useEffect(() => { load().finally(() => setLoading(false)) }, [])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return items
    return items.filter(item => item.name.toLowerCase().includes(q) || (item.join_code || '').toLowerCase().includes(q))
  }, [items, query])

  if (!user) return null

  return (
    <PageContainer>
      <PageHeader
        eyebrow="DANH SÁCH LỚP"
        title="Lớp học"
        subtitle="Nơi những câu hỏi hay gặp dữ liệu thật."
        action={user.role === 'teacher'
          ? <button className="button button-primary" onClick={() => setModal('create')}><Plus size={17} />Tạo lớp mới</button>
          : <button className="button button-primary" onClick={() => setModal('join')}><Plus size={17} />Tham gia lớp</button>}
      />
      {items.length > 0 && (
        <div className="toolbar">
          <div className="search-control">
            <span className="search-icon">⌕</span>
            <input
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Tìm theo tên lớp hoặc mã lớp..."
              aria-label="Tìm lớp học"
            />
          </div>
        </div>
      )}
      {loading ? (
        <LoadingState text="Đang tải lớp học…" />
      ) : filtered.length ? (
        <div className="class-grid class-grid-large">{filtered.map((item, i) => <ClassCard key={item.id} item={item} index={i} />)}</div>
      ) : items.length ? (
        <EmptyState icon={<Users />} title="Không tìm thấy lớp" text={`Không có lớp nào khớp với "${query}".`} />
      ) : (
        <EmptyState
          icon={<Users />}
          title={user.role === 'teacher' ? 'Bắt đầu với lớp đầu tiên' : 'Bạn chưa tham gia lớp nào'}
          text={user.role === 'teacher' ? 'Tạo lớp và mời sinh viên bằng mã tham gia.' : 'Nhập mã lớp giáo viên đã gửi để xem bài tập.'}
          action={<button className="button button-primary" onClick={() => setModal(user.role === 'teacher' ? 'create' : 'join')}>{user.role === 'teacher' ? 'Tạo lớp học' : 'Nhập mã lớp'}<ArrowRight size={16} /></button>}
        />
      )}
      {modal && <ClassModal mode={modal} close={() => setModal(null)} done={() => { setModal(null); load() }} />}
    </PageContainer>
  )
}

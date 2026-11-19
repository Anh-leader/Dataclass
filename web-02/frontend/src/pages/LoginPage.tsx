import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, BookOpen, Check, Eye, EyeOff, FileText, GraduationCap, Loader2, LockKeyhole, Mail, MessageCircle, Presentation, ShieldCheck, Sparkles, UserRound, Users } from 'lucide-react'
import { initializeCsrf, setCsrf } from '../api'
import { useAuth } from '../context/AuthContext'
import { authApi } from '../services/api'
import Brand from '../components/layout/Brand'

export default function LoginPage() {
  const [register, setRegister] = useState(false)
  const [registerRole, setRegisterRole] = useState<'student' | 'teacher'>('student')
  const [showPassword, setShowPassword] = useState(false)
  const [busy, setBusy] = useState(false)
  const [csrfReady, setCsrfReady] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const { login } = useAuth()

  useEffect(() => {
    initializeCsrf().then(() => setCsrfReady(true))
      .catch(() => setError('Không thể kết nối máy chủ. Hãy tải lại trang.'))
  }, [])

  function changeMode(next: boolean) {
    if (busy) return
    setRegister(next); setError(''); setShowPassword(false)
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (busy || !csrfReady) return
    setError(''); setBusy(true)
    const payload = Object.fromEntries(new FormData(event.currentTarget).entries()) as Record<string, string>
    try {
      const result = register ? await authApi.register(payload) : await authApi.login(payload)
      setCsrf(result.csrf_token)
      login(result.user)
      navigate('/')
    } catch (e) { setError((e as Error).message) } finally { setBusy(false) }
  }

  return <div className="auth-page auth-unified">
    <aside className="auth-story">
      <Brand to="/login" />
      <div className="auth-story-copy">
        <span className="auth-story-eyebrow"><span />HỌC HỎI TỪ MỖI GÓC NHÌN</span>
        <h1>Từ một câu hỏi,<br />mở ra <span>nhiều khám phá.</span></h1>
        <p>Một không gian để phân tích dữ liệu, chia sẻ cách nghĩ và cùng nhau tiến bộ mỗi ngày.</p>
        <div className="auth-product-preview">
          <div className="auth-preview-header"><span className="auth-preview-icon"><BookOpen size={20} /></span><div><strong>Hành trình học tập của bạn</strong><small>Bắt đầu từ sự tò mò</small></div><span className="auth-preview-spark"><Sparkles size={17} /></span></div>
          <div className="auth-preview-paper"><div className="auth-paper-label"><FileText size={14} /><span>Khám phá dữ liệu theo cách của bạn</span></div><div className="auth-preview-chart" aria-hidden="true"><span style={{height:'38%'}} /><span style={{height:'60%'}} /><span style={{height:'48%'}} /><span style={{height:'82%'}} /><span style={{height:'67%'}} /><span style={{height:'95%'}} /></div><div className="auth-paper-footer"><span><span />Đặt câu hỏi</span><span><span />Tìm bằng chứng</span><span><span />Tự kết luận</span></div></div>
          <div className="auth-preview-note"><span><Sparkles size={16} /></span><p>AI gợi mở hướng tư duy.<br /><strong>Bạn là người tạo nên lời giải.</strong></p><Check size={16} /></div>
        </div>
        <div className="auth-story-features"><span><FileText size={15} />Tự phân tích</span><span><Users size={15} />Cùng trao đổi</span><span><Sparkles size={15} />Từng bước tốt hơn</span></div>
      </div>
      <p className="auth-story-footer">Một lớp học. Nhiều góc nhìn. Vô vàn khám phá.</p>
    </aside>
    <main className="auth-entry">
      <div className="auth-entry-inner">
        <div className="auth-mobile-brand"><Brand to="/login" /></div>
        <div className="auth-mode-switch" role="group" aria-label="Chọn đăng nhập hoặc đăng ký"><button type="button" aria-label="Chuyển sang đăng nhập" aria-pressed={!register} className={!register ? 'active' : ''} disabled={busy} onClick={() => changeMode(false)}>Đăng nhập</button><button type="button" aria-label="Chuyển sang đăng ký" aria-pressed={register} className={register ? 'active' : ''} disabled={busy} onClick={() => changeMode(true)}>Đăng ký</button></div>
        <div className="auth-entry-heading"><span className="auth-heading-icon">{register ? <GraduationCap size={23} /> : <BookOpen size={23} />}</span><span className="auth-entry-kicker">{register ? 'MỘT KHỞI ĐẦU MỚI' : 'CHÀO MỪNG TRỞ LẠI'}</span><h2>{register ? 'Bắt đầu cùng DataClass' : 'Tiếp tục hành trình của bạn'}</h2><p>{register ? 'Tạo tài khoản để kết nối với lớp học và khám phá dữ liệu.' : 'Đăng nhập để trở lại lớp học và những khám phá đang chờ.'}</p></div>
        <form key={register ? 'register' : 'login'} onSubmit={submit} className="auth-entry-form" aria-label={register ? 'Đăng ký tài khoản' : 'Đăng nhập tài khoản'}>
          {register && <div className="auth-field"><label htmlFor="auth-full-name">Họ và tên</label><div className="auth-input-shell"><UserRound size={17} aria-hidden="true" /><input id="auth-full-name" name="full_name" placeholder="Nguyễn Minh Anh" autoComplete="name" required minLength={2} maxLength={120} disabled={busy} /></div></div>}
          <div className="auth-field"><label htmlFor="auth-email">Email</label><div className="auth-input-shell"><Mail size={17} aria-hidden="true" /><input id="auth-email" type="email" name="email" placeholder="ban@truong.edu.vn" autoComplete="email" autoCapitalize="none" spellCheck={false} required maxLength={254} disabled={busy} /></div></div>
          <div className="auth-field"><label htmlFor="auth-password">Mật khẩu</label><div className="auth-input-shell"><LockKeyhole size={17} aria-hidden="true" /><input id="auth-password" type={showPassword ? 'text' : 'password'} name="password" placeholder={register ? 'Tạo mật khẩu của bạn' : 'Nhập mật khẩu của bạn'} autoComplete={register ? 'new-password' : 'current-password'} required minLength={register ? 10 : 1} maxLength={128} disabled={busy} aria-describedby={register ? 'auth-password-hint' : undefined} /><button type="button" className="auth-password-toggle" aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'} aria-pressed={showPassword} onClick={() => setShowPassword(value => !value)}>{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button></div>{register && <small id="auth-password-hint">Sử dụng từ 10 đến 128 ký tự cho mật khẩu.</small>}</div>
          {register && <fieldset className="auth-role-picker"><legend>Bạn tham gia với vai trò</legend><div className="auth-role-options"><label className={registerRole === 'student' ? 'active' : ''}><input type="radio" name="role" value="student" aria-label="Sinh viên" checked={registerRole === 'student'} disabled={busy} onChange={() => setRegisterRole('student')} /><span className="auth-role-icon"><GraduationCap size={20} /></span><span><strong>Sinh viên</strong><small>Tham gia và làm bài</small></span><span className="auth-role-check">{registerRole === 'student' && <Check size={11} />}</span></label><label className={registerRole === 'teacher' ? 'active' : ''}><input type="radio" name="role" value="teacher" aria-label="Giáo viên" checked={registerRole === 'teacher'} disabled={busy} onChange={() => setRegisterRole('teacher')} /><span className="auth-role-icon"><Presentation size={20} /></span><span><strong>Giáo viên</strong><small>Tạo lớp và hướng dẫn</small></span><span className="auth-role-check">{registerRole === 'teacher' && <Check size={11} />}</span></label></div></fieldset>}
          {error && <div className="form-error" role="alert">{error}</div>}
          <button className="button button-primary auth-submit" disabled={busy || !csrfReady}>{busy ? <Loader2 size={17} className="comparison-spin" /> : null}<span>{busy ? 'Đang xử lý…' : !csrfReady ? 'Đang kết nối…' : register ? 'Tạo tài khoản' : 'Đăng nhập'}</span>{!busy && <ArrowRight size={17} />}</button>
        </form>
        <p className="auth-entry-switch">{register ? 'Bạn đã có tài khoản?' : 'Chưa có tài khoản?'} <button type="button" disabled={busy} onClick={() => changeMode(!register)}>{register ? 'Đăng nhập ngay' : 'Đăng ký ngay'}<ArrowRight size={13} /></button></p>
        <div className="auth-entry-footer"><ShieldCheck size={16} /><span>Không gian học tập riêng cho từng lớp học</span></div>
      </div>
      <span className="auth-entry-caption"><MessageCircle size={13} />Học từ dữ liệu. Tiến bộ cùng nhau.</span>
    </main>
  </div>
}


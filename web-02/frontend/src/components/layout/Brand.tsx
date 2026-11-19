import { Link } from 'react-router-dom'

export default function Brand({ to = '/' }: { to?: string }) {
  return (
    <Link to={to} className="brand">
      <span className="brand-mark">D</span>
      <span>data<span className="brand-light">class</span><small>LEARN BY ANALYZING</small></span>
    </Link>
  )
}

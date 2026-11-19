export default function StudentAvatar({ name, seed = 0, small = false }: { name: string; seed?: number; small?: boolean }) {
  const initials = name.replace(/\s*\([^)]*\)\s*$/, '').trim().split(/\s+/).slice(-2).map(word => Array.from(word)[0]).join('').toLocaleUpperCase('vi')
  return <span className={`student-avatar avatar-tone-${seed % 6} ${small ? 'student-avatar-small' : ''}`} aria-hidden="true">{initials}</span>
}

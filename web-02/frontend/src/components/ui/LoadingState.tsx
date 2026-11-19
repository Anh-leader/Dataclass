export default function LoadingState({ text = 'Đang tải…' }: { text?: string }) {
  return <div className="loading-card">{text}</div>
}

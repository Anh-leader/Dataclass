let csrf = ''

export async function initializeCsrf() {
  const response = await fetch('/api/auth/csrf', { credentials: 'include' })
  const data = await response.json()
  csrf = data.csrf_token
}

export function setCsrf(value: string) { csrf = value }

export async function api<T = any>(path: string, options: RequestInit = {}): Promise<T> {
  const method = (options.method || 'GET').toUpperCase()
  const headers = new Headers(options.headers || {})
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) headers.set('X-CSRF-Token', csrf)
  const response = await fetch(path.startsWith('/api') ? path : `/api${path}`, { ...options, method, headers, credentials: 'include' })
  const contentType = response.headers.get('content-type') || ''
  const data = contentType.includes('application/json') ? await response.json() : null
  if (!response.ok) throw new Error(data?.detail || `Yêu cầu thất bại (${response.status})`)
  return data as T
}

export function post<T = any>(path: string, body?: unknown): Promise<T> {
  return api<T>(path, { method: 'POST', body: body instanceof FormData ? body : JSON.stringify(body || {}) })
}
export const put = <T = any>(path: string, body: unknown): Promise<T> => api<T>(path, { method: 'PUT', body: JSON.stringify(body) })
export const del = (path: string) => api(path, { method: 'DELETE' })

export async function pollJob<T = any>(id: number, onStatus?: (status: string) => void): Promise<T> {
  for (let i = 0; i < 240; i++) {
    const job = await api<any>(`/jobs/${id}`)
    onStatus?.(job.status)
    if (job.status === 'done') return job.result as T
    if (job.status === 'failed') throw new Error(job.error || 'Tác vụ AI thất bại.')
    await new Promise(resolve => setTimeout(resolve, i < 12 ? 1000 : 2500))
  }
  throw new Error('Tác vụ AI đang chạy lâu hơn dự kiến. Bạn có thể mở lại trang sau.')
}

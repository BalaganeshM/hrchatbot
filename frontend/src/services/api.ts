const BASE = 'http://44.192.6.64:8000'

async function request(path: string, options: RequestInit = {}) {
  const token = localStorage.getItem('token')
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${BASE}${path}`, { ...options, headers })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(err || `HTTP ${res.status}`)
  }
  const ct = res.headers.get('content-type')
  if (ct && ct.includes('application/json')) return res.json()
  return res.text()
}

export const api = {
  // Auth
  login: (email: string, password: string) =>
    request('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  register: (data: any) =>
    request('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  getMe: () => request('/auth/me'),

  // Employees
  listEmployees: (departmentId?: string) =>
    request(`/employees/${departmentId ? `?department_id=${departmentId}` : ''}`),
  getEmployee: (id: string) => request(`/employees/${id}`),
  createEmployee: (data: any) =>
    request('/employees/', { method: 'POST', body: JSON.stringify(data) }),
  updateEmployee: (id: string, data: any) =>
    request(`/employees/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteEmployee: (id: string) =>
    request(`/employees/${id}`, { method: 'DELETE' }),

  // Org
  getOrgStructure: () => request('/org/structure'),
  getTeam: (managerId: string) => request(`/org/team/${managerId}`),
  getManagers: () => request('/org/managers'),
  getMyChain: () => request('/org/my-chain'),

  // Chat
  ask: (message: string, session_id?: string) =>
    request('/chat/ask', { method: 'POST', body: JSON.stringify({ message, session_id }) }),

  askStream: (
    message: string,
    session_id: string | undefined,
    onToken: (token: string) => void,
    onDone: () => void,
    onError: (err: Error) => void,
    signal?: AbortSignal,
  ) => {
    const token = localStorage.getItem('token')
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    if (token) headers['Authorization'] = `Bearer ${token}`

    fetch(`${BASE}/chat/ask`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ message, session_id }),
      signal,
    })
      .then(async (res) => {
        if (!res.ok) {
          const err = await res.text()
          throw new Error(err || `HTTP ${res.status}`)
        }
        const reader = res.body!.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6)
              if (data === '[DONE]') {
                onDone()
                return
              }
              try {
                const parsed = JSON.parse(data)
                if (parsed.token) onToken(parsed.token)
                if (parsed.error) {
                  onError(new Error(parsed.error))
                  return
                }
              } catch {
                /* ignore partial parse */
              }
            }
          }
        }
        onDone()
      })
      .catch((err) => onError(err instanceof Error ? err : new Error(String(err))))
  },
}

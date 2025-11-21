export async function apiFetch(path: string, opts?: RequestInit) {
  const url = path.startsWith('/') ? `/api/py${path}` : `/api/py/${path}`
  const res = await fetch(url, opts)
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res
}

const BASE_URL = import.meta.env.DEV
  ? 'http://localhost:8000'
  : window.location.origin

async function request(method, path, body = null) {
  const options = {
    method,
    headers: {
      'Content-Type': 'application/json',
    },
  }
  if (body) {
    options.body = JSON.stringify(body)
  }

  const res = await fetch(`${BASE_URL}${path}`, options)

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Ein Fehler ist aufgetreten.' }))
    throw new Error(error.detail || `HTTP ${res.status}`)
  }

  return res.json()
}

export function startScan(domain) {
  return request('POST', '/api/scan', { domain })
}

export function getScanResult(scanId) {
  return request('GET', `/api/scan/${scanId}`)
}

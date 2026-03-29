const BASE_URL = import.meta.env.DEV
  ? 'http://localhost:8000'
  : window.location.origin

function getAuthHeaders() {
  const token = localStorage.getItem('agentcheck_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request(method, path, body = null) {
  const options = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
  }
  if (body) {
    options.body = JSON.stringify(body)
  }

  const res = await fetch(`${BASE_URL}${path}`, options)

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'An error occurred.' }))
    throw new Error(error.detail || `HTTP ${res.status}`)
  }

  return res.json()
}

export function startScan(domain) {
  return request('POST', '/api/scan', { domain })
}

export async function getScanResult(scanId) {
  const raw = await request('GET', `/api/scan/${scanId}`)

  // Normalize: backend nests data under `report`, flatten for frontend
  const report = raw.report || {}
  return {
    scan_id: raw.scan_id,
    status: raw.status,
    domain: raw.domain,
    score: raw.total_score ?? report.total_score ?? 0,
    grade: raw.grade ?? report.grade ?? '',
    categories: report.categories || {},
    checks: report.checks || [],
    fixes: report.top_fixes || [],
    error: raw.error,
  }
}

// Auth
export function registerUser(email, password) {
  return request('POST', '/api/auth/register', { email, password })
}

export function loginUser(email, password) {
  return request('POST', '/api/auth/login', { email, password })
}

export function getMe() {
  return request('GET', '/api/auth/me')
}

// Checkout
export function createCheckoutSession(priceType, scanId) {
  return request('POST', '/api/checkout/session', { price_type: priceType, scan_id: scanId })
}

// Scan access
export function getScanAccess(scanId) {
  return request('GET', `/api/scan/${scanId}/access`)
}

// Fix files download (returns blob)
export async function downloadFixFiles(scanId) {
  const res = await fetch(`${BASE_URL}/api/scan/${scanId}/fixes/download`, {
    headers: { ...getAuthHeaders() },
  })
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Download failed.' }))
    throw new Error(error.detail || `HTTP ${res.status}`)
  }
  return res.blob()
}

// Delete scan
export function deleteScan(scanId) {
  return request('DELETE', `/api/scan/${scanId}`)
}

// User scans
export function getUserScans() {
  return request('GET', '/api/user/scans')
}

// Monitoring
export function getMonitors() {
  return request('GET', '/api/monitoring')
}

export function addMonitor(domain) {
  return request('POST', '/api/monitoring', { domain })
}

export function removeMonitor(id) {
  return request('DELETE', `/api/monitoring/${id}`)
}

// Compare
export function compareDomains(domains) {
  return request('POST', '/api/compare', { domains })
}

// History
export function getScoreHistory(domain) {
  return request('GET', `/api/history/${encodeURIComponent(domain)}`)
}

// Billing portal
export function createBillingPortal() {
  return request('POST', '/api/billing/portal')
}

// AI Insights
export function getScanInsights(scanId) {
  return request('GET', `/api/scan/${scanId}/insights`)
}

// AI Discovery
export function runDiscoveryTest(scanId) {
  return request('POST', `/api/scan/${scanId}/discovery`)
}

export function quickDiscovery(domain) {
  return request('POST', '/api/discovery/quick', { domain })
}

// Hosted Files
export function activateHostedFiles(domain, scanId) {
  return request('POST', '/api/hosted-files/activate', { domain, scan_id: scanId })
}
export function getHostedFiles() {
  return request('GET', '/api/hosted-files')
}

// Crawler Pings
export function pingCrawlers() {
  return request('POST', '/api/crawler-ping')
}
export function getPingHistory() {
  return request('GET', '/api/crawler-ping/history')
}

// Mention Tracking
export function getMentions(domain) {
  return request('GET', `/api/mentions/${encodeURIComponent(domain)}`)
}
export function trackMentions(domain) {
  return request('POST', `/api/mentions/${encodeURIComponent(domain)}/track`)
}

// Competitor Tracking
export function getCompetitors(domain) {
  return request('GET', `/api/competitors/${encodeURIComponent(domain)}`)
}
export function discoverCompetitors(domain) {
  return request('POST', `/api/competitors/${encodeURIComponent(domain)}/discover`)
}
export function scanCompetitors(domain) {
  return request('POST', `/api/competitors/${encodeURIComponent(domain)}/scan`)
}
export function removeCompetitor(domain, competitor) {
  return request('DELETE', `/api/competitors/${encodeURIComponent(domain)}/${encodeURIComponent(competitor)}`)
}

// Content Optimizer
export function optimizeContent(scanId) {
  return request('POST', `/api/content-optimize/${scanId}`)
}

// Agent Simulator
export function simulateAgent(scanId) {
  return request('POST', `/api/simulate/${scanId}`)
}

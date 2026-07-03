import axios from 'axios'

const http = axios.create({ baseURL: '/api', timeout: 20000 })

http.interceptors.response.use(
  (r) => r,
  (err) => {
    const detail = err?.response?.data?.detail
    const msg = Array.isArray(detail)
      ? detail.map((d) => d.msg).join('; ')
      : detail || err.message || '请求失败'
    window.__toast?.(msg, 'error')
    return Promise.reject(err)
  },
)

export const api = {
  // ── Tabs ──────────────────────────────────────────
  tabs:        ()           => http.get('/tabs').then((r) => r.data),
  createTab:   (data)       => http.post('/tabs', data).then((r) => r.data),
  updateTab:   (id, data)   => http.patch(`/tabs/${id}`, data).then((r) => r.data),
  deleteTab:   (id)         => http.delete(`/tabs/${id}`),
  reorderTabs: (items)      => http.post('/tabs/reorder', { items }),

  // ── Indicators ────────────────────────────────────
  indicators:        (tabId, since) => http.get(`/tabs/${tabId}/indicators`, { params: since ? { since } : {} }).then((r) => r.data),
  createIndicator:   (tabId, d)   => http.post(`/tabs/${tabId}/indicators`, d).then((r) => r.data),
  updateIndicator:   (id, d)      => http.patch(`/indicators/${id}`, d).then((r) => r.data),
  deleteIndicator:   (id)         => http.delete(`/indicators/${id}`),
  reorderIndicators: (items)      => http.post('/indicators/reorder', { items }),

  // ── Records ───────────────────────────────────────
  records:      (indicatorId)    => http.get(`/indicators/${indicatorId}/records`).then((r) => r.data),
  createRecord: (indicatorId, d) => http.post(`/indicators/${indicatorId}/records`, d).then((r) => r.data),
  updateRecord: (id, d)          => http.patch(`/records/${id}`, d).then((r) => r.data),
  deleteRecord: (id)             => http.delete(`/records/${id}`),
  sources:      ()               => http.get('/sources').then((r) => r.data),

  // ── Data ──────────────────────────────────────────
  exportCsv: () => http.get('/data/export', { responseType: 'blob' }).then((r) => r.data),
  importCsv: (file) => {
    const form = new FormData()
    form.append('file', file)
    return http.post('/data/import', form, { headers: { 'Content-Type': 'multipart/form-data' } }).then((r) => r.data)
  },
}

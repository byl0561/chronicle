import { reactive } from 'vue'
import { api } from './api.js'

// ── 全局 Tab 列表 ──────────────────────────────────────────────────────────
export const store = reactive({
  tabs: [],
  loaded: false,
})

export async function loadTabs() {
  store.tabs = await api.tabs()
  store.loaded = true
}

export async function reloadTabs() {
  store.tabs = await api.tabs()
}

// ── 确认对话框 ────────────────────────────────────────────────────────────
export const confirmState = reactive({
  open: false,
  title: '确认',
  message: '',
  confirmText: '确定',
  cancelText: '取消',
  danger: false,
  _resolve: null,
})

export function askConfirm(opts = {}) {
  return new Promise((resolve) => {
    Object.assign(confirmState, {
      open: true,
      title: opts.title || '确认',
      message: opts.message || '',
      confirmText: opts.confirmText || '确定',
      cancelText: opts.cancelText || '取消',
      danger: opts.danger ?? false,
      _resolve: resolve,
    })
  })
}

export function resolveConfirm(value) {
  if (!confirmState.open) return
  confirmState.open = false
  const done = confirmState._resolve
  confirmState._resolve = null
  done?.(value)
}

// ── 区间工具 ──────────────────────────────────────────────────────────────
// 记录的有效区间：记录自带优先，否则回退指标默认。参数可传记录或 { ref_low, ref_high }。
export function effectiveRef(rec, indicator) {
  const low  = rec?.ref_low  != null ? rec.ref_low  : indicator?.ref_low  ?? null
  const high = rec?.ref_high != null ? rec.ref_high : indicator?.ref_high ?? null
  return { low, high }
}

// 越界判定（按给定区间与方向）
function outOfRange(value, low, high, direction) {
  if (direction === 'lower')  return high != null && value > high
  if (direction === 'higher') return low  != null && value < low
  // range
  if (low  != null && value < low)  return true
  if (high != null && value > high) return true
  return false
}

// 归一化：把值映射到「正常区间 = [0,1]」的无量纲刻度，>1 超上限、<0 低于下限。
// 单边指标退化为 Multiple of ULN / LLN。无法归一化时返回 null。
export function normalize(value, low, high, direction) {
  if (direction === 'lower') {
    return high != null && high !== 0 ? value / high : null
  }
  if (direction === 'higher') {
    return low != null && low !== 0 ? value / low : null
  }
  // range：需要上下两界
  if (low != null && high != null && high > low) {
    return (value - low) / (high - low)
  }
  return null
}

// ── 状态判断工具 ──────────────────────────────────────────────────────────
export function calcStatus(indicator) {
  const { latest_value, direction } = indicator
  if (!latest_value) return 'nodata'
  const { low, high } = effectiveRef(latest_value, indicator)
  // 该方向下是否存在可用的参考界；都没有 → 无从判断正常/越界
  const judgeable =
    direction === 'lower'  ? high != null :
    direction === 'higher' ? low  != null :
    (low != null || high != null)
  if (!judgeable) return 'norange'
  return outOfRange(latest_value.value, low, high, direction) ? 'danger' : 'ok'
}

// 判断某条记录是否越界（用记录自己的区间，回退指标默认）
export function isRecordOutOfRange(rec, indicator) {
  const { low, high } = effectiveRef(rec, indicator)
  return outOfRange(rec.value, low, high, indicator.direction)
}

// 兼容旧签名：按指标默认区间判断一个裸值是否越界
export function isOutOfRange(value, indicator) {
  return outOfRange(value, indicator.ref_low, indicator.ref_high, indicator.direction)
}

export function statusLabel(status) {
  return { ok: '正常', danger: '越界', norange: '无区间', nodata: '暂无' }[status] ?? ''
}

// 状态对应的图形色（sparkline / 圆点等），与 CSS 状态色保持一致
export function statusColor(status) {
  return {
    ok: '#2D9E5F', danger: '#D63F3F', norange: '#3B5BDB', nodata: '#94A3B8',
  }[status] ?? '#2D9E5F'
}

export function directionLabel(direction) {
  return { range: '区间内正常', lower: '越低越好', higher: '越高越好' }[direction] ?? direction
}

// sparkline 取值序列：优先用逐点归一化值（跨医院/方法可比），
// 任一点无法归一化则整条回退原始值。返回 { nums, normalized }。
export function sparkSeries(indicator) {
  const tv = indicator.trend_values || []
  const normed = tv.map((p) => {
    const { low, high } = effectiveRef(p, indicator)
    return normalize(p.value, low, high, indicator.direction)
  })
  if (tv.length && normed.every((n) => n != null)) {
    return { nums: normed, normalized: true }
  }
  return { nums: tv.map((p) => p.value), normalized: false }
}

// 迷你 sparkline SVG polyline points 字符串（接收数值数组）
export function sparkPoints(nums, width = 100, height = 40) {
  if (!nums || nums.length < 2) return ''
  const min = Math.min(...nums)
  const max = Math.max(...nums)
  const range = max - min || 1
  const pad = 3
  return nums
    .map((v, i) => {
      const x = (i / (nums.length - 1)) * width
      const y = height - pad - ((v - min) / range) * (height - pad * 2)
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
}

// 渐变填充区域 polygon points（封闭到底边）
export function sparkArea(nums, width = 100, height = 40) {
  if (!nums || nums.length < 2) return ''
  const min = Math.min(...nums)
  const max = Math.max(...nums)
  const range = max - min || 1
  const pad = 3
  const pts = nums.map((v, i) => {
    const x = (i / (nums.length - 1)) * width
    const y = height - pad - ((v - min) / range) * (height - pad * 2)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })
  return `${pts.join(' ')} ${width},${height} 0,${height}`
}

// 日期格式化：2025-06-20 → 6月20日
export function fmtDate(dateStr) {
  if (!dateStr) return ''
  const parts = dateStr.split('-')
  if (parts.length < 3) return dateStr
  return `${+parts[1]}月${+parts[2]}日`
}

// 含年份的日期：2025-06-20 → 2025年6月20日（历史记录用，避免跨年歧义）
export function fmtDateFull(dateStr) {
  if (!dateStr) return ''
  const parts = dateStr.split('-')
  if (parts.length < 3) return dateStr
  return `${+parts[0]}年${+parts[1]}月${+parts[2]}日`
}

// 参考范围进度条数据（用于卡片内可视化）
// 返回 { okLeft, okWidth, valPct, oor } 百分比，或 null
export function refBarData(indicator) {
  const { direction } = indicator
  const latest = indicator.latest_value
  const v = latest?.value
  if (v == null) return null
  // 用最新记录的有效区间（记录自带优先，回退指标默认）
  const { low: ref_low, high: ref_high } = effectiveRef(latest, indicator)

  let barMin, barMax, okMin, okMax

  if (direction === 'range') {
    if (ref_low == null && ref_high == null) return null
    const lo = ref_low ?? Math.min(0, v * 0.6)
    const hi = ref_high ?? v * 1.6
    const span = Math.max(hi - lo, 1)
    barMin = Math.max(0, lo - span * 0.28)
    barMax = Math.max(hi + span * 0.28, v * 1.02)
    okMin  = ref_low  != null ? ref_low  : barMin
    okMax  = ref_high != null ? ref_high : barMax
  } else if (direction === 'lower') {
    if (ref_high == null) return null
    barMin = 0
    barMax = Math.max(ref_high * 1.55, v * 1.08, ref_high + 1)
    okMin  = 0
    okMax  = ref_high
  } else if (direction === 'higher') {
    if (ref_low == null) return null
    barMin = Math.max(0, ref_low * 0.25)
    barMax = Math.max(ref_low * 1.75, v * 1.08, ref_low + 1)
    okMin  = ref_low
    okMax  = barMax
  } else {
    return null
  }

  const span = barMax - barMin
  if (span <= 0) return null

  const pct = (x) => Math.min(97, Math.max(3, ((x - barMin) / span) * 100))
  const clampedV = Math.min(Math.max(v, barMin), barMax)

  return {
    okLeft:  pct(okMin),
    okWidth: Math.max(0, pct(okMax) - pct(okMin)),
    valPct:  pct(clampedV),
    oor:     isRecordOutOfRange(latest, indicator),
  }
}

// 趋势：与上一次记录相比的方向和变化量
// 返回 { dir: 'up'|'down'|'flat', str: '+5.4' } 或 null
export function trendDelta(indicator) {
  const tv = indicator.trend_values
  if (!tv || tv.length < 2) return null
  const latest = tv[tv.length - 1].value
  const prev   = tv[tv.length - 2].value
  const raw    = latest - prev
  if (Math.abs(raw) < 1e-9) return { dir: 'flat', str: '持平' }

  const abs = Math.abs(raw)
  let str
  if (abs < 0.001)     str = raw.toFixed(4)
  else if (abs < 0.01) str = raw.toFixed(3)
  else if (abs < 0.1)  str = raw.toFixed(2)
  else if (abs < 10)   str = raw.toFixed(1)
  else                 str = Math.round(raw).toString()

  return { dir: raw > 0 ? 'up' : 'down', str: (raw > 0 ? '+' : '') + str }
}

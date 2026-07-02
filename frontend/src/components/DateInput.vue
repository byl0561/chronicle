<script setup>
/**
 * 自定义日历选择器。
 * - 使用 <Teleport to="body"> + position:fixed，在 Sheet 内不会被裁剪。
 * - v-model 绑定 YYYY-MM-DD 字符串（与 input[type=date] 一致）。
 * - 自动判断弹出方向（空间不足时向上展开）。
 */
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: '选择日期' },
})
const emit = defineEmits(['update:modelValue'])

const open      = ref(false)
const triggerEl = ref(null)
const panelStyle = ref({})

const WEEKDAYS = ['日','一','二','三','四','五','六']
const MONTHS   = ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月']

// ── 当前视图年月 ──────────────────────────────────────────────────────────
const viewYear  = ref(new Date().getFullYear())
const viewMonth = ref(new Date().getMonth())

// ── 选中日期解析 ──────────────────────────────────────────────────────────
const selected = computed(() => {
  if (!props.modelValue) return null
  const [y, m, d] = props.modelValue.split('-').map(Number)
  return { year: y, month: m - 1, day: d }
})

const display = computed(() => {
  if (!props.modelValue) return ''
  const [y, m, d] = props.modelValue.split('-')
  return `${y}年${+m}月${+d}日`
})

// ── 日期格格 ──────────────────────────────────────────────────────────────
const daysGrid = computed(() => {
  const y = viewYear.value, mo = viewMonth.value
  const firstDow = new Date(y, mo, 1).getDay()          // 0=日
  const total    = new Date(y, mo + 1, 0).getDate()      // 本月天数
  const cells = Array(firstDow).fill(null)
  for (let d = 1; d <= total; d++) cells.push(d)
  while (cells.length % 7 !== 0) cells.push(null)
  return cells
})

function isSelected(d) {
  const s = selected.value
  return d && s && s.year === viewYear.value && s.month === viewMonth.value && s.day === d
}
function isToday(d) {
  if (!d) return false
  const n = new Date()
  return n.getFullYear() === viewYear.value && n.getMonth() === viewMonth.value && n.getDate() === d
}

// ── 月份导航 ──────────────────────────────────────────────────────────────
function prevMonth() {
  if (viewMonth.value === 0) { viewMonth.value = 11; viewYear.value-- }
  else viewMonth.value--
}
function nextMonth() {
  if (viewMonth.value === 11) { viewMonth.value = 0; viewYear.value++ }
  else viewMonth.value++
}
function prevYear() { viewYear.value-- }
function nextYear() { viewYear.value++ }

// ── 选择 ──────────────────────────────────────────────────────────────────
function pickDay(day) {
  if (!day) return
  const m = String(viewMonth.value + 1).padStart(2, '0')
  const d = String(day).padStart(2, '0')
  emit('update:modelValue', `${viewYear.value}-${m}-${d}`)
  close()
}
function pickToday() {
  const n = new Date()
  const m = String(n.getMonth() + 1).padStart(2, '0')
  const d = String(n.getDate()).padStart(2, '0')
  emit('update:modelValue', `${n.getFullYear()}-${m}-${d}`)
  close()
}
function clearDate() {
  emit('update:modelValue', '')
  close()
}

// ── 开关面板 ──────────────────────────────────────────────────────────────
function toggle() {
  if (open.value) { close(); return }
  // 视图跳到当前选中日期（或今天）
  if (selected.value) {
    viewYear.value  = selected.value.year
    viewMonth.value = selected.value.month
  } else {
    const n = new Date()
    viewYear.value  = n.getFullYear()
    viewMonth.value = n.getMonth()
  }
  open.value = true
  nextTick(updatePos)
}
function close() { open.value = false }

// ── 面板定位（Teleport + fixed）────────────────────────────────────────────
const PANEL_H = 340
function updatePos() {
  if (!triggerEl.value) return
  const r = triggerEl.value.getBoundingClientRect()
  const spaceBelow = window.innerHeight - r.bottom
  const above = spaceBelow < PANEL_H + 8
  panelStyle.value = {
    position: 'fixed',
    left: `${r.left}px`,
    width: `${r.width}px`,
    minWidth: '280px',
    zIndex: 400,
    ...(above
      ? { bottom: `${window.innerHeight - r.top + 6}px`, top: 'auto' }
      : { top:    `${r.bottom + 6}px`,                  bottom: 'auto' }),
  }
}

// ── 外部点击 / ESC 关闭 ────────────────────────────────────────────────────
function onClickOut(e) {
  if (open.value && triggerEl.value && !triggerEl.value.contains(e.target)) {
    const panel = document.getElementById('dp-panel')
    if (!panel?.contains(e.target)) close()
  }
}
function onKey(e) { if (e.key === 'Escape') close() }
function onResize() { if (open.value) updatePos() }

onMounted(() => {
  document.addEventListener('pointerdown', onClickOut)
  document.addEventListener('keydown', onKey)
  window.addEventListener('resize', onResize)
  window.addEventListener('scroll', onResize, true)
})
onUnmounted(() => {
  document.removeEventListener('pointerdown', onClickOut)
  document.removeEventListener('keydown', onKey)
  window.removeEventListener('resize', onResize)
  window.removeEventListener('scroll', onResize, true)
})
</script>

<template>
  <!-- 触发区域 -->
  <div
    ref="triggerEl"
    class="dp-trigger"
    :class="{ 'dp-trigger--open': open }"
    @click="toggle"
    tabindex="0"
    @keydown.enter.prevent="toggle"
    @keydown.space.prevent="toggle"
  >
    <svg class="dp-cal-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="4" width="18" height="18" rx="2"/>
      <line x1="16" y1="2" x2="16" y2="6"/>
      <line x1="8"  y1="2" x2="8"  y2="6"/>
      <line x1="3"  y1="10" x2="21" y2="10"/>
    </svg>
    <span v-if="display" class="dp-display">{{ display }}</span>
    <span v-else class="dp-ph">{{ placeholder }}</span>
  </div>

  <!-- 日历面板（Teleport 到 body，不受 Sheet overflow 裁剪）-->
  <Teleport to="body">
    <Transition name="dp-fade">
      <div v-if="open" id="dp-panel" class="dp-panel" :style="panelStyle">
        <!-- 年月导航 -->
        <div class="dp-nav-row">
          <button class="dp-nav-btn" @click="prevYear"  title="上一年">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
              stroke-linecap="round" stroke-linejoin="round" width="14" height="14">
              <path d="M11 17l-5-5 5-5M18 17l-5-5 5-5"/>
            </svg>
          </button>
          <button class="dp-nav-btn" @click="prevMonth" title="上个月">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
              stroke-linecap="round" stroke-linejoin="round" width="14" height="14">
              <path d="M15 18l-6-6 6-6"/>
            </svg>
          </button>
          <span class="dp-title">{{ viewYear }}年{{ MONTHS[viewMonth] }}</span>
          <button class="dp-nav-btn" @click="nextMonth" title="下个月">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
              stroke-linecap="round" stroke-linejoin="round" width="14" height="14">
              <path d="M9 18l6-6-6-6"/>
            </svg>
          </button>
          <button class="dp-nav-btn" @click="nextYear"  title="下一年">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
              stroke-linecap="round" stroke-linejoin="round" width="14" height="14">
              <path d="M13 17l5-5-5-5M6 17l5-5-5-5"/>
            </svg>
          </button>
        </div>

        <!-- 星期头 -->
        <div class="dp-weekdays">
          <span v-for="w in WEEKDAYS" :key="w" class="dp-wd">{{ w }}</span>
        </div>

        <!-- 日期格 -->
        <div class="dp-grid">
          <button
            v-for="(day, i) in daysGrid"
            :key="i"
            type="button"
            class="dp-day"
            :class="{
              'dp-day--sel':   isSelected(day),
              'dp-day--today': isToday(day) && !isSelected(day),
              'dp-day--empty': !day,
            }"
            :disabled="!day"
            @click="pickDay(day)"
          >{{ day }}</button>
        </div>

        <!-- 底部操作 -->
        <div class="dp-footer">
          <button class="dp-foot-btn" @click="clearDate">清除</button>
          <button class="dp-foot-btn dp-foot-btn--primary" @click="pickToday">今天</button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* ── 触发器 ─────────────────────────────────────────── */
.dp-trigger {
  display: flex; align-items: center; gap: 10px;
  width: 100%; padding: 9px 12px;
  border: 1.5px solid var(--border); border-radius: var(--r);
  background: var(--surface); cursor: pointer; user-select: none;
  font-size: 14px; color: var(--text);
  transition: border-color .15s, box-shadow .15s;
  min-height: 42px; outline: none;
}
.dp-trigger--open,
.dp-trigger:focus {
  border-color: var(--brand);
  box-shadow: 0 0 0 3px var(--brand-alpha);
}
.dp-cal-ico { color: var(--muted); flex-shrink: 0; width: 16px; height: 16px; }
.dp-display { flex: 1; }
.dp-ph      { flex: 1; color: var(--muted); }

/* ── 面板（Teleport 到 body，fixed 定位）────────────── */
.dp-panel {
  background: var(--surface);
  border: 1.5px solid var(--border);
  border-radius: var(--r-xl);
  box-shadow: 0 16px 48px rgba(0,0,0,.18), 0 4px 16px rgba(0,0,0,.10);
  padding: 14px;
  overflow: hidden;
}

/* ── 年月导航 ───────────────────────────────────────── */
.dp-nav-row {
  display: flex; align-items: center; gap: 4px; margin-bottom: 12px;
}
.dp-nav-btn {
  width: 30px; height: 30px; border-radius: var(--r);
  border: none; background: transparent;
  display: grid; place-items: center; cursor: pointer;
  color: var(--text-2); transition: background .12s;
  flex-shrink: 0;
}
.dp-nav-btn:hover { background: var(--surface-2); color: var(--brand); }
.dp-title {
  flex: 1; text-align: center;
  font-size: 14px; font-weight: 700; color: var(--text);
}

/* ── 星期头 ─────────────────────────────────────────── */
.dp-weekdays {
  display: grid; grid-template-columns: repeat(7, 1fr);
  margin-bottom: 6px;
}
.dp-wd {
  text-align: center; font-size: 11.5px; font-weight: 600;
  color: var(--muted); padding: 3px 0;
}

/* ── 日期格 ─────────────────────────────────────────── */
.dp-grid {
  display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px;
}
.dp-day {
  aspect-ratio: 1; border-radius: var(--r);
  border: none; background: transparent;
  font-size: 13px; cursor: pointer; color: var(--text);
  display: grid; place-items: center;
  transition: background .1s, color .1s;
  font-variant-numeric: tabular-nums;
  min-height: 36px;
}
.dp-day:not(.dp-day--empty):hover {
  background: var(--surface-2); color: var(--brand);
}
.dp-day--today {
  background: var(--brand-light); color: var(--brand);
  font-weight: 600;
}
.dp-day--sel {
  background: var(--brand) !important; color: #fff !important;
  font-weight: 700;
}
.dp-day--empty { cursor: default; opacity: 0; pointer-events: none; }

/* ── 底部按钮 ───────────────────────────────────────── */
.dp-footer {
  display: flex; align-items: center; justify-content: space-between;
  margin-top: 12px; padding-top: 10px;
  border-top: 1px solid var(--border);
}
.dp-foot-btn {
  padding: 6px 14px; border-radius: var(--r);
  border: 1.5px solid var(--border); background: transparent;
  font-size: 13px; font-weight: 500; cursor: pointer;
  color: var(--text-2); transition: background .12s, color .12s, border-color .12s;
}
.dp-foot-btn:hover { background: var(--surface-2); color: var(--text); }
.dp-foot-btn--primary {
  background: var(--brand); color: #fff; border-color: var(--brand);
}
.dp-foot-btn--primary:hover { background: var(--brand-hover); border-color: var(--brand-hover); }

/* ── 出入动画 ───────────────────────────────────────── */
.dp-fade-enter-active, .dp-fade-leave-active {
  transition: opacity .18s ease, transform .18s cubic-bezier(.32,.72,0,1);
}
.dp-fade-enter-from, .dp-fade-leave-to {
  opacity: 0; transform: translateY(-6px) scale(.97);
}
</style>

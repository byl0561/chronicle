<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api.js'
import { store, calcStatus, statusLabel, statusColor, sparkPoints, sparkArea, sparkSeries, fmtDate, refBarData, trendDelta, askConfirm } from '../store.js'
import Icon from '../components/Icon.vue'
import Sheet from '../components/Sheet.vue'
import CustomSelect from '../components/CustomSelect.vue'
import DateInput from '../components/DateInput.vue'
import SourceInput from '../components/SourceInput.vue'
import EmptyIllustration from '../components/EmptyIllustration.vue'

const route = useRoute()
const router = useRouter()

const tabId = computed(() => Number(route.params.tabId))
const tab = computed(() => store.tabs.find((t) => t.id === tabId.value))
const indicators = ref([])
const loading = ref(false)
const sources = ref([])

async function loadIndicators() {
  if (!tabId.value) return
  loading.value = true
  try {
    indicators.value = await api.indicators(tabId.value)
  } finally {
    loading.value = false
  }
}

async function loadSources() {
  try { sources.value = await api.sources() } catch { /* 忽略 */ }
}

// sparkline 归一化取值序列
function sparkNums(ind) {
  return sparkSeries(ind).nums
}

onMounted(() => { loadIndicators(); loadSources() })
watch(tabId, loadIndicators)

const summary = computed(() => ({
  ok:      indicators.value.filter(i => calcStatus(i) === 'ok').length,
  danger:  indicators.value.filter(i => calcStatus(i) === 'danger').length,
  norange: indicators.value.filter(i => calcStatus(i) === 'norange').length,
  nodata:  indicators.value.filter(i => calcStatus(i) === 'nodata').length,
}))

// ── 添加 / 编辑指标 Sheet ────────────────────────────────────────────────
const sheetOpen = ref(false)
const editingIndicator = ref(null)
const form = ref({})
const TAB_COLORS = ['#3B5BDB','#7C3AED','#C026D3','#E11D48','#EA580C','#CA8A04','#16A34A','#0891B2','#0284C7','#64748B']
const DIRECTIONS = [
  { value: 'range',  label: '区间内正常' },
  { value: 'lower',  label: '越低越好' },
  { value: 'higher', label: '越高越好' },
]

function openAdd() {
  editingIndicator.value = null
  form.value = { name: '', unit: '', ref_low: '', ref_high: '', direction: 'range' }
  sheetOpen.value = true
}

function openEdit(ind, e) {
  e.stopPropagation()
  editingIndicator.value = ind
  form.value = {
    name: ind.name,
    unit: ind.unit || '',
    ref_low: ind.ref_low ?? '',
    ref_high: ind.ref_high ?? '',
    direction: ind.direction,
  }
  sheetOpen.value = true
}

async function saveIndicator() {
  const payload = {
    name: form.value.name.trim(),
    unit: form.value.unit.trim() || null,
    ref_low: form.value.ref_low !== '' ? Number(form.value.ref_low) : null,
    ref_high: form.value.ref_high !== '' ? Number(form.value.ref_high) : null,
    direction: form.value.direction,
  }
  if (!payload.name) return
  if (editingIndicator.value) {
    await api.updateIndicator(editingIndicator.value.id, payload)
    window.__toast?.('指标已更新', 'success')
  } else {
    payload.sort = indicators.value.length
    await api.createIndicator(tabId.value, payload)
    window.__toast?.('指标已添加', 'success')
  }
  sheetOpen.value = false
  await loadIndicators()
}

async function deleteIndicator(ind, e) {
  e.stopPropagation()
  const ok = await askConfirm({
    title: '删除指标',
    message: `确认删除「${ind.name}」及其所有历史记录？此操作不可撤销。`,
    confirmText: '删除',
    danger: true,
  })
  if (!ok) return
  await api.deleteIndicator(ind.id)
  window.__toast?.('已删除', 'success')
  await loadIndicators()
}

// ── 快速录入 Sheet ────────────────────────────────────────────────────────
const recordSheetOpen = ref(false)
const activeIndicator = ref(null)
const activeRecords = ref([])   // 当前指标的历史记录，供按来源回填区间
const recordForm = ref({ value: '', measured_at: '', note: '' })

function openRecordEntry(ind, e) {
  e.stopPropagation()
  activeIndicator.value = ind
  recordForm.value = {
    value: '',
    measured_at: new Date().toISOString().slice(0, 10),
    note: '',
    // 参考区间预填指标默认值，可按当次化验单改写
    ref_low: ind.ref_low ?? '',
    ref_high: ind.ref_high ?? '',
    source: '',
  }
  recordSheetOpen.value = true
  // 预取该指标历史记录，选中来源时用于回填区间
  activeRecords.value = []
  api.records(ind.id).then((recs) => { activeRecords.value = recs }).catch(() => {})
}

// 选中历史来源后，用该来源在本指标下最近一条带区间的记录回填参考上下限
function fillRangeFromSource(src) {
  const rec = activeRecords.value.find(
    (r) => r.source === src && (r.ref_low != null || r.ref_high != null),
  )
  if (!rec) return
  recordForm.value.ref_low = rec.ref_low ?? ''
  recordForm.value.ref_high = rec.ref_high ?? ''
}

async function saveRecord() {
  if (!recordForm.value.value) return
  await api.createRecord(activeIndicator.value.id, {
    value: Number(recordForm.value.value),
    measured_at: recordForm.value.measured_at,
    note: recordForm.value.note.trim() || null,
    ref_low: recordForm.value.ref_low !== '' ? Number(recordForm.value.ref_low) : null,
    ref_high: recordForm.value.ref_high !== '' ? Number(recordForm.value.ref_high) : null,
    source: recordForm.value.source.trim() || null,
  })
  window.__toast?.('记录已添加', 'success')
  recordSheetOpen.value = false
  await Promise.all([loadIndicators(), loadSources()])
}

// ── 排序：上移 / 下移 ────────────────────────────────────────────────────
async function moveIndicator(index, dir) {
  const arr = [...indicators.value]
  const swapIdx = index + dir
  if (swapIdx < 0 || swapIdx >= arr.length) return
  ;[arr[index], arr[swapIdx]] = [arr[swapIdx], arr[index]]
  const items = arr.map((ind, i) => ({ id: ind.id, sort: i }))
  await api.reorderIndicators(items)
  await loadIndicators()
}

function goToDetail(ind) {
  router.push(`/t/${tabId.value}/i/${ind.id}`)
}
</script>

<template>
  <div>
    <!-- 页面标题 -->
    <div class="page-head">
      <div>
        <h1 v-if="tab" class="row" style="gap:8px">
          <span
            class="tab-color-dot"
            :style="{ background: tab.color || 'var(--brand)' }"
          />
          {{ tab.name }}
        </h1>
        <div class="sub">{{ indicators.length }} 个指标</div>
      </div>
      <div class="page-head-actions">
        <button class="btn btn-primary btn-sm" @click="openAdd">
          <Icon name="plus" :size="15" /> 添加指标
        </button>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!loading && indicators.length === 0" class="empty-state" style="margin-top:32px">
      <div class="empty-svg-wrap">
        <EmptyIllustration type="chart" />
      </div>
      <h3>还没有指标</h3>
      <p>点击「添加指标」创建第一个需要追踪的指标，例如肌酐、血压、血糖。</p>
      <button class="btn btn-primary mt-3" @click="openAdd">
        <Icon name="plus" :size="15" /> 添加指标
      </button>
    </div>

    <!-- 概况横幅 -->
    <div v-if="indicators.length > 0 && !loading" class="dash-overview">
      <div v-if="summary.ok > 0" class="do-item">
        <span class="do-dot ok" />
        <span class="do-num ok">{{ summary.ok }}</span>
        <span class="do-lbl">正常</span>
      </div>
      <div v-if="summary.danger > 0" class="do-item">
        <span class="do-dot danger" />
        <span class="do-num danger">{{ summary.danger }}</span>
        <span class="do-lbl">越界</span>
      </div>
      <div v-if="summary.norange > 0" class="do-item">
        <span class="do-dot norange" />
        <span class="do-num norange">{{ summary.norange }}</span>
        <span class="do-lbl">无区间</span>
      </div>
      <div v-if="summary.nodata > 0" class="do-item">
        <span class="do-dot nodata" />
        <span class="do-num nodata">{{ summary.nodata }}</span>
        <span class="do-lbl">暂无数据</span>
      </div>
    </div>

    <!-- 指标卡片网格 -->
    <div v-if="!loading && indicators.length > 0" class="indicator-grid">
      <div
        v-for="(ind, idx) in indicators"
        :key="ind.id"
        class="metric-card"
        :class="`status-${calcStatus(ind)}`"
        @click="goToDetail(ind)"
      >
        <!-- 头部：名称 + 状态徽章 -->
        <div class="mc-header">
          <span class="mc-name">{{ ind.name }}</span>
          <span class="mc-badge" :class="calcStatus(ind)">{{ statusLabel(calcStatus(ind)) }}</span>
        </div>

        <!-- 数值 + 趋势箭头 -->
        <div class="mc-value-area">
          <div class="mc-val-row">
            <template v-if="ind.latest_value">
              <span class="mc-val" :class="{ danger: calcStatus(ind) === 'danger' }">{{ ind.latest_value.value }}</span>
              <span v-if="ind.unit" class="mc-unit">{{ ind.unit }}</span>
            </template>
            <span v-else class="mc-val nodata">—</span>
          </div>
          <div v-if="trendDelta(ind)" class="mc-trend" :class="trendDelta(ind).dir">
            <span>{{ trendDelta(ind).dir === 'up' ? '↑' : trendDelta(ind).dir === 'down' ? '↓' : '→' }}</span>
            <span>{{ trendDelta(ind).str }}</span>
          </div>
        </div>

        <!-- Sparkline + 渐变填充 -->
        <div v-if="ind.trend_values.length >= 2" class="mc-spark">
          <svg viewBox="0 0 100 40" preserveAspectRatio="none">
            <defs>
              <linearGradient :id="`sg-${ind.id}`" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%"
                  :stop-color="statusColor(calcStatus(ind))"
                  stop-opacity="0.2"
                />
                <stop offset="100%"
                  :stop-color="statusColor(calcStatus(ind))"
                  stop-opacity="0"
                />
              </linearGradient>
            </defs>
            <polygon
              :points="sparkArea(sparkNums(ind))"
              :fill="`url(#sg-${ind.id})`"
            />
            <polyline
              :points="sparkPoints(sparkNums(ind))"
              fill="none"
              :stroke="statusColor(calcStatus(ind))"
              stroke-width="1.6"
              stroke-linejoin="round"
              stroke-linecap="round"
            />
          </svg>
        </div>

        <!-- 参考范围进度条 -->
        <div v-if="refBarData(ind)" class="mc-refbar-wrap">
          <div class="mc-refbar">
            <div class="mc-refbar-ok"
              :style="{ left: refBarData(ind).okLeft + '%', width: refBarData(ind).okWidth + '%' }"
            />
            <div class="mc-refbar-dot"
              :class="{ oor: refBarData(ind).oor }"
              :style="{ left: refBarData(ind).valPct + '%' }"
            />
          </div>
        </div>

        <!-- 底部：参考范围 + 日期 + 快捷操作 -->
        <div class="mc-footer" @click.stop>
          <span v-if="ind.ref_low != null || ind.ref_high != null" class="mc-ref">
            {{ ind.ref_low ?? '—' }}–{{ ind.ref_high ?? '∞' }}{{ ind.unit ? ' ' + ind.unit : '' }}
          </span>
          <span v-else class="mc-ref" />
          <span v-if="ind.latest_value" class="mc-date">{{ fmtDate(ind.latest_value.measured_at) }}</span>
          <div class="mc-btns">
            <button class="mc-btn" @click.stop="openEdit(ind, $event)" title="编辑指标">
              <Icon name="edit" :size="11" />
            </button>
            <button class="mc-btn" @click.stop="openRecordEntry(ind, $event)" title="录入数据">
              <Icon name="plus" :size="13" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加/编辑指标 Sheet -->
    <Sheet v-model="sheetOpen" :title="editingIndicator ? '编辑指标' : '添加指标'">
      <div class="field">
        <label>指标名称 *</label>
        <input class="input" v-model="form.name" placeholder="例如：肌酐、血压、空腹血糖" />
      </div>
      <div class="field">
        <label>单位</label>
        <input class="input" v-model="form.unit" placeholder="例如：μmol/L、mmHg（可留空）" />
      </div>
      <div class="field">
        <label>参考范围方向</label>
        <CustomSelect v-model="form.direction" :options="DIRECTIONS" />
      </div>
      <div class="grid2">
        <div class="field">
          <label>参考下限</label>
          <input class="input" type="number" v-model="form.ref_low" placeholder="可留空" />
        </div>
        <div class="field">
          <label>参考上限</label>
          <input class="input" type="number" v-model="form.ref_high" placeholder="可留空" />
        </div>
      </div>
      <template #foot>
        <button class="btn btn-outline" @click="sheetOpen = false">取消</button>
        <button class="btn btn-primary" @click="saveIndicator" :disabled="!form.name.trim()">
          {{ editingIndicator ? '保存修改' : '添加指标' }}
        </button>
      </template>
    </Sheet>

    <!-- 快速录入 Sheet -->
    <Sheet v-model="recordSheetOpen" :title="activeIndicator ? `录入 · ${activeIndicator.name}` : '录入'">
      <div class="field">
        <label>数值 {{ activeIndicator?.unit ? `(${activeIndicator.unit})` : '' }} *</label>
        <div class="input-with-unit">
          <input
            class="input lg"
            type="number"
            step="any"
            v-model="recordForm.value"
            placeholder="0.00"
            autofocus
          />
          <span v-if="activeIndicator?.unit" class="input-unit">{{ activeIndicator.unit }}</span>
        </div>
      </div>
      <div class="field">
        <label>测量日期</label>
        <DateInput v-model="recordForm.measured_at" />
      </div>
      <div class="field">
        <label>检测来源（可选）</label>
        <SourceInput v-model="recordForm.source" :options="sources" @select="fillRangeFromSource" />
      </div>
      <div class="grid2">
        <div class="field">
          <label>本次参考下限</label>
          <input class="input" type="number" step="any" v-model="recordForm.ref_low" placeholder="继承默认" />
        </div>
        <div class="field">
          <label>本次参考上限</label>
          <input class="input" type="number" step="any" v-model="recordForm.ref_high" placeholder="继承默认" />
        </div>
      </div>
      <div class="field">
        <label>备注（可选）</label>
        <input class="input" v-model="recordForm.note" placeholder="例如：复查、空腹状态、用药后" />
      </div>
      <template #foot>
        <button class="btn btn-outline" @click="recordSheetOpen = false">取消</button>
        <button class="btn btn-primary" @click="saveRecord" :disabled="!recordForm.value">
          保存记录
        </button>
      </template>
    </Sheet>
  </div>
</template>

<style scoped>
.tab-color-dot {
  width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0;
  display: inline-block;
}
</style>

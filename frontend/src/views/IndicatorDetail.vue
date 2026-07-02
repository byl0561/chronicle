<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api.js'
import { store, calcStatus, statusLabel, isRecordOutOfRange, directionLabel, fmtDate, askConfirm } from '../store.js'
import Icon from '../components/Icon.vue'
import Sheet from '../components/Sheet.vue'
import IndicatorChart from '../components/IndicatorChart.vue'
import DateInput from '../components/DateInput.vue'
import SourceInput from '../components/SourceInput.vue'
import EmptyIllustration from '../components/EmptyIllustration.vue'

const route = useRoute()
const router = useRouter()

const tabId = computed(() => Number(route.params.tabId))
const indicatorId = computed(() => Number(route.params.indicatorId))

const indicator = ref(null)
const records = ref([])
const loading = ref(true)
const sources = ref([])

async function load() {
  loading.value = true
  try {
    const [inds, recs, srcs] = await Promise.all([
      api.indicators(tabId.value),
      api.records(indicatorId.value),
      api.sources().catch(() => []),
    ])
    indicator.value = inds.find((i) => i.id === indicatorId.value) || null
    records.value = recs
    sources.value = srcs
  } finally {
    loading.value = false
  }
}

onMounted(load)

const status = computed(() => indicator.value ? calcStatus(indicator.value) : 'nodata')

function goBack() {
  router.push(`/t/${tabId.value}`)
}

// ── 快速录入 Sheet ────────────────────────────────────────────────────────
const addSheetOpen = ref(false)
const recordForm = ref({ value: '', measured_at: '', note: '', ref_low: '', ref_high: '', source: '' })

function openAdd() {
  recordForm.value = {
    value: '',
    measured_at: new Date().toISOString().slice(0, 10),
    note: '',
    // 参考区间预填指标默认值，可按当次化验单改写
    ref_low: indicator.value?.ref_low ?? '',
    ref_high: indicator.value?.ref_high ?? '',
    source: '',
  }
  addSheetOpen.value = true
}

async function saveRecord() {
  if (!recordForm.value.value) return
  await api.createRecord(indicatorId.value, {
    value: Number(recordForm.value.value),
    measured_at: recordForm.value.measured_at,
    note: recordForm.value.note.trim() || null,
    ref_low: recordForm.value.ref_low !== '' ? Number(recordForm.value.ref_low) : null,
    ref_high: recordForm.value.ref_high !== '' ? Number(recordForm.value.ref_high) : null,
    source: recordForm.value.source.trim() || null,
  })
  window.__toast?.('记录已添加', 'success')
  addSheetOpen.value = false
  await load()
}

// ── 编辑记录 Sheet ────────────────────────────────────────────────────────
const editSheetOpen = ref(false)
const editingRecord = ref(null)
const editForm = ref({ value: '', measured_at: '', note: '', ref_low: '', ref_high: '', source: '' })

function openEdit(rec) {
  editingRecord.value = rec
  editForm.value = {
    value: rec.value,
    measured_at: rec.measured_at,
    note: rec.note || '',
    ref_low: rec.ref_low ?? '',
    ref_high: rec.ref_high ?? '',
    source: rec.source || '',
  }
  editSheetOpen.value = true
}

async function saveEdit() {
  if (!editForm.value.value) return
  await api.updateRecord(editingRecord.value.id, {
    value: Number(editForm.value.value),
    measured_at: editForm.value.measured_at,
    note: editForm.value.note.trim() || null,
    ref_low: editForm.value.ref_low !== '' ? Number(editForm.value.ref_low) : null,
    ref_high: editForm.value.ref_high !== '' ? Number(editForm.value.ref_high) : null,
    source: editForm.value.source.trim() || null,
  })
  window.__toast?.('记录已更新', 'success')
  editSheetOpen.value = false
  await load()
}

// ── 删除记录 ──────────────────────────────────────────────────────────────
async function deleteRecord(rec) {
  const ok = await askConfirm({
    title: '删除记录',
    message: `确认删除 ${rec.measured_at} 的记录（${rec.value}）？`,
    confirmText: '删除',
    danger: true,
  })
  if (!ok) return
  await api.deleteRecord(rec.id)
  window.__toast?.('已删除', 'success')
  await load()
}

// 统计汇总（最新/最高/最低/均值）
const stats = computed(() => {
  if (!records.value.length) return null
  const vals = records.value.map((r) => r.value)
  const latest = indicator.value?.latest_value?.value ?? vals[0]
  const min = Math.min(...vals)
  const max = Math.max(...vals)
  const avg = (vals.reduce((a, b) => a + b, 0) / vals.length)
  const avgStr = Number.isInteger(avg) ? avg.toString() : avg.toFixed(1)
  return { latest, min, max, avg: avgStr, count: vals.length }
})

// 参考范围描述文字
const refDesc = computed(() => {
  if (!indicator.value) return ''
  const { ref_low, ref_high, unit, direction } = indicator.value
  const u = unit ? ` ${unit}` : ''
  if (direction === 'range') {
    if (ref_low != null && ref_high != null) return `参考范围 ${ref_low}–${ref_high}${u}`
    if (ref_low != null) return `下限 ${ref_low}${u}`
    if (ref_high != null) return `上限 ${ref_high}${u}`
  } else if (direction === 'lower') {
    return ref_high != null ? `上限 ${ref_high}${u}（越低越好）` : '越低越好'
  } else if (direction === 'higher') {
    return ref_low != null ? `下限 ${ref_low}${u}（越高越好）` : '越高越好'
  }
  return ''
})
</script>

<template>
  <div>
    <!-- 顶部返回导航 -->
    <div class="row" style="gap:8px; margin-bottom:18px">
      <button class="btn btn-ghost btn-sm" style="padding:6px 10px" @click="goBack">
        <Icon name="arrow-left" :size="16" /> 返回
      </button>
    </div>

    <div v-if="loading" class="empty-state">
      <p class="muted">加载中…</p>
    </div>

    <template v-else-if="indicator">
      <!-- 指标信息头 -->
      <div class="page-head">
        <div>
          <div class="row" style="gap:10px; align-items:baseline">
            <h1>{{ indicator.name }}</h1>
            <span v-if="indicator.unit" class="muted fs-sm">{{ indicator.unit }}</span>
            <span class="badge" :class="status">{{ statusLabel(status) }}</span>
          </div>
          <div v-if="refDesc" class="sub mt-1">{{ refDesc }}</div>
        </div>
        <div class="page-head-actions">
          <button class="btn btn-primary btn-sm" @click="openAdd">
            <Icon name="plus" :size="15" /> 添加记录
          </button>
        </div>
      </div>

      <!-- 统计汇总行 -->
      <div v-if="stats" class="stats-row">
        <div class="stat-item">
          <div class="stat-label">最新值</div>
          <div class="stat-value" :class="{ danger: status === 'danger' }">{{ stats.latest }}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">最高</div>
          <div class="stat-value">{{ stats.max }}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">最低</div>
          <div class="stat-value">{{ stats.min }}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">均值</div>
          <div class="stat-value">{{ stats.avg }}</div>
        </div>
      </div>

      <!-- 趋势图卡片 -->
      <div class="card card-body" style="padding: 16px">
        <IndicatorChart :indicator="indicator" :records="[...records].reverse()" />
      </div>

      <!-- 历史记录 -->
      <div class="section-head">
        <h2>历史记录</h2>
        <span class="muted fs-xs">共 {{ records.length }} 条</span>
      </div>

      <div v-if="records.length === 0" class="empty-state" style="padding:36px 20px">
        <div class="empty-svg-wrap">
          <EmptyIllustration type="clipboard" />
        </div>
        <h3>还没有记录</h3>
        <p>点击「添加记录」录入第一条测量数据。</p>
      </div>

      <div v-else class="card">
        <div class="record-list">
          <div
            v-for="rec in records"
            :key="rec.id"
            class="record-item"
          >
            <div class="record-date">{{ fmtDate(rec.measured_at) }}</div>
            <div class="row" style="align-items:baseline; gap:0; min-width:80px">
              <div
                class="record-value"
                :class="{ danger: indicator && isRecordOutOfRange(rec, indicator) }"
              >{{ rec.value }}</div>
              <span v-if="indicator?.unit" class="record-unit">{{ indicator.unit }}</span>
            </div>
            <div class="record-note">
              <span v-if="rec.source" class="record-source">{{ rec.source }}</span>
              <span v-if="rec.note">{{ rec.note }}</span>
            </div>
            <div class="record-actions">
              <button class="btn btn-icon" @click="openEdit(rec)" title="编辑">
                <Icon name="edit" :size="15" />
              </button>
              <button
                class="btn btn-icon"
                style="color:var(--danger)"
                @click="deleteRecord(rec)"
                title="删除"
              >
                <Icon name="trash" :size="15" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- 添加记录 Sheet -->
    <Sheet v-model="addSheetOpen" :title="indicator ? `录入 · ${indicator.name}` : '添加记录'">
      <div class="field">
        <label>数值 {{ indicator?.unit ? `(${indicator.unit})` : '' }} *</label>
        <div class="input-with-unit">
          <input
            class="input lg"
            type="number"
            step="any"
            v-model="recordForm.value"
            placeholder="0.00"
            autofocus
          />
          <span v-if="indicator?.unit" class="input-unit">{{ indicator.unit }}</span>
        </div>
      </div>
      <div class="field">
        <label>测量日期</label>
        <DateInput v-model="recordForm.measured_at" />
      </div>
      <div class="field">
        <label>检测来源（可选）</label>
        <SourceInput v-model="recordForm.source" :options="sources" />
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
        <button class="btn btn-outline" @click="addSheetOpen = false">取消</button>
        <button class="btn btn-primary" @click="saveRecord" :disabled="!recordForm.value">
          保存记录
        </button>
      </template>
    </Sheet>

    <!-- 编辑记录 Sheet -->
    <Sheet v-model="editSheetOpen" title="编辑记录">
      <div class="field">
        <label>数值 {{ indicator?.unit ? `(${indicator.unit})` : '' }} *</label>
        <div class="input-with-unit">
          <input
            class="input lg"
            type="number"
            step="any"
            v-model="editForm.value"
          />
          <span v-if="indicator?.unit" class="input-unit">{{ indicator.unit }}</span>
        </div>
      </div>
      <div class="field">
        <label>测量日期</label>
        <DateInput v-model="editForm.measured_at" />
      </div>
      <div class="field">
        <label>检测来源（可选）</label>
        <SourceInput v-model="editForm.source" :options="sources" />
      </div>
      <div class="grid2">
        <div class="field">
          <label>本次参考下限</label>
          <input class="input" type="number" step="any" v-model="editForm.ref_low" placeholder="继承默认" />
        </div>
        <div class="field">
          <label>本次参考上限</label>
          <input class="input" type="number" step="any" v-model="editForm.ref_high" placeholder="继承默认" />
        </div>
      </div>
      <div class="field">
        <label>备注（可选）</label>
        <input class="input" v-model="editForm.note" placeholder="可留空" />
      </div>
      <template #foot>
        <button class="btn btn-outline" @click="editSheetOpen = false">取消</button>
        <button class="btn btn-primary" @click="saveEdit" :disabled="!editForm.value">
          保存修改
        </button>
      </template>
    </Sheet>
  </div>
</template>

<style scoped>
.record-note {
  display: flex; align-items: center; gap: 8px;
  flex: 1; min-width: 0; overflow: hidden;
}
.record-source {
  display: inline-flex; align-items: center; flex-shrink: 0;
  padding: 2px 8px; border-radius: 999px;
  background: var(--brand-light); color: var(--brand);
  font-size: 11.5px; font-weight: 600; white-space: nowrap;
}
.record-note > span:not(.record-source) {
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
</style>

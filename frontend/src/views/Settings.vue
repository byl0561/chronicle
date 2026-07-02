<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api.js'
import { store, reloadTabs, askConfirm } from '../store.js'
import Icon from '../components/Icon.vue'
import Sheet from '../components/Sheet.vue'
import CustomSelect from '../components/CustomSelect.vue'

// ── Tab 管理 ──────────────────────────────────────────────────────────────
const tabSheetOpen = ref(false)
const editingTab = ref(null)
const tabForm = ref({ name: '', color: '#3B5BDB' })

const TAB_COLORS = [
  '#3B5BDB', '#7C3AED', '#C026D3', '#E11D48',
  '#EA580C', '#CA8A04', '#16A34A', '#0891B2',
  '#0284C7', '#64748B',
]

function openAddTab() {
  editingTab.value = null
  tabForm.value = { name: '', color: TAB_COLORS[0] }
  tabSheetOpen.value = true
}

function openEditTab(tab) {
  editingTab.value = tab
  tabForm.value = { name: tab.name, color: tab.color || TAB_COLORS[0] }
  tabSheetOpen.value = true
}

async function saveTab() {
  if (!tabForm.value.name.trim()) return
  if (editingTab.value) {
    await api.updateTab(editingTab.value.id, {
      name: tabForm.value.name.trim(),
      color: tabForm.value.color,
    })
    window.__toast?.('分类已更新', 'success')
  } else {
    await api.createTab({
      name: tabForm.value.name.trim(),
      color: tabForm.value.color,
      sort: store.tabs.length,
    })
    window.__toast?.('分类已创建', 'success')
  }
  tabSheetOpen.value = false
  await reloadTabs()
}

async function deleteTab(tab) {
  const ok = await askConfirm({
    title: '删除分类',
    message: `确认删除「${tab.name}」？该分类下的所有指标和历史记录将一并删除，此操作不可撤销。`,
    confirmText: '删除',
    danger: true,
  })
  if (!ok) return
  await api.deleteTab(tab.id)
  window.__toast?.('已删除', 'success')
  await reloadTabs()
}

async function moveTab(index, dir) {
  const arr = [...store.tabs]
  const swapIdx = index + dir
  if (swapIdx < 0 || swapIdx >= arr.length) return
  ;[arr[index], arr[swapIdx]] = [arr[swapIdx], arr[index]]
  const items = arr.map((t, i) => ({ id: t.id, sort: i }))
  await api.reorderTabs(items)
  await reloadTabs()
}

// ── 指标管理 ──────────────────────────────────────────────────────────────
const selectedTabId = ref(null)
const tabIndicators = ref([])
const loadingInds = ref(false)

async function selectTab(tabId) {
  if (selectedTabId.value === tabId) return
  selectedTabId.value = tabId
  loadingInds.value = true
  try {
    tabIndicators.value = await api.indicators(tabId)
  } finally {
    loadingInds.value = false
  }
}

onMounted(() => {
  if (store.tabs.length > 0) selectTab(store.tabs[0].id)
})

const indSheetOpen = ref(false)
const editingInd = ref(null)
const indForm = ref({})

const DIRECTIONS = [
  { value: 'range',  label: '区间内正常' },
  { value: 'lower',  label: '越低越好' },
  { value: 'higher', label: '越高越好' },
]

function openAddInd() {
  editingInd.value = null
  indForm.value = { name: '', unit: '', ref_low: '', ref_high: '', direction: 'range' }
  indSheetOpen.value = true
}

function openEditInd(ind) {
  editingInd.value = ind
  indForm.value = {
    name: ind.name, unit: ind.unit || '',
    ref_low: ind.ref_low ?? '', ref_high: ind.ref_high ?? '',
    direction: ind.direction,
  }
  indSheetOpen.value = true
}

async function saveInd() {
  if (!indForm.value.name.trim() || !selectedTabId.value) return
  const payload = {
    name: indForm.value.name.trim(),
    unit: indForm.value.unit.trim() || null,
    ref_low: indForm.value.ref_low !== '' ? Number(indForm.value.ref_low) : null,
    ref_high: indForm.value.ref_high !== '' ? Number(indForm.value.ref_high) : null,
    direction: indForm.value.direction,
  }
  if (editingInd.value) {
    await api.updateIndicator(editingInd.value.id, payload)
    window.__toast?.('指标已更新', 'success')
  } else {
    await api.createIndicator(selectedTabId.value, { ...payload, sort: tabIndicators.value.length })
    window.__toast?.('指标已添加', 'success')
  }
  indSheetOpen.value = false
  tabIndicators.value = await api.indicators(selectedTabId.value)
}

async function deleteInd(ind) {
  const ok = await askConfirm({
    title: '删除指标',
    message: `确认删除「${ind.name}」及其所有历史记录？`,
    confirmText: '删除',
    danger: true,
  })
  if (!ok) return
  await api.deleteIndicator(ind.id)
  window.__toast?.('已删除', 'success')
  tabIndicators.value = await api.indicators(selectedTabId.value)
}

async function moveInd(index, dir) {
  const arr = [...tabIndicators.value]
  const swapIdx = index + dir
  if (swapIdx < 0 || swapIdx >= arr.length) return
  ;[arr[index], arr[swapIdx]] = [arr[swapIdx], arr[index]]
  await api.reorderIndicators(arr.map((it, i) => ({ id: it.id, sort: i })))
  tabIndicators.value = await api.indicators(selectedTabId.value)
}

// ── CSV 导入 / 导出 ────────────────────────────────────────────────────────
const importInput = ref(null)
const importing = ref(false)

async function exportData() {
  const blob = await api.exportCsv()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `chronicle_export_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
  window.__toast?.('导出成功', 'success')
}

async function onFileChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  importing.value = true
  try {
    const result = await api.importCsv(file)
    const { imported } = result
    window.__toast?.(
      `导入完成：${imported.tabs} 个分类，${imported.indicators} 个指标，${imported.records} 条记录，${imported.skipped} 条跳过`,
      'success',
    )
    await reloadTabs()
    if (selectedTabId.value) {
      tabIndicators.value = await api.indicators(selectedTabId.value)
    }
  } finally {
    importing.value = false
    e.target.value = ''
  }
}
</script>

<template>
  <div>
    <div class="page-head">
      <div>
        <h1>设置</h1>
        <div class="sub">管理分类、指标和数据</div>
      </div>
    </div>

    <!-- ── 分类管理 ──────────────────────────────────────────────────────── -->
    <div class="section-head">
      <h2>分类管理</h2>
      <button class="btn btn-primary btn-sm" @click="openAddTab">
        <Icon name="plus" :size="13" /> 新建分类
      </button>
    </div>

    <div class="card">
      <div v-if="store.tabs.length === 0" class="empty-state" style="padding:30px 20px">
        <div class="empty-state-icon">📂</div>
        <p>还没有分类，点击「新建分类」开始。</p>
      </div>
      <template v-else>
        <div
          v-for="(tab, idx) in store.tabs"
          :key="tab.id"
          class="setting-item"
        >
          <span
            class="color-dot-lg"
            :style="{ background: tab.color || 'var(--brand)' }"
          />
          <div class="setting-item-body">
            <div class="setting-item-name">{{ tab.name }}</div>
          </div>
          <div class="setting-item-actions">
            <button
              v-if="idx > 0"
              class="btn btn-icon"
              @click="moveTab(idx, -1)"
              title="上移"
            ><Icon name="move-up" :size="14" /></button>
            <button
              v-if="idx < store.tabs.length - 1"
              class="btn btn-icon"
              @click="moveTab(idx, 1)"
              title="下移"
            ><Icon name="move-down" :size="14" /></button>
            <button class="btn btn-icon" @click="openEditTab(tab)" title="编辑">
              <Icon name="edit" :size="14" />
            </button>
            <button
              class="btn btn-icon"
              style="color:var(--danger)"
              @click="deleteTab(tab)"
              title="删除"
            ><Icon name="trash" :size="14" /></button>
          </div>
        </div>
      </template>
    </div>

    <!-- ── 指标管理 ──────────────────────────────────────────────────────── -->
    <div class="section-head" style="margin-top:28px">
      <h2>指标管理</h2>
      <button
        v-if="selectedTabId"
        class="btn btn-primary btn-sm"
        @click="openAddInd"
      >
        <Icon name="plus" :size="13" /> 添加指标
      </button>
    </div>

    <!-- 分类选择 -->
    <div v-if="store.tabs.length > 0" class="tab-select-row">
      <button
        v-for="tab in store.tabs"
        :key="tab.id"
        class="tab-select-btn"
        :class="{ active: selectedTabId === tab.id }"
        :style="selectedTabId === tab.id ? { background: tab.color || 'var(--brand)', color:'#fff', borderColor: tab.color || 'var(--brand)' } : {}"
        @click="selectTab(tab.id)"
      >
        {{ tab.name }}
      </button>
    </div>

    <div class="card">
      <div v-if="!selectedTabId" class="empty-state" style="padding:30px 20px">
        <p class="muted">请先选择一个分类</p>
      </div>
      <div v-else-if="loadingInds" class="empty-state" style="padding:30px 20px">
        <p class="muted">加载中…</p>
      </div>
      <div v-else-if="tabIndicators.length === 0" class="empty-state" style="padding:30px 20px">
        <div class="empty-state-icon">🩺</div>
        <p>当前分类下还没有指标。</p>
      </div>
      <template v-else>
        <div
          v-for="(ind, idx) in tabIndicators"
          :key="ind.id"
          class="setting-item"
        >
          <div class="setting-item-body">
            <div class="setting-item-name">{{ ind.name }}</div>
            <div class="setting-item-meta">
              <span v-if="ind.unit">{{ ind.unit }}</span>
              <span v-if="ind.ref_low != null || ind.ref_high != null">
                · {{ ind.ref_low ?? '—' }}~{{ ind.ref_high ?? '—' }}
              </span>
              · {{ ind.direction === 'range' ? '区间内正常' : ind.direction === 'lower' ? '越低越好' : '越高越好' }}
            </div>
          </div>
          <div class="setting-item-actions">
            <button
              v-if="idx > 0"
              class="btn btn-icon"
              @click="moveInd(idx, -1)"
              title="上移"
            ><Icon name="move-up" :size="14" /></button>
            <button
              v-if="idx < tabIndicators.length - 1"
              class="btn btn-icon"
              @click="moveInd(idx, 1)"
              title="下移"
            ><Icon name="move-down" :size="14" /></button>
            <button class="btn btn-icon" @click="openEditInd(ind)" title="编辑">
              <Icon name="edit" :size="14" />
            </button>
            <button
              class="btn btn-icon"
              style="color:var(--danger)"
              @click="deleteInd(ind)"
              title="删除"
            ><Icon name="trash" :size="14" /></button>
          </div>
        </div>
      </template>
    </div>

    <!-- ── 数据管理 ──────────────────────────────────────────────────────── -->
    <div class="section-head" style="margin-top:28px">
      <h2>数据管理</h2>
    </div>

    <div class="card card-body">
      <div class="row" style="gap:16px; flex-wrap:wrap">
        <div style="flex:1; min-width:220px">
          <div style="font-size:14px; font-weight:600; margin-bottom:4px">导出数据</div>
          <div class="muted fs-sm" style="margin-bottom:12px">
            将所有分类、指标和历史记录导出为 CSV 文件，可用于备份或迁移。
          </div>
          <button class="btn btn-outline" @click="exportData">
            <Icon name="download" :size="15" /> 导出 CSV
          </button>
        </div>
        <div class="divider" style="width:1px; height:auto; margin:0; align-self:stretch" />
        <div style="flex:1; min-width:220px">
          <div style="font-size:14px; font-weight:600; margin-bottom:4px">导入数据</div>
          <div class="muted fs-sm" style="margin-bottom:12px">
            从同格式 CSV 文件导入数据，重复记录自动跳过（幂等导入）。
          </div>
          <input
            ref="importInput"
            type="file"
            accept=".csv"
            style="display:none"
            @change="onFileChange"
          />
          <button class="btn btn-outline" :disabled="importing" @click="importInput.click()">
            <Icon name="upload" :size="15" />
            {{ importing ? '导入中…' : '选择 CSV 文件' }}
          </button>
        </div>
      </div>
    </div>

    <!-- CSV 格式说明 -->
    <div class="card card-body" style="margin-top:10px">
      <div class="muted fs-xs" style="line-height:1.8">
        <strong style="color:var(--text-2)">CSV 格式：</strong>
        必须包含表头
        <code>tab_name, tab_color, indicator_name, unit, ref_low, ref_high, direction, measured_at, value, note</code>，
        其中 <code>direction</code> 取值为 <code>range</code> / <code>lower</code> / <code>higher</code>，
        <code>measured_at</code> 格式为 <code>YYYY-MM-DD</code>。
      </div>
    </div>

    <!-- 分类 Sheet -->
    <Sheet v-model="tabSheetOpen" :title="editingTab ? '编辑分类' : '新建分类'">
      <div class="field">
        <label>分类名称 *</label>
        <input class="input" v-model="tabForm.name" placeholder="例如：慢性肾炎、心血管、肝功能" autofocus />
      </div>
      <div class="field">
        <label>标识颜色</label>
        <div class="color-picker">
          <div
            v-for="c in TAB_COLORS"
            :key="c"
            class="color-swatch"
            :style="{ background: c }"
            :class="{ selected: tabForm.color === c }"
            @click="tabForm.color = c"
          />
        </div>
      </div>
      <template #foot>
        <button class="btn btn-outline" @click="tabSheetOpen = false">取消</button>
        <button class="btn btn-primary" @click="saveTab" :disabled="!tabForm.name.trim()">
          {{ editingTab ? '保存修改' : '创建分类' }}
        </button>
      </template>
    </Sheet>

    <!-- 指标 Sheet -->
    <Sheet v-model="indSheetOpen" :title="editingInd ? '编辑指标' : '添加指标'">
      <div class="field">
        <label>指标名称 *</label>
        <input class="input" v-model="indForm.name" placeholder="例如：肌酐、尿蛋白" />
      </div>
      <div class="field">
        <label>单位</label>
        <input class="input" v-model="indForm.unit" placeholder="例如：μmol/L（可留空）" />
      </div>
      <div class="field">
        <label>方向</label>
        <CustomSelect v-model="indForm.direction" :options="DIRECTIONS" />
      </div>
      <div class="grid2">
        <div class="field">
          <label>参考下限</label>
          <input class="input" type="number" v-model="indForm.ref_low" placeholder="可留空" />
        </div>
        <div class="field">
          <label>参考上限</label>
          <input class="input" type="number" v-model="indForm.ref_high" placeholder="可留空" />
        </div>
      </div>
      <template #foot>
        <button class="btn btn-outline" @click="indSheetOpen = false">取消</button>
        <button class="btn btn-primary" @click="saveInd" :disabled="!indForm.name.trim()">
          {{ editingInd ? '保存修改' : '添加指标' }}
        </button>
      </template>
    </Sheet>
  </div>
</template>

<style scoped>
.color-dot-lg {
  width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0;
}
.tab-select-row {
  display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px;
}
.tab-select-btn {
  padding: 6px 14px; border-radius: 999px;
  border: 1.5px solid var(--border-2); background: var(--surface);
  font-size: 13px; font-weight: 500; cursor: pointer; color: var(--text-2);
  transition: all .15s;
}
.tab-select-btn:hover { border-color: var(--brand); color: var(--brand); }
.tab-select-btn.active { font-weight: 600; }
</style>

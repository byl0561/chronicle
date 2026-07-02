<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { store, loadTabs, reloadTabs, askConfirm } from './store.js'
import { api } from './api.js'
import Icon from './components/Icon.vue'
import ConfirmDialog from './components/ConfirmDialog.vue'
import Sheet from './components/Sheet.vue'
import EmptyIllustration from './components/EmptyIllustration.vue'
import AppLogo from './components/AppLogo.vue'

const route = useRoute()
const router = useRouter()

// ── 初始化：加载 Tabs ─────────────────────────────────────────────────────
onMounted(async () => {
  await loadTabs()
  // 如果在根路径且有 Tab，跳转到第一个
  if (route.path === '/' && store.tabs.length > 0) {
    router.replace(`/t/${store.tabs[0].id}`)
  }
})

// 当前激活的 Tab
const activeTabId = computed(() => {
  const id = Number(route.params.tabId)
  return isNaN(id) ? null : id
})

// 当前路由页面标题（用于移动端顶栏）
const pageTitle = computed(() => route.meta?.title || 'Chronicle')
const isSettings = computed(() => route.path === '/settings')

// ── 新建 Tab Sheet（侧边栏底部快捷入口） ─────────────────────────────────
const addTabOpen = ref(false)
const tabForm = ref({ name: '', color: '#3B5BDB' })
const TAB_COLORS = [
  '#3B5BDB','#7C3AED','#C026D3','#E11D48',
  '#EA580C','#CA8A04','#16A34A','#0891B2',
  '#0284C7','#64748B',
]

function openAddTab() {
  tabForm.value = { name: '', color: TAB_COLORS[0] }
  addTabOpen.value = true
}

async function saveTab() {
  if (!tabForm.value.name.trim()) return
  const tab = await api.createTab({
    name: tabForm.value.name.trim(),
    color: tabForm.value.color,
    sort: store.tabs.length,
  })
  addTabOpen.value = false
  await reloadTabs()
  router.push(`/t/${tab.id}`)
  window.__toast?.('分类已创建', 'success')
}

// ── Toast 系统 ────────────────────────────────────────────────────────────
const toasts = ref([])
let toastSeq = 0

onMounted(() => {
  window.__toast = (msg, type = 'info') => {
    const id = ++toastSeq
    toasts.value.push({ id, msg, type })
    setTimeout(() => {
      toasts.value = toasts.value.filter((t) => t.id !== id)
    }, 3000)
  }
})

// 侧边栏导航到 Tab
function navToTab(tabId) {
  router.push(`/t/${tabId}`)
}

// 当无 Tab 时在根路径停留，有新 Tab 后跳转
watch(() => store.tabs.length, (len, oldLen) => {
  if (len > 0 && oldLen === 0 && route.path === '/') {
    router.replace(`/t/${store.tabs[0].id}`)
  }
})
</script>

<template>
  <div class="layout">
    <!-- ══ 侧边栏（桌面）══════════════════════════════════════════════════ -->
    <aside class="sidebar">
      <div class="sb-header">
        <div class="sb-logo"><AppLogo /></div>
        <div>
          <div class="sb-brand-name">Chronicle</div>
          <div class="sb-brand-sub">健康日志</div>
        </div>
      </div>

      <div class="sb-section-label">我的分类</div>

      <nav>
        <div
          v-if="store.tabs.length === 0"
          style="padding: 8px 16px; font-size:12.5px; color: var(--sb-text); opacity:.6"
        >
          还没有分类
        </div>
        <router-link
          v-for="tab in store.tabs"
          :key="tab.id"
          :to="`/t/${tab.id}`"
          class="sb-item"
          :class="{ active: activeTabId === tab.id }"
        >
          <span
            class="sb-dot"
            :style="{ background: tab.color || 'var(--brand)' }"
          />
          <span class="sb-label">{{ tab.name }}</span>
        </router-link>

        <button class="sb-item" style="background:transparent; border:none; width:100%; text-align:left; cursor:pointer" @click="openAddTab">
          <Icon name="plus" :size="15" style="color:var(--sb-text)" />
          <span class="sb-label" style="font-size:13px">新建分类</span>
        </button>
      </nav>

      <div class="sb-spacer" />

      <div class="sb-footer">
        <router-link to="/settings" class="sb-item" :class="{ active: isSettings }">
          <Icon name="settings" :size="16" />
          <span class="sb-label">设置</span>
        </router-link>
      </div>
    </aside>

    <!-- ══ 主内容区 ══════════════════════════════════════════════════════ -->
    <div class="main">
      <!-- 顶栏（移动端） -->
      <header class="topbar">
        <div class="topbar-brand">
          <div class="topbar-logo"><AppLogo /></div>
          Chronicle
        </div>
        <span class="topbar-title" v-if="pageTitle !== 'Chronicle'">{{ pageTitle }}</span>
        <div class="topbar-spacer" />
        <router-link to="/settings" class="btn btn-icon">
          <Icon name="settings" :size="18" />
        </router-link>
      </header>

      <!-- Tab 横向滚动（移动端） -->
      <nav class="tab-rail" v-if="store.tabs.length > 0 || route.path === '/'">
        <router-link
          v-for="tab in store.tabs"
          :key="tab.id"
          :to="`/t/${tab.id}`"
          class="tab-pill"
          :class="{ active: activeTabId === tab.id }"
        >
          <span
            class="dot"
            :style="{ background: tab.color || 'var(--brand)' }"
          />
          {{ tab.name }}
        </router-link>
        <button class="tab-pill add-tab" @click="openAddTab">
          <Icon name="plus" :size="13" /> 新建
        </button>
      </nav>

      <!-- 页面主体 -->
      <main class="page">
        <!-- 欢迎/空状态（无 Tab 时） -->
        <div v-if="store.loaded && store.tabs.length === 0 && route.path === '/'" class="empty-state" style="margin-top:48px">
          <div class="empty-svg-wrap">
            <EmptyIllustration type="welcome" />
          </div>
          <h3>欢迎使用 Chronicle</h3>
          <p>创建第一个分类开始追踪你的健康指标，例如「慢性肾炎」「心血管」「肝功能」。</p>
          <button class="btn btn-primary mt-3" @click="openAddTab">
            <Icon name="plus" :size="15" /> 创建第一个分类
          </button>
        </div>

        <Transition name="page-fade" mode="out-in" v-else>
          <router-view :key="route.fullPath" />
        </Transition>

        <!-- 免责声明 -->
        <p class="disclaimer">
          本工具仅供个人记录与可视化，不构成医疗建议，不能替代医生的诊断与随访。
        </p>
      </main>
    </div>

    <!-- ── 新建 Tab Sheet ──────────────────────────────────────────────── -->
    <Sheet v-model="addTabOpen" title="新建分类">
      <div class="field">
        <label>分类名称 *</label>
        <input
          class="input"
          v-model="tabForm.name"
          placeholder="例如：慢性肾炎、心血管、肝功能"
          autofocus
          @keyup.enter="saveTab"
        />
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
        <button class="btn btn-outline" @click="addTabOpen = false">取消</button>
        <button class="btn btn-primary" @click="saveTab" :disabled="!tabForm.name.trim()">
          创建分类
        </button>
      </template>
    </Sheet>

    <!-- ── 全局确认弹窗 ──────────────────────────────────────────────────── -->
    <ConfirmDialog />

    <!-- ── Toast ────────────────────────────────────────────────────────── -->
    <div class="toast-wrap" aria-live="polite">
      <TransitionGroup name="toast">
        <div
          v-for="t in toasts"
          :key="t.id"
          class="toast"
          :class="t.type"
        >
          <Icon
            :name="t.type === 'error' ? 'close' : 'check'"
            :size="15"
          />
          {{ t.msg }}
        </div>
      </TransitionGroup>
    </div>
  </div>
</template>

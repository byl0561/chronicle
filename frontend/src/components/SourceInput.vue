<script setup>
/**
 * 检测来源输入框（医院/方法）。
 * - 自由文本输入，聚焦/输入时从历史来源里弹出建议（自定义下拉，非原生 datalist）。
 * - 样式对齐 CustomSelect / .input，符合项目主题。
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'
import Icon from './Icon.vue'

const props = defineProps({
  modelValue:  { type: String, default: '' },
  options:     { type: Array,  default: () => [] }, // 历史来源字符串数组
  placeholder: { type: String, default: '例如：协和医院 · 酶法（可留空）' },
})
const emit = defineEmits(['update:modelValue'])

const open = ref(false)
const el   = ref(null)

// 按当前输入过滤历史来源；输入为空时展示全部
const suggestions = computed(() => {
  const q = (props.modelValue || '').trim().toLowerCase()
  const list = props.options.filter(Boolean)
  if (!q) return list
  return list.filter((s) => s.toLowerCase().includes(q) && s.toLowerCase() !== q)
})

function onInput(e) {
  emit('update:modelValue', e.target.value)
  open.value = true
}
function onFocus() { if (suggestions.value.length) open.value = true }
function pick(val) { emit('update:modelValue', val); open.value = false }
function onClickOut(e) { if (el.value && !el.value.contains(e.target)) open.value = false }
function onKey(e) { if (e.key === 'Escape') open.value = false }

onMounted(() => {
  document.addEventListener('pointerdown', onClickOut)
  document.addEventListener('keydown', onKey)
})
onUnmounted(() => {
  document.removeEventListener('pointerdown', onClickOut)
  document.removeEventListener('keydown', onKey)
})
</script>

<template>
  <div ref="el" class="src" :class="{ 'src--open': open && suggestions.length }">
    <input
      class="input"
      type="text"
      :value="modelValue"
      :placeholder="placeholder"
      @input="onInput"
      @focus="onFocus"
    />
    <Transition name="src-pop">
      <div v-if="open && suggestions.length" class="src-menu" role="listbox">
        <button
          v-for="s in suggestions"
          :key="s"
          type="button"
          role="option"
          class="src-opt"
          :class="{ 'src-opt--on': s === modelValue }"
          @click="pick(s)"
        >
          <Icon name="clock" :size="13" class="src-ico" />
          <span class="src-txt">{{ s }}</span>
          <Icon v-if="s === modelValue" name="check" :size="14" class="src-check" />
        </button>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.src { position: relative; width: 100%; }

.src-menu {
  position: absolute; left: 0; right: 0; top: calc(100% + 5px); z-index: 200;
  background: var(--surface);
  border: 1.5px solid var(--border);
  border-radius: var(--r-lg);
  box-shadow: 0 12px 32px rgba(0,0,0,.12), 0 2px 8px rgba(0,0,0,.07);
  padding: 5px;
  max-height: 216px; overflow-y: auto;
}

.src-opt {
  display: flex; align-items: center; gap: 9px;
  width: 100%; padding: 9px 11px;
  border-radius: var(--r); border: none;
  background: transparent; color: var(--text);
  font-size: 13.5px; cursor: pointer; text-align: left;
  transition: background .1s;
  min-height: 40px;
}
.src-opt:hover   { background: var(--surface-2); }
.src-opt--on     { color: var(--brand); font-weight: 600; background: var(--brand-light); }

.src-ico  { color: var(--muted); flex-shrink: 0; }
.src-txt  { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.src-check { color: var(--brand); flex-shrink: 0; }

.src-pop-enter-active, .src-pop-leave-active {
  transition: opacity .18s ease, transform .18s cubic-bezier(.32,.72,0,1);
}
.src-pop-enter-from, .src-pop-leave-to {
  opacity: 0; transform: translateY(-6px) scale(.97);
}
</style>

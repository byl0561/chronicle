<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import Icon from './Icon.vue'

const props = defineProps({
  modelValue: { default: '' },
  options:    { type: Array, default: () => [] }, // [{ value, label }]
  placeholder:{ type: String, default: '请选择' },
})
const emit = defineEmits(['update:modelValue'])

const open = ref(false)
const el   = ref(null)
const selectedOpt = computed(() => props.options.find(o => o.value === props.modelValue))

function toggle()    { open.value = !open.value }
function pick(val)   { emit('update:modelValue', val); open.value = false }
function onClickOut(e) { if (el.value && !el.value.contains(e.target)) open.value = false }
function onKey(e)    { if (e.key === 'Escape') open.value = false }

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
  <div ref="el" class="csel" :class="{ 'csel--open': open }">
    <button type="button" class="csel-trigger" @click="toggle">
      <span :class="selectedOpt ? 'csel-val' : 'csel-ph'">
        {{ selectedOpt ? selectedOpt.label : placeholder }}
      </span>
      <Icon name="chevron-down" :size="16" class="csel-arrow" />
    </button>
    <Transition name="csel-pop">
      <div v-if="open" class="csel-menu" role="listbox">
        <button
          v-for="opt in options"
          :key="opt.value"
          type="button"
          role="option"
          class="csel-opt"
          :class="{ 'csel-opt--on': opt.value === modelValue }"
          @click="pick(opt.value)"
        >
          <span>{{ opt.label }}</span>
          <Icon v-if="opt.value === modelValue" name="check" :size="14" class="csel-check" />
        </button>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.csel { position: relative; width: 100%; }

.csel-trigger {
  display: flex; align-items: center; justify-content: space-between;
  gap: 8px; width: 100%; padding: 9px 12px;
  border: 1.5px solid var(--border); border-radius: var(--r);
  background: var(--surface); color: var(--text);
  font-size: 14px; cursor: pointer; text-align: left;
  transition: border-color .15s, box-shadow .15s;
  min-height: 42px;
}
.csel--open .csel-trigger {
  border-color: var(--brand);
  box-shadow: 0 0 0 3px var(--brand-alpha);
}

.csel-val { color: var(--text); }
.csel-ph  { color: var(--muted); }

.csel-arrow {
  color: var(--muted); flex-shrink: 0;
  transition: transform .22s cubic-bezier(.32,.72,0,1);
}
.csel--open .csel-arrow { transform: rotate(180deg); }

.csel-menu {
  position: absolute; left: 0; right: 0; top: calc(100% + 5px); z-index: 200;
  background: var(--surface);
  border: 1.5px solid var(--border);
  border-radius: var(--r-lg);
  box-shadow: 0 12px 32px rgba(0,0,0,.12), 0 2px 8px rgba(0,0,0,.07);
  padding: 5px;
  overflow: hidden;
}

.csel-opt {
  display: flex; align-items: center; justify-content: space-between;
  gap: 8px; width: 100%; padding: 10px 12px;
  border-radius: var(--r); border: none;
  background: transparent; color: var(--text);
  font-size: 13.5px; cursor: pointer; text-align: left;
  transition: background .1s;
  min-height: 44px;
}
.csel-opt:hover     { background: var(--surface-2); }
.csel-opt--on       { color: var(--brand); font-weight: 600; background: var(--brand-light); }

.csel-check { color: var(--brand); flex-shrink: 0; }

/* 弹出动画 */
.csel-pop-enter-active, .csel-pop-leave-active {
  transition: opacity .18s ease, transform .18s cubic-bezier(.32,.72,0,1);
}
.csel-pop-enter-from, .csel-pop-leave-to {
  opacity: 0; transform: translateY(-6px) scale(.97);
}
</style>

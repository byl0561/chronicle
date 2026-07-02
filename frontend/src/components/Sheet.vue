<script setup>
import { watch } from 'vue'
import Icon from './Icon.vue'

const props = defineProps({ modelValue: Boolean, title: String })
const emit = defineEmits(['update:modelValue'])

function close() { emit('update:modelValue', false) }

let prevOverflow = ''
watch(() => props.modelValue, (v) => {
  if (v) {
    prevOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = prevOverflow
  }
})
</script>

<template>
  <Teleport to="body">
    <Transition name="sheet">
      <div v-if="modelValue" class="sheet-mask" @click.self="close">
        <div class="sheet" role="dialog" :aria-label="title">
          <div class="sheet-handle" />
          <div class="sheet-head">
            <h3>{{ title }}</h3>
            <button class="btn btn-icon" @click="close" aria-label="关闭">
              <Icon name="close" :size="18" />
            </button>
          </div>
          <div class="sheet-body">
            <slot />
          </div>
          <div v-if="$slots.foot" class="sheet-foot">
            <slot name="foot" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

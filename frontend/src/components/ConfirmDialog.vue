<script setup>
import { watch } from 'vue'
import { confirmState, resolveConfirm } from '../store.js'

let prevOverflow = ''
watch(() => confirmState.open, (v) => {
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
    <Transition name="dialog">
      <div v-if="confirmState.open" class="dialog-mask" @click.self="resolveConfirm(false)">
        <div class="dialog-box" role="alertdialog" aria-modal="true">
          <h3 class="dialog-title">{{ confirmState.title }}</h3>
          <p v-if="confirmState.message" class="dialog-msg">{{ confirmState.message }}</p>
          <div class="dialog-actions">
            <button class="btn btn-outline" @click="resolveConfirm(false)">
              {{ confirmState.cancelText }}
            </button>
            <button
              class="btn"
              :class="confirmState.danger ? 'btn-danger' : 'btn-primary'"
              @click="resolveConfirm(true)"
            >
              {{ confirmState.confirmText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<template>
  <transition name="slide-down"
  @enter="onEnter"
  @after-enter="onAfterEnter"
  @after-leave="emit('height', 0)">
    <div v-if="active" ref="root" class="topbar" role="status" aria-live="polite" :aria-label="ariaText">
      <div class="inner">
        <div class="row">
          <div class="label">
            <span v-if="isIdle">Preparing…</span>
            <span v-else>{{ snap.label }}</span>
          </div>
          <div v-if="!isIdle" class="count">{{ snap.current }} / {{ snap.total }}</div>
        </div>

        <n-progress
          v-if="!isIdle"
          type="line"
          :percentage="percent"
          :height="6"
          processing
        />
        <div v-else class="idle-msg">{{ (snap as any).message }}</div>
        <div v-if="error" class="err">⚠️ {{ error }}</div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed, watch, onMounted, onUnmounted } from 'vue'
import { ref, onUpdated, nextTick } from 'vue'
import { NProgress } from 'naive-ui'
import { useProgress } from '../composables/useProgress'

console.log('[TopProgressBar] mounted')

const props = defineProps<{ active: boolean }>()

const root = ref<HTMLElement | null>(null)
const emit = defineEmits<{ (e:'done'):void; (e:'height', h:number):void }>()

async function onEnter() {
  // Wait until DOM update, then one frame for styles/layout to apply
  await nextTick()
  requestAnimationFrame(measureAndEmit)
}

async function onAfterEnter() {
  // One more pass in case height changes after progress bar mounts
  await nextTick()
  requestAnimationFrame(measureAndEmit)
}

const reportHeight = () => {
  if (root.value) emit('height', root.value.offsetHeight)
}

onMounted(reportHeight)
onUpdated(reportHeight)

watch(() => props.active, async (on) => {
  if (on) {
    await nextTick()
    requestAnimationFrame(measureAndEmit)
    start()
  } else {
    stop()
  }
}, { immediate: true })

const { data, error, start, stop } = useProgress(1000)

const isIdle = computed(() => (data.value as any).status === 'idle')
const snap = computed(() => data.value as any)
const percent = computed(() => {
  if (isIdle.value) return 0
  const c = Number(snap.value.current || 0)
  const t = Math.max(1, Number(snap.value.total || 0))
  return Math.min(100, Math.round((c / t) * 100))
})
const ariaText = computed(() =>
  isIdle.value ? (snap.value.message || 'Waiting…') : `${snap.value.label}: ${snap.value.current} of ${snap.value.total}`
)

watch(() => props.active, (on) => {
  if (on) start()
  else stop()
}, { immediate: true })

// auto-hide shortly after 100%
let hideTimer: number | null = null
watch(percent, (p) => {
  if (p === 100 && !isIdle.value) {
    if (hideTimer) clearTimeout(hideTimer)
    hideTimer = window.setTimeout(() => emit('done'), 1200)
  }
})
onUnmounted(() => hideTimer && clearTimeout(hideTimer))
</script>

<style scoped>
.topbar {
  position: fixed;
  top: 0; left: 0; right: 0;
  z-index: 10000;
  background: rgba(255,255,255,0.92);
  backdrop-filter: blur(8px) saturate(120%);
  box-shadow: 0 2px 10px rgba(0,0,0,0.06);
}
.inner { max-width: 960px; margin: 0 auto; padding: 8px 16px 10px; }
.row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.label { font-weight: 600; }
.count { font-variant-numeric: tabular-nums; opacity: 0.85; }
.idle-msg { font-size: 0.85rem; opacity: 0.75; }
.err { margin-top: 6px; font-size: 0.8rem; color: #c64343; }
.slide-down-enter-active, .slide-down-leave-active { transition: transform .18s ease, opacity .18s ease; }
.slide-down-enter-from, .slide-down-leave-to { transform: translateY(-12px); opacity: 0; }
</style>

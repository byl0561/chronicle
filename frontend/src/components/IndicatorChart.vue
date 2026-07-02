<script setup>
import { onMounted, onUnmounted, watch } from 'vue'
import { ref as vRef } from 'vue'
import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  TimeScale,
  Tooltip,
  Filler,
} from 'chart.js'
import 'chartjs-adapter-date-fns'
import { effectiveRef, isRecordOutOfRange } from '../store.js'

Chart.register(
  LineController, LineElement, PointElement,
  LinearScale, TimeScale, Tooltip, Filler,
)

const props = defineProps({
  indicator: { type: Object, required: true },
  records: { type: Array, default: () => [] },
})

const canvas = vRef(null)
let chart = null

function buildChart() {
  if (chart) { chart.destroy(); chart = null }
  if (!canvas.value || !props.records.length) return

  const sorted = [...props.records].sort(
    (a, b) => new Date(a.measured_at) - new Date(b.measured_at),
  )

  const brandColor = '#3B5BDB'
  const dangerColor = '#D63F3F'
  const bandLine = 'rgba(45,158,95,.30)'
  const bandFill = 'rgba(45,158,95,.09)'
  const gridColor = 'rgba(148,163,184,.14)'
  const tickColor = '#94A3B8'

  // 每条记录各自的有效参考区间（记录自带优先，回退指标默认）
  const highPts = sorted.map((r) => ({ x: r.measured_at, y: effectiveRef(r, props.indicator).high }))
  const lowPts  = sorted.map((r) => ({ x: r.measured_at, y: effectiveRef(r, props.indicator).low }))
  const hasHigh = highPts.some((p) => p.y != null)
  const hasLow  = lowPts.some((p) => p.y != null)

  const pointColors = sorted.map((r) =>
    isRecordOutOfRange(r, props.indicator) ? dangerColor : brandColor,
  )
  const pointRadius = sorted.map((r) =>
    isRecordOutOfRange(r, props.indicator) ? 6 : 4,
  )
  const pointHover = sorted.map((r) =>
    isRecordOutOfRange(r, props.indicator) ? 8 : 6,
  )

  // 阶梯参考带：上限、下限各一条阶梯线，两者都存在时填充成带
  const bandStyle = {
    borderColor: bandLine,
    borderWidth: 1,
    borderDash: [4, 4],
    pointRadius: 0,
    pointHoverRadius: 0,
    stepped: 'after',
    tension: 0,
    spanGaps: true,
  }
  const datasets = []
  if (hasHigh) {
    datasets.push({ ...bandStyle, label: '参考上限', data: highPts, fill: false })
  }
  if (hasLow) {
    datasets.push({
      ...bandStyle, label: '参考下限', data: lowPts,
      fill: hasHigh ? '-1' : false,
      backgroundColor: bandFill,
    })
  }

  // 实际值折线（置于最上层）
  datasets.push({
    __isValue: true,
    label: '实测值',
    data: sorted.map((r) => ({ x: r.measured_at, y: r.value })),
    borderColor: brandColor,
    borderWidth: 2.5,
    fill: false,
    pointBackgroundColor: pointColors,
    pointBorderColor: '#fff',
    pointBorderWidth: 2,
    pointRadius,
    pointHoverRadius: pointHover,
    tension: 0.35,
  })

  chart = new Chart(canvas.value, {
    type: 'line',
    data: { datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(15,23,42,.92)',
          titleColor: '#94A3B8',
          bodyColor: '#F1F5F9',
          padding: 12,
          cornerRadius: 10,
          boxPadding: 4,
          titleFont: { size: 11.5 },
          bodyFont: { size: 15, weight: '700' },
          // 只对实测值点显示 tooltip，忽略参考带
          filter: (item) => item.dataset.__isValue === true,
          callbacks: {
            title: (items) => items[0]?.label?.slice(0, 10) ?? '',
            label: (ctx) => {
              const rec = sorted[ctx.dataIndex]
              const unit = props.indicator.unit ? ` ${props.indicator.unit}` : ''
              const oor = rec ? isRecordOutOfRange(rec, props.indicator) : false
              const { low, high } = rec ? effectiveRef(rec, props.indicator) : {}
              const range = (low != null || high != null)
                ? `  区间 ${low ?? '—'}–${high ?? '∞'}`
                : ''
              const src = rec?.source ? `  · ${rec.source}` : ''
              return ` ${ctx.parsed.y}${unit}${oor ? '  ⚠ 越界' : ''}${range}${src}`
            },
          },
        },
      },
      scales: {
        x: {
          type: 'time',
          time: {
            tooltipFormat: 'yyyy-MM-dd',
            displayFormats: { day: 'M/d', month: 'yyyy-MM', year: 'yyyy' },
          },
          grid: { color: gridColor, drawTicks: false },
          ticks: {
            color: tickColor, maxTicksLimit: 7, maxRotation: 0,
            font: { size: 11 }, padding: 6,
          },
          border: { color: 'transparent' },
        },
        y: {
          grid: { color: gridColor, drawTicks: false },
          ticks: {
            color: tickColor, maxTicksLimit: 6,
            font: { size: 11 }, padding: 8,
            callback: (v) => props.indicator.unit ? `${v} ${props.indicator.unit}` : v,
          },
          border: { color: 'transparent' },
        },
      },
    },
  })
}

onMounted(buildChart)
watch(() => [props.records, props.indicator], buildChart, { deep: true })
onUnmounted(() => chart?.destroy())
</script>

<template>
  <div v-if="records.length" class="chart-wrap">
    <canvas ref="canvas" />
  </div>
  <div v-else class="chart-empty">
    <div class="chart-empty-icon">📈</div>
    <div class="chart-empty-text">暂无记录数据，添加第一条记录后图表将显示在这里</div>
  </div>
</template>

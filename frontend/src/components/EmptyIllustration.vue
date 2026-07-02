<script setup>
defineProps({
  type: {
    type: String,
    default: 'chart',
    // chart | clipboard | welcome
  },
})
</script>

<template>
  <!-- 仪表盘空状态：还没有指标 -->
  <svg v-if="type === 'chart'"
    class="empty-svg" viewBox="0 0 160 120" fill="none" xmlns="http://www.w3.org/2000/svg">
    <!-- 坐标轴 -->
    <line x1="24" y1="90" x2="136" y2="90" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" opacity=".4"/>
    <line x1="24" y1="20" x2="24"  y2="90" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" opacity=".4"/>
    <!-- 刻度点 -->
    <circle cx="24" cy="70" r="2" fill="currentColor" opacity=".3"/>
    <circle cx="24" cy="50" r="2" fill="currentColor" opacity=".3"/>
    <circle cx="24" cy="30" r="2" fill="currentColor" opacity=".3"/>
    <!-- 虚线折线（占位趋势） -->
    <polyline
      points="36,75 58,60 80,50 102,55 124,38"
      stroke="currentColor" stroke-width="2" stroke-dasharray="5 4"
      stroke-linecap="round" stroke-linejoin="round" opacity=".35"
    />
    <!-- 数据点 -->
    <circle cx="36"  cy="75" r="3.5" fill="currentColor" opacity=".25"/>
    <circle cx="80"  cy="50" r="3.5" fill="currentColor" opacity=".25"/>
    <circle cx="124" cy="38" r="3.5" fill="currentColor" opacity=".25"/>
    <!-- 参考带（横向绿色区间示意） -->
    <rect x="24" y="44" width="112" height="20" fill="currentColor" opacity=".06" rx="2"/>
    <!-- 右下角「+」按钮圆 -->
    <circle cx="124" cy="90" r="16" fill="currentColor" opacity=".12"/>
    <line x1="124" y1="83" x2="124" y2="97" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
    <line x1="117" y1="90" x2="131" y2="90" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
  </svg>

  <!-- 历史记录空状态：还没有记录 -->
  <svg v-else-if="type === 'clipboard'"
    class="empty-svg" viewBox="0 0 120 130" fill="none" xmlns="http://www.w3.org/2000/svg">
    <!-- 剪贴板本体 -->
    <rect x="20" y="22" width="80" height="96" rx="8" stroke="currentColor" stroke-width="2" opacity=".45"/>
    <!-- 顶部夹子 -->
    <rect x="40" y="14" width="40" height="16" rx="8" stroke="currentColor" stroke-width="2" opacity=".45"/>
    <rect x="50" y="16" width="20" height="12" rx="6" fill="currentColor" opacity=".12"/>
    <!-- 线条（占位内容） -->
    <line x1="34" y1="56" x2="86" y2="56" stroke="currentColor" stroke-width="2" stroke-linecap="round" opacity=".3"/>
    <line x1="34" y1="70" x2="72" y2="70" stroke="currentColor" stroke-width="2" stroke-linecap="round" opacity=".3"/>
    <line x1="34" y1="84" x2="80" y2="84" stroke="currentColor" stroke-width="2" stroke-linecap="round" opacity=".3"/>
    <!-- 「+」符号居中 -->
    <circle cx="60" cy="42" r="12" fill="currentColor" opacity=".1"/>
    <line x1="60" y1="36" x2="60" y2="48" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>
    <line x1="54" y1="42" x2="66" y2="42" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>
  </svg>

  <!-- 欢迎页：没有任何分类 -->
  <svg v-else-if="type === 'welcome'"
    class="empty-svg" viewBox="0 0 180 110" fill="none" xmlns="http://www.w3.org/2000/svg">
    <!-- 心电图波形 -->
    <polyline
      points="10,60 38,60 50,20 62,95 72,42 84,60 112,60 124,45 136,75 148,60 170,60"
      stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" opacity=".5"
    />
    <!-- 外框装饰（心跳监护仪屏幕） -->
    <rect x="4" y="8" width="172" height="94" rx="10"
      stroke="currentColor" stroke-width="1.5" opacity=".18"/>
    <!-- 左上角小圆点（电源） -->
    <circle cx="16" cy="20" r="4" fill="currentColor" opacity=".25"/>
    <!-- 右上角「正常」状态文字占位 -->
    <rect x="130" y="14" width="36" height="12" rx="6" fill="currentColor" opacity=".12"/>
    <!-- 底部参考线 -->
    <line x1="20" y1="90" x2="160" y2="90" stroke="currentColor" stroke-width="1" stroke-dasharray="4 3" opacity=".2"/>
  </svg>
</template>

<style scoped>
.empty-svg {
  width: 130px;
  height: auto;
  color: var(--brand);
  opacity: .75;
}
</style>

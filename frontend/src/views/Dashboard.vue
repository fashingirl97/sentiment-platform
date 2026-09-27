<template>
  <div class="page-container">
    <!-- 核心指标卡片 -->
    <el-row :gutter="16">
      <el-col :span="4" v-for="card in metricCards" :key="card.label">
        <div class="card metric-card">
          <div class="metric-icon" :style="{ background: card.bg }">
            <el-icon :size="22" :color="card.color"><component :is="card.icon" /></el-icon>
          </div>
          <div>
            <div class="metric-label">{{ card.label }}</div>
            <div class="metric-value" :style="{ color: card.color }">{{ card.value }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 声量趋势 + 情感分布 -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="16">
        <div class="card">
          <div class="card-title">
            全网舆情声量趋势
            <el-button size="small" type="primary" style="margin-left: auto" @click="onIngest">模拟接入新舆情</el-button>
          </div>
          <div ref="trendChart" style="height: 320px"></div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="card">
          <div class="card-title">情感倾向分布</div>
          <div ref="sentimentChart" style="height: 320px"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 词云 + 实时预警 -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="14">
        <div class="card" style="height: 340px">
          <div class="card-title">热点词云</div>
          <div class="word-cloud">
            <span v-for="w in hotWords" :key="w.name" :style="wordStyle(w)">{{ w.name }}</span>
          </div>
        </div>
      </el-col>
      <el-col :span="10">
        <div class="card" style="height: 340px">
          <div class="card-title">实时风险预警</div>
          <div class="alert-list">
            <div v-for="a in displayAlerts" :key="a.id" class="alert-item">
              <el-tag :type="levelTag(a.level)" size="small" effect="dark">{{ a.level }}</el-tag>
              <div class="alert-body">
                <div class="alert-title">{{ a.title }}</div>
                <div class="muted">{{ a.created_at }} · {{ a.type }}</div>
              </div>
            </div>
            <el-empty v-if="!displayAlerts.length" description="暂无预警" :image-size="60" />
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import api from '../api'

const overview = ref({})
const trend = ref([])
const sentiment = ref([])
const hotWords = ref([])
const alerts = ref([])

const trendChart = ref(null)
const sentimentChart = ref(null)
let trendInstance = null
let sentimentInstance = null
let rotateTimer = null

const metricCards = computed(() => [
  { label: '全网总声量', value: overview.value.total_volume ?? '-', color: '#409eff', bg: '#ecf5ff', icon: 'ChatDotRound' },
  { label: '今日新增', value: overview.value.today_volume ?? '-', color: '#67c23a', bg: '#f0f9eb', icon: 'TrendCharts' },
  { label: '负面率', value: (overview.value.negative_ratio ?? 0) + '%', color: '#f56c6c', bg: '#fef0f0', icon: 'Warning' },
  { label: '活跃事件', value: overview.value.active_events ?? '-', color: '#e6a23c', bg: '#fdf6ec', icon: 'Flag' },
  { label: '高危预警', value: overview.value.high_risk_alerts ?? '-', color: '#f56c6c', bg: '#fef0f0', icon: 'Bell' },
])

const displayAlerts = ref([])

function levelTag(level) {
  return { S: 'danger', A: 'danger', B: 'warning', C: 'info' }[level] || 'info'
}

function wordStyle(w) {
  const size = Math.max(12, Math.min(40, w.value * 1.5))
  const colors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399', '#5c6ac4', '#13c2c2']
  const color = colors[Math.abs(w.name.length) % colors.length]
  return { fontSize: size + 'px', color, opacity: 0.85, margin: '4px 6px', display: 'inline-block' }
}

async function loadAll() {
  const [ov, tr, se, hw, al] = await Promise.all([
    api.get('/dashboard/overview'),
    api.get('/dashboard/trend', { params: { hours: 48 } }),
    api.get('/dashboard/sentiment'),
    api.get('/dashboard/hot-words', { params: { limit: 60 } }),
    api.get('/dashboard/risk-alerts'),
  ])
  overview.value = ov
  trend.value = tr
  sentiment.value = se
  hotWords.value = hw
  alerts.value = al
  renderCharts()
  rotateAlerts()
}

function renderCharts() {
  if (trendInstance) {
    trendInstance.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['正向', '中性', '负向'], bottom: 0 },
      grid: { left: 40, right: 20, top: 30, bottom: 40 },
      xAxis: { type: 'category', data: trend.value.map((t) => t.time), boundaryGap: false },
      yAxis: { type: 'value' },
      series: [
        { name: '正向', type: 'line', stack: 'total', smooth: true, areaStyle: {}, data: trend.value.map((t) => t.positive), itemStyle: { color: '#67c23a' } },
        { name: '中性', type: 'line', stack: 'total', smooth: true, areaStyle: {}, data: trend.value.map((t) => t.neutral), itemStyle: { color: '#909399' } },
        { name: '负向', type: 'line', stack: 'total', smooth: true, areaStyle: {}, data: trend.value.map((t) => t.negative), itemStyle: { color: '#f56c6c' } },
      ],
    })
  }
  if (sentimentInstance) {
    sentimentInstance.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} 条 ({d}%)' },
      legend: { bottom: 0 },
      color: ['#67c23a', '#909399', '#f56c6c'],
      series: [
        {
          type: 'pie',
          radius: ['45%', '70%'],
          avoidLabelOverlap: true,
          itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
          label: { formatter: '{b}\n{c} 条' },
          data: sentiment.value.map((s) => ({ name: s.name, value: s.value })),
        },
      ],
    })
  }
}

function rotateAlerts() {
  clearInterval(rotateTimer)
  const items = alerts.value.slice()
  let idx = 0
  const show = () => {
    if (items.length <= 8) {
      displayAlerts.value = items
    } else {
      displayAlerts.value = Array.from({ length: 8 }, (_, i) => items[(idx + i) % items.length])
      idx = (idx + 1) % items.length
    }
  }
  show()
  rotateTimer = setInterval(show, 3000)
}

async function onIngest() {
  try {
    const data = await api.post('/posts/ingest')
    ElMessage.success(`已接入新舆情（${data.alerts.length} 条预警触发）`)
    await loadAll()
  } catch (e) {
    ElMessage.error('接入失败')
  }
}

function onResize() {
  trendInstance?.resize()
  sentimentInstance?.resize()
}

onMounted(async () => {
  trendInstance = echarts.init(trendChart.value)
  sentimentInstance = echarts.init(sentimentChart.value)
  window.addEventListener('resize', onResize)
  await loadAll()
})

onBeforeUnmount(() => {
  clearInterval(rotateTimer)
  window.removeEventListener('resize', onResize)
  trendInstance?.dispose()
  sentimentInstance?.dispose()
})
</script>

<style scoped>
.metric-card {
  display: flex;
  align-items: center;
  gap: 12px;
}
.metric-icon {
  width: 46px;
  height: 46px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.metric-label {
  font-size: 13px;
  color: #909399;
}
.metric-value {
  font-size: 24px;
  font-weight: 700;
}
.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
}
.word-cloud {
  height: 260px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.alert-list {
  height: 260px;
  overflow: hidden;
}
.alert-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 4px;
  border-bottom: 1px dashed #ebeef5;
}
.alert-body {
  flex: 1;
}
.alert-title {
  font-size: 13px;
  color: #303133;
  margin-bottom: 2px;
}
</style>

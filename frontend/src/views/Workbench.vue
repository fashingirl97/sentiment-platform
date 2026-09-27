<template>
  <div class="page-container workbench">
    <!-- 筛选区 -->
    <div class="card filter-bar">
      <el-select v-model="filters.topic_id" placeholder="监测主题" clearable style="width: 140px" @change="loadPosts">
        <el-option v-for="t in topics" :key="t.id" :label="t.name" :value="t.id" />
      </el-select>
      <el-select v-model="filters.source_id" placeholder="信源渠道" clearable style="width: 120px" @change="loadPosts">
        <el-option v-for="s in sources" :key="s.id" :label="s.name" :value="s.id" />
      </el-select>
      <el-select v-model="filters.sentiment" placeholder="情感标签" clearable style="width: 110px" @change="loadPosts">
        <el-option label="正向" value="positive" />
        <el-option label="中性" value="neutral" />
        <el-option label="负向" value="negative" />
      </el-select>
      <el-select v-model="filters.risk_level" placeholder="风险等级" clearable style="width: 110px" @change="loadPosts">
        <el-option label="S 极高危" value="S" />
        <el-option label="A 高危" value="A" />
        <el-option label="B 中危" value="B" />
        <el-option label="C 低危" value="C" />
      </el-select>
      <el-select v-model="filters.time_range" placeholder="时间跨度" style="width: 120px" @change="loadPosts">
        <el-option label="近 6 小时" value="6" />
        <el-option label="近 12 小时" value="12" />
        <el-option label="近 24 小时" value="24" />
        <el-option label="近 48 小时" value="48" />
        <el-option label="全部" value="0" />
      </el-select>
      <el-input v-model="filters.keyword" placeholder="关键词搜索" clearable style="width: 180px" @keyup.enter="loadPosts" @clear="loadPosts" />
      <el-button type="primary" @click="loadPosts">筛选</el-button>
    </div>

    <el-row :gutter="16" style="margin-top: 16px">
      <!-- 左：监测流 -->
      <el-col :span="9">
        <div class="card post-panel">
          <div class="card-title">舆情监测流 <span class="muted">（共 {{ postTotal }} 条）</span></div>
          <div class="post-list">
            <div v-for="p in posts" :key="p.id" class="post-item" :class="{ active: p.id === currentPost?.id }" @click="openPost(p)">
              <div class="post-head">
                <el-tag size="small" effect="plain">{{ p.platform }}</el-tag>
                <span class="post-author">{{ p.author }}</span>
                <el-tag size="small" :type="sentimentTag(p.sentiment)" effect="light">{{ sentimentText(p.sentiment) }}</el-tag>
                <el-tag size="small" :type="riskTag(p.risk_level)" effect="dark">{{ p.risk_level }}</el-tag>
              </div>
              <div class="post-content">{{ p.content }}</div>
              <div class="post-foot muted">
                <span>{{ p.publish_time }}</span>
                <span v-if="p.emotion">· {{ p.emotion }}</span>
                <span v-if="p.ocr_text || p.asr_text">· 多模态</span>
                <span style="margin-left:auto">👍{{ p.like_count }} 💬{{ p.comment_count }} 🔄{{ p.share_count }}</span>
              </div>
            </div>
            <el-empty v-if="!posts.length" description="暂无舆情数据" :image-size="60" />
          </div>
          <el-pagination
            v-model:current-page="page"
            :page-size="20"
            :total="postTotal"
            layout="prev, pager, next, total"
            small
            style="margin-top: 10px; justify-content: center"
            @current-change="loadPosts"
          />
        </div>
      </el-col>

      <!-- 右：事件研判 + 处置 -->
      <el-col :span="15">
        <div class="card">
          <div class="card-title" style="gap: 10px">
            事件研判
            <el-select v-model="currentEventId" placeholder="选择事件" style="width: 300px" @change="onEventChange">
              <el-option v-for="e in events" :key="e.id" :label="e.title" :value="e.id" />
            </el-select>
          </div>
          <el-tabs v-model="activeTab" @tab-change="onTabChange">
            <!-- 研判分析 -->
            <el-tab-pane label="事件分析与溯源" name="analysis">
              <div class="event-overview" v-if="event">
                <el-tag :type="riskTag(event.risk_level)" effect="dark" size="large">{{ event.risk_level }} 级</el-tag>
                <el-tag type="info" effect="plain">{{ event.category }}</el-tag>
                <el-tag effect="plain">热度 {{ event.heat_index }}</el-tag>
                <el-tag effect="plain">声量 {{ event.post_count }}</el-tag>
                <el-tag type="danger" effect="plain">负面率 {{ event.sentiment_negative_ratio }}%</el-tag>
              </div>
              <el-row :gutter="16">
                <el-col :span="12">
                  <div class="sub-title">传播溯源时间线</div>
                  <el-timeline>
                    <el-timeline-item v-for="(n, i) in timeline" :key="i" :timestamp="n.time" :type="timelineType(n.node_type)" placement="top">
                      <b :class="nodeClass(n.node_type)">{{ n.node_type }}</b>
                      <div class="node-title">{{ n.title }}</div>
                      <div class="muted">{{ n.description }}</div>
                    </el-timeline-item>
                  </el-timeline>
                </el-col>
                <el-col :span="12">
                  <div class="sub-title">核心观点聚类</div>
                  <div v-for="(c, i) in clusters" :key="i" class="cluster-item">
                    <div class="cluster-head">
                      <span>{{ c.label }}</span>
                      <el-tag size="small" :type="sentimentTag(c.sentiment)">{{ c.count }} 条</el-tag>
                      <el-tag size="small" type="info" effect="plain">{{ c.intent }}</el-tag>
                    </div>
                    <div class="muted">{{ c.representative_text }}</div>
                  </div>
                </el-col>
              </el-row>
              <div class="sub-title" style="margin-top: 8px">实体关系图谱</div>
              <div ref="graphChart" style="height: 320px"></div>
            </el-tab-pane>

            <!-- 处置协同 -->
            <el-tab-pane label="处置协同与应对" name="disposition">
              <div class="sub-title">风险等级人工复核与处置动作</div>
              <div class="action-group">
                <el-radio-group v-model="disposition.action">
                  <el-radio-button label="跟踪" />
                  <el-radio-button label="已核实" />
                  <el-radio-button label="辟谣处理" />
                  <el-radio-button label="已处理" />
                  <el-radio-button label="忽略" />
                </el-radio-group>
              </div>
              <el-input v-model="disposition.note" type="textarea" :rows="2" placeholder="填写处置备注（可选）" style="margin: 10px 0" />
              <div style="display: flex; gap: 10px">
                <el-button type="primary" @click="onDisposition">提交处置</el-button>
                <el-button type="success" plain @click="onDraftResponse">生成公关回应草案</el-button>
              </div>

              <div v-if="draft" class="draft-box">
                <div class="sub-title">大模型公关回应草案</div>
                <div class="draft-md" v-html="draftHtml"></div>
              </div>

              <div class="sub-title" style="margin-top: 16px">处置记录</div>
              <el-timeline>
                <el-timeline-item v-for="d in dispositions" :key="d.id" :timestamp="d.created_at">
                  <b>{{ d.operator }}</b> · {{ d.action }}
                  <div v-if="d.note" class="muted">{{ d.note }}</div>
                </el-timeline-item>
              </el-timeline>
            </el-tab-pane>
          </el-tabs>
        </div>
      </el-col>
    </el-row>

    <!-- 多模态详情弹窗 -->
    <el-dialog v-model="postDialog" title="舆情内容详情" width="640px">
      <template v-if="currentPost">
        <div class="detail-head">
          <el-tag size="small">{{ currentPost.platform }}</el-tag>
          <span><b>{{ currentPost.author }}</b></span>
          <el-tag size="small" :type="sentimentTag(currentPost.sentiment)">{{ sentimentText(currentPost.sentiment) }}</el-tag>
          <el-tag size="small" :type="riskTag(currentPost.risk_level)" effect="dark">{{ currentPost.risk_level }} 级</el-tag>
          <span class="muted">{{ currentPost.publish_time }}</span>
        </div>
        <p class="detail-content">{{ currentPost.content }}</p>
        <div v-if="currentPost.ocr_text" class="multimodal-box">
          <div class="sub-title">图片 OCR 识别文本</div>
          <p>{{ currentPost.ocr_text }}</p>
        </div>
        <div v-if="currentPost.asr_text" class="multimodal-box">
          <div class="sub-title">音视频 ASR 转录文本</div>
          <p>{{ currentPost.asr_text }}</p>
        </div>
        <div v-if="currentPost.entity_names?.length" class="multimodal-box">
          <div class="sub-title">识别实体</div>
          <el-tag v-for="e in currentPost.entity_names" :key="e" size="small" style="margin-right: 6px">{{ e }}</el-tag>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import api from '../api'

const topics = ref([])
const sources = ref([])
const events = ref([])
const posts = ref([])
const postTotal = ref(0)
const page = ref(1)

const filters = ref({ topic_id: null, source_id: null, sentiment: null, risk_level: null, time_range: '48', keyword: '' })

const currentEventId = ref(null)
const event = ref(null)
const clusters = ref([])
const timeline = ref([])
const graph = ref({ nodes: [], edges: [] })

const activeTab = ref('analysis')
const disposition = ref({ action: '跟踪', note: '' })
const draft = ref('')
const dispositions = ref([])

const currentPost = ref(null)
const postDialog = ref(false)

const graphChart = ref(null)
let graphInstance = null

const sentimentText = (s) => ({ positive: '正向', neutral: '中性', negative: '负向' }[s] || s)
const sentimentTag = (s) => ({ positive: 'success', neutral: 'info', negative: 'danger' }[s] || 'info')
const riskTag = (r) => ({ S: 'danger', A: 'danger', B: 'warning', C: 'info' }[r] || 'info')
const timelineType = (t) => ({ 首发: 'primary', 引爆: 'danger', 扩散: 'warning' }[t] || 'primary')
const nodeClass = (t) => ({ 首发: 'text-success', 引爆: 'text-danger', 扩散: 'text-warning' }[t] || '')

const draftHtml = computed(() => marked.parse(draft.value || ''))

async function loadBase() {
  const [t, s, e] = await Promise.all([api.get('/topics'), api.get('/sources'), api.get('/events')])
  topics.value = t
  sources.value = s
  events.value = e
  if (e.length && !currentEventId.value) {
    currentEventId.value = e[0].id
    await loadEvent()
  }
}

async function loadPosts() {
  const params = { page: page.value, page_size: 20, ...filters.value }
  if (filters.value.time_range && filters.value.time_range !== '0') {
    const d = new Date(Date.now() - Number(filters.value.time_range) * 3600 * 1000)
    params.start_time = formatDate(d)
  }
  const data = await api.get('/posts', { params })
  posts.value = data.items
  postTotal.value = data.total
}

async function loadEvent() {
  if (!currentEventId.value) return
  const [detail, clu, tl, gr, dis] = await Promise.all([
    api.get(`/events/${currentEventId.value}`),
    api.get(`/events/${currentEventId.value}/clusters`),
    api.get(`/events/${currentEventId.value}/timeline`),
    api.get(`/events/${currentEventId.value}/graph`),
    api.get(`/events/${currentEventId.value}/dispositions`),
  ])
  event.value = detail
  clusters.value = clu
  timeline.value = tl
  graph.value = gr
  dispositions.value = dis
  draft.value = ''
  renderGraph()
}

function onEventChange() {
  loadEvent()
}

function onTabChange(name) {
  if (name === 'analysis') {
    setTimeout(() => graphInstance?.resize(), 50)
  }
}

function renderGraph() {
  if (!graphInstance) return
  const typeIndex = { 机构: 0, 产品: 1, 人物: 2 }
  const categories = [{ name: '机构' }, { name: '产品' }, { name: '人物' }]
  graphInstance.setOption({
    tooltip: { formatter: (p) => (p.dataType === 'node' ? `${p.name}（${p.data.type}）` : `${p.data.source} → ${p.data.target}`) },
    legend: [{ data: categories.map((c) => c.name) }],
    series: [
      {
        type: 'graph',
        layout: 'force',
        roam: true,
        categories,
        data: graph.value.nodes.map((n) => ({
          name: n.name,
          type: n.type,
          category: typeIndex[n.type] ?? 0,
          symbolSize: Math.max(24, Math.min(60, n.weight * 8)),
        })),
        links: graph.value.edges.map((e) => ({ source: e.source, target: e.target, value: e.weight, label: { show: true, formatter: e.relation, fontSize: 10 } })),
        label: { show: true, position: 'right', fontSize: 12 },
        force: { repulsion: 260, edgeLength: 80 },
        lineStyle: { color: '#c0c4cc', curveness: 0.1 },
      },
    ],
  })
}

async function openPost(p) {
  currentPost.value = p
  postDialog.value = true
}

async function onDisposition() {
  if (!currentEventId.value) return
  try {
    await api.post(`/events/${currentEventId.value}/disposition`, disposition.value)
    ElMessage.success('处置已提交')
    disposition.value.note = ''
    await loadEvent()
  } catch (e) {
    ElMessage.error('提交失败')
  }
}

async function onDraftResponse() {
  if (!currentEventId.value) return
  try {
    const data = await api.post(`/events/${currentEventId.value}/draft-response`, { event_id: currentEventId.value })
    draft.value = data.response
    ElMessage.success('回应草案已生成')
  } catch (e) {
    ElMessage.error('生成失败')
  }
}

function formatDate(d) {
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
}

function onResize() {
  graphInstance?.resize()
}

onMounted(async () => {
  graphInstance = echarts.init(graphChart.value)
  window.addEventListener('resize', onResize)
  await loadBase()
  await loadPosts()
  renderGraph()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  graphInstance?.dispose()
})
</script>

<style scoped>
.workbench {
  display: flex;
  flex-direction: column;
}
.filter-bar {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
}
.card-title {
  font-size: 15px;
  font-weight: 600;
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}
.post-panel {
  height: calc(100vh - 210px);
  display: flex;
  flex-direction: column;
}
.post-list {
  flex: 1;
  overflow: auto;
}
.post-item {
  padding: 10px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
}
.post-item:hover,
.post-item.active {
  border-color: #409eff;
  background: #f0f7ff;
}
.post-head {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}
.post-author {
  font-weight: 600;
  font-size: 13px;
}
.post-content {
  font-size: 13px;
  color: #303133;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.post-foot {
  display: flex;
  gap: 6px;
  margin-top: 6px;
}
.event-overview {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}
.sub-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 10px;
}
.node-title {
  font-size: 13px;
  color: #303133;
}
.cluster-item {
  padding: 8px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  margin-bottom: 8px;
}
.cluster-head {
  display: flex;
  gap: 6px;
  align-items: center;
  margin-bottom: 4px;
  font-weight: 600;
  font-size: 13px;
}
.action-group {
  margin-bottom: 4px;
}
.draft-box {
  margin-top: 16px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 14px;
  background: #fafafa;
}
.draft-md {
  font-size: 13px;
  line-height: 1.7;
  color: #303133;
}
.draft-md :deep(h2) {
  font-size: 15px;
  margin: 10px 0 6px;
}
.detail-head {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 12px;
}
.detail-content {
  font-size: 14px;
  line-height: 1.7;
}
.multimodal-box {
  margin-top: 12px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 6px;
  font-size: 13px;
}
</style>

<template>
  <div class="page-container">
    <div class="card">
      <div class="toolbar">
        <div class="card-title" style="margin: 0">研判报告列表</div>
        <el-button type="primary" @click="genDialog = true">生成报告</el-button>
      </div>

      <el-table :data="reports" stripe style="margin-top: 12px">
        <el-table-column prop="title" label="报告标题" min-width="260" />
        <el-table-column label="类型" width="110">
          <template #default="{ row }">
            <el-tag :type="row.type === 'special' ? 'danger' : 'primary'" effect="plain">{{ row.type === 'special' ? '突发事件专项' : '周期性简报' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_by" label="创建人" width="120" />
        <el-table-column prop="created_at" label="生成时间" width="180" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="preview(row)">预览</el-button>
            <el-button link type="success" @click="exportMd(row)">导出 Markdown</el-button>
            <el-button link type="warning" @click="preview(row, true)">导出 PDF</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 生成报告对话框 -->
    <el-dialog v-model="genDialog" title="生成研判报告" width="480px">
      <el-form label-width="90px">
        <el-form-item label="报告类型">
          <el-radio-group v-model="genForm.type">
            <el-radio-button label="special">突发事件专项</el-radio-button>
            <el-radio-button label="periodic">周期性简报</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="genForm.type === 'special'" label="选择事件">
          <el-select v-model="genForm.event_id" placeholder="请选择事件" style="width: 100%">
            <el-option v-for="e in events" :key="e.id" :label="e.title" :value="e.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="报告标题">
          <el-input v-model="genForm.title" placeholder="留空则自动生成标题" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="genDialog = false">取消</el-button>
        <el-button type="primary" :loading="generating" @click="onGenerate">生成</el-button>
      </template>
    </el-dialog>

    <!-- 预览对话框 -->
    <el-dialog v-model="previewDialog" title="报告预览" width="820px" top="4vh" :close-on-click-modal="false">
      <div class="report-body">
        <div class="report-md" v-html="previewHtml"></div>
      </div>
      <template #footer>
        <el-button @click="previewDialog = false">关闭</el-button>
        <el-button type="success" @click="exportMd(previewReport)">导出 Markdown</el-button>
        <el-button type="warning" @click="exportPdf(previewReport)">导出 PDF</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { marked } from 'marked'
import api from '../api'

const reports = ref([])
const events = ref([])
const genDialog = ref(false)
const previewDialog = ref(false)
const generating = ref(false)

const genForm = ref({ type: 'special', event_id: null, title: '' })
const previewReport = ref(null)
const previewHtml = computed(() => marked.parse(previewReport.value?.content_md || ''))

async function loadReports() {
  reports.value = await api.get('/reports')
}

async function loadEvents() {
  events.value = await api.get('/events')
}

async function onGenerate() {
  if (genForm.value.type === 'special' && !genForm.value.event_id) {
    ElMessage.warning('请选择事件')
    return
  }
  generating.value = true
  try {
    await api.post('/reports/generate', genForm.value)
    ElMessage.success('报告生成成功')
    genDialog.value = false
    genForm.value = { type: 'special', event_id: null, title: '' }
    await loadReports()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '生成失败')
  } finally {
    generating.value = false
  }
}

function preview(row, isPdf = false) {
  previewReport.value = row
  if (isPdf) {
    // 打开预览后延迟执行打印
    previewDialog.value = true
    setTimeout(() => exportPdf(row), 600)
  } else {
    previewDialog.value = true
  }
}

function exportMd(row) {
  const blob = new Blob([row.content_md], { type: 'text/markdown;charset=utf-8' })
  downloadBlob(blob, `${row.title}.md`)
}

function exportPdf(row) {
  const html = renderReportHtml(row)
  const w = window.open('', '_blank')
  if (!w) {
    ElMessage.warning('浏览器拦截了弹窗，请允许弹窗后重试')
    return
  }
  w.document.write(html)
  w.document.close()
  setTimeout(() => {
    w.focus()
    w.print()
  }, 500)
}

function renderReportHtml(row) {
  const body = marked.parse(row.content_md || '')
  return `<!DOCTYPE html><html><head><meta charset="utf-8"><title>${row.title}</title>
<style>
body{font-family:'Microsoft YaHei',sans-serif;margin:40px;color:#303133;line-height:1.8}
h1{font-size:24px;text-align:center}h2{font-size:18px;border-bottom:2px solid #409eff;padding-bottom:6px;margin-top:24px}
table{border-collapse:collapse;width:100%;margin:12px 0}td,th{border:1px solid #dcdfe6;padding:8px;font-size:13px}th{background:#f5f7fa}
blockquote{color:#909399;border-left:3px solid #dcdfe6;padding-left:12px}
</style></head><body>${body}</body></html>`
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

async function remove(row) {
  await ElMessageBox.confirm('确认删除该报告？', '提示', { type: 'warning' })
  await api.delete(`/reports/${row.id}`)
  ElMessage.success('已删除')
  await loadReports()
}

onMounted(async () => {
  await Promise.all([loadReports(), loadEvents()])
})
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.card-title {
  font-size: 15px;
  font-weight: 600;
}
.report-body {
  max-height: 70vh;
  overflow: auto;
  padding: 10px 6px;
}
.report-md {
  line-height: 1.8;
  color: #303133;
}
.report-md :deep(h1) {
  font-size: 22px;
  text-align: center;
}
.report-md :deep(h2) {
  font-size: 17px;
  border-bottom: 2px solid #409eff;
  padding-bottom: 6px;
  margin-top: 20px;
}
.report-md :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 10px 0;
}
.report-md :deep(td),
.report-md :deep(th) {
  border: 1px solid #dcdfe6;
  padding: 7px 9px;
  font-size: 13px;
}
.report-md :deep(th) {
  background: #f5f7fa;
}
.report-md :deep(blockquote) {
  color: #909399;
  border-left: 3px solid #dcdfe6;
  padding-left: 12px;
  margin-left: 0;
}
</style>

<template>
  <div class="page-container">
    <div class="card">
      <el-tabs v-model="tab">
        <!-- 监测主题 -->
        <el-tab-pane label="监测主题词包" name="topics">
          <div class="toolbar">
            <el-button type="primary" @click="openTopicDialog()">新增监测主题</el-button>
          </div>
          <el-table :data="topics" stripe style="margin-top: 12px">
            <el-table-column prop="name" label="主题名称" min-width="160" />
            <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
            <el-table-column label="关键词" min-width="260">
              <template #default="{ row }">
                <el-tag v-for="k in row.keywords" :key="k" size="small" style="margin: 2px 4px 2px 0">{{ k }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">{{ row.status === 'active' ? '启用' : '停用' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="170" />
            <el-table-column label="操作" width="140">
              <template #default="{ row }">
                <el-button link type="primary" @click="openTopicDialog(row)">编辑</el-button>
                <el-button link type="danger" @click="removeTopic(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 信源通道 -->
        <el-tab-pane label="信源接入通道" name="sources">
          <el-table :data="sources" stripe style="margin-top: 12px">
            <el-table-column prop="name" label="信源名称" min-width="140" />
            <el-table-column label="类型" width="120">
              <template #default="{ row }">
                <el-tag size="small" effect="plain">{{ sourceTypeText(row.type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="接入开关" width="140">
              <template #default="{ row }">
                <el-switch v-model="row.enabled" @change="toggleSource(row)" />
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 预警规则 -->
        <el-tab-pane label="预警阈值与通知规则" name="alerts">
          <el-table :data="configs" stripe style="margin-top: 12px">
            <el-table-column prop="key" label="配置项" min-width="180" />
            <el-table-column prop="description" label="说明" min-width="260" />
            <el-table-column label="当前值" width="220">
              <template #default="{ row }">
                <el-input v-model="row.value" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button link type="primary" @click="saveConfig(row)">保存</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 主题编辑对话框 -->
    <el-dialog v-model="topicDialog" :title="topicForm.id ? '编辑监测主题' : '新增监测主题'" width="520px">
      <el-form label-width="80px">
        <el-form-item label="主题名称">
          <el-input v-model="topicForm.name" placeholder="如：星耀 X20 Pro 质量舆情" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="topicForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="topicForm.keywordsText" type="textarea" :rows="3" placeholder="逗号或空格分隔，如：星耀, 发热, 续航" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="topicDialog = false">取消</el-button>
        <el-button type="primary" @click="saveTopic">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const tab = ref('topics')
const topics = ref([])
const sources = ref([])
const configs = ref([])

const topicDialog = ref(false)
const topicForm = ref({ id: null, name: '', description: '', keywordsText: '' })

const sourceTypeText = (t) => ({ social: '社交媒体', news: '新闻门户', video: '短视频平台', forum: '行业论坛' }[t] || t)

async function loadAll() {
  const [t, s, c] = await Promise.all([api.get('/topics'), api.get('/sources'), api.get('/configs')])
  topics.value = t
  sources.value = s
  configs.value = c
}

function openTopicDialog(row = null) {
  if (row) {
    topicForm.value = { id: row.id, name: row.name, description: row.description, keywordsText: (row.keywords || []).join(', ') }
  } else {
    topicForm.value = { id: null, name: '', description: '', keywordsText: '' }
  }
  topicDialog.value = true
}

async function saveTopic() {
  if (!topicForm.value.name) {
    ElMessage.warning('请输入主题名称')
    return
  }
  const keywords = topicForm.value.keywordsText.split(/[,，、\s]+/).filter(Boolean)
  const body = { name: topicForm.value.name, description: topicForm.value.description, keywords }
  if (topicForm.value.id) {
    await api.put(`/topics/${topicForm.value.id}`, body)
  } else {
    await api.post('/topics', body)
  }
  ElMessage.success('保存成功')
  topicDialog.value = false
  await loadAll()
}

async function removeTopic(row) {
  await ElMessageBox.confirm(`确认删除主题「${row.name}」？`, '提示', { type: 'warning' })
  await api.delete(`/topics/${row.id}`)
  ElMessage.success('已删除')
  await loadAll()
}

async function toggleSource(row) {
  await api.put(`/sources/${row.id}`, { enabled: row.enabled })
  ElMessage.success(`${row.name} 已${row.enabled ? '开启' : '关闭'}`)
}

async function saveConfig(row) {
  await api.put(`/configs/${row.key}`, { key: row.key, value: row.value, description: row.description })
  ElMessage.success('配置已保存')
}

onMounted(loadAll)
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: flex-end;
}
</style>

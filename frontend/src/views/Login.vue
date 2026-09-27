<template>
  <div class="login-wrap">
    <div class="login-card">
      <div class="login-title">
        <el-icon :size="30" color="#409eff"><Monitor /></el-icon>
        <h2>舆情分析平台</h2>
        <p>全网舆情监测 · 智能研判 · 风险预警</p>
      </div>
      <el-form :model="form" @keyup.enter="onLogin">
        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名" size="large" :prefix-icon="User" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" placeholder="密码" size="large" show-password :prefix-icon="Lock" />
        </el-form-item>
        <el-button type="primary" size="large" style="width: 100%" :loading="loading" @click="onLogin">登 录</el-button>
      </el-form>
      <div class="tips">
        <p>演示账号：</p>
        <p>分析师 analyst / analyst123</p>
        <p>公关运营 pr / pr123</p>
        <p>管理员 admin / admin123</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import api from '../api'
import { useAuthStore } from '../store/auth'

const router = useRouter()
const auth = useAuthStore()
const form = ref({ username: 'analyst', password: 'analyst123' })
const loading = ref(false)

async function onLogin() {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const data = await api.post('/auth/login', form.value)
    auth.setAuth(data.token, { username: data.username, name: data.name, role: data.role })
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrap {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
}
.login-card {
  width: 380px;
  background: #fff;
  border-radius: 10px;
  padding: 40px 36px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
}
.login-title {
  text-align: center;
  margin-bottom: 28px;
}
.login-title h2 {
  margin: 8px 0 4px;
  color: #303133;
}
.login-title p {
  margin: 0;
  color: #909399;
  font-size: 13px;
}
.tips {
  margin-top: 20px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
  font-size: 12px;
  color: #909399;
}
.tips p {
  margin: 2px 0;
}
</style>

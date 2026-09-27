<template>
  <el-container class="layout">
    <el-aside width="220px" class="aside">
      <div class="logo">
        <el-icon :size="22" color="#409eff"><Monitor /></el-icon>
        <span>舆情分析平台</span>
      </div>
      <el-menu :default-active="$route.path" router background-color="#001529" text-color="#bfcbd9" active-text-color="#409eff">
        <el-menu-item index="/dashboard"><el-icon><DataAnalysis /></el-icon><span>态势大盘</span></el-menu-item>
        <el-menu-item index="/workbench"><el-icon><Monitor /></el-icon><span>研判工作台</span></el-menu-item>
        <el-menu-item index="/report"><el-icon><Document /></el-icon><span>报告中心</span></el-menu-item>
        <el-menu-item index="/config"><el-icon><Setting /></el-icon><span>监测配置</span></el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="header-title">{{ $route.meta.title || '' }}</div>
        <div class="header-user">
          <el-tag size="small" type="info" effect="plain">{{ roleText }}</el-tag>
          <span class="username">{{ user?.name || user?.username }}</span>
          <el-button link type="primary" @click="logout">退出</el-button>
        </div>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'

const router = useRouter()
const auth = useAuthStore()
const user = computed(() => auth.user)

const roleMap = { analyst: '舆情分析师', pr: '公关运营人员', admin: '系统管理员' }
const roleText = computed(() => roleMap[user.value?.role] || '用户')

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.layout {
  height: 100%;
}
.aside {
  background: #001529;
}
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  border-bottom: 1px solid #1f2d3d;
}
.aside :deep(.el-menu) {
  border-right: none;
}
.header {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
}
.header-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}
.header-user {
  display: flex;
  align-items: center;
  gap: 10px;
}
.username {
  font-weight: 500;
}
.main {
  padding: 16px;
  overflow: auto;
}
</style>

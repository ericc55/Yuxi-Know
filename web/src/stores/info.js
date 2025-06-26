import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { infoApi } from '@/apis/public_api'

export const useInfoStore = defineStore('info', () => {
  // 状态
  const infoConfig = ref({})
  const isLoading = ref(false)
  const isLoaded = ref(false)

  // 计算属性 - 组织信息
  const organization = computed(() => infoConfig.value.organization || {
    name: "Yuxi-Know",
    short_name: "Yuxi",
    avatar: '/favicon.png',
    logo: '/favicon.png'
  })

  // 计算属性 - 品牌信息
  const brand = computed(() => infoConfig.value.brand || {
    name: "Yuxi-Know",
    subtitle: "AI-Powered Knowledge Management Tool",
    description: "Combining knowledge base with knowledge graph for more accurate and comprehensive answers"
  })

  // 计算属性 - 功能特性
  const features = computed(() => infoConfig.value.features || [
    "📚 Flexible Knowledge Base",
    "🕸️ Knowledge Graph Integration", 
    "🤖 Multi-Model Support"
  ])

  // 计算属性 - 页脚信息
  const footer = computed(() => infoConfig.value.footer || {
    copyright: "© Yuxi-Know 2025 [WIP] v0.12.138 | © Ericc 2025 | MIT License"
  })

  // 动作方法
  function setInfoConfig(newConfig) {
    infoConfig.value = newConfig
    isLoaded.value = true
  }

  async function loadInfoConfig(force = false) {
    // 如果已经加载过且不强制刷新，则不重新加载
    if (isLoaded.value && !force) {
      return infoConfig.value
    }

    try {
      isLoading.value = true
      const response = await infoApi.getInfoConfig()

      if (response.success && response.data) {
        setInfoConfig(response.data)
        console.log('信息配置加载成功:', response.data)
        return response.data
      } else {
        console.warn('信息配置加载失败，使用默认配置')
        return null
      }
    } catch (error) {
      console.error('加载信息配置时发生错误:', error)
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function reloadInfoConfig() {
    try {
      isLoading.value = true
      const response = await infoApi.reloadInfoConfig()

      if (response.success && response.data) {
        setInfoConfig(response.data)
        console.log('信息配置重新加载成功:', response.data)
        return response.data
      } else {
        console.warn('信息配置重新加载失败')
        return null
      }
    } catch (error) {
      console.error('重新加载信息配置时发生错误:', error)
      return null
    } finally {
      isLoading.value = false
    }
  }

    return {
    // 状态
    infoConfig,
    isLoading,
    isLoaded,

    // 计算属性
    organization,
    brand,
    features,
    footer,

    // 方法
    setInfoConfig,
    loadInfoConfig,
    reloadInfoConfig
  }
})
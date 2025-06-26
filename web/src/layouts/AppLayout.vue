<script setup>
import { ref, reactive, KeepAlive, onMounted, computed } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  UserOutlined,
  CommentOutlined,
  DatabaseOutlined,
  RobotOutlined,
  PartitionOutlined,
  SettingOutlined,
  PoweroffOutlined,
  ApiOutlined,
  BugOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons-vue'
import { Bot, Waypoints, LibraryBig, MessageSquareMore, Settings } from 'lucide-vue-next';

import { useConfigStore } from '@/stores/config'
import { useDatabaseStore } from '@/stores/database'
import { useInfoStore } from '@/stores/info'
import DebugComponent from '@/components/DebugComponent.vue'
import UserInfoComponent from '@/components/UserInfoComponent.vue'
import LanguageSwitcher from '@/components/LanguageSwitcher.vue'

const { t } = useI18n()
const configStore = useConfigStore()
const databaseStore = useDatabaseStore()
const infoStore = useInfoStore()
const { locale } = useI18n()

const layoutSettings = reactive({
  showDebug: false,
  useTopBar: false, // 是否使用顶栏
})

// Computed property for language-specific styling
const languageClass = computed(() => {
  return `lang-${locale.value}`
})

const getRemoteConfig = () => {
  configStore.refreshConfig()
}

const getRemoteDatabase = () => {
  if (!configStore.config.enable_knowledge_base) {
    return
  }
  databaseStore.refreshDatabase()
}

onMounted(async () => {
  // 加载信息配置
  await infoStore.loadInfoConfig()
  // 加载其他配置
  getRemoteConfig()
  getRemoteDatabase()
})

// 打印当前页面的路由信息，使用 vue3 的 setup composition API
const route = useRoute()
console.log(route)

// 下面是导航菜单部分，添加智能体项
const mainList = computed(() => [{
    name: t('navbar.chat'),
    path: '/chat',
    icon: MessageSquareMore,
    activeIcon: MessageSquareMore,
  }, {
    name: t('navbar.agents'),
    path: '/agent',
    icon: Bot,
    activeIcon: Bot,
  }, {
    name: t('navbar.knowledgeGraph'),
    path: '/graph',
    icon: Waypoints,
    activeIcon: Waypoints,
    // hidden: !configStore.config.enable_knowledge_graph,
  }, {
    name: t('navbar.knowledgeBase'),
    path: '/database',
    icon: LibraryBig,
    activeIcon: LibraryBig,
    // hidden: !configStore.config.enable_knowledge_base,
  }
])
</script>

<template>
  <div class="app-layout" :class="{ 'use-top-bar': layoutSettings.useTopBar, [languageClass]: true }">
    <div class="debug-panel" >
      <a-float-button
        @click="layoutSettings.showDebug = !layoutSettings.showDebug"
        :tooltip="t('common.debug')"
        :style="{
          right: '12px',
        }"
      >
        <template #icon>
          <UserOutlined />
        </template>
      </a-float-button>
      <a-drawer
        v-model:open="layoutSettings.showDebug"
        :title="t('common.debugPanel')"
        width="800"
        :contentWrapperStyle="{ maxWidth: '100%'}"
        placement="right"
      >
        <DebugComponent />
      </a-drawer>
    </div>
    <div class="header" :class="{ 'top-bar': layoutSettings.useTopBar }">
      <div class="logo circle">
        <router-link to="/">
          <img 
            :src="infoStore.organization.avatar" 
            :alt="infoStore.organization.name"
            @error="(e) => { console.error('Logo failed to load:', e.target.src); e.target.src = '/favicon.png' }"
            @load="() => console.log('Logo loaded successfully:', infoStore.organization.avatar)"
          >
          <span class="logo-text">{{ infoStore.organization.short_name }}</span>
        </router-link>
      </div>
      <div class="nav">
        <!-- 使用mainList渲染导航项 -->
        <RouterLink
          v-for="(item, index) in mainList"
          :key="index"
          :to="item.path"
          v-show="!item.hidden"
          class="nav-item"
          active-class="active">
          <component class="icon" :is="route.path.startsWith(item.path) ? item.activeIcon : item.icon" size="22"/>
          <span class="text">{{item.name}}</span>
        </RouterLink>

        <a-tooltip placement="right">
          <template #title>{{ t('errors.serverError') }}</template>
          <div class="nav-item warning" v-if="!configStore.config._config_items">
            <component class="icon" :is="CommentOutlined" />
            <span class="text">{{ t('common.warning') }}</span>
          </div>
        </a-tooltip>
      </div>
      <div class="fill" style="flex-grow: 1;"></div>

      <!-- 用户信息组件 -->
      <div class="nav-item user-info">
        <a-tooltip placement="right">
          <template #title>{{ t('navbar.user') }}</template>
          <UserInfoComponent />
        </a-tooltip>
      </div>

      <!-- 语言切换器 -->
      <div class="nav-item language-switcher">
        <a-tooltip placement="right">
          <template #title>{{ t('navbar.switchLanguage') }}</template>
          <LanguageSwitcher />
        </a-tooltip>
      </div>

      <RouterLink class="nav-item setting" to="/setting" active-class="active">
        <a-tooltip placement="right">
          <template #title>{{ t('navbar.settings') }}</template>
          <SettingOutlined />
        </a-tooltip>
      </RouterLink>
    </div>
    <div class="header-mobile">
      <RouterLink to="/chat" class="nav-item" active-class="active">{{ t('navbar.chat') }}</RouterLink>
      <RouterLink to="/database" class="nav-item" active-class="active">{{ t('navbar.knowledgeBase') }}</RouterLink>
      <RouterLink to="/setting" class="nav-item" active-class="active">{{ t('navbar.settings') }}</RouterLink>
    </div>
    <router-view v-slot="{ Component, route }" id="app-router-view">
      <keep-alive v-if="route.meta.keepAlive !== false">
        <component :is="Component" />
      </keep-alive>
      <component :is="Component" v-else />
    </router-view>
  </div>
</template>

<style lang="less" scoped>
@import '@/assets/main.css';

:root {
  --header-width: 85px;
}

.app-layout {
  display: flex;
  flex-direction: row;
  width: 100%;
  height: 100vh;
  min-width: var(--min-width);

  .header-mobile {
    display: none;
  }

  .debug-panel {
    position: absolute;
    z-index: 100;
    right: 0;
    bottom: 50px;
    border-radius: 20px 0 0 20px;
    cursor: pointer;
  }
  
  /* Language-specific adjustments for navigation text */
  &.lang-en .nav-item .text {
    font-size: 10px;
    line-height: 1.1;
    letter-spacing: -0.02em;
  }
  
  &.lang-ja .nav-item .text {
    font-size: 10px;
    line-height: 1.1;
    letter-spacing: -0.01em;
  }
  
  &.lang-zh .nav-item .text {
    font-size: 11px;
    line-height: 1.2;
  }
}

div.header, #app-router-view {
  height: 100%;
  max-width: 100%;
  user-select: none;
}

#app-router-view {
  flex: 1 1 auto;
  overflow-y: auto;
}

.header {
  display: flex;
  flex-direction: column;
  flex: 0 0 var(--header-width);
  justify-content: flex-start;
  align-items: center;
  background-color: var(--gray-100);
  height: 100%;
  width: var(--header-width);
  border-right: 1px solid var(--gray-300);

  .logo {
    width: 40px;
    height: 40px;
    margin: 14px 0 14px 0;

    img {
      width: 100%;
      height: 100%;
      border-radius: 4px;  // 50% for circle
    }

    .logo-text {
      display: none;
    }

    & > a {
      text-decoration: none;
      font-size: 24px;
      font-weight: bold;
      color: #333;
    }
  }

  .nav-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 72px;
    min-height: 60px;
    padding: 6px 4px;
    border: 1px solid transparent;
    border-radius: 8px;
    background-color: transparent;
    color: #222;
    font-size: 20px;
    transition: background-color 0.2s ease-in-out;
    margin: 2px 0;
    text-decoration: none;
    cursor: pointer;

    &.api-docs {
      padding: 10px 12px;
    }
    &.active {
      font-weight: bold;
      color: var(--main-600);
      background-color: white;
      border: 1px solid white;
    }

    &.warning {
      color: red;
    }

    &:hover {
      background-color: rgba(255, 255, 255, 0.8);
      backdrop-filter: blur(10px);
    }

    .text {
      font-size: 11px;
      margin-top: 4px;
      text-align: center;
      line-height: 1.2;
      max-width: 68px;
      word-wrap: break-word;
      hyphens: auto;
      overflow: hidden;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
    }
  }

  .setting {
    width: auto;
    font-size: 20px;
    color: #333;
    margin-bottom: 8px;
    padding: 16px 12px;

    &:hover {
      cursor: pointer;
    }
  }
}

.header .nav {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: center;
  position: relative;
  height: auto;
  gap: 8px;
}

@media (max-width: 520px) {
  .app-layout {
    flex-direction: column-reverse;

    div.header {
      display: none;
    }

    .debug-panel {
      bottom: 10rem;
    }

  }
  .app-layout div.header-mobile {
    display: flex;
    flex-direction: row;
    width: 100%;
    padding: 0 10px;
    justify-content: space-around;
    align-items: center;
    flex: 0 0 60px;
    border-right: none;
    height: 40px;

    .nav-item {
      text-decoration: none;
      min-width: 60px;
      color: var(--gray-900);
      font-size: 0.9rem;
      font-weight: bold;
      transition: color 0.1s ease-in-out, font-size 0.1s ease-in-out;
      text-align: center;
      line-height: 1.2;

      &.active {
        color: black;
        font-size: 1rem;
      }
    }
  }
  
  /* Mobile language-specific adjustments */
  .app-layout.lang-en div.header-mobile .nav-item {
    font-size: 0.8rem;
    line-height: 1.1;
    
    &.active {
      font-size: 0.9rem;
    }
  }
  
  .app-layout.lang-ja div.header-mobile .nav-item {
    font-size: 0.8rem;
    line-height: 1.1;
    
    &.active {
      font-size: 0.9rem;
    }
  }
  
  .app-layout .chat-box::webkit-scrollbar {
    width: 0;
  }
}

.app-layout.use-top-bar {
  flex-direction: column;
}

.header.top-bar {
  flex-direction: row;
  flex: 0 0 50px;
  width: 100%;
  height: 50px;
  border-right: none;
  border-bottom: 1px solid var(--main-light-2);
  background-color: var(--main-light-3);
  padding: 0 20px;
  gap: 24px;

  .logo {
    width: fit-content;
    height: 28px;
    margin-right: 16px;
    display: flex;
    align-items: center;

    a {
      display: flex;
      align-items: center;
      text-decoration: none;
      color: inherit;
    }

    img {
      width: 28px;
      height: 28px;
      margin-right: 8px;
    }

    .logo-text {
      display: block;
      font-size: 16px;
      font-weight: 600;
      letter-spacing: 0.5px;
      color: var(--main-600);
      white-space: nowrap;
    }
  }

  .nav {
    flex-direction: row;
    height: auto;
    gap: 20px;
  }

  .nav-item {
    flex-direction: row;
    width: auto;
    padding: 4px 16px;
    margin: 0;

    .icon {
      margin-right: 8px;
      font-size: 15px; // 减小图标大小
      border: none;
      outline: none;

      &:focus, &:active {
        border: none;
        outline: none;
      }
    }

    .text {
      margin-top: 0;
      font-size: 15px;
    }

    &.setting {
      padding: 8px 12px;

      .icon {
        margin-right: 0;
        font-size: 18px;
      }

      &.active {
        color: var(--main-600);
      }
    }
  }
}
</style>
<template>
  <div class="home-container">
    <div class="hero-section">
      <div class="glass-header">
        <div class="logo">
          <img :src="infoStore.organization.logo" :alt="infoStore.organization.name" class="logo-img" />
          <span style="font-size: 1.3rem; font-weight: bold;">{{ infoStore.organization.name }}</span>
        </div>
        <div class="header-actions">
          <!-- 语言切换器 -->
          <div class="language-switcher">
            <LanguageSwitcher />
          </div>
        </div>
      </div>

      <div class="hero-content">
        <h1>{{ t('home.title') }}</h1>
        <p class="subtitle">{{ t('home.subtitle') }}</p>
        <p class="description">{{ t('home.description') }}</p>
        <div class="features">
          <span>{{ t('home.features.flexibleKB') }}</span>
          <span>{{ t('home.features.knowledgeGraph') }}</span>
          <span>{{ t('home.features.multiModel') }}</span>
        </div>
        <button class="start-button" @click="goToChat">{{ t('home.startChat') }}</button>
      </div>
    </div>

    <!-- <div class="preview-section">
      <div class="preview-container">
        <img src="/home.png" :alt="t('home.systemPreview')" />
        <div class="preview-overlay">
          <div class="overlay-content">
            <h3>{{ t('home.powerfulQA') }}</h3>
            <p>{{ t('home.description') }}</p>
          </div>
        </div>
      </div>
    </div> -->

    <footer>
      <p>{{ infoStore.footer.copyright }}</p>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '@/stores/user'
import { useInfoStore } from '@/stores/info'
import { chatApi } from '@/apis/auth_api'
import LanguageSwitcher from '@/components/LanguageSwitcher.vue'

const router = useRouter()
const userStore = useUserStore()
const infoStore = useInfoStore()
const { t } = useI18n()

const goToChat = async () => {
  // 检查用户是否登录
  if (!userStore.isLoggedIn) {
    // 登录后应该跳转到默认智能体而不是/agent
    sessionStorage.setItem('redirect', '/');  // 设置为首页，登录后会通过路由守卫处理重定向
    router.push('/login');
    return;
  }

  // 根据用户角色进行跳转
  if (userStore.isAdmin) {
    // 管理员用户跳转到聊天页面
    router.push('/chat');
    return;
  }

  // 普通用户跳转到默认智能体
  try {
    // 获取默认智能体
    const data = await chatApi.getDefaultAgent();
    if (data.default_agent_id) {
      // 使用后端设置的默认智能体
      router.push(`/agent/${data.default_agent_id}`);
    } else {
      // 如果没有设置默认智能体，则获取智能体列表选择第一个
      const agentData = await chatApi.getAgents();
      if (agentData.agents && agentData.agents.length > 0) {
        router.push(`/agent/${agentData.agents[0].name}`);
      } else {
        // 没有可用智能体，回退到chat页面
        router.push("/chat");
      }
    }
  } catch (error) {
    console.error('跳转到智能体页面失败:', error);
    router.push("/chat");
  }
};

onMounted(async () => {
  // 加载信息配置
  await infoStore.loadInfoConfig()
})
</script>

<style lang="less" scoped>
.home-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  color: #333;
  background: linear-gradient(135deg, #f5f7fa, #e2e8f0, #f0f4f8, #eef2f7);
  background-size: 400% 400%;
  animation: gradientBackground 15s ease infinite;
}

@keyframes gradientBackground {
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}

.glass-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 1.2rem 2rem;
  background-color: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
}

.logo {
  display: flex;
  align-items: center;
  font-size: 1.4rem;
  font-weight: bold;
  color: var(--main-color, #333);

  .logo-img {
    height: 2rem;
    margin-right: 0.6rem;
  }
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.language-switcher {
  :deep(.language-switcher) {
    padding: 0.6rem 1.2rem;
    border-radius: 2rem;
    background-color: rgba(255, 255, 255, 0.4);
    transition: all 0.3s ease;

    &:hover {
      background-color: rgba(255, 255, 255, 0.6);
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }

    .current-language {
      color: #333;
      font-weight: 600;
    }
  }

  :deep(.ant-dropdown-menu) {
    background-color: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.3);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  }
}

.hero-section {
  height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  padding: 0 2rem;
}

.hero-content {
  max-width: 800px;
}

.title {
  font-size: 4rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
  background: linear-gradient(45deg, #333, #666);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.description {
  margin-bottom: 2.5rem;
}

.subtitle {
  font-size: 1.5rem;
  font-weight: 500;
  margin-bottom: 1.5rem;
  color: #555;
}

.features {
  display: flex;
  justify-content: center;
  gap: 1.5rem;
  font-size: 1.1rem;

  span {
    padding: 0.5rem 1rem;
    background-color: rgba(255, 255, 255, 0.6);
    border-radius: 2rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  }
}

.start-button {
  padding: 1rem 3rem;
  font-size: 1.2rem;
  font-weight: 600;
  color: white;
  background: linear-gradient(135deg, var(--main-500), var(--main-600));
  border: none;
  border-radius: 3rem;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);

  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 7px 20px rgba(0, 0, 0, 0.15);
    background: linear-gradient(135deg, var(--main-600), var(--main-700));
  }

  &:active {
    transform: translateY(-1px);
  }
}

.preview-section {
  padding: 5rem 2rem;
  display: flex;
  justify-content: center;
}

.preview-container {
  position: relative;
  max-width: 1000px;
  overflow: hidden;
  border-radius: 1rem;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);

    .preview-overlay {
      opacity: 1;
    }
  }

  img {
    width: 100%;
    height: auto;
    display: block;
    transition: transform 0.5s ease;
  }

  .preview-overlay {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    background: linear-gradient(to top, rgba(0, 0, 0, 0.7), transparent);
    padding: 2rem;
    opacity: 0.8;
    transition: opacity 0.3s ease;

    .overlay-content {
      color: white;

      h3 {
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
      }

      p {
        font-size: 1rem;
        opacity: 0.9;
      }
    }
  }
}

footer {
  margin-top: auto;
  text-align: center;
  padding: 2rem;
  color: #666;
  font-size: 0.9rem;
}

@media (max-width: 768px) {
  .glass-header {
    padding: 1rem;
  }

  .logo {
    font-size: 1.2rem;
  }

  .header-actions {
    gap: 0.5rem;
  }

  .language-switcher {
    :deep(.language-switcher) {
      padding: 0.4rem 0.8rem;
      
      .current-language {
        font-size: 0.9rem;
        
        .name {
          display: none; // Hide language name on mobile, show only language code
        }
      }
    }
  }

  .title {
    font-size: 2.5rem;
  }

  .subtitle {
    font-size: 1.2rem;
  }

  .features {
    flex-direction: column;
    gap: 0.8rem;
  }

  .start-button {
    padding: 0.8rem 2rem;
    font-size: 1rem;
  }

  .preview-section {
    padding: 3rem 1rem;
  }
}
</style>

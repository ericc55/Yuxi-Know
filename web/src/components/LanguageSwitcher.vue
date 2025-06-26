<template>
  <div class="language-switcher">
    <a-dropdown placement="bottom">
      <a class="ant-dropdown-link" @click.prevent>
        <div class="current-language">
          <span class="flag">{{ currentLanguage.flag }}</span>
          <span class="name">{{ currentLanguage.name }}</span>
          <DownOutlined />
        </div>
      </a>
      <template #overlay>
        <a-menu @click="handleLanguageChange">
          <a-menu-item 
            v-for="lang in availableLanguages" 
            :key="lang.code"
            :class="{ active: lang.code === languageStore.currentLanguage }"
          >
            <span class="flag">{{ lang.flag }}</span>
            <span class="name">{{ lang.name }}</span>
          </a-menu-item>
        </a-menu>
      </template>
    </a-dropdown>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { DownOutlined } from '@ant-design/icons-vue'
import { useLanguageStore } from '@/stores/language'

const { locale } = useI18n()
const languageStore = useLanguageStore()

const availableLanguages = computed(() => languageStore.availableLanguages)

const currentLanguage = computed(() => {
  return availableLanguages.value.find(lang => lang.code === languageStore.currentLanguage) || availableLanguages.value[0]
})

const handleLanguageChange = ({ key }) => {
  languageStore.setLanguage(key)
  locale.value = key
}
</script>

<style lang="less" scoped>
.language-switcher {
  .ant-dropdown-link {
    text-decoration: none;
    color: inherit;
  }

  .current-language {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
    font-weight: 500;

    .flag {
      font-size: 1.2rem;
    }

    .name {
      color: inherit;
    }
  }
}

:deep(.ant-dropdown-menu) {
  .ant-menu-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 8px 16px;

    &.active {
      background-color: var(--main-light-4);
      color: var(--main-color);
    }

    &:hover {
      background-color: var(--main-light-5);
    }

    .flag {
      font-size: 1.1rem;
    }

    .name {
      font-weight: 500;
    }
  }
}
</style> 
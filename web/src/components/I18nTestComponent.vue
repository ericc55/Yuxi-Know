<template>
  <div class="i18n-test">
    <h3>i18n Error Message Test</h3>
    
    <div class="language-switcher">
      <p>Current Language: {{ locale }}</p>
      <a-button @click="switchLanguage('en')">English</a-button>
      <a-button @click="switchLanguage('zh')">中文</a-button>
      <a-button @click="switchLanguage('ja')">日本語</a-button>
    </div>
    
    <div class="error-messages">
      <h4>Error Messages:</h4>
      <p><strong>Server Connection Failed:</strong> {{ t('errors.serverConnectionFailed') }}</p>
      <p><strong>Retry:</strong> {{ t('errors.retry') }}</p>
      <p><strong>Network Error:</strong> {{ t('errors.networkError') }}</p>
      <p><strong>Server Error:</strong> {{ t('errors.serverError') }}</p>
      <p><strong>Unauthorized:</strong> {{ t('errors.unauthorized') }}</p>
    </div>
    
    <div class="test-buttons">
      <h4>Test Error Notifications:</h4>
      <a-button @click="showConnectionError">{{ t('errors.serverConnectionFailed') }}</a-button>
      <a-button @click="showNetworkError">{{ t('errors.networkError') }}</a-button>
      <a-button @click="showRetryMessage">{{ t('errors.retry') }}</a-button>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'

const { t, locale } = useI18n()

const switchLanguage = (lang) => {
  locale.value = lang
  localStorage.setItem('app_language', lang)
}

const showConnectionError = () => {
  message.error(t('errors.serverConnectionFailed'))
}

const showNetworkError = () => {
  message.error(t('errors.networkError'))
}

const showRetryMessage = () => {
  message.info(t('errors.retry'))
}
</script>

<style scoped>
.i18n-test {
  padding: 20px;
  max-width: 600px;
  margin: 0 auto;
}

.language-switcher {
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f5f5;
  border-radius: 8px;
}

.language-switcher .ant-btn {
  margin-right: 10px;
}

.error-messages {
  margin-bottom: 20px;
  padding: 15px;
  background: #fff2f0;
  border-radius: 8px;
  border: 1px solid #ffccc7;
}

.test-buttons {
  padding: 15px;
  background: #f6ffed;
  border-radius: 8px;
  border: 1px solid #b7eb8f;
}

.test-buttons .ant-btn {
  margin-right: 10px;
  margin-bottom: 10px;
}
</style> 
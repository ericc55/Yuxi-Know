<template>
  <div class="i18n-example">
    <h2>{{ t('common.settings') }}</h2>
    
    <!-- Basic translations -->
    <p>{{ t('auth.pleaseLogin') }}</p>
    
    <!-- Using variables -->
    <p>{{ t('language.switchTo') }}{{ t('language.english') }}</p>
    
    <!-- Nested object access -->
    <p>{{ t('home.features.flexibleKB') }}</p>
    
    <!-- Using with reactive data -->
    <a-button @click="handleSave">{{ t('common.save') }}</a-button>
    <a-button @click="handleCancel">{{ t('common.cancel') }}</a-button>
    
    <!-- Form example -->
    <a-form>
      <a-form-item :label="t('auth.username')">
        <a-input :placeholder="t('auth.username')" />
      </a-form-item>
      <a-form-item :label="t('auth.password')">
        <a-input-password :placeholder="t('auth.password')" />
      </a-form-item>
    </a-form>
    
    <!-- Language-dependent content -->
    <div v-if="locale === 'zh'">
      <p>这是中文特定的内容</p>
    </div>
    <div v-else-if="locale === 'ja'">
      <p>これは日本語特有のコンテンツです</p>
    </div>
    <div v-else>
      <p>This is English-specific content</p>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'

const { t, locale } = useI18n()

const handleSave = () => {
  message.success(t('messages.saveSuccess'))
}

const handleCancel = () => {
  message.info(t('common.cancel'))
}
</script>

<style scoped>
.i18n-example {
  padding: 20px;
  max-width: 600px;
}
</style> 
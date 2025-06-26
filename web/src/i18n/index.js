import { createI18n } from 'vue-i18n';
import en from './index_en.js';
import zh from './index_zh.js';
import ja from './index_ja.js';

// Create and export i18n instance
export default createI18n({
  legacy: false,
  locale: localStorage.getItem('app_language') || 'zh', // Default to Chinese
  fallbackLocale: 'en',
  messages: {
    en,
    zh,
    ja
  }
}); 
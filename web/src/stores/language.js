import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'

export const useLanguageStore = defineStore('language', () => {
  // Available languages with flags and names
  const availableLanguages = ref([
    {
      code: 'zh',
      name: '中文',
      flag: '🇨🇳'
    },
    {
      code: 'en', 
      name: 'English',
      flag: '🇺🇸'
    },
    {
      code: 'ja',
      name: '日本語', 
      flag: '🇯🇵'
    }
  ])

  // Current language - get from localStorage or default to Chinese
  const currentLanguage = ref(localStorage.getItem('app_language') || 'zh')

  // Computed property to get current language info
  const currentLanguageInfo = computed(() => {
    return availableLanguages.value.find(lang => lang.code === currentLanguage.value) || availableLanguages.value[0]
  })

  // Set language and persist to localStorage
  function setLanguage(langCode) {
    if (availableLanguages.value.some(lang => lang.code === langCode)) {
      currentLanguage.value = langCode
      localStorage.setItem('app_language', langCode)
    }
  }

  // Get language name by code
  function getLanguageName(langCode) {
    const lang = availableLanguages.value.find(l => l.code === langCode)
    return lang ? lang.name : langCode
  }

  function getLanguageFlag(code) {
    const lang = availableLanguages.value.find(l => l.code === code)
    return lang ? lang.flag : '🌐'
  }

  return {
    availableLanguages,
    currentLanguage,
    currentLanguageInfo,
    setLanguage,
    getLanguageName,
    getLanguageFlag
  }
}) 
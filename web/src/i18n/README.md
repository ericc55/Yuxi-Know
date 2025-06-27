# Internationalization (i18n) Guide

This application supports multiple languages through Vue i18n. Currently supported languages:
- **English** (`en`)
- **Chinese** (`zh`) 
- **Japanese** (`ja`) - Default language

## Usage in Components

### Basic Translation
```vue
<template>
  <div>
    <!-- Simple translation -->
    <h1>{{ t('home.title') }}</h1>
    
    <!-- With variables -->
    <p>{{ t('common.showTotal', { total: 100 }) }}</p>
    
    <!-- In attributes -->
    <a-input :placeholder="t('auth.username')" />
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

const { t, locale } = useI18n()

// Use in JavaScript
const handleError = () => {
  message.error(t('errors.networkError'))
}

// Check current language
if (locale.value === 'zh') {
  // Chinese-specific logic
}
</script>
```

### Error Message Handling

For error messages, use the `errors` namespace:

```javascript
// Network errors
message.error(t('errors.networkError'))
message.error(t('errors.serverConnectionFailed'))

// Authentication errors  
message.error(t('errors.unauthorized'))

// Validation errors
message.error(t('errors.validationError'))

// General messages
message.success(t('messages.saveSuccess'))
message.info(t('messages.operationSuccess'))
```

### Available Error Message Keys

| Key | English | Chinese | Japanese |
|-----|---------|---------|----------|
| `errors.networkError` | Network error, please try again | 网络错误，请重试 | ネットワークエラー、再試行してください |
| `errors.serverConnectionFailed` | Server connection failed | 服务端连接失败 | サーバー接続に失敗しました |
| `errors.serverError` | Server error, please check logs | 服务器错误，请检查日志 | サーバーエラー、ログを確認してください |
| `errors.unauthorized` | Unauthorized, please login again | 未授权，请重新登录 | 未認証、再度ログインしてください |
| `errors.retry` | Retry | 重试 | 再試行 |

## Adding New Translations

1. **Add to English** (`web/src/i18n/index_en.js`):
```javascript
errors: {
  newError: 'New error message'
}
```

2. **Add to Chinese** (`web/src/i18n/index_zh.js`):
```javascript
errors: {
  newError: '新的错误消息'
}
```

3. **Add to Japanese** (`web/src/i18n/index_ja.js`):
```javascript
errors: {
  newError: '新しいエラーメッセージ'
}
```

4. **Use in component**:
```javascript
message.error(t('errors.newError'))
```

## Language Switching

The application automatically saves the selected language to localStorage:

```javascript
import { useI18n } from 'vue-i18n'

const { locale } = useI18n()

// Switch language
locale.value = 'en'  // or 'zh', 'ja'
```

## Best Practices

1. **Never hardcode text** - Always use i18n keys
2. **Use meaningful namespaces** - Group related translations
3. **Keep keys consistent** - Use similar patterns across languages
4. **Test all languages** - Verify translations work correctly
5. **Handle pluralization** - Use Vue i18n's plural features when needed

## Common Namespaces

- `common.*` - Generic UI elements (buttons, labels)
- `auth.*` - Authentication related text
- `errors.*` - Error messages
- `messages.*` - Success/info messages
- `navbar.*` - Navigation elements
- `settings.*` - Settings page text

## Example: Converting Hardcoded Text

**Before:**
```vue
<template>
  <div class="alert-title">服务端连接失败</div>
  <a-button @click="retry">重试</a-button>
</template>
```

**After:**
```vue
<template>
  <div class="alert-title">{{ t('errors.serverConnectionFailed') }}</div>
  <a-button @click="retry">{{ t('errors.retry') }}</a-button>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
</script>
```

This ensures your application works correctly in all supported languages! 
<template>
  <div>
    <!-- Loading state -->
    <div v-if="isLoading" class="loading-container">
      <a-spin :indicator="h(LoadingOutlined, { style: { fontSize: '24px', color: 'var(--main-color)' }})" />
      <div class="loading-text">{{ t('common.loading') }}</div>
    </div>
    
    <!-- Main content - only render when not loading -->
    <div v-else>
      <div class="model-provider-card custom-models-card">
        <div class="card-header">
          <h3>{{ t('components.customModels') }}</h3>
        </div>
        <div class="card-body">
          <div class="custom-model" v-for="(item, key) in configStore.config.custom_models" :key="item.custom_id">
            <div class="card-models__header">
              <div class="name" :title="item.name">{{ item.name }}</div>
              <div class="action">
                <a-popconfirm
                  :title="t('components.modelProviders.confirmDeleteModel')"
                  placement="left"
                  :ok-text="t('components.modelProviders.confirmDelete')"
                  :cancel-text="t('components.modelProviders.cancel')"
                  @confirm="handleDeleteCustomModel(item.custom_id)"
                >
                  <a-button type="text" :disabled="configStore.config.model_name == item.name" @click.stop><DeleteOutlined /></a-button>
                </a-popconfirm>
                <a-button type="text" @click.stop="prepareToEditCustomModel(item)"><EditOutlined /></a-button>
              </div>
            </div>
            <div class="api_base">{{ item.api_base }}</div>
          </div>
          <div class="card-models custom-model add-model" @click="prepareToAddCustomModel">
            <div class="card-models__header">
              <div class="name"> + {{ t('components.addModel') }}</div>
            </div>
            <div class="api_base">{{ t('components.addOpenAICompatibleModel') }}</div>
          </div>
        </div>
      </div>
      <div class="model-provider-card configured-provider" v-for="(item, key) in modelKeys" :key="key">
        <div class="card-header" @click="toggleExpand(item)">
          <div :class="{'model-icon': true, 'available': modelStatus[item]}">
            <img :src="modelIcons[item] || modelIcons.default" :alt="t('components.modelProviders.modelIcon')">
          </div>
          <div class="model-title-container">
            <h3>{{ modelNames[item]?.name || item }}</h3>
          </div>
          <a-button
            type="text"
            class="expand-button"
            @click.stop="openProviderConfig(item)"
            :title="t('components.modelProviders.configureProvider')"
          >
            <SettingOutlined />
          </a-button>
          <a-button
            type="text"
            class="expand-button"
            @click.stop="toggleExpand(item)"
          >
            <span class="icon-wrapper" :class="{'rotated': expandedModels[item]}">
              <DownCircleOutlined />
            </span>
          </a-button>
        </div>
        <div class="card-body-wrapper" :class="{'expanded': expandedModels[item]}">
          <div class="card-body" v-if="modelStatus[item]">
            <div class="card-models" v-for="(model, idx) in modelNames[item]?.models || []" :key="idx">
              <div class="model_name">{{ model }}</div>
            </div>
          </div>
        </div>
      </div>
      <div class="model-provider-card unconfigured-provider" v-for="(item, key) in notModelKeys" :key="key">
        <div class="card-header">
          <div class="model-icon">
            <img :src="modelIcons[item] || modelIcons.default" :alt="t('components.modelProviders.modelIcon')">
          </div>
          <div class="model-title-container">
            <h3 style="font-weight: 400">{{ modelNames[item]?.name || item }}</h3>
            <a :href="modelNames[item]?.url" target="_blank" class="model-url" v-if="modelNames[item]?.url">
              <InfoCircleOutlined />
            </a>
          </div>
          <a-button
            type="text"
            class="config-button"
            @click.stop="openProviderConfig(item)"
            :title="t('components.modelProviders.configureProvider')"
          >
            <SettingOutlined />
          </a-button>
          <div class="missing-keys">
            {{ t('components.modelProviders.requiresConfiguration') }}<span v-for="(key, idx) in modelNames[item]?.env || []" :key="idx">{{ key }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加和编辑自定义模型的弹窗 -->
    <a-modal
      class="custom-model-modal"
      v-model:open="customModel.visible"
      :title="customModel.edit_type === 'add' ? t('components.modelProviders.addCustomModel') : t('components.modelProviders.editCustomModel')"
      @ok="handleAddOrEditCustomModel"
      @cancel="handleCancelCustomModel"
      :okText="t('components.modelProviders.saveConfig')"
      :cancelText="t('components.modelProviders.cancel')"
      :okButtonProps="{disabled: !customModel.name || !customModel.api_base}"
      :ok-type="'primary'"
    >
      <p>{{ t('components.modelProviders.openAICompatibleDescription') }}</p>
      <a-form :model="customModel" layout="vertical">
        <a-form-item :label="t('components.modelProviders.modelName')" name="name" :rules="[{ required: true, message: t('components.modelProviders.enterModelName') }]">
          <p class="form-item-description">{{ t('components.modelProviders.modelNameDescription') }}</p>
          <a-input v-model:value="customModel.name" :disabled="customModel.edit_type == 'edit'"/>
        </a-form-item>
        <a-form-item :label="t('components.modelProviders.apiBase')" name="api_base" :rules="[{ required: true, message: t('components.modelProviders.enterApiBase') }]">
          <p class="form-item-description">{{ t('components.modelProviders.apiBaseDescription') }}</p>
          <a-input v-model:value="customModel.api_base" />
        </a-form-item>
        <a-form-item :label="t('components.modelProviders.apiKey')" name="api_key">
          <a-input-password v-model:value="customModel.api_key" :visibilityToggle="true" autocomplete="new-password"/>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 模型提供商配置弹窗 -->
    <a-modal
      class="provider-config-modal"
      v-model:open="providerConfig.visible"
      :title="t('components.modelProviders.configureProvider')"
      @ok="saveProviderConfig"
      @cancel="cancelProviderConfig"
      :okText="t('components.modelProviders.confirm')"
      :cancelText="t('components.modelProviders.cancel')"
      :ok-type="'primary'"
      :width="800"
    >
      <div v-if="providerConfig.loading" class="modal-loading-container">
        <a-spin :indicator="h(LoadingOutlined, { style: { fontSize: '32px', color: 'var(--main-color)' }})" />
        <div class="loading-text">{{ t('components.modelProviders.loadingModels') }}</div>
      </div>
      <div v-else class="modal-config-content">
        <div class="modal-config-header">
          <h3>{{ t('components.modelProviders.selectModels', { providerName: providerConfig.providerName }) }}</h3>
          <p class="description">{{ t('components.modelProviders.modelSelectionDescription') }}</p>
        </div>

        <div class="modal-models-section">
          <div class="model-search">
            <a-input
              v-model:value="providerConfig.searchQuery"
              :placeholder="t('components.modelProviders.searchModels')"
              allow-clear
            >
              <template #prefix>
                <SearchOutlined />
              </template>
            </a-input>
          </div>

          <!-- 显示选中统计信息 -->
          <div class="selection-summary">
            <span>{{ t('components.modelProviders.selectedModelsCount', { count: providerConfig.selectedModels.length }) }}</span>
            <span v-if="providerConfig.searchQuery" class="filter-info">
              {{ t('components.modelProviders.filteredModelsCount', { count: filteredModels.length }) }}
            </span>
          </div>

          <div class="modal-checkbox-list">
            <div v-for="(model, index) in filteredModels" :key="index" class="modal-checkbox-item">
              <a-checkbox
                :checked="providerConfig.selectedModels.includes(model.id)"
                @change="(e) => handleModelSelect(model.id, e.target.checked)"
              >
                {{ model.id }}
              </a-checkbox>
            </div>
          </div>
          <div v-if="providerConfig.allModels.length === 0" class="modal-no-models">
            <a-alert v-if="!modelStatus[providerConfig.provider]" type="warning" :message="t('components.modelProviders.configureApiKey')" />
            <div v-else>
              <a-alert type="warning" :message="t('components.modelProviders.providerNotSupported')" />
              <img src="@/assets/pics/guides/how-to-add-models.png" alt="添加模型指引" style="width: 100%; height: 100%;">
            </div>
          </div>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { computed, reactive, watch, h } from 'vue'
import { message } from 'ant-design-vue';
import {
  DeleteOutlined,
  EditOutlined,
  InfoCircleOutlined,
  SettingOutlined,
  DownCircleOutlined,
  LoadingOutlined,
  SearchOutlined
} from '@ant-design/icons-vue';
import { useConfigStore } from '@/stores/config';
import { modelIcons } from '@/utils/modelIcon';
import { chatApi } from '@/apis/auth_api';
import { useI18n } from 'vue-i18n';

const configStore = useConfigStore();
const { t } = useI18n();

// Optimize loading - check for critical data only
const isLoading = computed(() => !configStore.config?.model_names && !configStore.config?.custom_models);

// 计算属性 - Add safety checks
const modelNames = computed(() => configStore.config?.model_names || {});
const modelStatus = computed(() => configStore.config?.model_provider_status || {});

// 自定义模型相关状态
const customModel = reactive({
  modelTitle: '添加自定义模型',
  visible: false,
  custom_id: '',
  name: '',
  api_key: '',
  api_base: '',
  edit_type: 'add',
});

// 提供商配置相关状态
const providerConfig = reactive({
  visible: false,
  provider: '',
  providerName: '',
  models: [],
  allModels: [], // 所有可用的模型
  selectedModels: [], // 用户选择的模型
  loading: false,
  searchQuery: '',
});

// 筛选 modelStatus 中为真的key - Add safety checks
const modelKeys = computed(() => {
  if (!modelStatus.value || typeof modelStatus.value !== 'object') {
    return [];
  }
  return Object.keys(modelStatus.value).filter(key => modelStatus.value[key]);
});

// 筛选 modelStatus 中为假的key - Add safety checks
const notModelKeys = computed(() => {
  if (!modelStatus.value || typeof modelStatus.value !== 'object') {
    return [];
  }
  return Object.keys(modelStatus.value).filter(key => !modelStatus.value[key]);
});

// 模型展开状态管理
const expandedModels = reactive({});

// 优化的watch - Remove debouncing for faster loading
watch(modelKeys, (newKeys) => {
  if (Array.isArray(newKeys)) {
    newKeys.forEach(key => {
      if (key && expandedModels[key] === undefined) {
        expandedModels[key] = true;
      }
    });
  }
}, { immediate: true, flush: 'sync' }); // Restore immediate flag for faster initial load

// 生成随机哈希值
const generateRandomHash = (length) => {
  let chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  let hash = '';
  for (let i = 0; i < length; i++) {
    hash += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return hash;
};

// 处理自定义模型删除
const handleDeleteCustomModel = (customId) => {
  try {
    const currentModels = configStore.config?.custom_models || [];
    const updatedModels = currentModels.filter(item => item.custom_id !== customId);
    configStore.setConfigValue('custom_models', updatedModels);
  } catch (error) {
    console.error('删除自定义模型失败:', error);
    message.error('删除模型失败');
  }
};

// 准备编辑自定义模型
const prepareToEditCustomModel = (item) => {
  customModel.modelTitle = '编辑自定义模型';
  customModel.custom_id = item.custom_id;
  customModel.visible = true;
  customModel.edit_type = 'edit';
  customModel.name = item.name;
  customModel.api_key = item.api_key;
  customModel.api_base = item.api_base;
};

// 准备添加自定义模型
const prepareToAddCustomModel = () => {
  customModel.modelTitle = '添加自定义模型';
  customModel.edit_type = 'add';
  customModel.visible = true;
  clearCustomModel();
};

// 清除自定义模型表单
const clearCustomModel = () => {
  customModel.custom_id = '';
  customModel.name = '';
  customModel.api_key = '';
  customModel.api_base = '';
};

// 取消自定义模型添加/编辑
const handleCancelCustomModel = () => {
  clearCustomModel();
  customModel.visible = false;
};

// 添加或编辑自定义模型
const handleAddOrEditCustomModel = async () => {
  if (!customModel.name || !customModel.api_base) {
    message.error(t('components.modelProviders.completeModelInfo'));
    return;
  }

  try {
    let custom_models = configStore.config?.custom_models || [];

    const model_info = {
      custom_id: customModel.custom_id || `${customModel.name}-${generateRandomHash(4)}`,
      name: customModel.name,
      api_key: customModel.api_key,
      api_base: customModel.api_base,
    };

    if (customModel.edit_type === 'add') {
      if (custom_models.find(item => item.custom_id === customModel.custom_id)) {
        message.error(t('components.modelProviders.modelIdExists'));
        return;
      }
      custom_models.push(model_info);
    } else {
      // 如果 custom_id 相同，则更新
      custom_models = custom_models.map(item => item.custom_id === customModel.custom_id ? model_info : item);
    }

    customModel.visible = false;
    await configStore.setConfigValue('custom_models', custom_models);
    message.success(customModel.edit_type === 'add' ? t('components.modelProviders.modelAddSuccess') : t('components.modelProviders.modelEditSuccess'));
  } catch (error) {
    console.error('保存自定义模型失败:', error);
    message.error('保存模型失败');
  }
};

// 切换展开状态
const toggleExpand = (item) => {
  if (item && typeof item === 'string') {
    expandedModels[item] = !expandedModels[item];
  }
};

// 处理模型选择
const handleModelSelect = (modelId, checked) => {
  if (!modelId) return;
  
  const selectedModels = providerConfig.selectedModels;
  const index = selectedModels.indexOf(modelId);

  if (checked && index === -1) {
    selectedModels.push(modelId);
  } else if (!checked && index > -1) {
    selectedModels.splice(index, 1);
  }
};

// 打开提供商配置
const openProviderConfig = (provider) => {
  if (!provider || !modelNames.value[provider]) {
    message.error('无效的模型提供商');
    return;
  }

  providerConfig.provider = provider;
  providerConfig.providerName = modelNames.value[provider].name;
  providerConfig.allModels = [];
  providerConfig.visible = true;
  providerConfig.loading = true;
  providerConfig.searchQuery = ''; // 重置搜索关键词

  // 获取当前选择的模型作为初始选中值
  const currentModels = modelNames.value[provider]?.models || [];
  providerConfig.selectedModels = [...currentModels];

  // 获取所有可用模型
  fetchProviderModels(provider);
};

// 获取模型提供商的模型列表
const fetchProviderModels = async (provider) => {
  if (!provider) return;
  
  providerConfig.loading = true;
  
  try {
    const data = await chatApi.getProviderModels(provider);
    console.log(`${provider} model list:`, data);

    // 处理各种可能的API返回格式
    let modelsList = [];

    // 情况1: { data: [...] }
    if (data?.data && Array.isArray(data.data)) {
      modelsList = data.data;
    }
    // 情况2: { models: [...] } (字符串数组)
    else if (data?.models && Array.isArray(data.models)) {
      modelsList = data.models.map(model => typeof model === 'string' ? { id: model } : model);
    }
    // 情况3: { models: { data: [...] } }
    else if (data?.models?.data && Array.isArray(data.models.data)) {
      modelsList = data.models.data;
    }

    console.log("Processed model list:", modelsList);
    providerConfig.allModels = modelsList;
  } catch (error) {
    console.error(`获取${provider}模型列表失败:`, error);
    const providerName = modelNames.value[provider]?.name || provider;
    message.error({ content: t('components.modelProviders.getModelListFailed', { provider: providerName }), duration: 2 });
    providerConfig.allModels = [];
  } finally {
    providerConfig.loading = false;
  }
};

// 保存提供商配置
const saveProviderConfig = async () => {
  if (!modelStatus.value[providerConfig.provider]) {
    message.error(t('components.modelProviders.configureApiKeyFirst'));
    return;
  }

  message.loading({ content: t('components.modelProviders.savingConfig'), key: 'save-config', duration: 0 });

  try {
    // 发送选择的模型列表到后端
    const data = await chatApi.updateProviderModels(providerConfig.provider, providerConfig.selectedModels);
    console.log('Updated model list:', data.models);

    message.success({ content: t('components.modelProviders.modelConfigSaved'), key: 'save-config', duration: 2 });

    // 关闭弹窗
    providerConfig.visible = false;

    // 刷新配置
    configStore.refreshConfig();

  } catch (error) {
    console.error('保存配置失败:', error);
    message.error({ content: t('components.modelProviders.saveConfigFailed') + ': ' + error.message, key: 'save-config', duration: 2 });
  }
};

// 取消提供商配置
const cancelProviderConfig = () => {
  providerConfig.visible = false;
};

// 计算筛选后的模型列表 - Add safety checks and optimize
const filteredModels = computed(() => {
  const allModels = providerConfig.allModels;
  if (!Array.isArray(allModels) || allModels.length === 0) {
    return [];
  }
  
  const searchQuery = providerConfig.searchQuery?.toLowerCase() || '';
  if (!searchQuery) {
    return allModels;
  }
  
  return allModels.filter(model => {
    return model?.id?.toLowerCase().includes(searchQuery);
  });
});
</script>

<style lang="less" scoped>
.loading-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 200px;
  
  .loading-text {
    margin-top: 16px;
    color: var(--gray-600);
    font-size: 14px;
  }
}

.model-provider-card {
  border: 1px solid var(--gray-200);
  background-color: white;
  border-radius: 8px;
  margin-bottom: 12px;
  padding: 0;
  // box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
  transition: all 0.2s ease;
  overflow: hidden;

  &:hover {
    // box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
    border-color: var(--gray-300);
  }

  // 自定义模型容器特殊样式
  &.custom-models-card {
    .card-header {
      border-bottom: 1px solid var(--gray-200);

      h3 {
        color: var(--main-color);
        font-weight: 600;
      }
    }
  }

  // 已配置provider的样式
  &.configured-provider {
    .card-header {
      border-bottom: 1px solid var(--gray-200);

      .model-icon {
        &.available {
          position: relative;
          overflow: visible;
          &::after {
            content: '';
            position: absolute;
            top: -1px;
            right: -1px;
            width: 6px;
            height: 6px;
            background: #10b981;
            border: 1px solid white;
            border-radius: 50%;
          }
        }
      }
    }
  }

  // 未配置provider的样式
  &.unconfigured-provider {
    .card-header {
      background: #fafafa;
      border-bottom: 1px solid var(--gray-200);

      h3 {
        color: var(--gray-700);
      }

      .missing-keys {
        background: #fff7ed;
        border: 1px solid #fed7aa;
        border-radius: 4px;
        padding: 4px 8px;
        margin: 0;
      }
    }
  }

  .card-header {
    display: flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
    padding: 12px 14px;
    background: white;
    transition: all 0.2s ease;

    &:hover {
      background: var(--gray-50);
    }

    .model-title-container {
      display: flex;
      flex-direction: row;
      align-items: center;
      gap: 10px;
      flex: 1;
    }

    .model-url {
      font-size: 12px;
      width: fit-content;
      color: var(--gray-500);
      transition: color 0.2s ease;

      &:hover {
        color: var(--main-color);
      }
    }

    .model-icon {
      width: 28px;
      height: 28px;
      position: relative;
      border-radius: 6px;
      overflow: hidden;
      filter: grayscale(100%);
      transition: filter 0.2s ease;

      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        border: 1px solid var(--gray-200);
        border-radius: 6px;
      }

      &.available {
        filter: grayscale(0%);
      }
    }

    h3 {
      margin: 0;
      font-size: 15px;
      font-weight: 600;
      color: var(--gray-900);
    }

    a {
      text-decoration: none;
      color: var(--gray-500);
      font-size: 12px;
      transition: all 0.2s ease;

      &:hover {
        color: var(--main-color);
      }
    }

    .details, .missing-keys {
      margin-left: auto;
    }

    .missing-keys {
      color: var(--gray-700);
      font-size: 12px;
      font-weight: 500;

      & > span {
        margin-left: 6px;
        user-select: all;
        background-color: rgba(251, 146, 60, 0.15);
        color: #d97706;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 11px;
        border: 1px solid rgba(251, 146, 60, 0.2);
      }
    }

    .expand-button, .config-button {
      height: 32px;
      width: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 0;
      cursor: pointer;
      color: var(--gray-500);
      border-radius: 6px;
      transition: all 0.2s ease;

      &:hover {
        background-color: var(--gray-100);
        color: var(--gray-700);
      }

      .icon-wrapper {
        display: inline-flex;
        transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);

        &.rotated {
          transform: rotate(180deg);
        }
      }
    }
  }

  .card-body-wrapper {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    background: white;

    &.expanded {
      max-height: 800px;
    }
  }

  .card-body {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 10px;
    padding: 12px;
    background: #fafafa;

    // 普通模型卡片样式
    .card-models {
      width: 100%;
      border-radius: 6px;
      border: 1px solid var(--gray-200);
      padding: 10px 12px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-sizing: border-box;
      background: white;
      transition: all 0.2s ease;
      min-height: 42px;

      &:hover {
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
        border-color: var(--gray-400);
      }

      .model_name {
        font-size: 14px;
        font-weight: 500;
        color: var(--gray-900);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        line-height: 1.4;
      }

      .select-btn {
        width: 16px;
        height: 16px;
        flex: 0 0 16px;
        border-radius: 50%;
        border: 2px solid var(--gray-300);
        background: white;
        transition: all 0.2s ease;

        &:hover {
          border-color: var(--main-color);
        }
      }
    }

    // 自定义模型卡片样式 - 统一设计
    .custom-model {
      display: flex;
      flex-direction: column;
      align-items: stretch;
      padding: 10px 12px;
      gap: 8px;
      cursor: pointer;
      min-height: 64px;
      background: white;
      border-radius: 6px;
      border: 1px solid var(--gray-200);
      transition: all 0.2s ease;

      &:hover {
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
        border-color: var(--gray-400);

        .card-models__header .action {
          opacity: 1;
        }
      }

        .card-models__header {
        width: 100%;
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        min-height: 18px;

        .name {
          font-size: 14px;
          font-weight: 500;
          color: var(--gray-900);
          line-height: 1.4;
          flex: 1;
          margin-right: 8px;
          word-break: break-word;
        }

        .action {
          opacity: 0;
          transition: opacity 0.2s ease;
          display: flex;
          gap: 4px;
          flex-shrink: 0;
          margin-top: -1px;

          button {
            padding: 4px;
            height: 24px;
            width: 24px;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;

            &:hover {
              background-color: var(--gray-100);
            }

            &:disabled {
              opacity: 0.4;
              cursor: not-allowed;

              &:hover {
                background-color: transparent;
              }
            }
          }
        }
      }

      .api_base {
        font-size: 12px;
        color: var(--gray-600);
        line-height: 1.3;
        word-break: break-all;
        margin-top: auto;
      }

      // 添加模型的special样式
      &.add-model {
        border: 2px dashed var(--gray-300);
        background: white;
        justify-content: center;
        align-items: center;
        text-align: center;
        min-height: 64px;

        &:hover {
          border-color: var(--main-color);
          background: #fafafa;
        }

        .card-models__header {
          justify-content: center;
          align-items: center;
          text-align: center;

          .name {
            color: var(--main-color);
            font-weight: 600;
            margin-right: 0;
            text-align: center;
          }
        }

        .api_base {
          color: var(--gray-500);
          text-align: center;
          margin-top: 4px;
        }
      }
    }
  }
}

.custom-model-modal {
  .ant-form-item {
    margin-bottom: 10px;
    .form-item-description {
      font-size: 12px;
      color: var(--gray-600);
      margin-bottom: 10px;
    }
  }
}

.provider-config-modal {
  .ant-modal-body {
    padding: 16px 0 !important;
    .modal-loading-container {
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      height: 200px;

      .loading-text {
        margin-top: 20px;
        color: var(--gray-700);
        font-size: 14px;
      }
    }

    .modal-config-content {
      max-height: 70vh;
      overflow-y: auto;

      .modal-config-header {
        margin-bottom: 20px;

        .description {
          font-size: 14px;
          color: var(--gray-600);
          margin: 0;
        }
      }

      .modal-models-section {
        .model-search {
          margin-bottom: 10px;
          padding: 0 6px;

          .ant-input-affix-wrapper {
            border-radius: 6px;
            &:hover, &:focus {
              border-color: var(--main-color);
            }
            .anticon {
              color: var(--gray-500);
            }
          }
        }
        .selection-summary {
          margin: 0 6px 10px;
          font-size: 14px;
          color: var(--gray-600);

          .filter-info {
            color: var(--gray-500);
          }
        }
        .modal-checkbox-list {
          max-height: 50vh;
          overflow-y: auto;
          .modal-checkbox-item {
            display: inline-block;
            margin-bottom: 4px;
            padding: 4px 6px;
            border-radius: 6px;
            background-color: white;
            border: 1px solid var(--gray-200);

            &:hover {
              background-color: var(--gray-50);
            }
          }
        }
      }
    }
  }
}

// 针对不同状态的额外样式调整
.unconfigured-provider {
  .card-body {
    .card-models {
      opacity: 0.6;
      pointer-events: none;

      .model_name {
        color: var(--gray-500);
      }

      &:hover {
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
        border-color: var(--gray-300);
      }
    }
  }
}

// 响应式调整
@media (max-width: 768px) {
  .model-provider-card {
    margin-bottom: 10px;

    .card-body {
      grid-template-columns: 1fr;
      gap: 8px;
      padding: 10px;
    }

    .card-header {
      padding: 10px;
      gap: 8px;

      .model-icon {
        width: 24px;
        height: 24px;
      }

      h3 {
        font-size: 14px;
      }

      .expand-button, .config-button {
        height: 30px;
        width: 30px;
      }
    }
  }
}
</style>
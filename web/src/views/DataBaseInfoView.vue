<template>
<div>
  <HeaderComponent
    :title="database.name || t('database.databaseInfo')"
    :loading="state.databaseLoading"
  >
    <template #description>
      <div class="database-info">
        <a-tag color="blue" v-if="database.embed_model">{{ database.embed_model }}</a-tag>
        <a-tag color="green" v-if="database.dimension">{{ database.dimension }}</a-tag>
        <span class="row-count">{{ database.files ? Object.keys(database.files).length : 0 }} {{ t('database.files') }} · {{ database.db_id }}</span>
      </div>
    </template>
    <template #actions>
      <a-button type="primary" @click="backToDatabase">
        <LeftOutlined /> {{ t('common.back') }}
      </a-button>
      <a-button type="primary" @click="showEditModal">
        <EditOutlined />
      </a-button>
    </template>
  </HeaderComponent>
  <a-alert v-if="configStore.config.embed_model &&database.embed_model != configStore.config.embed_model" :message="t('database.vectorModelMismatch')" type="warning" style="margin: 10px 20px;" />

  <!-- 添加编辑对话框 -->
  <a-modal v-model:open="editModalVisible" :title="t('database.editKnowledgeBase')">
    <template #footer>
      <a-button danger @click="deleteDatabse" style="margin-right: auto; margin-left: 0;">
        <DeleteOutlined /> {{ t('database.deleteDatabase') }}
      </a-button>
      <a-button key="back" @click="editModalVisible = false">{{ t('common.cancel') }}</a-button>
      <a-button key="submit" type="primary" :loading="loading" @click="handleEditSubmit">{{ t('common.confirm') }}</a-button>
    </template>
    <a-form :model="editForm" :rules="rules" ref="editFormRef" layout="vertical">
      <a-form-item :label="t('database.knowledgeBaseName')" name="name" required>
        <a-input v-model:value="editForm.name" :placeholder="t('database.enterKnowledgeBaseName')" />
      </a-form-item>
      <a-form-item :label="t('database.knowledgeBaseDescription')" name="description">
        <a-textarea v-model:value="editForm.description" :placeholder="t('database.enterKnowledgeBaseDescription')" :rows="4" />
      </a-form-item>
    </a-form>
  </a-modal>

  <!-- 分块参数配置弹窗 -->
  <a-modal v-model:open="chunkConfigModalVisible" :title="t('database.chunkParameterConfig')" width="500px">
    <template #footer>
      <a-button key="back" @click="chunkConfigModalVisible = false">{{ t('common.cancel') }}</a-button>
      <a-button key="submit" type="primary" @click="handleChunkConfigSubmit">{{ t('common.confirm') }}</a-button>
    </template>
    <div class="chunk-config-content">
      <div class="params-info">
        <p>{{ t('database.chunkConfigDescription') }}</p>
      </div>
      <a-form
        :model="tempChunkParams"
        name="chunkConfig"
        autocomplete="off"
        layout="vertical"
      >
        <a-form-item :label="t('database.chunkSize')" name="chunk_size">
          <a-input-number v-model:value="tempChunkParams.chunk_size" :min="100" :max="10000" style="width: 100%;" />
          <p class="param-description">{{ t('database.chunkSizeDescription') }}</p>
        </a-form-item>
        <a-form-item :label="t('database.chunkOverlap')" name="chunk_overlap">
          <a-input-number v-model:value="tempChunkParams.chunk_overlap" :min="0" :max="1000" style="width: 100%;" />
          <p class="param-description">{{ t('database.chunkOverlapDescription') }}</p>
        </a-form-item>
        <a-form-item :label="t('database.autoIndexing')" name="auto_indexing">
          <a-switch v-model:checked="tempChunkParams.auto_indexing" />
          <p class="param-description">{{ t('database.autoIndexingDescription') }}</p>
        </a-form-item>
      </a-form>
    </div>
  </a-modal>

  <!-- 添加文件弹窗 -->
  <a-modal v-model:open="addFilesModalVisible" :title="t('database.addFiles')" width="800px">
    <template #footer>
      <a-button key="back" @click="addFilesModalVisible = false">{{ t('common.cancel') }}</a-button>
      <a-button
        key="submit"
        type="primary"
        @click="chunkData"
        :loading="state.chunkLoading"
        :disabled="(uploadMode === 'file' && fileList.length === 0) || (uploadMode === 'url' && !urlList.trim())"
      >
        {{ t('database.generateChunks') }}
      </a-button>
    </template>
    <div class="add-files-content">
      <div class="upload-header">
        <div class="source-selector">
          <div class="upload-mode-selector" @click="uploadMode = 'file'" :class="{ active: uploadMode === 'file' }">
            <FileOutlined /> {{ t('database.uploadFiles') }}
          </div>
          <div class="upload-mode-selector" @click="uploadMode = 'url'" :class="{ active: uploadMode === 'url' }">
            <LinkOutlined /> {{ t('database.enterWebUrls') }}
          </div>
        </div>
        <div class="config-controls">
          <a-button type="dashed" @click="showChunkConfigModal">
            <SettingOutlined /> {{ t('database.chunkParameterConfig') }} ({{ chunkParams.chunk_size }}/{{ chunkParams.chunk_overlap }}{{ chunkParams.auto_indexing ? '/' + t('database.autoIndexing') : '' }})
          </a-button>
        </div>
      </div>

      <div class="ocr-config">
        <a-form layout="horizontal">
          <a-form-item :label="t('database.useOcr')" name="enable_ocr">
            <a-select v-model:value="chunkParams.enable_ocr" :options="enable_ocr_options" style="width: 200px;" />
            <span class="param-description">{{ t('database.ocrDescription') }}</span>
          </a-form-item>
        </a-form>
      </div>

      <!-- 文件上传区域 -->
      <div class="upload" v-if="uploadMode === 'file'">
        <a-upload-dragger
          class="upload-dragger"
          v-model:fileList="fileList"
          name="file"
          :multiple="true"
          :disabled="state.chunkLoading"
          :action="'/api/data/upload?db_id=' + databaseId"
          :headers="getAuthHeaders()"
          @change="handleFileUpload"
          @drop="handleDrop"
        >
          <p class="ant-upload-text">{{ t('database.fileUploadArea') }}</p>
          <p class="ant-upload-hint">
            {{ t('database.fileUploadHint') }}
          </p>
        </a-upload-dragger>
      </div>

      <!-- URL 输入区域 -->
      <div class="url-input" v-else>
        <a-form layout="vertical">
          <a-form-item :label="t('database.webUrlsLabel')">
            <a-textarea
              v-model:value="urlList"
              :placeholder="t('database.enterWebUrls')"
              :rows="6"
              :disabled="state.chunkLoading"
            />
          </a-form-item>
        </a-form>
        <p class="url-hint">
          {{ t('database.urlHint') }}
        </p>
      </div>
    </div>
  </a-modal>

  <div class="db-main-container">
    <a-tabs v-model:activeKey="state.curPage" class="atab-container" type="card">

      <a-tab-pane key="files">
        <template #tab><span><ReadOutlined />{{ t('database.fileList') }}</span></template>
        <div class="db-tab-container">
          <div class="actions" style="display: flex; gap: 10px; justify-content: space-between;">
            <div class="left-actions" style="display: flex; gap: 10px;">
              <a-button type="primary" @click="showAddFilesModal" :loading="state.refrashing" :icon="h(PlusOutlined)">{{ t('database.addFiles') }}</a-button>
              <a-button @click="handleRefresh" :loading="state.refrashing">{{ t('database.refresh') }}</a-button>
            </div>
            <div class="batch-actions" style="display: flex; gap: 10px;" v-if="selectedRowKeys.length > 0">
              <span style="margin-right: 8px;">{{ t('database.selectedItems', { count: selectedRowKeys.length }) }}</span>
              <a-button
                type="primary"
                @click="handleBatchIndex"
                :loading="state.batchIndexing"
                :disabled="!hasSelectedPendingFiles"
              >
                {{ t('database.batchIndex') }}
              </a-button>
              <a-button
                type="primary"
                danger
                @click="handleBatchDelete"
                :loading="state.batchDeleting"
                :disabled="!canBatchDelete"
              >
                {{ t('database.batchDelete') }}
              </a-button>
            </div>
          </div>

          <a-table
            :columns="columns"
            :data-source="Object.values(database.files || {})"
            row-key="file_id"
            class="my-table"
            size="small"
            bordered
            :pagination="pagination"
            :row-selection="{
              selectedRowKeys: selectedRowKeys,
              onChange: onSelectChange,
              getCheckboxProps: getCheckboxProps
            }">
            <template #bodyCell="{ column, text, record }">
              <a-tooltip v-if="column.key === 'filename'" :title="record.file_id" placement="left">
                <a-button class="main-btn" type="link" @click="openFileDetail(record)">{{ text }}</a-button>
              </a-tooltip>
              <span v-else-if="column.key === 'type'" :class="['span-type', text]">{{ text?.toUpperCase() }}</span>
              <CheckCircleFilled v-else-if="column.key === 'status' && text === 'done'" style="color: #41A317;"/>
              <CloseCircleFilled v-else-if="column.key === 'status' && text === 'failed'" style="color: #FF4D4F ;"/>
              <HourglassFilled v-else-if="column.key === 'status' && text === 'processing'" style="color: #1677FF;"/>
              <ClockCircleFilled v-else-if="column.key === 'status' && text === 'waiting'" style="color: #FFCD43;"/>
              <HddOutlined v-else-if="column.key === 'status' && text === 'pending_indexing'" style="color: #FFCD43;"/>

              <a-tooltip v-else-if="column.key === 'created_at'" :title="record.status" placement="left">
                <span>{{ formatRelativeTime(Math.round(text*1000)) }}</span>
              </a-tooltip>

              <div v-else-if="column.key === 'action'" style="display: flex; gap: 10px;">
                <a-button
                  v-if="record.status === 'pending_indexing' || record.status === 'failed'"
                  type="link"
                  @click="handleIndexFile(record.file_id)"
                  :loading="state.indexingFile === record.file_id"
                  :disabled="state.lock || state.indexingFile === record.file_id"
                >
                  {{ t('database.indexing') }}
                </a-button>
                <a-button class="del-btn" type="link"
                  @click="handleDeleteFile(record.file_id)"
                  :disabled="state.lock || record.status === 'processing' || record.status === 'waiting' || state.indexingFile === record.file_id"
                  >
                  {{ t('database.deleteFile') }}
                </a-button>
              </div>
              <span v-else>{{ text }}</span>
            </template>
          </a-table>
          <a-modal
            v-model:open="state.fileDetailModalVisible"
            class="custom-class"
            :title="selectedFile?.filename || t('database.fileDetails')"
            width="1000px"
            @after-open="afterOpenChange"
            :footer="null"
          >
            <template v-if="state.fileDetailLoading">
              <div class="loading-container">
                <a-spin :tip="t('database.loading')" />
              </div>
            </template>
            <template v-else>
              <h3>{{ t('database.segments', { count: selectedFile?.lines?.length || 0 }) }}</h3>
              <div class="file-detail-content">
                <p v-for="line in selectedFile?.lines || []" :key="line.id" class="line-text">
                  {{ line.text }}
                </p>
              </div>
            </template>
          </a-modal>
        </div>
      </a-tab-pane>

      <a-tab-pane key="query-test" force-render>
        <template #tab><span><SearchOutlined />{{ t('database.retrievalTest') }}</span></template>
        <div class="query-test-container db-tab-container">
          <div class="sider">
            <div class="sider-top">
              <div class="query-params" v-if="state.curPage == 'query-test'">
                <!-- <h3 class="params-title">查询参数</h3> -->
                <div class="params-group">
                  <div class="params-item">
                    <p>{{ t('database.retrievalCount') }}：</p>
                    <a-input-number size="small" v-model:value="meta.maxQueryCount" :min="1" :max="20" />
                  </div>
                  <div class="params-item">
                    <p>{{ t('database.filterLowQuality') }}：</p>
                    <a-switch v-model:checked="meta.filter" />
                  </div>
                  <div class="params-item">
                    <p>{{ t('database.topK') }}：</p>
                    <a-input-number size="small" v-model:value="meta.topK" :min="1" :max="meta.maxQueryCount" />
                  </div>
                  <div class="params-item" v-if="configStore.config.enable_reranker">
                    <p>{{ t('database.sortingMethod') }}：</p>
                    <a-radio-group v-model:value="meta.sortBy" button-style="solid" size="small">
                      <a-radio-button value="rerank_score">{{ t('database.rerankerScore') }}</a-radio-button>
                      <a-radio-button value="distance">{{ t('database.similarity') }}</a-radio-button>
                    </a-radio-group>
                  </div>
                </div>
                <div class="params-group">
                  <div class="params-item w100" v-if="configStore.config.enable_reranker">
                    <p>{{ t('database.rerankerThreshold') }}：</p>
                    <a-slider v-model:value="meta.rerankThreshold" :min="0" :max="1" :step="0.01" />
                  </div>
                  <div class="params-item w100">
                    <p>{{ t('database.distanceThreshold') }}：</p>
                    <a-slider v-model:value="meta.distanceThreshold" :min="0" :max="1" :step="0.01" />
                  </div>
                </div>
                <div class="params-group">
                  <div class="params-item col">
                    <p>{{ t('database.queryRewrite') }}<small>{{ t('database.rewriteNote') }}</small>：</p>
                    <a-segmented v-model:value="meta.use_rewrite_query" :options="use_rewrite_queryOptions">
                      <template #label="{ payload }">
                        <div>
                          <p style="margin: 4px 0">{{ payload.subTitle }}</p>
                        </div>
                      </template>
                    </a-segmented>
                  </div>
                </div>
              </div>
            </div>
            <div class="sider-bottom">
            </div>
          </div>
          <div class="query-result-container">
            <div class="query-action">
              <a-textarea
                v-model:value="queryText"
                :placeholder="t('database.enterQuerySentence')"
                :auto-size="{ minRows: 2, maxRows: 10 }"
              />
              <a-button class="btn-query" @click="onQuery" :disabled="queryText.length == 0">
                <span v-if="!state.searchLoading"><SearchOutlined /> {{ t('database.retrieve') }}</span>
                <span v-else><LoadingOutlined /></span>
              </a-button>
            </div>

            <!-- 新增示例按钮 -->
            <!-- <div class="query-examples-container">
              <div class="examples-title">示例查询：</div>
              <div class="query-examples">
                <a-button v-for="example in queryExamples" :key="example" @click="useQueryExample(example)">
                  {{ example }}
                </a-button>
              </div>
            </div> -->
            <div class="query-test" v-if="queryResult">
              <div class="results-overview">
                <div class="results-stats">
                  <span class="stat-item">
                    <strong>{{ t('database.total') }}:</strong> {{ queryResult.all_results.length }}
                  </span>
                  <span class="stat-item">
                    <strong>{{ t('database.afterFiltering') }}:</strong> {{ filteredResults.length }}
                  </span>
                  <span class="stat-item">
                    <strong>{{ t('database.topK') }}:</strong> {{ meta.topK }}
                  </span>
                  <span class="stat-item">
                    <strong>{{ t('database.sortingMethod') }}:</strong> {{ meta.sortBy === 'rerank_score' ? t('database.rerankerScore') : t('database.similarity') }}
                  </span>
                </div>
                <div class="rewritten-query" v-if="queryResult.rw_query">
                  <strong>{{ t('database.rewrittenQuery') }}:</strong>
                  <span class="query-text">{{ queryResult.rw_query }}</span>
                </div>
              </div>
              <div class="query-result-card" v-for="(result, idx) in (filteredResults)" :key="idx">
                <p>
                  <strong>#{{ idx + 1 }}&nbsp;&nbsp;&nbsp;</strong>
                  <span>{{ result.file.filename }}&nbsp;&nbsp;&nbsp;</span>
                  <span><strong>{{ t('database.similarity') }}</strong>：{{ result.distance.toFixed(4) }}&nbsp;&nbsp;&nbsp;</span>
                  <span v-if="result.rerank_score"><strong>{{ t('database.rerankerScore') }}</strong>：{{ result.rerank_score.toFixed(4) }}</span>
                </p>
                <p class="query-text">{{ result.entity.text }}</p>
              </div>
            </div>
          </div>
        </div>
      </a-tab-pane>
      <!-- <a-tab-pane key="3" tab="Tab 3">Content of Tab Pane 3</a-tab-pane> -->
    </a-tabs>
  </div>
</div>
</template>

<script setup>
import { onMounted, reactive, ref, watch, toRaw, onUnmounted, computed } from 'vue';
import { message, Modal } from 'ant-design-vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useConfigStore } from '@/stores/config'
import { useUserStore } from '@/stores/user'
import { knowledgeBaseApi } from '@/apis/admin_api'
import HeaderComponent from '@/components/HeaderComponent.vue';
import {
  ReadOutlined,
  LeftOutlined,
  CheckCircleFilled,
  HourglassFilled,
  CloseCircleFilled,
  ClockCircleFilled,
  DeleteOutlined,
  CloudUploadOutlined,
  SearchOutlined,
  LoadingOutlined,
  FileOutlined,
  LinkOutlined,
  EditOutlined,
  PlusOutlined,
  HddOutlined,
  SettingOutlined,
} from '@ant-design/icons-vue'
import { h } from 'vue';

const { t } = useI18n()

const route = useRoute();
const router = useRouter();
const databaseId = ref(route.params.database_id);
const database = ref({});

const fileList = ref([]);
const selectedFile = ref(null);

// 查询测试
const queryText = ref('');
const queryResult = ref(null)
const filteredResults = ref([])
const configStore = useConfigStore()

const state = reactive({
  databaseLoading: false,
  adding: false,
  refrashing: false,
  searchLoading: false,
  lock: false,
  fileDetailModalVisible: false,
  fileDetailLoading: false,
  refreshInterval: null,
  curPage: "files",
  indexingFile: null,
  batchIndexing: false,
  batchDeleting: false,
  chunkLoading: false,
});

const meta = reactive({
  mode: 'search',
  maxQueryCount: 30,
  filter: true,
  use_rewrite_query: 'off',
  rerankThreshold: 0.1,
  distanceThreshold: 0.3,
  topK: 10,
  sortBy: 'rerank_score',
});

const enable_ocr_options = ref([
  { value: 'disable', payload: { title: t('database.off') } },
  { value: 'onnx_rapid_ocr', payload: { title: 'ONNX with RapidOCR' } },
  { value: 'mineru_ocr', payload: { title: 'MinerU OCR' } },
  { value: 'paddlex_ocr', payload: { title: 'Paddlex OCR' } },
])

const use_rewrite_queryOptions = ref([
  { value: 'off', payload: { title: 'off', subTitle: t('database.off') } },
  { value: 'on', payload: { title: 'on', subTitle: t('database.enableRewrite') } },
  { value: 'hyde', payload: { title: 'hyde', subTitle: t('database.pseudoDocGeneration') } },
])

const pagination = ref({
  pageSize: 15,
  current: 1,
  total: computed(() => database.value?.files?.length || 0),
  showSizeChanger: true,
  onChange: (page, pageSize) => pagination.value.current = page,
  showTotal: (total, range) => t('common.showTotal', { total }),
  onShowSizeChange: (current, pageSize) => pagination.value.pageSize = pageSize,
})

const filterQueryResults = () => {
  if (!queryResult.value || !queryResult.value.all_results) {
    return;
  }

  let results = toRaw(queryResult.value.all_results);
  console.log("results", results);

  if (meta.filter) {
    results = results.filter(r => r.distance >= meta.distanceThreshold);
    console.log("before", results);

    // 根据排序方式决定排序逻辑
    if (configStore.config.enable_reranker) {
      // 先过滤掉低于阈值的结果
      results = results.filter(r => r.rerank_score >= meta.rerankThreshold);

      // 根据选择的排序方式进行排序
      if (meta.sortBy === 'rerank_score') {
        results = results.sort((a, b) => b.rerank_score - a.rerank_score);
      } else {
        // 按距离排序 (数值越大表示越相似)
        results = results.sort((a, b) => b.distance - a.distance);
      }
    } else {
      // 没有启用重排序时，默认按距离排序
      results = results.sort((a, b) => b.distance - a.distance);
    }

    console.log("after", results);

    results = results.slice(0, meta.topK);
  }

  filteredResults.value = results;
}

const onQuery = () => {
  if (database.value.embed_model != configStore.config.embed_model) {
    message.error(t('database.vectorModelMismatch'))
    return
  }

  console.log(queryText.value)
  state.searchLoading = true
  if (!queryText.value.trim()) {
    message.error(t('chat.pleaseEnterMessage'))
    state.searchLoading = false
    return
  }

  knowledgeBaseApi.queryKnowledgeBase(databaseId.value, {
    query: queryText.value,
    limit: meta.maxQueryCount,
    use_rewrite_query: meta.use_rewrite_query
  })
    .then(data => {
      queryResult.value = data;
      filterQueryResults();
    })
    .catch(error => {
      console.error(error)
      message.error(error.message)
    })
    .finally(() => state.searchLoading = false)
}

const handleFileUpload = (event) => {
  console.log(event)
  console.log(fileList.value)
}

const handleDrop = (event) => {
  console.log(event)
  console.log(fileList.value)
}

const afterOpenChange = (visible) => {
  if (!visible) {
    selectedFile.value = null
  }
}

const backToDatabase = () => {
  router.push('/database')
}

const handleRefresh = () => {
  state.refrashing = true
  getDatabaseInfo().then(() => {
    state.refrashing = false
    console.log(database.value)
  })
}

const deleteDatabse = () => {
  Modal.confirm({
    title: t('messages.confirmDelete'),
    content: t('messages.confirmDelete'),
    okText: t('database.confirm'),
    cancelText: t('database.cancel'),
    onOk() {
      state.lock = true
      knowledgeBaseApi.deleteDatabase(databaseId.value)
        .then(data => {
          console.log(data)
          message.success(data.message || t('database.deleteSuccess'))
          router.push('/database')
        })
        .catch(error => {
          console.error(error)
          message.error(error.message || t('database.deleteFailed'))
        })
        .finally(() => {
          state.lock = false
        })
    },
  });
}

const openFileDetail = (record) => {
  selectedFile.value = record
  if (!record.lines) {
    state.fileDetailLoading = true
    knowledgeBaseApi.getFileDetail(databaseId.value, record.file_id)
      .then(data => {
        selectedFile.value.lines = data.lines
        state.fileDetailLoading = false
        state.fileDetailModalVisible = true
      })
      .catch(error => {
        console.error(error)
        message.error(t('messages.fileDetailsFailed'))
        state.fileDetailLoading = false
      })
  } else {
    state.fileDetailModalVisible = true
  }
}

const formatRelativeTime = (timestamp, offset = 0) => {
    // 如果调整为东八区时间（UTC+8），则offset为8，否则为0
    const timezoneOffset = offset * 60 * 60 * 1000; // 东八区偏移量（毫秒）
    const adjustedTimestamp = timestamp + timezoneOffset;

    const now = Date.now();
    const secondsPast = (now - adjustedTimestamp) / 1000;

    if (secondsPast < 60) {
        return Math.round(secondsPast) + ' 秒前';
    } else if (secondsPast < 3600) {
        return Math.round(secondsPast / 60) + ' 分钟前';
    } else if (secondsPast < 86400) {
        return Math.round(secondsPast / 3600) + ' 小时前';
    } else {
        const date = new Date(adjustedTimestamp);
        const year = date.getFullYear();
        const month = date.getMonth() + 1;
        const day = date.getDate();
        return `${year} 年 ${month} 月 ${day} 日`;
    }
}

const getDatabaseInfo = () => {
  state.databaseLoading = true
  knowledgeBaseApi.getDatabaseInfo(databaseId.value)
    .then(data => {
      database.value = data.database
      chunkParams.chunk_size = data.database.chunk_size || 1000
      chunkParams.chunk_overlap = data.database.chunk_overlap || 200
      chunkParams.auto_indexing = data.database.auto_indexing || false
      chunkParams.enable_ocr = data.database.enable_ocr || 'disable'
      editForm.name = data.database.name
      editForm.description = data.database.description
      state.databaseLoading = false
    })
    .catch(error => {
      console.error(error)
      message.error(error.message || t('database.loadFailed'))
      state.databaseLoading = false
    })
}

const deleteFile = (fileId) => {
  state.lock = true
  knowledgeBaseApi.deleteFile(databaseId.value, fileId)
    .then(data => {
      message.success(data.message || t('database.deleteSuccess'))
      handleRefresh()
    })
    .catch(error => {
      console.error(error)
      message.error(error.message || t('database.deleteFailed'))
    })
    .finally(() => state.lock = false)
}

const handleDeleteFile = (fileId) => {
  Modal.confirm({
    title: t('database.confirmDeleteFile'),
    content: t('database.confirmDeleteFile'),
    okText: t('database.confirm'),
    cancelText: t('database.cancel'),
    onOk() {
      deleteFile(fileId);
    },
  });
}

const handleBatchDelete = () => {
  const fileCount = selectedRowKeys.value.length;
  if (fileCount === 0) {
    message.info(t('database.noFilesToDelete'));
    return;
  }

  Modal.confirm({
    title: t('database.confirmBatchDelete', { count: fileCount }),
    content: t('database.confirmBatchDelete', { count: fileCount }),
    okText: t('database.confirm'),
    cancelText: t('database.cancel'),
    onOk() {
      batchDeleteFiles();
    },
  });
}

const batchDeleteFiles = async () => {
  state.batchDeleting = true;
  const filesToDelete = [...selectedRowKeys.value]; // 创建副本
  let succeeded = 0;
  let failed = 0;

  for (const fileId of filesToDelete) {
    try {
      await knowledgeBaseApi.deleteFile(databaseId.value, fileId);
      succeeded++;
      
      // 从选中列表中移除成功删除的文件
      const index = selectedRowKeys.value.indexOf(fileId);
      if (index > -1) {
        selectedRowKeys.value.splice(index, 1);
      }
    } catch (error) {
      console.error(`Failed to delete file ${fileId}:`, error);
      failed++;
    }
  }
  
  // 显示结果消息
  if (succeeded > 0) {
    message.success(t('database.deleteSuccessCount', { count: succeeded }));
  }
  if (failed > 0) {
    message.error(t('database.deleteFailedCount', { count: failed }));
  }
  
  if (succeeded > 0) {
    // 只有在有成功删除的情况下才刷新
    try {
      console.error('批量删除出错:', error);
      message.error(t('database.batchDeleteError'));
    } finally {
      state.batchDeleting = false;
    }
  } else {
    state.batchDeleting = false;
  }
}

const chunkParams = ref({
  chunk_size: 1000,
  chunk_overlap: 200,
  enable_ocr: 'disable',
  auto_indexing: false,
})

const chunkResults = ref([]);
const activeFileKeys = ref([]);

// 获取所有分块的总数
const getTotalChunks = () => {
  return chunkResults.value.reduce((total, file) => total + file.nodes.length, 0);
}

const chunkData = () => {
  // "生成分块" - 修改后的逻辑
  const files = fileList.value.filter(file => file.status === 'done').map(file => file.response.file_path)
  const urls = urlList.value.split('\n').filter(url => url.trim()).map(url => url.trim())

  if (uploadMode.value === 'file' && files.length === 0) {
    message.error(t('database.uploadFilesFirst'))
    return
  }

  const isValidUrl = (string) => {
    try {
      const url = new URL(string);
      return url.protocol === 'http:' || url.protocol === 'https:';
    } catch (_) {
      return false;
    }
  }

  if (uploadMode.value === 'url' && (!urls.every(isValidUrl))) {
    message.error(t('database.validUrlRequired'));
    return;
  }

  state.chunkLoading = true

  if (uploadMode.value === 'file') {
    const chunkDataPayload = {
      ...chunkParams.value,
      files: files
    }

    knowledgeBaseApi.chunkFiles(databaseId.value, chunkDataPayload)
      .then((data) => {
        console.log('文件处理结果:', data)
        if (data.status === 'success') {
          const autoIndexingInfo = chunkParams.value.auto_indexing ? '，自动索引已启用' : ''
          message.info(data.message + autoIndexingInfo || t('database.fileSubmittedForProcessing'));
          fileList.value = [];
          addFilesModalVisible.value = false;
          handleRefresh();
        } else {
          message.error(data.message || t('database.fileProcessingFailed'));
        }
      })
      .catch((error) => {
        console.error(error)
        message.error(error.message || t('database.fileProcessingRequestFailed'))
      })
      .finally(() => state.chunkLoading = false)
  } else {
    chunkUrls()
  }
}

const chunkUrls = () => {
  const urls = urlList.value.split('\n').filter(url => url.trim()).map(url => url.trim())

  state.chunkLoading = true
  const chunkDataPayload = {
    ...chunkParams.value,
    urls: urls
  }

  knowledgeBaseApi.chunkUrls(databaseId.value, chunkDataPayload)
    .then((data) => {
      const autoIndexingInfo = chunkParams.value.auto_indexing ? '，自动索引已启用' : ''
      if (data.status === 'success') {
        addFilesModalVisible.value = false
        handleRefresh()
        message.success(data.message + autoIndexingInfo || t('database.urlSubmittedForProcessing'));
      } else {
        message.error(data.message || t('database.urlProcessingFailed'));
      }
    })
    .catch((error) => {
      console.error(error)
      message.error(error.message || t('database.urlProcessingRequestFailed'));
    })
    .finally(() => state.chunkLoading = false)
}

const columns = computed(() => [
  // { title: '文件ID', dataIndex: 'file_id', key: 'file_id' },
  { title: t('database.filename'), dataIndex: 'filename', key: 'filename', ellipsis: true },
  { title: t('database.uploadTime'), dataIndex: 'created_at', key: 'created_at', width: 150 },
  { title: t('database.status'), dataIndex: 'status', key: 'status', width: 80 },
  { title: t('database.type'), dataIndex: 'type', key: 'type', width: 80 },
  { title: t('database.action'), key: 'action', dataIndex: 'file_id', width: 150 }
])

const queryExamples = computed(() => [
  t('database.queryExamples.example1'),
  t('database.queryExamples.example2'),
  t('database.queryExamples.example3'),
  t('database.queryExamples.example4'),
])

const updateDatabaseInfo = () => {
  knowledgeBaseApi.updateDatabaseInfo(databaseId.value, editForm)
    .then(() => {
      database.value.name = editForm.name
      database.value.description = editForm.description
      editModalVisible.value = false
      message.success(t('database.knowledgeBaseUpdateSuccess'));
    })
    .catch(error => {
      console.error(error)
      message.error(error.message || t('database.updateFailed'));
    })
}

const updateChunkParams = () => {
  chunkParams.chunk_size = tempChunkParams.chunk_size
  chunkParams.chunk_overlap = tempChunkParams.chunk_overlap
  chunkParams.auto_indexing = tempChunkParams.auto_indexing
  chunkConfigModalVisible.value = false
  message.success(t('database.chunkConfigUpdated'));
}

const handleIndexFile = (fileId) => {
  if (!fileId) {
    message.error(t('database.invalidFileId'));
    return;
  }

  state.indexingFile = fileId;
  
  knowledgeBaseApi.indexFile(databaseId.value, fileId)
    .then(response => {
      if (response.success) {
        message.success(response.message || t('database.fileIndexStarted', { fileId }));
      } else {
        message.error(response.message || t('database.fileIndexFailed', { fileId }));
      }
    })
    .catch(error => {
      console.error(error);
      message.error(error.message || t('database.fileIndexError', { fileId }));
    })
    .finally(() => {
      state.indexingFile = null;
      handleRefresh();
    });
}

const handleBatchIndex = async () => {
  const filesToIndex = selectedRowKeys.value.filter(fileId => {
    const file = Object.values(database.value.files || {}).find(f => f.file_id === fileId);
    return file && (file.status === 'pending_indexing' || file.status === 'failed');
  });

  if (filesToIndex.length === 0) {
    message.info(t('database.noFilesToIndex'));
    return;
  }

  state.batchIndexing = true;
  
  // 这里实现批量索引逻辑
  // 由于后端可能不支持批量索引，我们逐个进行索引
  for (const fileId of filesToIndex) {
    try {
      await knowledgeBaseApi.indexFile(databaseId.value, fileId);
    } catch (error) {
      console.error(`Failed to index file ${fileId}:`, error);
    }
  }
  
  state.batchIndexing = false;
  selectedRowKeys.value = [];
  handleRefresh();
}

const uploadMode = ref('file');
const urlList = ref('');

const showChunkConfigModal = () => {
  tempChunkParams.chunk_size = chunkParams.chunk_size
  tempChunkParams.chunk_overlap = chunkParams.chunk_overlap
  tempChunkParams.auto_indexing = chunkParams.auto_indexing
  chunkConfigModalVisible.value = true
}

const showAddFilesModal = () => {
  addFilesModalVisible.value = true
}

const handleEditSubmit = () => {
  try {
    updateDatabaseInfo()
  } catch (error) {
    message.error(error.message)
  }
}

const handleChunkConfigSubmit = () => {
  try {
    updateChunkParams()
  } catch (error) {
    message.error(error.message)
  }
}

const selectedRowKeys = ref([]);

const onSelectChange = (keys) => {
  selectedRowKeys.value = keys;
};

const getCheckboxProps = (record) => ({
  disabled: state.lock || record.status === 'processing' || record.status === 'waiting' || state.indexingFile === record.file_id,
});

const hasSelectedPendingFiles = computed(() => {
  const files = database.value.files || {};
  return selectedRowKeys.value.some(key => files[key]?.status === 'pending_indexing');
});

const canBatchDelete = computed(() => {
  const files = database.value.files || {};
  return selectedRowKeys.value.some(key => {
    const file = files[key];
    return !(state.lock || file.status === 'processing' || file.status === 'waiting' || state.indexingFile === file.file_id);
  });
});

watch(() => route.params.database_id, (newId) => {
    databaseId.value = newId;
    console.log(newId)
    clearInterval(state.refreshInterval)
    getDatabaseInfo()
  }
);

watch(() => meta, () => {
  filterQueryResults()
}, { deep: true })

const queryExamples = ref([
  t('database.queryExamples.example1'),
  t('database.queryExamples.example2'),
  t('database.queryExamples.example3'),
  t('database.queryExamples.example4'),
]);

const useQueryExample = (example) => {
  queryText.value = example;
  onQuery();
};

onMounted(() => {
  getDatabaseInfo();
  state.refreshInterval = setInterval(() => {
    getDatabaseInfo();
  }, 1000);
})

onUnmounted(() => {
  if (state.refreshInterval) {
    clearInterval(state.refreshInterval);
    state.refreshInterval = null;
  }
})

const uploadMode = ref('file');
const urlList = ref('');

const getAuthHeaders = () => {
  const userStore = useUserStore();
  return userStore.getAuthHeaders();
};

const editModalVisible = ref(false);
const editFormRef = ref(null);
const editForm = reactive({
  name: '',
  description: ''
});

const rules = {
  name: [{ required: true, message: '请输入知识库名称' }]
};

const chunkConfigModalVisible = ref(false);
const tempChunkParams = ref({
  chunk_size: 1000,
  chunk_overlap: 200,
  auto_indexing: false,
});

const addFilesModalVisible = ref(false);

const showEditModal = () => {
  editForm.name = database.value.name || '';
  editForm.description = database.value.description || '';
  editModalVisible.value = true;
};

</script>

<style lang="less" scoped>
.database-info {
  margin: 8px 0 0;
}

.db-main-container {
  display: flex;
  width: 100%;
}

.db-tab-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.query-test-container {
  display: flex;
  flex-direction: row;
  gap: 20px;

  .sider {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    width: 325px;
    height: 100%;
    padding: 0;
    flex: 0 0 325px;

    .sider-top {
      .query-params {
        display: flex;
        flex-direction: column;
        box-sizing: border-box;
        font-size: 15px;
        gap: 12px;
        padding-top: 12px;
        padding-right: 16px;
        border: 1px solid var(--main-light-3);
        background-color: var(--main-light-6);
        border-radius: 8px;
        padding: 16px;
        margin-right: 8px;

        .params-title {
          margin-top: 0;
          margin-bottom: 16px;
          color: var(--main-color);
          font-size: 18px;
          text-align: center;
          font-weight: bold;
        }

        .params-group {
          margin-bottom: 16px;
          padding-bottom: 16px;
          border-bottom: 1px solid var(--main-light-3);

          &:last-child {
            margin-bottom: 0;
            padding-bottom: 0;
            border-bottom: none;
          }
        }

        .params-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          margin-bottom: 12px;

          &:last-child {
            margin-bottom: 0;
          }

          p {
            margin: 0;
            color: var(--gray-900);
          }

          &.col {
            align-items: flex-start;
            flex-direction: column;
            width: 100%;
            height: auto;
          }

          &.w100,
          &.col {
            & > * {
              width: 100%;
            }
          }
        }

        .ant-slider {
          margin: 6px 0px;
        }
      }
    }
  }

  .query-result-container {
    flex: 1;
    padding-bottom: 20px;
  }

  .query-action {
    display: flex;
    gap: 8px;
    margin-bottom: 20px;

    textarea {
      padding: 12px 16px;
      border: 1px solid var(--main-light-2);
    }

    button.btn-query {
      height: auto;
      width: 100px;
      box-shadow: none;
      border: none;
      font-weight: bold;
      background: var(--main-light-3);
      color: var(--main-color);

      &:disabled {
        cursor: not-allowed;
        background: var(--main-light-4);
        color: var(--gray-700);
      }
    }
  }

  .query-examples-container {
    margin-bottom: 20px;
    padding: 12px;
    background: var(--main-light-6);
    border-radius: 8px;
    border: 1px solid var(--main-light-3);

    .examples-title {
      font-weight: bold;
      margin-bottom: 10px;
      color: var(--main-color);
    }

    .query-examples {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin: 10px 0 0;

      .ant-btn {
        font-size: 14px;
        padding: 4px 12px;
        height: auto;
        background-color: var(--gray-200);
        border: none;
        color: var(--gray-800);

        &:hover {
          color: var(--main-color);
        }
      }
    }
  }

  .query-test {
    display: flex;
    flex-direction: column;
    border-radius: 12px;
    gap: 20px;

    .results-overview {
      background-color: #fff;
      border-radius: 8px;
      padding: 16px;
      border: 1px solid var(--main-light-3);

      .results-stats {
        display: flex;
        justify-content: flex-start;

        .stat-item {
          border-radius: 4px;
          font-size: 14px;
          margin-right: 24px;
          padding: 4px 8px;
          strong {
            color: var(--main-color);
            margin-right: 4px;
          }
        }
      }

      .rewritten-query {
        border-radius: 4px;
        font-size: 14px;
        padding: 4px 8px;
        strong {
          color: var(--main-color);
          margin-right: 8px;
        }

        .query-text {
          font-style: italic;
          color: var(--gray-900);
        }
      }
    }

    .query-result-card {
      padding: 20px;
      border-radius: 8px;
      background: #fff;
      border: 1px solid var(--main-light-3);
      transition: box-shadow 0.3s ease;

      &:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
      }

      p {
        margin-bottom: 8px;
        line-height: 1.6;
        color: var(--gray-900);

        &:last-child {
          margin-bottom: 0;
        }
      }

      strong {
        color: var(--main-color);
      }

      .query-text {
        font-size: 15px;
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid var(--main-light-3);
      }
    }
  }
}

.my-table {
  button.ant-btn-link {
    padding: 0;
  }

  .span-type {
    color: white;
    padding: 2px 4px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: bold;
    opacity: 0.8;
    user-select: none;
    background: #005F77;
  }

  .pdf {
    background: #005F77;
  }

  .txt {
    background: #068033;
  }

  .docx, .doc {
    background: #2C59B7;
  }

  .md {
    background: #020817;
  }

  button.main-btn {
    font-weight: bold;
    font-size: 14px;
    color: var(--gray-800);
    &:hover {
      cursor: pointer;
      color: var(--main-color);
      font-weight: bold;
    }
  }

  button.del-btn {
    cursor: pointer;

    &:hover {
      color: var(--error-color);
    }
    &:disabled {
      cursor: not-allowed;
    }
  }
}

.file-detail-content {
  max-height: 60vh;
  overflow-y: auto;
  // padding: 0 10px;
}

.custom-class .line-text {
  padding: 10px;
  border-radius: 4px;
  margin: 8px 0;
  background-color: var(--gray-200);

  &:hover {
    background-color: var(--main-light-4);
  }
}

.add-files-content {
  .upload-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    gap: 20px;

    .source-selector {
      display: flex;
      gap: 10px;

      .upload-mode-selector {
        cursor: pointer;
        padding: 4px 16px;
        border-radius: 8px;
        background-color: var(--main-light-4);
        border: 1px solid var(--main-light-3);
        transition: all 0.2s ease;
        &.active {
          color: var(--main-color);
          background-color: var(--main-10);
          border-color: var(--main-color);
        }
      }
    }

    .config-controls {
      .ant-btn {
        border-color: var(--main-light-3);
        color: var(--gray-700);
        &:hover {
          border-color: var(--main-color);
          color: var(--main-color);
        }
      }
    }
  }

  .ocr-config {
    margin-bottom: 16px;
    padding: 12px 16px;
    background-color: var(--main-light-6);
    border-radius: 8px;
    border: 1px solid var(--main-light-3);

    .ant-form-item {
      margin-bottom: 0;

      .ant-form-item-label {
        color: var(--gray-800);
        font-weight: 500;
      }
    }

    .param-description {
      color: var(--gray-600);
      font-size: 12px;
      margin-left: 12px;
    }
  }

  .upload {
    margin-bottom: 20px;
    .upload-dragger {
      margin: 0px;
      min-height: 200px;
    }
  }

  .url-input {
    margin-bottom: 20px;

    .ant-textarea {
      border-color: var(--main-light-3);
      background-color: #fff;
      font-family: monospace;
      resize: vertical;
    }

    .ant-textarea:hover,
    .ant-textarea:focus {
      border-color: var(--main-color);
    }

    .url-hint {
      font-size: 13px;
      color: var(--gray-600);
      margin-top: 5px;
      line-height: 1.5;
    }
  }
}

.chunk-config-content {
  .params-info {
    background-color: var(--main-light-4);
    border-radius: 6px;
    padding: 10px 12px;
    margin-bottom: 16px;

    p {
      margin: 0;
      font-size: 13px;
      line-height: 1.5;
      color: var(--gray-700);
    }
  }

  .ant-form-item {
    margin-bottom: 16px;

    .ant-form-item-label {
      padding-bottom: 6px;

      label {
        color: var(--gray-800);
        font-weight: 500;
        font-size: 15px;
      }
    }
  }

  .ant-input-number {
    border-radius: 6px;

    &:hover, &:focus {
      border-color: var(--main-color);
    }
  }

  .param-description {
    color: var(--gray-600);
    font-size: 12px;
    margin-top: 4px;
    margin-bottom: 0;
  }
}

.chunk-preview {
  margin-top: 20px;

  .preview-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;

    h3 {
      margin: 0;
      color: var(--main-color);
      font-size: 18px;
    }
  }

  .result-cards {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(600px, 1fr));
    gap: 12px;
    margin-top: 10px;
  }

  .chunk {
    background-color: var(--main-light-5);
    border: 1px solid var(--main-light-3);
    border-radius: 8px;
    padding: 16px;
    word-wrap: break-word;
    word-break: break-all;
    transition: all 0.2s ease;

    &:hover {
      background-color: var(--main-light-4);
      border-color: var(--main-light-2);
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
    }

    p {
      margin: 0;
      line-height: 1.6;

      strong {
        color: var(--main-color);
        margin-right: 6px;
      }
    }
  }
}

.url-input {
  margin-bottom: 20px;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.ant-modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>

<style lang="less">
.atab-container {
  padding: 0;
  width: 100%;
  max-height: 100%;
  overflow: auto;

  div.ant-tabs-nav {
    background: var(--main-light-5);
    padding: 8px 20px;
    padding-bottom: 0;
  }

  .ant-tabs-content-holder {
    padding: 0 20px;
  }
}

.params-item.col .ant-segmented {
  width: 100%;

  div.ant-segmented-group {
    display: flex;
    justify-content: space-around;
  }
}

</style>

<style lang="less">
.db-main-container {
  .atab-container {
    padding: 0;
    width: 100%;
    max-height: 100%;
    overflow: auto;

    div.ant-tabs-nav {
      background: var(--main-light-5);
      padding: 8px 20px;
      padding-bottom: 0;
    }

    .ant-tabs-content-holder {
      padding: 0 20px;
    }
  }

  .params-item.col .ant-segmented {
    width: 100%;
    font-size: smaller;
    div.ant-segmented-group {
      display: flex;
      justify-content: space-around;
    }
    label.ant-segmented-item {
      flex: 1;
      text-align: center;
      div.ant-segmented-item-label > div > p {
        font-size: small;
      }
    }
  }
}

</style>


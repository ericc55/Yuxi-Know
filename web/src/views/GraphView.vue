<template>
  <div class="database-empty" v-if="!state.showPage">
    <a-empty>
      <template #description>
        <span>
          {{ t('graph.enableKnowledgeGraph') }} <router-link to="/setting" style="color: var(--main-color); font-weight: bold;">{{ t('navbar.settings') }}</router-link>
        </span>
      </template>
    </a-empty>
  </div>
  <div class="graph-container layout-container" v-else>
    <HeaderComponent
      :title="t('graph.title')"
      :description="graphDescription"
    >
      <template #actions>
        <div class="status-wrapper">
          <div class="status-indicator" :class="graphStatusClass"></div>
        </div>
        <a-button type="primary" @click="state.showModal = true" ><UploadOutlined/> {{ t('graph.uploadFile') }}</a-button>
        <a-button v-if="unindexedCount > 0" type="primary" @click="indexNodes" :loading="state.indexing">
          <SyncOutlined/> {{ t('graph.addIndex', { count: unindexedCount }) }}
        </a-button>
      </template>
    </HeaderComponent>

    <div class="actions">
      <div class="actions-left">
        <input
          v-model="state.searchInput"
          :placeholder="t('graph.searchEntityPlaceholder')"
          style="width: 200px"
          @keydown.enter="onSearch"
        />
        <a-button
          type="primary"
          :loading="state.searchLoading"
          :disabled="state.searchLoading"
          @click="onSearch"
        >
          {{ t('graph.searchEntity') }}
        </a-button>
      </div>
      <div class="actions-right">
        <input v-model="sampleNodeCount">
        <a-button @click="loadSampleNodes" :loading="state.fetching">{{ t('graph.getNodes') }}</a-button>
      </div>
    </div>
    <div class="main" id="container" ref="container" v-show="graphData.nodes.length > 0"></div>
    <a-empty v-show="graphData.nodes.length === 0" style="padding: 4rem 0;"/>

    <a-modal
      :open="state.showModal" :title="t('graph.uploadFile')"
      @ok="addDocumentByFile"
      @cancel="() => state.showModal = false"
      :ok-text="t('graph.addToGraph')" :cancel-text="t('common.cancel')"
      :ok-button-props="{ disabled: disabled }"
      :confirm-loading="state.precessing">
      <div v-if="graphInfo?.embed_model_name">
        <a-alert v-if="!modelMatched" :message="t('graph.modelMismatch')" type="warning" />
        <p>
          {{ t('graph.currentGraphModel', { model: graphInfo?.embed_model_name }) }}，
          {{ t('graph.currentSelectedModel', { model: cur_embed_model }) }}
        </p>
      </div>
      <p v-else>{{ t('graph.firstTimeNotice', { model: cur_embed_model }) }}</p>
      <div class="upload">
        <a-upload-dragger
          class="upload-dragger"
          v-model:fileList="fileList"
          name="file"
          :fileList="fileList"
          :max-count="1"
          :disabled="disabled"
          action="/api/data/upload"
          :headers="getAuthHeaders()"
          @change="handleFileUpload"
          @drop="handleDrop"
        >
          <p class="ant-upload-text">{{ t('graph.uploadNotice') }}</p>
          <p class="ant-upload-hint">
            {{ t('graph.uploadHint') }}
          </p>
        </a-upload-dragger>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { Graph } from "@antv/g6";
import { computed, onMounted, reactive, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { message, Button as AButton } from 'ant-design-vue';
import { useConfigStore } from '@/stores/config';
import { UploadOutlined, SyncOutlined } from '@ant-design/icons-vue';
import HeaderComponent from '@/components/HeaderComponent.vue';
import { graphApi } from '@/apis/admin_api';
import { useUserStore } from '@/stores/user';

const { t } = useI18n()
const configStore = useConfigStore();
const cur_embed_model = computed(() => configStore.config?.embed_model_names?.[configStore.config?.embed_model]?.name || '');
const modelMatched = computed(() => !graphInfo?.value?.embed_model_name || graphInfo.value.embed_model_name === cur_embed_model.value)
const disabled = computed(() => state.precessing || !modelMatched.value)

let graphInstance
const graphInfo = ref(null)
const container = ref(null);
const fileList = ref([]);
const sampleNodeCount = ref(100);
const graphData = reactive({
  nodes: [],
  edges: [],
});

const state = reactive({
  fetching: false,
  loadingGraphInfo: false,
  searchInput: '',
  searchLoading: false,
  showModal: false,
  precessing: false,
  indexing: false,
  showPage: computed(() => configStore.config.enable_knowledge_base && configStore.config.enable_knowledge_graph),
})

// 计算未索引节点数量
const unindexedCount = computed(() => {
  return graphInfo.value?.unindexed_node_count || 0;
});

const loadGraphInfo = () => {
  state.loadingGraphInfo = true
  graphApi.getGraphInfo()
    .then(data => {
      console.log(data)
      graphInfo.value = data
      state.loadingGraphInfo = false
    })
    .catch(error => {
      console.error(error)
      message.error(error.message || t('graph.loadGraphInfoFailed'))
      state.loadingGraphInfo = false
    })
}

const getGraphData = () => {
  // 计算每个节点的度数（连接数）
  const nodeDegrees = {};

  // 初始化所有节点的度数为0
  graphData.nodes.forEach(node => {
    nodeDegrees[node.id] = 0;
  });

  // 计算每个节点的连接数
  graphData.edges.forEach(edge => {
    nodeDegrees[edge.source_id] = (nodeDegrees[edge.source_id] || 0) + 1;
    nodeDegrees[edge.target_id] = (nodeDegrees[edge.target_id] || 0) + 1;
  });

  return {
    nodes: graphData.nodes.map(node => {
      // 计算节点大小，基础大小为15，每个连接增加5的大小，最小为15，最大为50
      const degree = nodeDegrees[node.id] || 0;
      const nodeSize = Math.min(15 + degree * 5, 50);

      return {
        id: node.id,
        data: {
          label: node.name,
          degree: degree, // 存储度数信息
        },
      }
    }),
    edges: graphData.edges.map(edge => {
      return {
        source: edge.source_id,
        target: edge.target_id,
        data: {
          label: edge.type
        }
      }
    }),
  }
}

const addDocumentByFile = () => {
  state.precessing = true
  const files = fileList.value.filter(file => file.status === 'done').map(file => file.response.file_path)
  graphApi.addByJsonl(files[0])
    .then((data) => {
      if (data.status === 'success') {
        message.success(data.message);
        state.showModal = false;
      } else {
        throw new Error(data.message);
      }
    })
    .catch((error) => {
      console.error(error)
      message.error(error.message || t('graph.addFileFailed'));
    })
    .finally(() => state.precessing = false)
};

const loadSampleNodes = () => {
  state.fetching = true
  graphApi.getNodes('neo4j', sampleNodeCount.value)
    .then((data) => {
      graphData.nodes = data.result.nodes
      graphData.edges = data.result.edges
      console.log(graphData)
      setTimeout(() => randerGraph(), 500)
    })
    .catch((error) => {
      console.error(error)
      message.error(error.message || t('graph.loadNodesFailed'));
      if (configStore?.config && !configStore?.config.enable_knowledge_graph) {
        message.error(t('graph.pleaseConfigureGraph'))
      }
    })
    .finally(() => state.fetching = false)
}

const onSearch = () => {
  if (state.searchLoading) {
    message.error(t('graph.pleaseRetryLater'))
    return
  }

  if (graphInfo?.value?.embed_model_name !== cur_embed_model.value) {
    if (!confirm(t('graph.confirmModelMismatch', {
      graphModel: graphInfo?.value?.embed_model_name,
      currentModel: cur_embed_model.value
    }))) {
      return
    }
  }

  if (!state.searchInput) {
    message.error(t('graph.pleaseEnterEntity'))
    return
  }

  state.searchLoading = true
  graphApi.queryNode(state.searchInput)
    .then((data) => {
      if (!data.result || !data.result.nodes || !data.result.edges) {
        throw new Error('返回数据格式不正确');
      }
      graphData.nodes = data.result.nodes
      graphData.edges = data.result.edges
      if (graphData.nodes.length === 0) {
        message.info(t('graph.noRelatedEntity'))
      }
      console.log(data)
      console.log(graphData)
      randerGraph()
    })
    .catch((error) => {
      console.error('查询错误:', error);
      message.error(t('graph.queryError', { error: error.message || '未知错误' }));
    })
    .finally(() => state.searchLoading = false)
};

const randerGraph = () => {

  if (graphInstance) {
    graphInstance.destroy();
  }

  initGraph();
  graphInstance.setData(getGraphData());
  graphInstance.render();
}

const initGraph = () => {
  graphInstance = new Graph({
    container: container.value,
    width: container.value.offsetWidth,
    height: container.value.offsetHeight,
    autoFit: true,
    autoResize: true,
    layout: {
      type: 'd3-force',
      preventOverlap: true,
      collide: {
        radius: 40,
        strength: 0.5, // 碰撞强度
      },
    },
    node: {
      type: 'circle',
      style: {
        labelText: (d) => d.data.label,
        // 使用节点度数来决定大小
        size: (d) => {
          const degree = d.data.degree || 0;
          // 基础大小为15，每个连接增加5的大小，最小为15，最大为50
          return Math.min(15 + degree * 5, 50);
        },
      },
      palette: {
        field: 'label',
        color: 'tableau',
      },
    },
    edge: {
      type: 'line',
      style: {
        labelText: (d) => d.data.label,
        labelBackground: '#fff',
        endArrow: true,
      },
    },
    behaviors: ['drag-element', 'zoom-canvas', 'drag-canvas'],
  });
  window.addEventListener('resize', randerGraph);
}

onMounted(() => {
  loadGraphInfo();
  loadSampleNodes();
});


const handleFileUpload = (event) => {
  console.log(event)
  console.log(fileList.value)
}

const handleDrop = (event) => {
  console.log(event)
  console.log(fileList.value)
}

const graphStatusClass = computed(() => {
  if (state.loadingGraphInfo) return 'loading';
  return graphInfo.value?.status === 'open' ? 'open' : 'closed';
});

const graphStatusText = computed(() => {
  if (state.loadingGraphInfo) return t('graph.loadingStatus');
  return graphInfo.value?.status === 'open' ? t('graph.connectedStatus') : t('graph.closedStatus');
});

const graphDescription = computed(() => {
  const dbName = graphInfo.value?.graph_name || '';
  const entityCount = graphInfo.value?.entity_count || 0;
  const relationCount = graphInfo.value?.relationship_count || 0;
  const modelName = graphInfo.value?.embed_model_name || '未上传文件';
  const unindexed = unindexedCount.value > 0 ? t('graph.unindexedSuffix', { count: unindexedCount.value }) : '';

  return t('graph.graphInfo', {
    dbName,
    entityCount,
    relationCount,
    modelName,
    unindexed
  });
});

// 为未索引节点添加索引
const indexNodes = () => {
  // 判断 embed_model_name 是否相同
  if (!modelMatched.value) {
    message.error(t('graph.vectorModelMismatch', {
      current: cur_embed_model.value,
      graph: graphInfo.value?.embed_model_name
    }))
    return
  }

  if (state.precessing) {
    message.error(t('graph.backendProcessing'))
    return
  }

  state.indexing = true;
  graphApi.indexNodes('neo4j')
    .then(data => {
      message.success(data.message || t('graph.indexAddSuccess'));
      // 刷新图谱信息
      loadGraphInfo();
    })
    .catch(error => {
      console.error(error);
      message.error(error.message || t('graph.indexAddFailed'));
    })
    .finally(() => {
      state.indexing = false;
    });
};

const getAuthHeaders = () => {
  const userStore = useUserStore();
  return userStore.getAuthHeaders();
};

</script>

<style lang="less" scoped>
.graph-container {
  padding: 0;
}

.status-wrapper {
  display: flex;
  align-items: center;
  margin-right: 16px;
  font-size: 14px;
  color: rgba(0, 0, 0, 0.65);
}

.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  display: inline-block;

  &.loading {
    background-color: #faad14;
    animation: pulse 1.5s infinite ease-in-out;
  }

  &.open {
    background-color: #52c41a;
  }

  &.closed {
    background-color: #f5222d;
  }
}

@keyframes pulse {
  0% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  50% {
    transform: scale(1.2);
    opacity: 1;
  }
  100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
}

.actions {
  display: flex;
  justify-content: space-between;
  margin: 20px 0;
  padding: 0 24px;

  .actions-left, .actions-right {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  input {
    width: 100px;
    border-radius: 8px;
    padding: 4px 12px;
    border: 2px solid var(--main-300);
    outline: none;
    height: 42px;

    &:focus {
      border-color: var(--main-color);
    }
  }

  button {
    border-width: 2px;
    height: 40px;
    box-shadow: none;
  }
}


.upload {
  margin-bottom: 20px;

  .upload-dragger {
    margin: 0px;
  }
}

#container {
  background: #F7F7F7;
  margin: 20px 24px;
  border-radius: 16px;
  width: calc(100% - 48px);
  height: calc(100vh - 200px);
  resize: horizontal;
  overflow: hidden;
}

.database-empty {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  flex-direction: column;
  color: var(--gray-900);
}
</style>

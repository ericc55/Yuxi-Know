<template>
  <div class="database-container layout-container" v-if="configStore.config.enable_knowledge_base">
    <HeaderComponent :title="t('database.title')" :loading="state.loading">
      <template #actions>
        <a-button type="primary" @click="newDatabase.open=true">
          {{ t('database.createDatabase') }}
        </a-button>
      </template>
    </HeaderComponent>

    <a-modal :open="newDatabase.open" :title="t('database.createDatabase')" @ok="createDatabase" @cancel="newDatabase.open=false">
      <h3>{{ t('database.databaseName') }}<span style="color: var(--error-color)">*</span></h3>
      <a-input v-model:value="newDatabase.name" :placeholder="t('database.databaseNamePlaceholder')" />
      <h3 style="margin-top: 20px;">{{ t('database.databaseDescription') }}</h3>
      <p style="color: var(--gray-700); font-size: 14px;">{{ t('database.descriptionHint') }}</p>
      <a-textarea
        v-model:value="newDatabase.description"
        :placeholder="t('database.databaseDescriptionPlaceholder')"
        :auto-size="{ minRows: 5, maxRows: 10 }"
      />
      <!-- <h3 style="margin-top: 20px;">向量维度</h3>
      <p>必须与向量模型 {{ configStore.config.embed_model }} 一致</p>
      <a-input v-model:value="newDatabase.dimension" placeholder="向量维度 (e.g. 768, 1024)" /> -->
      <template #footer>
        <a-button key="back" @click="newDatabase.open=false">{{ t('common.cancel') }}</a-button>
        <a-button key="submit" type="primary" :loading="newDatabase.loading" @click="createDatabase">{{ t('common.create') }}</a-button>
      </template>
    </a-modal>
    <div class="databases">
      <div class="new-database dbcard" @click="newDatabase.open=true">
        <div class="top">
          <div class="icon"><BookPlus /></div>
          <div class="info">
            <h3>{{ t('database.createDatabase') }}</h3>
          </div>
        </div>
        <p>{{ t('database.createDatabaseDescription') }}</p>
      </div>
      <div
        v-for="database in databases"
        :key="database.db_id"
        class="database dbcard"
        @click="navigateToDatabase(database.db_id)">
        <div class="top">
          <div class="icon"><ReadFilled /></div>
          <div class="info">
            <h3>{{ database.name }}</h3>
            <p><span>{{ database.files ? Object.keys(database.files).length : 0 }} {{ t('database.files') }}</span></p>
          </div>
        </div>
        <a-tooltip :title="database.description || t('database.noDescription')">
          <p class="description">{{ database.description || t('database.noDescription') }}</p>
        </a-tooltip>
        <div class="tags">
          <a-tag color="blue" v-if="database.embed_model">{{ database.embed_model }}</a-tag>
          <a-tag color="green" v-if="database.dimension">{{ database.dimension }}</a-tag>
        </div>
        <!-- <button @click="deleteDatabase(database.collection_name)">删除</button> -->
      </div>
    </div>
  </div>
  <div class="database-empty" v-else>
    <a-empty>
      <template #description>
        <span>
          {{ t('database.configureKnowledgeBase') }} <router-link to="/setting" style="color: var(--main-color); font-weight: bold;">{{ t('navbar.settings') }}</router-link> {{ t('database.page') }}
        </span>
      </template>
    </a-empty>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, watch, h } from 'vue'
import { useRouter, useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n'
import { message, Button } from 'ant-design-vue'
import { ReadFilled, PlusOutlined, AppstoreFilled, LoadingOutlined } from '@ant-design/icons-vue'
import { BookPlus } from 'lucide-vue-next';
import { useConfigStore } from '@/stores/config';
import { useUserStore } from '@/stores/user';
import HeaderComponent from '@/components/HeaderComponent.vue';
import { knowledgeBaseApi } from '@/apis/admin_api';

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const databases = ref([])
const graph = ref(null)
const graphloading = ref(false)
const userStore = useUserStore()

const indicator = h(LoadingOutlined, {spin: true});
const configStore = useConfigStore()

const state = reactive({
  loading: false,
})

const newDatabase = reactive({
  name: '',
  description: '',
  dimension: '',
  loading: false,
})

const loadDatabases = () => {
  state.loading = true
  // loadGraph()
  knowledgeBaseApi.getDatabases()
    .then(data => {
      console.log(data)
      databases.value = data.databases
      state.loading = false
    })
    .catch(error => {
      console.error('加载数据库列表失败:', error);
      if (error.message.includes('权限')) {
        message.error(t('database.adminPermissionRequired'))
      } else {
        message.error(t('database.loadFailed'))
      }
      state.loading = false
    })
}

const createDatabase = () => {
  newDatabase.loading = true
  console.log(newDatabase)
  if (!newDatabase.name) {
    message.error(t('database.databaseNameRequired'))
    newDatabase.loading = false
    return
  }

  knowledgeBaseApi.createDatabase({
      database_name: newDatabase.name,
      description: newDatabase.description,
      dimension: newDatabase.dimension ? parseInt(newDatabase.dimension) : null,
    })
  .then(data => {
    console.log(data)
    loadDatabases()
    newDatabase.open = false
    newDatabase.name = ''
    newDatabase.description = '',
    newDatabase.dimension = ''
    message.success(t('database.createSuccess'))
  })
  .catch(error => {
    console.error('创建数据库失败:', error)
    message.error(error.message || t('database.createFailed'))
  })
  .finally(() => {
    newDatabase.loading = false
  })
}

const navigateToDatabase = (databaseId) => {
  router.push({ path: `/database/${databaseId}` });
};

const navigateToGraph = () => {
  router.push({ path: `/database/graph` });
};

watch(() => route.path, (newPath, oldPath) => {
  if (newPath === '/database') {
    loadDatabases();
  }
});

onMounted(() => {
  loadDatabases()
})

</script>

<style lang="less" scoped>
.database-actions, .document-actions {
  margin-bottom: 20px;
}
.databases {
  padding: 20px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;

  .new-database {
    background-color: #F0F3F4;
  }
}

.database, .graphbase {
  background-color: white;
  box-shadow: 0px 1px 2px 0px rgba(16,24,40,.06),0px 1px 3px 0px rgba(16,24,40,.1);
  border: 2px solid white;
  transition: box-shadow 0.2s ease-in-out;

  &:hover {
    box-shadow: 0px 4px 6px -2px rgba(16,24,40,.03),0px 12px 16px -4px rgba(16,24,40,.08);
  }
}

.dbcard, .database {
  width: 100%;
  padding: 10px;
  border-radius: 12px;
  height: 160px;
  padding: 20px;
  cursor: pointer;

  .top {
    display: flex;
    align-items: center;
    height: 50px;
    margin-bottom: 10px;

    .icon {
      width: 50px;
      height: 50px;
      font-size: 28px;
      margin-right: 10px;
      display: flex;
      justify-content: center;
      align-items: center;
      background-color: #F5F8FF;
      border-radius: 8px;
      border: 1px solid #E0EAFF;
      color: var(--main-color);
    }

    .info {
      h3, p {
        margin: 0;
        color: black;
      }

      h3 {
        font-size: 16px;
        font-weight: bold;
      }

      p {
        color: var(--gray-900);
        font-size: small;
      }
    }
  }

  .description {
    color: var(--gray-900);
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 1;
    -webkit-box-orient: vertical;
    text-overflow: ellipsis;
    margin-bottom: 10px;
  }
}

// 整个卡片是模糊的
// .graphloading {
//   filter: blur(2px);
// }

.database-empty {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  flex-direction: column;
  color: var(--gray-900);
}

.database-container {
  padding: 0;
}
</style>

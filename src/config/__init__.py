import os
import json
import yaml
from pathlib import Path
from src.utils.logging_config import logger

DEFAULT_MOCK_API = 'this_is_mock_api_key_in_frontend'

class SimpleConfig(dict):

    def __key(self, key):
        return "" if key is None else key  # 目前忘记了这里为什么要 lower 了，只能说配置项最好不要有大写的

    def __str__(self):
        return json.dumps(self)

    def __setattr__(self, key, value):
        self[self.__key(key)] = value

    def __getattr__(self, key):
        return self.get(self.__key(key))

    def __getitem__(self, key):
        return self.get(self.__key(key))

    def __setitem__(self, key, value):
        return super().__setitem__(self.__key(key), value)

    def __dict__(self):
        return {k: v for k, v in self.items()}

    def update(self, other):
        for key, value in other.items():
            self[key] = value


class Config(SimpleConfig):

    def __init__(self):
        super().__init__()
        self._config_items = {}
        self.save_dir = "saves"
        self.filename = str(Path("saves/config/base.yaml"))
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)

        self._update_models_from_file()

        ### >>> 默认配置
        # 功能选项
        self.add_item("enable_reranker", default=False, des="是否开启重排序")
        self.add_item("enable_knowledge_base", default=False, des="是否开启知识库")
        self.add_item("enable_knowledge_graph", default=False, des="是否开启知识图谱")
        self.add_item("enable_web_search", default=False, des="是否开启网页搜索（注：现阶段会根据 TAVILY_API_KEY 自动开启，无法手动配置，将会在下个版本移除此配置项）")  # noqa: E501
        # 默认智能体配置
        self.add_item("default_agent_id", default="", des="默认智能体ID")
        # 模型配置
        ## 注意这里是模型名，而不是具体的模型路径，默认使用 HuggingFace 的路径
        ## 如果需要自定义本地模型路径，则在 src/.env 中配置 MODEL_DIR
        self.add_item("model_provider", default="openai", des="模型提供商", choices=list(self.model_names.keys()))
        self.add_item("model_name", default="gpt-3.5-turbo", des="模型名称")

        self.add_item("embed_model", default="siliconflow/BAAI/bge-m3", des="Embedding 模型", choices=list(self.embed_model_names.keys()))
        self.add_item("reranker", default="siliconflow/BAAI/bge-reranker-v2-m3", des="Re-Ranker 模型", choices=list(self.reranker_names.keys()))  # noqa: E501
        self.add_item("model_local_paths", default={}, des="本地模型路径")
        self.add_item("use_rewrite_query", default="on", des="重写查询", choices=["off", "on", "hyde"])
        self.add_item("device", default="cuda", des="运行本地模型的设备", choices=["cpu", "cuda"])
        ### <<< 默认配置结束

        self.load()
        self.handle_self()

    def add_item(self, key, default, des=None, choices=None):
        self.__setattr__(key, default)
        self._config_items[key] = {
            "default": default,
            "des": des,
            "choices": choices
        }

    def __dict__(self):
        blocklist = [
            "_config_items",
            "model_names",
            "model_provider_status",
            "embed_model_names",
            "reranker_names",
        ]
        return {k: v for k, v in self.items() if k not in blocklist}

    def _update_models_from_file(self):
        """
        从 models.yaml 和 models.private.yml 中更新 MODEL_NAMES
        """

        with open(Path("src/static/models.yaml"), encoding='utf-8') as f:
            _models = yaml.safe_load(f)

        # 尝试打开一个 models.private.yml 文件，用来覆盖 models.yaml 中的配置
        try:
            with open(Path("src/static/models.private.yml"), encoding='utf-8') as f:
                _models_private = yaml.safe_load(f)
        except FileNotFoundError:
            _models_private = {}

        # 修改为按照子元素合并
        # _models = {**_models, **_models_private}

        self.model_names = {**_models["MODEL_NAMES"], **_models_private.get("MODEL_NAMES", {})}
        self.embed_model_names = {**_models["EMBED_MODEL_INFO"], **_models_private.get("EMBED_MODEL_INFO", {})}
        self.reranker_names = {**_models["RERANKER_LIST"], **_models_private.get("RERANKER_LIST", {})}

    def _save_models_to_file(self):
        _models = {
            "MODEL_NAMES": self.model_names,
            "EMBED_MODEL_INFO": self.embed_model_names,
            "RERANKER_LIST": self.reranker_names,
        }
        with open(Path("src/static/models.private.yml"), 'w', encoding='utf-8') as f:
            yaml.dump(_models, f, indent=2, allow_unicode=True)

    def handle_self(self):
        """
        处理配置
        """
        model_provider_info = self.model_names.get(self.model_provider, {})
        self.model_dir = os.environ.get("MODEL_DIR", "")

        if self.model_dir:
            if os.path.exists(self.model_dir):
                logger.debug(f"The model directory （{self.model_dir}） contains the following folders: {os.listdir(self.model_dir)}")
            else:
                logger.warning(f"Warning: The model directory （{self.model_dir}） does not exist. If not configured, please ignore it. If configured, please check if the configuration is correct;"
                               "For example, the mapping in the docker-compose file")


        # 检查模型提供商是否存在
        if self.model_provider != "custom":
            if "models" not in model_provider_info:
                logger.error(f"Model provider {self.model_provider} is missing 'models' configuration. Available providers: {list(self.model_names.keys())}")
                # Fallback to first available provider
                available_providers = list(self.model_names.keys())
                if available_providers:
                    self.model_provider = available_providers[0]
                    model_provider_info = self.model_names.get(self.model_provider, {})
                    logger.warning(f"Switched to provider: {self.model_provider}")
                else:
                    logger.error("No model providers available in configuration")
                    return

            if self.model_name not in model_provider_info.get("models", []):
                logger.warning(f"Model name {self.model_name} not in {self.model_provider}, using default model name")
                self.model_name = model_provider_info.get("default", "gpt-3.5-turbo")

            default_model_name = model_provider_info.get("default", "gpt-3.5-turbo")
            self.model_name = self.get("model_name") or default_model_name
        else:
            self.model_name = self.get("model_name")
            if self.model_name not in [item["custom_id"] for item in self.get("custom_models", [])]:
                logger.warning(f"Model name {self.model_name} not in custom models, using default model name")
                if self.get("custom_models", []):
                    self.model_name = self.get("custom_models", [])[0]["custom_id"]
                else:
                    self.model_name = self._config_items["model_name"]["default"]
                    self.model_provider = self._config_items["model_provider"]["default"]
                    logger.error(f"No custom models found, using default model {self.model_name} from {self.model_provider}")

        # 检查模型提供商的环境变量
        conds = {}
        self.model_provider_status = {}
        for provider in self.model_names:
            conds[provider] = self.model_names[provider]["env"]
            conds_bool = [bool(os.getenv(_k)) for _k in conds[provider]]
            self.model_provider_status[provider] = all(conds_bool)

        # 检查web_search的环境变量
        # if self.enable_web_search and not os.getenv("TAVILY_API_KEY"):
        #     logger.warning("TAVILY_API_KEY not set, web search will be disabled")
        #     self.enable_web_search = False

        # 2025.04.08 修改为不手动配置，只要配置了TAVILY_API_KEY，就默认开启web_search
        if os.getenv("TAVILY_API_KEY"):
            self.enable_web_search = True

        self.valuable_model_provider = [k for k, v in self.model_provider_status.items() if v]
        
        if len(self.valuable_model_provider) == 0:
            logger.warning(f"No model providers with valid API keys found. API_KEY_LIST: {conds}")
            logger.warning("The system will start but model functionality will be limited.")
            logger.warning("Please configure at least one API key in src/.env file")
            logger.info(f"To enable model providers, set one of these environment variables: {[env for provider_envs in conds.values() for env in provider_envs]}")
        else:
            logger.info(f"Available model providers: {self.valuable_model_provider}")

    def load(self):
        """根据传入的文件覆盖掉默认配置"""
        logger.info(f"Loading config from {self.filename}")
        if self.filename is not None and os.path.exists(self.filename):

            if self.filename.endswith(".json"):
                with open(self.filename) as f:
                    content = f.read()
                    if content:
                        local_config = json.loads(content)
                        self.update(local_config)
                    else:
                        print(f"{self.filename} is empty.")

            elif self.filename.endswith(".yaml"):
                with open(self.filename) as f:
                    content = f.read()
                    if content:
                        local_config = yaml.safe_load(content)
                        self.update(local_config)
                    else:
                        print(f"{self.filename} is empty.")
            else:
                logger.warning(f"Unknown config file type {self.filename}")

    def save(self):
        logger.info(f"Saving config to {self.filename}")
        if self.filename is None:
            logger.warning("Config file is not specified, save to default config/base.yaml")
            self.filename = os.path.join(self.save_dir, "config", "base.yaml")
            os.makedirs(os.path.dirname(self.filename), exist_ok=True)

        if self.filename.endswith(".json"):
            with open(self.filename, 'w+') as f:
                json.dump(self.__dict__(), f, indent=4, ensure_ascii=False)
        elif self.filename.endswith(".yaml"):
            with open(self.filename, 'w+') as f:
                yaml.dump(self.__dict__(), f, indent=2, allow_unicode=True)
        else:
            logger.warning(f"Unknown config file type {self.filename}, save as json")
            with open(self.filename, 'w+') as f:
                json.dump(self, f, indent=4)

        logger.info(f"Config file {self.filename} saved")

    def dump_config(self):
        return json.loads(str(self))

    def compare_custom_models(self, value):
        """
        比较 custom_models 中的 api_key，如果输入的 api_key 与当前的 api_key 相同，则不修改
        如果输入的 api_key 为 DEFAULT_MOCK_API，则使用当前的 api_key
        """
        current_models_dict = {model["custom_id"]: model.get("api_key") for model in self.get("custom_models", [])}

        for i, model in enumerate(value):
            input_custom_id = model.get("custom_id")
            input_api_key = model.get("api_key")

            if input_custom_id in current_models_dict:
                current_api_key = current_models_dict[input_custom_id]
                if input_api_key == DEFAULT_MOCK_API or input_api_key == current_api_key:
                    value[i]["api_key"] = current_api_key

        return value

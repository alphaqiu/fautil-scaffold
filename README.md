# 项目名称

## 简介

此项目是一个使用 FastAPI、SQLAlchemy 和 Pydantic 开发的应用程序，旨在提供高效的 Web 服务。项目采用了依赖注入、面向接口编程等现代软件工程实践。

## 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```

2. **安装 Poetry**
   - macOS, Linux:
     ```bash
     curl -sSL https://install.python-poetry.org | python3 -
     ```
   - Windows:
     ```bash
     (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
     echo 'if (-not (Get-Command poetry -ErrorAction Ignore)) { $env:Path += ";C:\Users\xxx\AppData\Roaming\Python\Scripts" }' | Out-File -Append $PROFILE
     ```

3. **安装项目依赖**
   ```bash
   poetry install --no-root
   ```

4. **激活虚拟环境**
   - macOS, Linux:
     ```bash
     poetry env activate
     ```
   - Windows:
     ```bash
     Invoke-Expression (poetry env activate)
     ```

## 配置管理

本项目采用灵活的配置管理策略，支持从多种来源加载配置，并按照优先级应用配置。

### 配置来源与优先级

配置按以下优先级从高到低加载：

1. **环境变量**（最高优先级）
2. **.env 文件**中的设置
3. **配置文件**（YAML/JSON）中的设置
4. **默认值**（最低优先级）

### 配置文件

支持两种格式的配置文件：YAML（优先）和 JSON。配置文件查找顺序如下：

1. 明确指定的路径
2. 当前工作目录（`config.yaml` 或 `config.json`）
3. 用户主目录下的 `.fautil` 目录
4. Windows 系统：`%APPDATA%/.fautil` 目录
5. Linux 系统：`/etc/fautil` 目录

在 `examples` 目录中提供了完整的配置示例：
- [YAML配置示例](examples/config.yaml)
- [JSON配置示例](examples/config.json)
- [环境变量示例](examples/.env.example)

#### 示例配置文件（YAML）

```yaml
app:
  title: "我的应用"
  description: "应用描述"
  version: "1.0.0"
  debug: true
  port: 8000
  cors_origins:
    - "http://localhost:3000"
    - "https://example.com"
  jwt_secret: "your-jwt-secret"

db:
  url: "postgresql://user:pass@localhost:5432/dbname"
  echo: false
  pool_size: 5
  max_overflow: 10

log:
  level: "INFO"
  file_path: "/tmp/app.log"
  rotation: "20 MB"
```

#### 示例配置文件（JSON）

```json
{
  "app": {
    "title": "我的应用",
    "description": "应用描述",
    "version": "1.0.0",
    "debug": true,
    "port": 8000,
    "cors_origins": ["http://localhost:3000", "https://example.com"],
    "jwt_secret": "your-jwt-secret"
  },
  "db": {
    "url": "postgresql://user:pass@localhost:5432/dbname",
    "echo": false,
    "pool_size": 5
  },
  "log": {
    "level": "INFO",
    "file_path": "/tmp/app.log"
  }
}
```

### 环境变量

您可以使用环境变量覆盖任何配置项。环境变量命名规则如下：

#### 环境变量命名规则

1. **基本规则**：
   - 所有环境变量均以 `FAUTIL_` 前缀开头
   - 环境变量名称全部大写，下划线分隔单词
   - 配置属性通常采用小写下划线命名法

2. **顶级配置项映射**：
   - 格式：`FAUTIL_<配置项>_<属性名>`
   - 示例：`FAUTIL_APP_TITLE` 映射到 `settings.app.title`

3. **嵌套配置项映射**：
   - 格式：`FAUTIL_<配置项>__<属性名>`（注意是双下划线）
   - 示例：`FAUTIL_DB__URL` 映射到 `settings.db.url`

#### 类型转换规则

环境变量值会根据目标配置项的类型自动转换：

- **布尔值**：字符串 "true", "1", "yes", "y", "t" (不区分大小写) 均被转换为 `True`
- **整数**：自动转换为 `int` 类型（如 `"8000"` → `8000`）
- **浮点数**：自动转换为 `float` 类型
- **列表**：逗号分隔的字符串自动转换为列表（如 `"item1,item2,item3"` → `["item1", "item2", "item3"]`）

#### 环境变量示例

```bash
# 应用配置
FAUTIL_APP_TITLE="生产环境应用"
FAUTIL_APP_DEBUG=false
FAUTIL_APP_PORT=80
FAUTIL_APP_CORS_ORIGINS=https://example.com,https://api.example.com

# 数据库配置
FAUTIL_DB__URL=postgresql://prod_user:prod_pass@db.example.com:5432/prod_db
FAUTIL_DB__POOL_SIZE=20

# 日志配置
FAUTIL_LOG_LEVEL=WARNING
FAUTIL_LOG_FILE_PATH=/var/log/app.log
```

### .env 文件

您也可以使用 `.env` 文件设置环境变量。`.env` 文件查找顺序与配置文件相同。

示例 `.env` 文件：

```
FAUTIL_APP_TITLE=开发环境应用
FAUTIL_APP_DEBUG=true
FAUTIL_APP_PORT=8000
FAUTIL_DB__URL=postgresql://dev_user:dev_pass@localhost:5432/dev_db
FAUTIL_LOG_LEVEL=DEBUG
```

### 在代码中使用配置

```python
from src.core.config import Settings, load_settings

# 加载配置
settings = load_settings(Settings)

# 使用配置
app_title = settings.app.title
db_url = settings.db.url if settings.db else None
```

### 扩展配置

要扩展配置，只需在 `Settings` 类中添加新的字段或创建新的配置类：

```python
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

# 创建新的配置类
class CustomConfig(BaseModel):
    feature_flag: bool = False
    api_key: str = "default-key"
    timeout: int = 30

# 扩展Settings类
class ExtendedSettings(Settings):
    custom: CustomConfig = Field(default_factory=CustomConfig)
```

然后，您可以通过环境变量设置这些新配置：

```
FAUTIL_CUSTOM__FEATURE_FLAG=true
FAUTIL_CUSTOM__API_KEY=your-api-key
FAUTIL_CUSTOM__TIMEOUT=60
```

## 使用说明

- **运行应用程序**
  ```bash
  uvicorn src.wsgi:app --reload
  ```

- **运行测试**
  ```bash
  pytest
  ```

- **生成测试覆盖率报告**
  ```bash
  pytest --cov=src tests/
  ```

## 贡献指南

欢迎贡献者！请遵循以下步骤进行贡献：

1. Fork 此仓库。
2. 创建一个新的分支：
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. 提交您的更改：
   ```bash
   git commit -m 'Add some feature'
   ```
4. 推送到分支：
   ```bash
   git push origin feature/your-feature-name
   ```
5. 提交 Pull Request。

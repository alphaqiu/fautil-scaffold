# 配置示例

本目录包含了项目配置的示例文件，帮助您快速开始配置应用。

## 文件说明

- **config.yaml**: YAML格式的完整配置示例，包含所有可配置选项及其说明
- **config.json**: JSON格式的配置示例，功能上与YAML示例等效
- **.env.example**: 环境变量配置示例，展示了环境变量的命名规则和使用方法

## 使用方法

### 配置文件

1. 复制配置文件到支持的位置：
   ```bash
   # 复制到项目根目录（最常用的方式）
   cp examples/config.yaml ./config.yaml

   # 或者复制到用户主目录下的.fautil目录
   mkdir -p ~/.fautil
   cp examples/config.yaml ~/.fautil/config.yaml
   ```

2. 根据您的需要修改配置文件中的参数

### 环境变量

1. 复制环境变量示例文件：
   ```bash
   cp examples/.env.example ./.env
   ```

2. 编辑.env文件，根据需要调整设置

3. 也可以直接在系统中设置环境变量（例如在Docker容器中或生产环境）：
   ```bash
   export FAUTIL_APP_TITLE="我的应用"
   export FAUTIL_APP_PORT=8000
   export FAUTIL_DB__URL="postgresql://user:pass@db:5432/mydb"
   ```

## 配置优先级

请记住配置的优先级顺序（从高到低）：
1. 系统环境变量
2. .env文件中的设置
3. 配置文件中的设置
4. 代码中的默认值

这意味着您可以使用环境变量覆盖任何配置文件中的设置，从而支持不同环境（开发、测试、生产）的配置管理。

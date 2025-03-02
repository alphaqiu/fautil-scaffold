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

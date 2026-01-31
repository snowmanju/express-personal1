# 快递查询网站 (Express Tracking Website)

一个基于FastAPI的快递查询和理货单管理系统。

## 功能特性

- 🔍 **智能快递查询**: 支持快递单号查询，自动判断集包单号
- 📋 **理货单管理**: 支持CSV/Excel文件批量上传和管理
- 🔐 **后台管理**: 管理员登录和权限控制
- 🚀 **快递100集成**: 集成快递100 API获取实时物流信息
- 📱 **响应式设计**: 支持多设备访问

## 技术栈

- **后端**: FastAPI + SQLAlchemy + Alembic
- **数据库**: MySQL
- **认证**: JWT
- **文件处理**: pandas + openpyxl
- **API集成**: requests

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 到 `.env` 并修改配置：

```bash
cp .env.example .env
```

### 3. 初始化数据库

```bash
# 初始化Alembic
alembic init alembic

# 创建迁移
alembic revision --autogenerate -m "Initial migration"

# 执行迁移
alembic upgrade head
```

### 4. 启动应用

```bash
python run.py
```

应用将在 http://localhost:8000 启动

## API文档

启动应用后，访问以下地址查看API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 项目结构

```
├── app/                    # 应用程序主目录
│   ├── api/               # API路由
│   │   └── v1/           # API版本1
│   ├── core/             # 核心配置
│   ├── models/           # 数据库模型
│   ├── schemas/          # Pydantic模式
│   └── services/         # 业务逻辑服务
├── alembic/              # 数据库迁移
├── static/               # 静态文件
├── requirements.txt      # Python依赖
└── run.py               # 启动脚本
```

## 开发指南

### 添加新的API端点

1. 在 `app/api/v1/` 下创建新的路由文件
2. 在 `app/api/v1/api.py` 中注册路由
3. 在 `app/schemas/` 中定义请求/响应模式
4. 在 `app/services/` 中实现业务逻辑

### 数据库迁移

```bash
# 创建新迁移
alembic revision --autogenerate -m "描述变更"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

## 许可证

MIT License
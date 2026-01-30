# SF Express 快递查询系统

## 项目简介

智能物流追踪系统，提供快递单号查询和理货单管理功能。

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置数据库
复制 `.env.example` 为 `.env`，配置数据库连接：
```
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/express_tracking
```

### 3. 初始化数据库
```bash
python tests/setup_database.py
python tests/create_admin_user.py
```

### 4. 启动服务
```bash
python run.py
```

访问：http://localhost:8000

## 功能特性

- ✅ 快递单号智能查询
- ✅ 理货单批量上传管理
- ✅ 管理后台系统
- ✅ 数据统计分析
- ✅ 科技风格UI

## 目录结构

```
sf-express/
├── app/                    # 应用核心代码
│   ├── api/               # API路由
│   ├── core/              # 核心配置
│   ├── models/            # 数据模型
│   ├── schemas/           # 数据模式
│   └── services/          # 业务逻辑
├── static/                # 静态文件
│   ├── admin/            # 管理后台
│   ├── customer/         # 客户端
│   └── templates/        # 模板文件
├── tests/                 # 测试文件
├── tools/                 # 工具脚本
├── docs/                  # 文档
├── uploads/               # 上传文件
├── .env                   # 环境配置
├── requirements.txt       # 依赖包
└── run.py                # 启动文件
```

## 文档

- [快速启动指南](docs/快速启动指南.md)
- [平台测试指南](docs/平台测试指南.md)
- [理货单模板说明](docs/理货单模板说明_最终版.md)

## 技术栈

- **后端**: FastAPI + Python 3.8+
- **数据库**: MySQL 8.0+
- **前端**: HTML5 + CSS3 + JavaScript
- **部署**: Docker + Docker Compose

## 默认账号

- 管理员: admin / admin123

## 许可证

MIT License

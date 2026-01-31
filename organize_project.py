"""
整理项目文件到 sf-express 文件夹
"""
import os
import shutil
from pathlib import Path

def organize_project():
    """整理项目文件"""
    
    print("=" * 60)
    print("开始整理项目文件到 sf-express 文件夹")
    print("=" * 60)
    
    # 创建目标文件夹
    target_dir = Path("sf-express")
    target_dir.mkdir(exist_ok=True)
    
    # 定义需要保留的核心文件和文件夹
    core_items = {
        # 核心应用文件夹
        'app': 'app',
        'static': 'static',
        'alembic': 'alembic',
        'scripts': 'scripts',
        'uploads': 'uploads',
        
        # 核心配置文件
        '.env': '.env',
        '.env.example': '.env.example',
        'alembic.ini': 'alembic.ini',
        'requirements.txt': 'requirements.txt',
        'run.py': 'run.py',
        'Dockerfile': 'Dockerfile',
        'docker-compose.yml': 'docker-compose.yml',
        
        # 核心文档
        'README.md': 'README.md',
        'DEPLOYMENT.md': 'DEPLOYMENT.md',
    }
    
    # 需要移动的文档文件（整理到 docs 文件夹）
    docs_files = [
        '快速启动指南.md',
        '平台测试指南.md',
        '理货单模板说明_最终版.md',
    ]
    
    # 需要移动的测试文件（整理到 tests 文件夹）
    test_files = [
        'test_template_upload.py',
        'setup_database.py',
        'create_admin_user.py',
        'create_test_data.py',
        'create_excel_template.py',
    ]
    
    # 需要移动的工具脚本（整理到 tools 文件夹）
    tool_files = [
        'check_mysql_service.py',
        'start_mysql.py',
        'quick_diagnose.py',
        'diagnose_server.py',
    ]
    
    print("\n1. 复制核心文件和文件夹...")
    for source, dest in core_items.items():
        source_path = Path(source)
        dest_path = target_dir / dest
        
        if source_path.exists():
            if source_path.is_dir():
                if dest_path.exists():
                    shutil.rmtree(dest_path)
                shutil.copytree(source_path, dest_path)
                print(f"   ✓ 复制文件夹: {source} -> {dest_path}")
            else:
                shutil.copy2(source_path, dest_path)
                print(f"   ✓ 复制文件: {source} -> {dest_path}")
        else:
            print(f"   ! 跳过不存在的: {source}")
    
    print("\n2. 整理文档文件到 docs 文件夹...")
    docs_dir = target_dir / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    for doc_file in docs_files:
        source_path = Path(doc_file)
        if source_path.exists():
            dest_path = docs_dir / doc_file
            shutil.copy2(source_path, dest_path)
            print(f"   ✓ 复制文档: {doc_file}")
    
    print("\n3. 整理测试文件到 tests 文件夹...")
    tests_dir = target_dir / "tests"
    tests_dir.mkdir(exist_ok=True)
    
    for test_file in test_files:
        source_path = Path(test_file)
        if source_path.exists():
            dest_path = tests_dir / test_file
            shutil.copy2(source_path, dest_path)
            print(f"   ✓ 复制测试: {test_file}")
    
    print("\n4. 整理工具脚本到 tools 文件夹...")
    tools_dir = target_dir / "tools"
    tools_dir.mkdir(exist_ok=True)
    
    for tool_file in tool_files:
        source_path = Path(tool_file)
        if source_path.exists():
            dest_path = tools_dir / tool_file
            shutil.copy2(source_path, dest_path)
            print(f"   ✓ 复制工具: {tool_file}")
    
    print("\n5. 创建项目说明文件...")
    
    # 创建主 README
    readme_content = """# SF Express 快递查询系统

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
"""
    
    with open(target_dir / "README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    print("   ✓ 创建 README.md")
    
    # 创建 .gitignore
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Environment
.env
.env.local
.env.production

# Database
*.db
*.sqlite3

# Logs
logs/
*.log

# Uploads
uploads/*
!uploads/.gitkeep

# OS
.DS_Store
Thumbs.db

# Testing
.pytest_cache/
.hypothesis/
.coverage
htmlcov/

# Docker
docker/mysql/data/
"""
    
    with open(target_dir / ".gitignore", "w", encoding="utf-8") as f:
        f.write(gitignore_content)
    print("   ✓ 创建 .gitignore")
    
    print("\n" + "=" * 60)
    print("项目整理完成！")
    print("=" * 60)
    print(f"\n新项目位置: {target_dir.absolute()}")
    print("\n下一步:")
    print("1. cd sf-express")
    print("2. 复制 .env 文件并配置")
    print("3. python tests/setup_database.py")
    print("4. python run.py")
    print()

if __name__ == "__main__":
    try:
        organize_project()
    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()

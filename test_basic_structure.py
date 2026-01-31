#!/usr/bin/env python3
"""
基础项目结构测试
Basic Project Structure Test
"""

import os
import sys

def test_project_structure():
    """测试项目结构是否正确创建"""
    
    # 检查主要目录
    required_dirs = [
        "app",
        "app/api",
        "app/api/v1", 
        "app/core",
        "app/models",
        "app/schemas",
        "app/services",
        "static",
        "uploads",
        "alembic"
    ]
    
    # 检查主要文件
    required_files = [
        "requirements.txt",
        "run.py",
        "README.md",
        ".env.example",
        "alembic.ini",
        "app/__init__.py",
        "app/main.py",
        "app/core/__init__.py",
        "app/core/config.py",
        "app/core/database.py",
        "app/api/__init__.py",
        "app/api/v1/__init__.py",
        "app/api/v1/api.py",
        "static/index.html"
    ]
    
    print("🔍 检查项目结构...")
    
    # 检查目录
    missing_dirs = []
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            missing_dirs.append(dir_path)
        else:
            print(f"✅ 目录存在: {dir_path}")
    
    # 检查文件
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"✅ 文件存在: {file_path}")
    
    # 报告结果
    if missing_dirs:
        print(f"\n❌ 缺少目录: {missing_dirs}")
        return False
    
    if missing_files:
        print(f"\n❌ 缺少文件: {missing_files}")
        return False
    
    print("\n🎉 项目结构检查通过!")
    return True

def test_basic_imports():
    """测试基础模块导入"""
    print("\n🔍 测试基础模块导入...")
    
    try:
        # 测试基础Python模块
        import os
        import sys
        print("✅ 基础Python模块导入成功")
        
        # 测试项目模块结构
        sys.path.insert(0, '.')
        
        # 测试app包导入
        import app
        print("✅ app包导入成功")
        
        # 测试核心模块导入
        import app.core
        print("✅ app.core包导入成功")
        
        # 测试API模块导入
        import app.api
        import app.api.v1
        print("✅ app.api包导入成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_configuration():
    """测试配置文件基础结构"""
    print("\n🔍 测试配置文件...")
    
    try:
        # 读取配置文件内容
        with open('app/core/config.py', 'r', encoding='utf-8') as f:
            config_content = f.read()
        
        # 检查关键配置项
        required_configs = [
            'PROJECT_NAME',
            'DATABASE_URL',
            'KUAIDI100_KEY',
            'KUAIDI100_CUSTOMER',
            'SECRET_KEY',
            'Settings'
        ]
        
        for config in required_configs:
            if config in config_content:
                print(f"✅ 配置项存在: {config}")
            else:
                print(f"❌ 配置项缺失: {config}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ 配置文件测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("快递查询网站 - 项目初始化验证")
    print("Express Tracking Website - Project Initialization Test")
    print("=" * 50)
    
    tests = [
        ("项目结构检查", test_project_structure),
        ("基础模块导入", test_basic_imports),
        ("配置文件检查", test_configuration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 执行测试: {test_name}")
        if test_func():
            passed += 1
            print(f"✅ {test_name} - 通过")
        else:
            print(f"❌ {test_name} - 失败")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过! 项目初始化成功!")
        print("\n📝 下一步:")
        print("1. 安装依赖: pip install -r requirements.txt")
        print("2. 配置数据库连接")
        print("3. 运行应用: python run.py")
        return True
    else:
        print("❌ 部分测试失败，请检查项目结构")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
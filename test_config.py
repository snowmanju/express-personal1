"""
测试配置 - 使用SQLite数据库
"""

import os
import tempfile

# 创建临时SQLite数据库
temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
temp_db.close()

# 设置环境变量使用SQLite
os.environ['DATABASE_URL'] = f'sqlite:///{temp_db.name}'

print(f"Using SQLite database: {temp_db.name}")
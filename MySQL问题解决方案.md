# 🚨 MySQL服务未找到 - 解决方案

## 问题诊断结果

✗ **MySQL服务未找到或未启动**

错误信息：
```
Can't connect to MySQL server on 'localhost' 
由于目标计算机积极拒绝，无法连接
```

---

## 🔍 可能的情况

### 情况1: MySQL未安装
MySQL可能根本没有安装在你的系统上

### 情况2: MySQL已安装但未作为服务运行
MySQL可能是手动安装的，没有注册为Windows服务

### 情况3: MySQL服务名称不同
MySQL服务可能使用了不同的名称（如MySQL80, MySQL57等）

---

## 💡 解决方案

### 方案1: 检查MySQL是否已安装 ⭐ 先做这个

**步骤1: 检查MySQL命令是否可用**
```bash
mysql --version
```

**如果显示版本号**（如 `mysql Ver 8.0.xx`）：
- ✓ MySQL已安装
- 继续方案2或方案3

**如果显示错误**（`'mysql' 不是内部或外部命令`）：
- ✗ MySQL未安装
- 继续方案4（安装MySQL）

---

### 方案2: 手动查找并启动MySQL服务 ⭐ 推荐

**步骤1: 打开服务管理器**
1. 按 `Win + R`
2. 输入 `services.msc`
3. 按回车

**步骤2: 查找MySQL服务**
在服务列表中查找包含以下关键词的服务：
- MySQL
- MySQL80
- MySQL57
- MariaDB（如果安装的是MariaDB）

**步骤3: 启动服务**
1. 找到MySQL服务后，右键点击
2. 选择"启动"
3. 等待服务启动完成

**步骤4: 设置自动启动（可选）**
1. 右键点击MySQL服务
2. 选择"属性"
3. 将"启动类型"改为"自动"
4. 点击"确定"

---

### 方案3: 使用命令行查找MySQL服务

**在PowerShell中运行：**
```powershell
Get-Service | Where-Object {$_.Name -match "mysql|maria"} | Format-Table Name, DisplayName, Status
```

**或在CMD中运行：**
```cmd
sc query state= all | findstr /i "mysql"
```

**找到服务名后，启动它：**
```cmd
net start <服务名>
```

例如：
```cmd
net start MySQL80
```

---

### 方案4: 安装MySQL（如果未安装）

#### 选项A: 使用MySQL Installer（推荐）

**1. 下载MySQL Installer**
- 访问: https://dev.mysql.com/downloads/installer/
- 下载 `mysql-installer-community-x.x.xx.msi`

**2. 运行安装程序**
- 选择 "Developer Default" 或 "Server only"
- 按照向导完成安装

**3. 配置MySQL**
- 设置root密码（记住这个密码！）
- 选择"Configure MySQL Server as a Windows Service"
- 服务名称使用默认的 "MySQL80" 或自定义

**4. 完成安装后**
- MySQL服务会自动启动
- 更新 `.env` 文件中的密码

#### 选项B: 使用便携版MySQL

**1. 下载MySQL ZIP包**
- 访问: https://dev.mysql.com/downloads/mysql/
- 下载 Windows ZIP Archive

**2. 解压并配置**
```cmd
# 解压到 C:\mysql
# 创建配置文件 C:\mysql\my.ini
```

**3. 初始化MySQL**
```cmd
cd C:\mysql\bin
mysqld --initialize-insecure
```

**4. 安装为服务**
```cmd
mysqld --install MySQL --defaults-file=C:\mysql\my.ini
```

**5. 启动服务**
```cmd
net start MySQL
```

---

### 方案5: 使用替代方案（临时解决）

如果暂时无法安装MySQL，可以使用SQLite作为临时数据库：

**步骤1: 修改数据库配置**

编辑 `.env` 文件，将：
```
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/express_tracking
```

改为：
```
DATABASE_URL=sqlite:///./express_tracking.db
```

**步骤2: 修改数据库引擎导入**

编辑 `app/core/database.py`，确保支持SQLite

**步骤3: 运行迁移**
```bash
alembic upgrade head
```

**注意**: SQLite是临时方案，生产环境建议使用MySQL

---

## 🎯 快速检查清单

执行以下命令来诊断：

```bash
# 1. 检查MySQL是否安装
mysql --version

# 2. 检查MySQL服务（PowerShell）
Get-Service | Where-Object {$_.Name -match "mysql"}

# 3. 尝试连接MySQL
mysql -u root -p

# 4. 检查端口3306是否开放
netstat -ano | findstr :3306
```

---

## 📋 根据检查结果采取行动

### 如果 `mysql --version` 有输出：
✓ MySQL已安装
→ 使用方案2或方案3启动服务

### 如果 `mysql --version` 无输出：
✗ MySQL未安装
→ 使用方案4安装MySQL

### 如果找到MySQL服务但无法启动：
⚠ 服务配置问题
→ 检查MySQL错误日志
→ 重新安装MySQL

### 如果急需测试系统：
⏰ 时间紧迫
→ 使用方案5（SQLite临时方案）

---

## 🔧 安装MySQL后的配置步骤

**1. 设置root密码**
```bash
mysql -u root
ALTER USER 'root'@'localhost' IDENTIFIED BY '你的密码';
FLUSH PRIVILEGES;
exit;
```

**2. 创建数据库**
```bash
mysql -u root -p
CREATE DATABASE express_tracking CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
exit;
```

**3. 更新.env文件**
```
DATABASE_URL=mysql+pymysql://root:你的密码@localhost:3306/express_tracking
```

**4. 运行数据库迁移**
```bash
alembic upgrade head
```

**5. 创建管理员用户**
```bash
python create_admin_user.py
```

**6. 启动服务器**
```bash
python run.py
```

---

## 💊 常见问题

### Q: 我不知道MySQL root密码
**A**: 重置密码：
1. 停止MySQL服务
2. 以安全模式启动MySQL
3. 重置密码
4. 重启MySQL服务

### Q: MySQL服务启动后立即停止
**A**: 检查：
1. 端口3306是否被占用
2. MySQL错误日志（通常在MySQL安装目录的data文件夹）
3. my.ini配置文件是否正确

### Q: 我想使用其他数据库
**A**: 支持的数据库：
- MySQL（推荐）
- MariaDB（MySQL的分支）
- SQLite（开发/测试用）
- PostgreSQL（需要修改配置）

---

## 📞 下一步

完成MySQL安装/启动后：

1. **验证MySQL运行**
   ```bash
   mysql -u root -p
   ```

2. **重新运行诊断**
   ```bash
   python capture_error.py
   ```

3. **如果诊断通过，启动服务器**
   ```bash
   python run.py
   ```

4. **访问管理后台**
   http://localhost:8000/admin/login.html

---

## 🎉 成功标志

当一切正常时，你应该看到：

```
[3/6] 测试数据库连接...
✓ 数据库连接成功: express_tracking

[4/6] 导入应用核心模块...
✓ 数据库模块导入成功
✓ 认证模块导入成功

[5/6] 导入FastAPI应用...
✓ FastAPI应用导入成功
✓ 注册了 XX 个路由

[6/6] 检查端口...
✓ 端口8000可用

正在启动服务器...
INFO:     Uvicorn running on http://0.0.0.0:8000
```

祝你顺利！🚀

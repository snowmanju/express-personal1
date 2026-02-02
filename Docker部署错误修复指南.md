# Docker部署错误修复指南

## 🚨 问题描述

运行 `docker-compose --env-file .env.production ps` 后出现两个错误：

1. **Python模块缺失**: `ModuleNotFoundError: No module named 'psutil'`
2. **SSL证书缺失**: `nginx: [emerg] cannot load certificate "/etc/nginx/ssl/cert.pem"`

---

## ⚡ 快速修复（按顺序执行）

### 修复1: 添加缺失的Python模块

#### 步骤1: 更新 requirements.txt

```bash
# 进入项目目录
cd /opt/sf-express

# 编辑 requirements.txt
nano requirements.txt
```

在文件末尾添加：
```
psutil==5.9.6
```

完整的 requirements.txt 应该包含：
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
pymysql==1.1.0
cryptography==46.0.3
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
bcrypt==4.0.1
pandas==2.1.3
openpyxl==3.1.2
xlrd==2.0.1
requests==2.31.0
httpx==0.27.2
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0
hypothesis==6.92.1
psutil==5.9.6
```

保存文件（Ctrl+X, Y, Enter）

---

### 修复2: 生成SSL证书

```bash
# 创建SSL目录（如果不存在）
mkdir -p /opt/sf-express/docker/nginx/ssl

# 生成自签名SSL证书
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /opt/sf-express/docker/nginx/ssl/key.pem \
    -out /opt/sf-express/docker/nginx/ssl/cert.pem \
    -subj "/C=CN/ST=Beijing/L=Beijing/O=SF Express/CN=localhost"

# 设置权限
chmod 600 /opt/sf-express/docker/nginx/ssl/*.pem

# 验证证书文件
ls -la /opt/sf-express/docker/nginx/ssl/
```

应该看到：
```
-rw------- 1 root root cert.pem
-rw------- 1 root root key.pem
```

---

### 修复3: 重新构建并启动服务

```bash
# 停止所有容器
cd /opt/sf-express
docker-compose --env-file .env.production down

# 清理旧镜像（可选）
docker-compose --env-file .env.production rm -f

# 重新构建镜像
docker-compose --env-file .env.production build --no-cache

# 启动服务
docker-compose --env-file .env.production up -d

# 等待30秒让服务启动
sleep 30

# 查看状态
docker-compose --env-file .env.production ps
```

---

## ✅ 验证修复

### 1. 检查容器状态

```bash
docker-compose --env-file .env.production ps
```

**期望结果**: 所有容器状态为 `Up`

```
NAME                    STATUS
express-tracking-app    Up
express-tracking-db     Up (healthy)
express-tracking-nginx  Up
express-tracking-redis  Up
```

### 2. 检查日志

```bash
# 查看应用日志
docker-compose --env-file .env.production logs app

# 查看Nginx日志
docker-compose --env-file .env.production logs nginx

# 查看所有日志
docker-compose --env-file .env.production logs
```

**期望结果**: 没有错误信息

### 3. 测试访问

```bash
# 测试健康检查
curl http://localhost:8000/health

# 测试前端
curl http://localhost

# 测试HTTPS（如果配置了）
curl -k https://localhost
```

---

## 🔍 详细问题分析

### 问题1: psutil模块缺失

**原因**: `requirements.txt` 中没有包含 `psutil` 模块，但代码中使用了它。

**影响**: 应用容器无法启动

**解决**: 在 `requirements.txt` 中添加 `psutil==5.9.6`

---

### 问题2: SSL证书缺失

**原因**: 
1. 没有生成SSL证书
2. 证书文件路径不正确
3. 证书文件权限问题

**影响**: Nginx容器反复重启

**解决**: 生成自签名证书或使用Let's Encrypt证书

---

## 🛠️ 完整的修复脚本

创建一个修复脚本：

```bash
# 创建修复脚本
cat > /opt/sf-express/fix_deployment.sh << 'EOF'
#!/bin/bash

echo "开始修复部署问题..."

# 1. 检查并添加psutil到requirements.txt
if ! grep -q "psutil" requirements.txt; then
    echo "添加psutil到requirements.txt..."
    echo "psutil==5.9.6" >> requirements.txt
fi

# 2. 创建SSL目录
echo "创建SSL目录..."
mkdir -p docker/nginx/ssl

# 3. 生成SSL证书
if [ ! -f docker/nginx/ssl/cert.pem ]; then
    echo "生成SSL证书..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout docker/nginx/ssl/key.pem \
        -out docker/nginx/ssl/cert.pem \
        -subj "/C=CN/ST=Beijing/L=Beijing/O=SF Express/CN=localhost" \
        2>/dev/null
    chmod 600 docker/nginx/ssl/*.pem
fi

# 4. 停止服务
echo "停止现有服务..."
docker-compose --env-file .env.production down

# 5. 重新构建
echo "重新构建镜像..."
docker-compose --env-file .env.production build --no-cache

# 6. 启动服务
echo "启动服务..."
docker-compose --env-file .env.production up -d

# 7. 等待服务启动
echo "等待服务启动..."
sleep 30

# 8. 检查状态
echo "检查服务状态..."
docker-compose --env-file .env.production ps

echo "修复完成！"
EOF

# 添加执行权限
chmod +x /opt/sf-express/fix_deployment.sh

# 运行修复脚本
/opt/sf-express/fix_deployment.sh
```

---

## 📋 如果还有问题

### 检查清单

- [ ] requirements.txt 包含 psutil
- [ ] SSL证书文件存在
- [ ] SSL证书权限正确（600）
- [ ] docker-compose.yml 配置正确
- [ ] .env.production 配置正确
- [ ] Docker服务运行正常

### 查看详细日志

```bash
# 查看应用容器日志
docker logs express-tracking-app

# 查看Nginx容器日志
docker logs express-tracking-nginx

# 查看数据库容器日志
docker logs express-tracking-db

# 实时查看所有日志
docker-compose --env-file .env.production logs -f
```

### 进入容器调试

```bash
# 进入应用容器
docker-compose --env-file .env.production exec app bash

# 检查Python模块
python -c "import psutil; print(psutil.__version__)"

# 检查文件
ls -la /app

# 退出容器
exit
```

---

## 🔧 替代方案：不使用Docker部署

如果Docker部署问题太多，可以考虑直接部署：

### 步骤1: 安装Python和依赖

```bash
# 安装Python 3.11
apt install -y python3.11 python3.11-venv python3-pip

# 创建虚拟环境
cd /opt/sf-express
python3.11 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 步骤2: 安装MySQL

```bash
# 安装MySQL
apt install -y mysql-server

# 启动MySQL
systemctl start mysql
systemctl enable mysql

# 创建数据库
mysql -u root -p << EOF
CREATE DATABASE express_tracking CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'express_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON express_tracking.* TO 'express_user'@'localhost';
FLUSH PRIVILEGES;
EOF
```

### 步骤3: 配置并启动应用

```bash
# 配置环境变量
cp .env.example .env
nano .env  # 修改配置

# 运行数据库迁移
alembic upgrade head

# 创建管理员
python create_admin_user.py

# 启动应用
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 📞 常见错误及解决

### 错误1: "Cannot connect to the Docker daemon"

```bash
# 启动Docker服务
systemctl start docker
systemctl enable docker
```

### 错误2: "port is already allocated"

```bash
# 查看端口占用
netstat -tlnp | grep :8000

# 停止占用端口的进程
kill -9 <PID>
```

### 错误3: "no space left on device"

```bash
# 清理Docker
docker system prune -a

# 查看磁盘空间
df -h
```

### 错误4: "permission denied"

```bash
# 修复权限
chown -R root:root /opt/sf-express
chmod -R 755 /opt/sf-express
```

---

## ✅ 成功标志

部署成功后，应该看到：

1. **所有容器运行正常**
```bash
docker-compose ps
# 所有容器状态为 Up
```

2. **可以访问应用**
```bash
curl http://localhost:8000/health
# 返回 {"status": "ok"}
```

3. **可以访问前端**
```bash
curl http://localhost
# 返回HTML内容
```

4. **没有错误日志**
```bash
docker-compose logs | grep -i error
# 没有输出或只有无关紧要的错误
```

---

## 🎯 总结

**主要问题**:
1. ✅ requirements.txt 缺少 psutil
2. ✅ SSL证书文件缺失

**解决方案**:
1. 添加 `psutil==5.9.6` 到 requirements.txt
2. 生成SSL证书
3. 重新构建并启动服务

**一键修复**:
```bash
cd /opt/sf-express
echo "psutil==5.9.6" >> requirements.txt
mkdir -p docker/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout docker/nginx/ssl/key.pem -out docker/nginx/ssl/cert.pem -subj "/C=CN/ST=Beijing/L=Beijing/O=SF Express/CN=localhost"
docker-compose --env-file .env.production down
docker-compose --env-file .env.production build --no-cache
docker-compose --env-file .env.production up -d
```

需要更多帮助吗？

# Docker部署快速修复指南

## 🎯 问题概述

运行 `docker-compose ps` 后出现两个错误：
1. **Python模块缺失**: `ModuleNotFoundError: No module named 'psutil'`
2. **SSL证书缺失**: `nginx: [emerg] cannot load certificate "/etc/nginx/ssl/cert.pem"`

---

## ⚡ 一键自动修复（推荐）

已经为您准备好了自动修复脚本，只需在服务器上执行以下命令：

```bash
# 进入项目目录
cd /opt/sf-express

# 添加执行权限
chmod +x fix_docker_deployment.sh

# 运行修复脚本
./fix_docker_deployment.sh
```

脚本会自动完成以下操作：
- ✅ 添加 psutil 到 requirements.txt
- ✅ 创建 SSL 证书目录
- ✅ 生成自签名 SSL 证书
- ✅ 停止现有服务
- ✅ 重新构建 Docker 镜像
- ✅ 启动所有服务
- ✅ 验证服务状态
- ✅ 测试应用访问

**预计耗时**: 5-10分钟（主要是镜像构建时间）

---

## 🔧 手动修复步骤

如果自动脚本无法运行，可以手动执行以下步骤：

### 步骤1: 添加 psutil 模块

```bash
cd /opt/sf-express
echo "psutil==5.9.6" >> requirements.txt
```

### 步骤2: 生成 SSL 证书

```bash
# 创建SSL目录
mkdir -p docker/nginx/ssl

# 生成自签名证书
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout docker/nginx/ssl/key.pem \
    -out docker/nginx/ssl/cert.pem \
    -subj "/C=CN/ST=Beijing/L=Beijing/O=SF Express/CN=localhost"

# 设置权限
chmod 600 docker/nginx/ssl/*.pem
```

### 步骤3: 重新构建并启动

```bash
# 停止服务
docker-compose --env-file .env.production down

# 重新构建（不使用缓存）
docker-compose --env-file .env.production build --no-cache

# 启动服务
docker-compose --env-file .env.production up -d

# 等待30秒
sleep 30

# 查看状态
docker-compose --env-file .env.production ps
```

---

## ✅ 验证修复结果

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

### 2. 查看日志（如有错误）

```bash
# 查看所有日志
docker-compose --env-file .env.production logs

# 查看应用日志
docker-compose --env-file .env.production logs app

# 查看Nginx日志
docker-compose --env-file .env.production logs nginx

# 实时查看日志
docker-compose --env-file .env.production logs -f
```

### 3. 测试应用访问

```bash
# 测试健康检查
curl http://localhost:8000/health

# 测试前端
curl http://localhost

# 测试API
curl http://localhost:8000/docs
```

**期望结果**: 
- 健康检查返回: `{"status":"ok"}`
- 前端返回: HTML内容
- API文档可访问

---

## 🌐 访问应用

修复成功后，可以通过以下地址访问：

- **前端首页**: `http://your-server-ip/`
- **管理后台**: `http://your-server-ip/admin/login.html`
- **API文档**: `http://your-server-ip:8000/docs`
- **健康检查**: `http://your-server-ip:8000/health`

**默认管理员账号**:
- 用户名: `admin`
- 密码: `admin123`

---

## 🔍 常见问题排查

### 问题1: 容器反复重启

```bash
# 查看容器日志
docker logs express-tracking-app
docker logs express-tracking-nginx
docker logs express-tracking-db

# 检查资源使用
docker stats
```

### 问题2: 端口被占用

```bash
# 查看端口占用
netstat -tlnp | grep :8000
netstat -tlnp | grep :80
netstat -tlnp | grep :3306

# 停止占用端口的进程
kill -9 <PID>
```

### 问题3: 磁盘空间不足

```bash
# 查看磁盘空间
df -h

# 清理Docker
docker system prune -a
docker volume prune
```

### 问题4: 数据库连接失败

```bash
# 检查数据库容器
docker-compose --env-file .env.production logs db

# 进入数据库容器
docker-compose --env-file .env.production exec db bash

# 测试数据库连接
mysql -u express_user -p express_tracking
```

### 问题5: 权限问题

```bash
# 修复文件权限
chown -R root:root /opt/sf-express
chmod -R 755 /opt/sf-express

# 修复SSL证书权限
chmod 600 /opt/sf-express/docker/nginx/ssl/*.pem
```

---

## 📋 完整的修复命令（复制粘贴）

如果您想一次性执行所有命令，可以复制以下内容：

```bash
# 进入项目目录
cd /opt/sf-express

# 添加psutil
echo "psutil==5.9.6" >> requirements.txt

# 创建SSL目录
mkdir -p docker/nginx/ssl

# 生成SSL证书
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout docker/nginx/ssl/key.pem \
    -out docker/nginx/ssl/cert.pem \
    -subj "/C=CN/ST=Beijing/L=Beijing/O=SF Express/CN=localhost"

# 设置权限
chmod 600 docker/nginx/ssl/*.pem

# 停止服务
docker-compose --env-file .env.production down

# 重新构建
docker-compose --env-file .env.production build --no-cache

# 启动服务
docker-compose --env-file .env.production up -d

# 等待启动
sleep 30

# 查看状态
docker-compose --env-file .env.production ps

# 测试访问
curl http://localhost:8000/health
```

---

## 🎉 成功标志

当您看到以下结果时，说明部署成功：

1. ✅ 所有容器状态为 `Up`
2. ✅ 健康检查返回 `{"status":"ok"}`
3. ✅ 可以访问前端页面
4. ✅ 可以访问管理后台
5. ✅ 日志中没有错误信息

---

## 📞 需要帮助？

如果按照以上步骤仍然无法解决问题，请提供以下信息：

1. 容器状态: `docker-compose --env-file .env.production ps`
2. 应用日志: `docker-compose --env-file .env.production logs app | tail -50`
3. Nginx日志: `docker-compose --env-file .env.production logs nginx | tail -50`
4. 系统信息: `df -h` 和 `free -h`

---

## 🔄 重新开始（如果需要）

如果想完全重新开始部署：

```bash
# 停止并删除所有容器
docker-compose --env-file .env.production down -v

# 删除所有镜像
docker rmi $(docker images -q express-tracking*)

# 清理系统
docker system prune -a

# 重新开始部署
./fix_docker_deployment.sh
```

---

**最后更新**: 2026-02-02

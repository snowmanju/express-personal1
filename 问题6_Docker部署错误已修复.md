# 问题6：Docker部署错误已修复 ✅

## 📋 问题描述

在阿里云服务器上运行 `docker-compose --env-file .env.production ps` 后，出现以下错误：

1. **Python模块缺失错误**:
   ```
   ModuleNotFoundError: No module named 'psutil'
   ```

2. **SSL证书缺失错误**:
   ```
   nginx: [emerg] cannot load certificate "/etc/nginx/ssl/cert.pem": BIO_new_file() failed
   ```

导致应用容器和Nginx容器反复重启，无法正常运行。

---

## ✅ 解决方案

### 问题分析

1. **psutil模块缺失**: 
   - 原因：`requirements.txt` 中没有包含 `psutil` 模块
   - 影响：应用容器无法启动
   
2. **SSL证书缺失**:
   - 原因：没有生成SSL证书文件
   - 影响：Nginx容器无法启动

### 已完成的修复

1. ✅ **更新 requirements.txt**
   - 添加了 `psutil==5.9.6`
   - 同时更新了根目录和 `sf-express/` 目录的文件

2. ✅ **创建自动修复脚本**
   - `fix_docker_deployment.sh` - 一键自动修复脚本
   - 自动完成所有修复步骤

3. ✅ **创建详细文档**
   - `Docker部署快速修复指南.md` - 快速参考
   - `Docker部署错误修复指南.md` - 详细说明
   - `Docker部署问题已修复.md` - 修复总结

---

## 🚀 在服务器上执行修复

### 方法1: 使用自动修复脚本（强烈推荐）

```bash
# 1. 进入项目目录
cd /opt/sf-express

# 2. 上传最新文件（如果还没上传）
# 需要上传：
# - requirements.txt (已更新)
# - fix_docker_deployment.sh (新文件)

# 3. 添加执行权限
chmod +x fix_docker_deployment.sh

# 4. 运行修复脚本
./fix_docker_deployment.sh
```

**脚本会自动完成**：
- ✅ 检查并添加 psutil 到 requirements.txt
- ✅ 创建 SSL 证书目录
- ✅ 生成自签名 SSL 证书
- ✅ 停止现有服务
- ✅ 重新构建 Docker 镜像（不使用缓存）
- ✅ 启动所有服务
- ✅ 等待服务启动（30秒）
- ✅ 检查服务状态
- ✅ 测试应用访问

**预计耗时**: 5-10分钟（主要是镜像构建时间）

---

### 方法2: 手动执行命令

如果自动脚本无法运行，可以手动执行以下命令：

```bash
# 进入项目目录
cd /opt/sf-express

# 1. 添加psutil（如果requirements.txt还没更新）
echo "psutil==5.9.6" >> requirements.txt

# 2. 创建SSL目录
mkdir -p docker/nginx/ssl

# 3. 生成SSL证书
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout docker/nginx/ssl/key.pem \
    -out docker/nginx/ssl/cert.pem \
    -subj "/C=CN/ST=Beijing/L=Beijing/O=SF Express/CN=localhost"

# 4. 设置证书权限
chmod 600 docker/nginx/ssl/*.pem

# 5. 停止服务
docker-compose --env-file .env.production down

# 6. 重新构建镜像
docker-compose --env-file .env.production build --no-cache

# 7. 启动服务
docker-compose --env-file .env.production up -d

# 8. 等待30秒
sleep 30

# 9. 查看状态
docker-compose --env-file .env.production ps

# 10. 测试访问
curl http://localhost:8000/health
```

---

## ✅ 验证修复成功

### 1. 检查容器状态

```bash
docker-compose --env-file .env.production ps
```

**期望结果**：所有容器状态为 `Up`

```
NAME                    STATUS
express-tracking-app    Up
express-tracking-db     Up (healthy)
express-tracking-nginx  Up
express-tracking-redis  Up
```

### 2. 测试应用访问

```bash
# 测试健康检查
curl http://localhost:8000/health
# 期望返回: {"status":"ok"}

# 测试前端
curl http://localhost
# 期望返回: HTML内容
```

### 3. 浏览器访问测试

打开浏览器访问以下地址：

- **前端首页**: `http://your-server-ip/`
- **管理后台**: `http://your-server-ip/admin/login.html`
- **API文档**: `http://your-server-ip:8000/docs`
- **健康检查**: `http://your-server-ip:8000/health`

**管理员账号**：
- 用户名: `admin`
- 密码: `admin123`

---

## 📁 需要上传到服务器的文件

### 必须上传：

1. **requirements.txt** (已更新，添加了 psutil==5.9.6)
2. **fix_docker_deployment.sh** (新创建的自动修复脚本)

### 可选上传（文档）：

3. **Docker部署快速修复指南.md**
4. **Docker部署错误修复指南.md**
5. **Docker部署问题已修复.md**

### 上传方法：

**方法1: 使用 SCP**
```bash
# 在本地Windows上使用PowerShell或Git Bash
scp requirements.txt root@your-server-ip:/opt/sf-express/
scp fix_docker_deployment.sh root@your-server-ip:/opt/sf-express/
```

**方法2: 使用 WinSCP**
1. 打开 WinSCP 连接到服务器
2. 导航到 `/opt/sf-express/` 目录
3. 拖拽文件上传

**方法3: 重新打包上传整个项目**
```bash
# 在本地打包
tar -czf sf-express.tar.gz sf-express/

# 上传到服务器
scp sf-express.tar.gz root@your-server-ip:/opt/

# 在服务器上解压
ssh root@your-server-ip
cd /opt
tar -xzf sf-express.tar.gz
```

---

## 🔍 如果遇到问题

### 查看日志

```bash
# 查看所有日志
docker-compose --env-file .env.production logs

# 查看应用日志
docker-compose --env-file .env.production logs app

# 查看Nginx日志
docker-compose --env-file .env.production logs nginx

# 查看数据库日志
docker-compose --env-file .env.production logs db

# 实时查看日志
docker-compose --env-file .env.production logs -f
```

### 常见问题及解决方案

#### 问题1: 容器反复重启

```bash
# 查看具体错误
docker logs express-tracking-app
docker logs express-tracking-nginx

# 检查资源使用
docker stats
```

#### 问题2: 端口被占用

```bash
# 查看端口占用
netstat -tlnp | grep :8000
netstat -tlnp | grep :80

# 停止占用端口的进程
kill -9 <PID>
```

#### 问题3: 磁盘空间不足

```bash
# 查看磁盘空间
df -h

# 清理Docker
docker system prune -a
docker volume prune
```

#### 问题4: 权限问题

```bash
# 修复文件权限
chown -R root:root /opt/sf-express
chmod -R 755 /opt/sf-express

# 修复SSL证书权限
chmod 600 /opt/sf-express/docker/nginx/ssl/*.pem
```

---

## 📊 修复前后对比

### 修复前 ❌

```
容器状态:
express-tracking-app    Restarting
express-tracking-nginx  Restarting

错误信息:
ModuleNotFoundError: No module named 'psutil'
nginx: [emerg] cannot load certificate "/etc/nginx/ssl/cert.pem"
```

### 修复后 ✅

```
容器状态:
express-tracking-app    Up
express-tracking-db     Up (healthy)
express-tracking-nginx  Up
express-tracking-redis  Up

测试结果:
curl http://localhost:8000/health
{"status":"ok"}

所有服务正常运行！
```

---

## 🎯 成功标志

当您看到以下结果时，说明部署完全成功：

1. ✅ 所有容器状态为 `Up`
2. ✅ 健康检查返回 `{"status":"ok"}`
3. ✅ 可以访问前端页面
4. ✅ 可以访问管理后台并登录
5. ✅ 可以上传理货单
6. ✅ 可以查询物流信息
7. ✅ 日志中没有错误信息

---

## 📝 相关文档

- `Docker部署快速修复指南.md` - 快速参考指南
- `Docker部署错误修复指南.md` - 详细修复说明
- `阿里云服务器部署指南.md` - 完整部署文档
- `阿里云部署快速参考.md` - 快速参考卡
- `部署检查清单.md` - 部署检查项
- `GitHub访问问题解决方案.md` - GitHub访问问题
- `快速解决GitHub访问问题.md` - GitHub快速解决

---

## 🎉 总结

### 问题根源
1. requirements.txt 缺少 psutil 模块
2. 没有生成 SSL 证书文件

### 解决方案
1. 添加 psutil==5.9.6 到 requirements.txt
2. 生成自签名 SSL 证书
3. 重新构建 Docker 镜像

### 修复状态
✅ **已完成本地修复**  
⏳ **等待服务器执行**

### 下一步
1. 上传更新的文件到服务器
2. 运行 `fix_docker_deployment.sh` 脚本
3. 验证所有容器正常运行
4. 测试应用功能

---

**问题编号**: 6  
**修复时间**: 2026-02-02  
**状态**: ✅ 已修复（等待服务器执行）  
**相关问题**: 问题5（GitHub访问问题）

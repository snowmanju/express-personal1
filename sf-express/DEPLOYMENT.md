# 快递查询网站部署指南

## 概述

本文档提供了快递查询网站的完整部署指南，包括开发环境、生产环境和监控系统的配置。

## 系统要求

### 最低硬件要求
- CPU: 2核心
- 内存: 4GB RAM
- 存储: 20GB 可用空间
- 网络: 稳定的互联网连接

### 软件要求
- Docker 20.10+
- Docker Compose 2.0+
- Git
- OpenSSL（用于生成SSL证书）

## 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd express-tracking-website
```

### 2. 配置环境变量
```bash
# 复制环境配置模板
cp .env.example .env.production

# 编辑生产环境配置
nano .env.production
```

**重要配置项：**
- `SECRET_KEY`: JWT密钥，必须设置为强密钥
- `MYSQL_ROOT_PASSWORD`: MySQL root密码
- `MYSQL_PASSWORD`: 应用数据库用户密码
- `REDIS_PASSWORD`: Redis密码
- `KUAIDI100_*`: 快递100 API配置

### 3. 生产环境部署
```bash
# 运行部署脚本
bash scripts/deploy.sh

# 或者手动部署
docker-compose --env-file .env.production up -d
```

### 4. 验证部署
访问以下地址验证部署：
- 前台查询: http://localhost
- 后台管理: http://localhost/admin
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## 详细部署步骤

### 开发环境部署

```bash
# 启动开发环境
bash scripts/deploy.sh dev

# 或者直接使用docker-compose
docker-compose -f docker-compose.dev.yml up -d
```

开发环境特点：
- 代码热重载
- 详细日志输出
- 简化的配置
- 无SSL要求

### 生产环境部署

#### 1. 准备工作

```bash
# 创建必要目录
mkdir -p logs uploads docker/nginx/ssl

# 生成SSL证书（自签名）
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout docker/nginx/ssl/key.pem \
    -out docker/nginx/ssl/cert.pem \
    -subj "/C=CN/ST=Beijing/L=Beijing/O=Express Tracking/CN=yourdomain.com"
```

#### 2. 配置环境变量

编辑 `.env.production` 文件：

```env
# 数据库配置
MYSQL_ROOT_PASSWORD=your-strong-root-password
MYSQL_PASSWORD=your-strong-user-password
DATABASE_URL=mysql+pymysql://express_user:your-strong-user-password@db:3306/express_tracking

# JWT密钥配置
SECRET_KEY=your-very-strong-secret-key-for-jwt-tokens

# 快递100 API配置
KUAIDI100_KEY=fypLxFrg3636
KUAIDI100_CUSTOMER=3564B6CF145FA93724CE18C1FB149036
KUAIDI100_SECRET=8fa1052ba57e4d9ca0427938a77e2e30
KUAIDI100_USERID=a1ffc21f3de94cf5bdd908faf3bbc81d

# Redis配置
REDIS_PASSWORD=your-redis-password

# 日志级别
LOG_LEVEL=INFO
```

#### 3. 启动服务

```bash
# 构建并启动所有服务
docker-compose --env-file .env.production up -d

# 查看服务状态
docker-compose --env-file .env.production ps

# 查看日志
docker-compose --env-file .env.production logs -f
```

#### 4. 运行数据库迁移

```bash
# 等待数据库启动后运行迁移
docker-compose --env-file .env.production exec app alembic upgrade head
```

### 监控系统部署

```bash
# 启动监控服务
bash scripts/deploy.sh monitoring

# 或者直接使用docker-compose
docker-compose -f docker-compose.monitoring.yml --env-file .env.production up -d
```

监控服务访问地址：
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- AlertManager: http://localhost:9093

## 服务管理

### 常用命令

```bash
# 查看服务状态
docker-compose --env-file .env.production ps

# 查看实时日志
docker-compose --env-file .env.production logs -f

# 重启特定服务
docker-compose --env-file .env.production restart app

# 停止所有服务
docker-compose --env-file .env.production down

# 重新构建并启动
docker-compose --env-file .env.production up -d --build
```

### 数据库管理

```bash
# 连接到数据库
docker-compose --env-file .env.production exec db mysql -u root -p

# 备份数据库
docker-compose --env-file .env.production exec db mysqldump \
    -u root -p express_tracking > backup.sql

# 恢复数据库
docker-compose --env-file .env.production exec -T db mysql \
    -u root -p express_tracking < backup.sql
```

### 应用管理

```bash
# 进入应用容器
docker-compose --env-file .env.production exec app bash

# 运行数据库迁移
docker-compose --env-file .env.production exec app alembic upgrade head

# 创建管理员用户
docker-compose --env-file .env.production exec app python create_admin_user.py
```

## 备份和恢复

### 自动备份

```bash
# 运行备份脚本
bash scripts/backup.sh

# 设置定时备份（crontab）
0 2 * * * /path/to/scripts/backup.sh
```

### 手动备份

```bash
# 备份数据库
docker-compose --env-file .env.production exec db mysqldump \
    -u root -p${MYSQL_ROOT_PASSWORD} \
    --single-transaction express_tracking > backup_$(date +%Y%m%d).sql

# 备份上传文件
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz uploads/

# 备份配置文件
tar -czf config_backup_$(date +%Y%m%d).tar.gz .env.production docker/
```

### 恢复备份

```bash
# 恢复数据库
docker-compose --env-file .env.production exec -T db mysql \
    -u root -p${MYSQL_ROOT_PASSWORD} express_tracking < backup.sql

# 恢复上传文件
tar -xzf uploads_backup.tar.gz
```

## 安全配置

### SSL/TLS配置

1. **获取真实SSL证书**（推荐Let's Encrypt）
```bash
# 使用certbot获取证书
certbot certonly --standalone -d yourdomain.com
```

2. **更新Nginx配置**
```bash
# 将证书复制到正确位置
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem docker/nginx/ssl/cert.pem
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem docker/nginx/ssl/key.pem
```

### 防火墙配置

```bash
# 开放必要端口
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp

# 限制数据库端口访问
ufw deny 3306/tcp
```

### 密码安全

1. 使用强密码
2. 定期更换密码
3. 启用双因素认证（如果支持）
4. 限制管理员账户数量

## 性能优化

### 数据库优化

```sql
-- 添加索引
CREATE INDEX idx_tracking_number ON cargo_manifest(tracking_number);
CREATE INDEX idx_package_number ON cargo_manifest(package_number);
CREATE INDEX idx_manifest_date ON cargo_manifest(manifest_date);

-- 优化MySQL配置
SET GLOBAL innodb_buffer_pool_size = 1073741824; -- 1GB
SET GLOBAL query_cache_size = 268435456; -- 256MB
```

### 应用优化

1. **启用Redis缓存**
```python
# 在应用中配置Redis缓存
REDIS_URL = "redis://redis:6379/0"
```

2. **调整Worker数量**
```bash
# 根据CPU核心数调整
uvicorn app.main:app --workers 4
```

### Nginx优化

```nginx
# 启用gzip压缩
gzip on;
gzip_comp_level 6;
gzip_types text/plain text/css application/json application/javascript;

# 设置缓存
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## 监控和日志

### 日志管理

```bash
# 查看应用日志
docker-compose --env-file .env.production logs app

# 查看Nginx访问日志
docker-compose --env-file .env.production exec nginx tail -f /var/log/nginx/access.log

# 查看系统日志
journalctl -u docker -f
```

### 监控指标

关键监控指标：
- 应用响应时间
- 错误率
- 数据库连接数
- 内存使用率
- CPU使用率
- 磁盘空间

### 告警配置

在 `docker/monitoring/alert_rules.yml` 中配置告警规则：
- 应用宕机告警
- 高错误率告警
- 资源使用率告警
- 数据库性能告警

## 故障排除

### 常见问题

1. **服务无法启动**
```bash
# 检查端口占用
netstat -tlnp | grep :8000

# 检查Docker日志
docker-compose --env-file .env.production logs
```

2. **数据库连接失败**
```bash
# 检查数据库状态
docker-compose --env-file .env.production exec db mysqladmin ping

# 检查网络连接
docker network ls
```

3. **SSL证书问题**
```bash
# 验证证书
openssl x509 -in docker/nginx/ssl/cert.pem -text -noout

# 测试SSL连接
openssl s_client -connect localhost:443
```

### 日志分析

```bash
# 查找错误日志
grep -i error logs/app.log

# 分析访问模式
awk '{print $1}' logs/nginx/access.log | sort | uniq -c | sort -nr

# 监控响应时间
tail -f logs/nginx/access.log | awk '{print $NF}'
```

## 升级和维护

### 应用升级

```bash
# 拉取最新代码
git pull origin main

# 重新构建镜像
docker-compose --env-file .env.production build --no-cache

# 滚动更新
docker-compose --env-file .env.production up -d
```

### 数据库维护

```bash
# 运行数据库迁移
docker-compose --env-file .env.production exec app alembic upgrade head

# 优化数据库表
docker-compose --env-file .env.production exec db mysql -u root -p -e "OPTIMIZE TABLE express_tracking.cargo_manifest;"
```

### 定期维护任务

1. **每日**
   - 检查服务状态
   - 查看错误日志
   - 监控资源使用

2. **每周**
   - 数据库备份
   - 清理旧日志
   - 更新系统包

3. **每月**
   - 安全更新
   - 性能分析
   - 容量规划

## 联系支持

如果遇到问题，请：
1. 查看本文档的故障排除部分
2. 检查应用日志
3. 联系技术支持团队

---

**注意**: 本部署指南适用于生产环境，请确保在部署前充分测试所有配置。
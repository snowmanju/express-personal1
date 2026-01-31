# 快速解决GitHub访问问题

## 🚨 问题

在阿里云服务器上无法访问GitHub，报错：
```
curl: (28) Failed to connect to github.com port 443 after 136218 ms: Couldn't connect to server
```

---

## ⚡ 快速解决（3个命令）

### 方案1: 使用国内镜像 ⭐⭐⭐⭐⭐

```bash
# 一行命令安装Docker Compose
curl -L "https://get.daocloud.io/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && chmod +x /usr/local/bin/docker-compose && docker-compose --version
```

**成功标志**: 显示 `Docker Compose version v2.23.0`

---

### 方案2: 使用包管理器 ⭐⭐⭐⭐⭐

```bash
# Ubuntu系统
apt update && apt install -y docker-compose && docker-compose --version

# CentOS系统
yum install -y epel-release && yum install -y docker-compose && docker-compose --version
```

**优点**: 最简单，不需要访问GitHub

---

### 方案3: 修改DNS后重试 ⭐⭐⭐⭐

```bash
# 1. 修改DNS为阿里云DNS
cat > /etc/resolv.conf << EOF
nameserver 223.5.5.5
nameserver 223.6.6.6
EOF

# 2. 测试连接
ping github.com

# 3. 重新下载
curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && chmod +x /usr/local/bin/docker-compose
```

---

## 📋 推荐执行顺序

```
1. 先试方案1（国内镜像）
   ↓ 如果失败
2. 再试方案2（包管理器）
   ↓ 如果失败
3. 最后试方案3（修改DNS）
```

---

## ✅ 验证安装

```bash
# 检查版本
docker-compose --version

# 应该显示：
# Docker Compose version v2.23.0
# 或其他版本号
```

---

## 🔧 其他常见GitHub访问问题

### 问题1: git clone失败

```bash
# 使用GitHub代理
git clone https://ghproxy.com/https://github.com/user/repo.git
```

### 问题2: Docker镜像拉取慢

```bash
# 配置阿里云镜像加速
mkdir -p /etc/docker
cat > /etc/docker/daemon.json << EOF
{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com",
    "https://registry.docker-cn.com"
  ]
}
EOF

systemctl daemon-reload
systemctl restart docker
```

---

## 📞 需要详细说明？

查看完整文档：[GitHub访问问题解决方案.md](GitHub访问问题解决方案.md)

---

**记住**: 在中国大陆的服务器上，优先使用国内镜像源！

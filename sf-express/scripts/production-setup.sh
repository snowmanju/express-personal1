#!/bin/bash

# 生产环境设置脚本
# Production Environment Setup Script

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 生成强密钥
generate_secret_key() {
    openssl rand -hex 32
}

# 生成强密码
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# 设置生产环境配置
setup_production_config() {
    log_info "设置生产环境配置..."
    
    if [ -f ".env.production" ]; then
        log_warning ".env.production已存在，创建备份..."
        cp .env.production .env.production.backup.$(date +%Y%m%d_%H%M%S)
    fi
    
    # 生成强密钥和密码
    SECRET_KEY=$(generate_secret_key)
    MYSQL_ROOT_PASSWORD=$(generate_password)
    MYSQL_PASSWORD=$(generate_password)
    REDIS_PASSWORD=$(generate_password)
    GRAFANA_PASSWORD=$(generate_password)
    
    # 创建生产环境配置文件
    cat > .env.production << EOF
# 生产环境配置文件 - 自动生成于 $(date)
# 注意：此文件包含敏感信息，不应提交到版本控制系统

# 数据库配置
MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
MYSQL_PASSWORD=${MYSQL_PASSWORD}
DATABASE_URL=mysql+pymysql://express_user:${MYSQL_PASSWORD}@db:3306/express_tracking

# JWT密钥配置
SECRET_KEY=${SECRET_KEY}

# 快递100 API配置
KUAIDI100_KEY=fypLxFrg3636
KUAIDI100_CUSTOMER=3564B6CF145FA93724CE18C1FB149036
KUAIDI100_SECRET=8fa1052ba57e4d9ca0427938a77e2e30
KUAIDI100_USERID=a1ffc21f3de94cf5bdd908faf3bbc81d

# Redis配置
REDIS_PASSWORD=${REDIS_PASSWORD}

# Grafana配置
GRAFANA_PASSWORD=${GRAFANA_PASSWORD}

# 日志级别
LOG_LEVEL=INFO

# 应用环境
ENVIRONMENT=production

# SSL证书路径
SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
SSL_KEY_PATH=/etc/nginx/ssl/key.pem
EOF

    log_success "生产环境配置文件已创建"
    log_info "生成的密码信息："
    echo "  MySQL Root密码: ${MYSQL_ROOT_PASSWORD}"
    echo "  MySQL用户密码: ${MYSQL_PASSWORD}"
    echo "  Redis密码: ${REDIS_PASSWORD}"
    echo "  Grafana密码: ${GRAFANA_PASSWORD}"
    echo ""
    log_warning "请妥善保存这些密码信息！"
}

# 设置文件权限
setup_file_permissions() {
    log_info "设置文件权限..."
    
    # 设置环境文件权限
    chmod 600 .env.production
    
    # 设置脚本执行权限
    chmod +x scripts/*.sh
    
    # 设置日志目录权限
    mkdir -p logs uploads
    chmod 755 logs uploads
    
    log_success "文件权限设置完成"
}

# 优化系统设置
optimize_system() {
    log_info "优化系统设置..."
    
    # 创建系统优化配置
    cat > /tmp/sysctl-express-tracking.conf << EOF
# 快递查询网站系统优化配置

# 网络优化
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 1200
net.ipv4.tcp_max_tw_buckets = 5000

# 文件描述符限制
fs.file-max = 65535

# 内存优化
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
EOF

    if [ "$EUID" -eq 0 ]; then
        cp /tmp/sysctl-express-tracking.conf /etc/sysctl.d/99-express-tracking.conf
        sysctl -p /etc/sysctl.d/99-express-tracking.conf
        log_success "系统优化配置已应用"
    else
        log_warning "需要root权限应用系统优化，配置文件已保存到 /tmp/sysctl-express-tracking.conf"
        log_info "请以root权限运行以下命令："
        echo "  sudo cp /tmp/sysctl-express-tracking.conf /etc/sysctl.d/99-express-tracking.conf"
        echo "  sudo sysctl -p /etc/sysctl.d/99-express-tracking.conf"
    fi
}

# 设置防火墙规则
setup_firewall() {
    log_info "设置防火墙规则..."
    
    if command -v ufw &> /dev/null; then
        # 允许SSH
        ufw allow 22/tcp
        
        # 允许HTTP和HTTPS
        ufw allow 80/tcp
        ufw allow 443/tcp
        
        # 允许监控端口（仅本地）
        ufw allow from 127.0.0.1 to any port 3000  # Grafana
        ufw allow from 127.0.0.1 to any port 9090  # Prometheus
        ufw allow from 127.0.0.1 to any port 9093  # AlertManager
        
        # 拒绝数据库和Redis端口的外部访问
        ufw deny 3306/tcp
        ufw deny 6379/tcp
        
        log_success "防火墙规则设置完成"
        log_info "运行 'sudo ufw enable' 启用防火墙"
    else
        log_warning "未找到ufw防火墙，请手动配置防火墙规则"
    fi
}

# 创建systemd服务文件
create_systemd_service() {
    log_info "创建systemd服务文件..."
    
    cat > /tmp/express-tracking.service << EOF
[Unit]
Description=Express Tracking Website
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$(pwd)
ExecStart=/usr/local/bin/docker-compose --env-file .env.production up -d
ExecStop=/usr/local/bin/docker-compose --env-file .env.production down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

    if [ "$EUID" -eq 0 ]; then
        cp /tmp/express-tracking.service /etc/systemd/system/
        systemctl daemon-reload
        systemctl enable express-tracking.service
        log_success "systemd服务已创建并启用"
    else
        log_warning "需要root权限创建systemd服务，服务文件已保存到 /tmp/express-tracking.service"
        log_info "请以root权限运行以下命令："
        echo "  sudo cp /tmp/express-tracking.service /etc/systemd/system/"
        echo "  sudo systemctl daemon-reload"
        echo "  sudo systemctl enable express-tracking.service"
    fi
}

# 设置日志轮转
setup_log_rotation() {
    log_info "设置日志轮转..."
    
    cat > /tmp/express-tracking-logrotate << EOF
$(pwd)/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        docker-compose --env-file $(pwd)/.env.production restart app
    endscript
}
EOF

    if [ "$EUID" -eq 0 ]; then
        cp /tmp/express-tracking-logrotate /etc/logrotate.d/express-tracking
        log_success "日志轮转配置已创建"
    else
        log_warning "需要root权限设置日志轮转，配置文件已保存到 /tmp/express-tracking-logrotate"
        log_info "请以root权限运行以下命令："
        echo "  sudo cp /tmp/express-tracking-logrotate /etc/logrotate.d/express-tracking"
    fi
}

# 创建备份定时任务
setup_backup_cron() {
    log_info "设置备份定时任务..."
    
    # 创建备份脚本的cron条目
    CRON_JOB="0 2 * * * $(pwd)/scripts/backup.sh"
    
    # 检查是否已存在
    if crontab -l 2>/dev/null | grep -q "backup.sh"; then
        log_info "备份定时任务已存在"
    else
        (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
        log_success "备份定时任务已创建（每天凌晨2点执行）"
    fi
}

# 主函数
main() {
    log_info "开始生产环境设置..."
    
    setup_production_config
    setup_file_permissions
    optimize_system
    setup_firewall
    create_systemd_service
    setup_log_rotation
    setup_backup_cron
    
    log_success "生产环境设置完成！"
    echo ""
    echo "下一步："
    echo "1. 检查并编辑 .env.production 文件"
    echo "2. 运行 'bash scripts/deploy.sh' 部署应用"
    echo "3. 运行 'bash scripts/deploy.sh monitoring' 部署监控系统"
    echo "4. 配置域名和SSL证书"
    echo "5. 测试所有功能"
    echo ""
}

# 处理命令行参数
case "${1:-}" in
    "config-only")
        setup_production_config
        setup_file_permissions
        ;;
    "system-only")
        optimize_system
        setup_firewall
        create_systemd_service
        setup_log_rotation
        setup_backup_cron
        ;;
    *)
        main
        ;;
esac
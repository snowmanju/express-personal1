#!/bin/bash

# SF Express 快递查询系统 - 阿里云一键部署脚本
# 适用于Ubuntu 22.04 / CentOS 8

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [ "$EUID" -ne 0 ]; then 
        print_error "请使用root用户运行此脚本"
        exit 1
    fi
}

# 检测操作系统
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VERSION=$VERSION_ID
    else
        print_error "无法检测操作系统"
        exit 1
    fi
    
    print_info "检测到操作系统: $OS $VERSION"
}

# 安装Docker
install_docker() {
    print_info "开始安装Docker..."
    
    if command -v docker &> /dev/null; then
        print_warning "Docker已安装，跳过安装步骤"
        return
    fi
    
    if [ "$OS" = "ubuntu" ]; then
        # Ubuntu安装Docker
        apt-get update
        apt-get install -y apt-transport-https ca-certificates curl software-properties-common
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
        add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
        apt-get update
        apt-get install -y docker-ce docker-ce-cli containerd.io
    elif [ "$OS" = "centos" ]; then
        # CentOS安装Docker
        yum install -y yum-utils device-mapper-persistent-data lvm2
        yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
        yum install -y docker-ce docker-ce-cli containerd.io
    else
        print_error "不支持的操作系统: $OS"
        exit 1
    fi
    
    # 启动Docker
    systemctl start docker
    systemctl enable docker
    
    print_success "Docker安装完成"
}

# 安装Docker Compose
install_docker_compose() {
    print_info "开始安装Docker Compose..."
    
    if command -v docker-compose &> /dev/null; then
        print_warning "Docker Compose已安装，跳过安装步骤"
        return
    fi
    
    curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    print_success "Docker Compose安装完成"
}

# 安装Git
install_git() {
    print_info "开始安装Git..."
    
    if command -v git &> /dev/null; then
        print_warning "Git已安装，跳过安装步骤"
        return
    fi
    
    if [ "$OS" = "ubuntu" ]; then
        apt-get install -y git
    elif [ "$OS" = "centos" ]; then
        yum install -y git
    fi
    
    print_success "Git安装完成"
}

# 配置防火墙
configure_firewall() {
    print_info "配置防火墙..."
    
    if [ "$OS" = "ubuntu" ]; then
        # Ubuntu使用ufw
        if command -v ufw &> /dev/null; then
            ufw allow 22/tcp
            ufw allow 80/tcp
            ufw allow 443/tcp
            ufw --force enable
            print_success "防火墙配置完成"
        fi
    elif [ "$OS" = "centos" ]; then
        # CentOS使用firewalld
        if command -v firewall-cmd &> /dev/null; then
            firewall-cmd --permanent --add-service=ssh
            firewall-cmd --permanent --add-service=http
            firewall-cmd --permanent --add-service=https
            firewall-cmd --reload
            print_success "防火墙配置完成"
        fi
    fi
}

# 创建项目目录
create_directories() {
    print_info "创建项目目录..."
    
    PROJECT_DIR="/opt/sf-express"
    
    if [ -d "$PROJECT_DIR" ]; then
        print_warning "项目目录已存在: $PROJECT_DIR"
        read -p "是否删除并重新创建? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$PROJECT_DIR"
        else
            print_error "部署取消"
            exit 1
        fi
    fi
    
    mkdir -p "$PROJECT_DIR"
    mkdir -p "$PROJECT_DIR/uploads"
    mkdir -p "$PROJECT_DIR/logs"
    mkdir -p "$PROJECT_DIR/docker/nginx/ssl"
    
    print_success "项目目录创建完成: $PROJECT_DIR"
}

# 配置环境变量
configure_env() {
    print_info "配置环境变量..."
    
    cd "$PROJECT_DIR"
    
    # 生成随机密钥
    SECRET_KEY=$(openssl rand -base64 32)
    MYSQL_ROOT_PASSWORD=$(openssl rand -base64 16)
    MYSQL_PASSWORD=$(openssl rand -base64 16)
    REDIS_PASSWORD=$(openssl rand -base64 16)
    
    # 创建.env.production文件
    cat > .env.production << EOF
# MySQL配置
MYSQL_ROOT_PASSWORD=$MYSQL_ROOT_PASSWORD
MYSQL_PASSWORD=$MYSQL_PASSWORD

# JWT密钥
SECRET_KEY=$SECRET_KEY

# 快递100 API配置
KUAIDI100_KEY=fypLxFrg3636
KUAIDI100_CUSTOMER=3564B6CF145FA93724CE18C1FB149036
KUAIDI100_SECRET=8fa1052ba57e4d9ca0427938a77e2e30
KUAIDI100_USERID=a1ffc21f3de94cf5bdd908faf3bbc81d

# Redis配置
REDIS_PASSWORD=$REDIS_PASSWORD

# 日志级别
LOG_LEVEL=INFO
EOF
    
    print_success "环境变量配置完成"
    print_info "MySQL Root密码: $MYSQL_ROOT_PASSWORD"
    print_info "MySQL用户密码: $MYSQL_PASSWORD"
    print_info "请妥善保存这些密码！"
    
    # 保存密码到文件
    cat > "$PROJECT_DIR/passwords.txt" << EOF
MySQL Root密码: $MYSQL_ROOT_PASSWORD
MySQL用户密码: $MYSQL_PASSWORD
Redis密码: $REDIS_PASSWORD
Secret Key: $SECRET_KEY
EOF
    chmod 600 "$PROJECT_DIR/passwords.txt"
    print_info "密码已保存到: $PROJECT_DIR/passwords.txt"
}

# 生成SSL证书
generate_ssl() {
    print_info "生成SSL证书（自签名）..."
    
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$PROJECT_DIR/docker/nginx/ssl/key.pem" \
        -out "$PROJECT_DIR/docker/nginx/ssl/cert.pem" \
        -subj "/C=CN/ST=Beijing/L=Beijing/O=SF Express/CN=localhost" \
        2>/dev/null
    
    print_success "SSL证书生成完成"
    print_warning "这是自签名证书，生产环境请使用Let's Encrypt证书"
}

# 启动服务
start_services() {
    print_info "启动服务..."
    
    cd "$PROJECT_DIR"
    
    # 构建并启动
    docker-compose --env-file .env.production up -d --build
    
    print_info "等待服务启动..."
    sleep 30
    
    # 检查服务状态
    docker-compose --env-file .env.production ps
    
    print_success "服务启动完成"
}

# 初始化数据库
init_database() {
    print_info "初始化数据库..."
    
    cd "$PROJECT_DIR"
    
    # 运行数据库迁移
    docker-compose --env-file .env.production exec -T app alembic upgrade head
    
    # 创建管理员账号
    docker-compose --env-file .env.production exec -T app python create_admin_user.py
    
    print_success "数据库初始化完成"
}

# 显示访问信息
show_access_info() {
    SERVER_IP=$(curl -s ifconfig.me)
    
    echo ""
    echo "=========================================="
    echo "  部署完成！"
    echo "=========================================="
    echo ""
    echo "访问地址："
    echo "  前台查询: http://$SERVER_IP"
    echo "  管理后台: http://$SERVER_IP/admin/login.html"
    echo "  API文档:  http://$SERVER_IP:8000/docs"
    echo ""
    echo "默认管理员账号："
    echo "  用户名: admin"
    echo "  密码: admin123"
    echo ""
    echo "重要文件："
    echo "  项目目录: $PROJECT_DIR"
    echo "  密码文件: $PROJECT_DIR/passwords.txt"
    echo "  环境配置: $PROJECT_DIR/.env.production"
    echo ""
    echo "常用命令："
    echo "  查看状态: cd $PROJECT_DIR && docker-compose --env-file .env.production ps"
    echo "  查看日志: cd $PROJECT_DIR && docker-compose --env-file .env.production logs -f"
    echo "  重启服务: cd $PROJECT_DIR && docker-compose --env-file .env.production restart"
    echo "  停止服务: cd $PROJECT_DIR && docker-compose --env-file .env.production down"
    echo ""
    echo "下一步："
    echo "  1. 修改管理员密码"
    echo "  2. 配置域名和SSL证书"
    echo "  3. 设置定期备份"
    echo ""
    echo "=========================================="
}

# 主函数
main() {
    echo ""
    echo "=========================================="
    echo "  SF Express 快递查询系统"
    echo "  阿里云一键部署脚本"
    echo "=========================================="
    echo ""
    
    # 检查root权限
    check_root
    
    # 检测操作系统
    detect_os
    
    # 安装依赖
    install_docker
    install_docker_compose
    install_git
    
    # 配置防火墙
    configure_firewall
    
    # 创建目录
    create_directories
    
    # 配置环境
    configure_env
    
    # 生成SSL证书
    generate_ssl
    
    # 提示上传项目文件
    print_warning "请将项目文件上传到: $PROJECT_DIR"
    print_info "可以使用以下方法："
    print_info "  1. Git: git clone <repository-url> $PROJECT_DIR"
    print_info "  2. SCP: scp -r /local/path/* root@server:$PROJECT_DIR/"
    echo ""
    read -p "项目文件已上传完成? (y/n): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "请先上传项目文件"
        exit 1
    fi
    
    # 启动服务
    start_services
    
    # 初始化数据库
    init_database
    
    # 显示访问信息
    show_access_info
}

# 运行主函数
main

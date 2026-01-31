#!/bin/bash

# 快递查询网站部署脚本
# Express Tracking Website Deployment Script

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
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

# 检查必要的工具
check_requirements() {
    log_info "检查部署要求..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    log_success "部署要求检查通过"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    mkdir -p logs
    mkdir -p uploads
    mkdir -p docker/nginx/ssl
    
    log_success "目录创建完成"
}

# 生成SSL证书（自签名，生产环境应使用真实证书）
generate_ssl_certificates() {
    log_info "生成SSL证书..."
    
    if [ ! -f "docker/nginx/ssl/cert.pem" ] || [ ! -f "docker/nginx/ssl/key.pem" ]; then
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout docker/nginx/ssl/key.pem \
            -out docker/nginx/ssl/cert.pem \
            -subj "/C=CN/ST=Beijing/L=Beijing/O=Express Tracking/CN=localhost"
        
        log_success "SSL证书生成完成"
    else
        log_info "SSL证书已存在，跳过生成"
    fi
}

# 检查环境配置文件
check_env_file() {
    log_info "检查环境配置文件..."
    
    if [ ! -f ".env.production" ]; then
        log_warning ".env.production文件不存在，从模板创建..."
        cp .env.example .env.production
        log_warning "请编辑.env.production文件，设置生产环境配置"
        return 1
    fi
    
    # 检查关键配置项
    if grep -q "your-secret-key-change-in-production" .env.production; then
        log_error "请修改.env.production中的SECRET_KEY为强密钥"
        return 1
    fi
    
    if grep -q "your-strong-root-password-here" .env.production; then
        log_error "请修改.env.production中的数据库密码"
        return 1
    fi
    
    log_success "环境配置文件检查通过"
}

# 构建Docker镜像
build_images() {
    log_info "构建Docker镜像..."
    
    docker-compose --env-file .env.production build --no-cache
    
    log_success "Docker镜像构建完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    # 启动主要服务
    docker-compose --env-file .env.production up -d
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 30
    
    # 检查服务状态
    if docker-compose --env-file .env.production ps | grep -q "Up"; then
        log_success "服务启动成功"
    else
        log_error "服务启动失败"
        docker-compose --env-file .env.production logs
        exit 1
    fi
}

# 运行数据库迁移
run_migrations() {
    log_info "运行数据库迁移..."
    
    # 等待数据库就绪
    log_info "等待数据库就绪..."
    sleep 10
    
    # 运行Alembic迁移
    docker-compose --env-file .env.production exec app alembic upgrade head
    
    log_success "数据库迁移完成"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    # 检查应用健康状态
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log_success "应用健康检查通过"
    else
        log_error "应用健康检查失败"
        return 1
    fi
    
    # 检查数据库连接
    if docker-compose --env-file .env.production exec db mysqladmin ping -h localhost > /dev/null 2>&1; then
        log_success "数据库健康检查通过"
    else
        log_error "数据库健康检查失败"
        return 1
    fi
}

# 显示部署信息
show_deployment_info() {
    log_success "部署完成！"
    echo ""
    echo "服务访问地址："
    echo "  - 前台查询页面: http://localhost"
    echo "  - 后台管理页面: http://localhost/admin"
    echo "  - API文档: http://localhost:8000/docs"
    echo "  - 健康检查: http://localhost:8000/health"
    echo ""
    echo "管理命令："
    echo "  - 查看日志: docker-compose --env-file .env.production logs -f"
    echo "  - 停止服务: docker-compose --env-file .env.production down"
    echo "  - 重启服务: docker-compose --env-file .env.production restart"
    echo ""
}

# 主函数
main() {
    log_info "开始部署快递查询网站..."
    
    check_requirements
    create_directories
    generate_ssl_certificates
    
    if ! check_env_file; then
        log_error "请先配置环境文件后再运行部署脚本"
        exit 1
    fi
    
    build_images
    start_services
    run_migrations
    
    if health_check; then
        show_deployment_info
    else
        log_error "部署验证失败，请检查日志"
        exit 1
    fi
}

# 处理命令行参数
case "${1:-}" in
    "dev")
        log_info "启动开发环境..."
        docker-compose -f docker-compose.dev.yml up -d
        ;;
    "monitoring")
        log_info "启动监控服务..."
        docker-compose -f docker-compose.monitoring.yml --env-file .env.production up -d
        ;;
    "stop")
        log_info "停止所有服务..."
        docker-compose --env-file .env.production down
        docker-compose -f docker-compose.monitoring.yml down
        ;;
    "logs")
        docker-compose --env-file .env.production logs -f
        ;;
    *)
        main
        ;;
esac
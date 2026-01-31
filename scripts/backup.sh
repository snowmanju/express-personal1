#!/bin/bash

# 快递查询网站备份脚本
# Express Tracking Website Backup Script

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
BACKUP_DIR="backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="express_tracking_backup_${DATE}"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 创建备份目录
create_backup_dir() {
    log_info "创建备份目录..."
    mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}"
}

# 备份数据库
backup_database() {
    log_info "备份数据库..."
    
    docker-compose --env-file .env.production exec -T db mysqldump \
        -u root -p${MYSQL_ROOT_PASSWORD} \
        --single-transaction \
        --routines \
        --triggers \
        express_tracking > "${BACKUP_DIR}/${BACKUP_NAME}/database.sql"
    
    log_success "数据库备份完成"
}

# 备份上传文件
backup_uploads() {
    log_info "备份上传文件..."
    
    if [ -d "uploads" ]; then
        cp -r uploads "${BACKUP_DIR}/${BACKUP_NAME}/"
        log_success "上传文件备份完成"
    else
        log_info "上传目录不存在，跳过"
    fi
}

# 备份配置文件
backup_config() {
    log_info "备份配置文件..."
    
    cp .env.production "${BACKUP_DIR}/${BACKUP_NAME}/"
    cp docker-compose.yml "${BACKUP_DIR}/${BACKUP_NAME}/"
    
    if [ -d "docker/nginx/ssl" ]; then
        mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}/ssl"
        cp docker/nginx/ssl/* "${BACKUP_DIR}/${BACKUP_NAME}/ssl/"
    fi
    
    log_success "配置文件备份完成"
}

# 压缩备份
compress_backup() {
    log_info "压缩备份文件..."
    
    cd "${BACKUP_DIR}"
    tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}"
    rm -rf "${BACKUP_NAME}"
    cd ..
    
    log_success "备份压缩完成: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
}

# 清理旧备份（保留最近7个）
cleanup_old_backups() {
    log_info "清理旧备份..."
    
    cd "${BACKUP_DIR}"
    ls -t *.tar.gz | tail -n +8 | xargs -r rm --
    cd ..
    
    log_success "旧备份清理完成"
}

# 主函数
main() {
    log_info "开始备份快递查询网站..."
    
    create_backup_dir
    backup_database
    backup_uploads
    backup_config
    compress_backup
    cleanup_old_backups
    
    log_success "备份完成！"
}

# 恢复功能
restore() {
    local backup_file=$1
    
    if [ -z "$backup_file" ]; then
        log_error "请指定备份文件"
        echo "用法: $0 restore <backup_file.tar.gz>"
        exit 1
    fi
    
    log_info "开始恢复备份: $backup_file"
    
    # 解压备份
    tar -xzf "$backup_file" -C /tmp/
    backup_name=$(basename "$backup_file" .tar.gz)
    
    # 恢复数据库
    log_info "恢复数据库..."
    docker-compose --env-file .env.production exec -T db mysql \
        -u root -p${MYSQL_ROOT_PASSWORD} \
        express_tracking < "/tmp/${backup_name}/database.sql"
    
    # 恢复上传文件
    if [ -d "/tmp/${backup_name}/uploads" ]; then
        log_info "恢复上传文件..."
        rm -rf uploads
        cp -r "/tmp/${backup_name}/uploads" .
    fi
    
    # 清理临时文件
    rm -rf "/tmp/${backup_name}"
    
    log_success "备份恢复完成！"
}

# 处理命令行参数
case "${1:-}" in
    "restore")
        restore "$2"
        ;;
    *)
        main
        ;;
esac
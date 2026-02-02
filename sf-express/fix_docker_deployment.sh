#!/bin/bash

# Docker部署自动修复脚本
# 用途：修复psutil缺失和SSL证书缺失问题

set -e  # 遇到错误立即退出

echo "=========================================="
echo "  Docker部署自动修复脚本"
echo "=========================================="
echo ""

# 检查是否在正确的目录
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 错误：未找到 docker-compose.yml 文件"
    echo "请确保在项目根目录运行此脚本"
    exit 1
fi

echo "✅ 找到项目目录"
echo ""

# 步骤1: 检查并添加psutil到requirements.txt
echo "步骤1: 检查 requirements.txt..."
if grep -q "psutil" requirements.txt; then
    echo "✅ psutil 已存在于 requirements.txt"
else
    echo "📝 添加 psutil==5.9.6 到 requirements.txt..."
    echo "psutil==5.9.6" >> requirements.txt
    echo "✅ 已添加 psutil"
fi
echo ""

# 步骤2: 创建SSL目录
echo "步骤2: 创建SSL证书目录..."
mkdir -p docker/nginx/ssl
echo "✅ SSL目录已创建"
echo ""

# 步骤3: 生成SSL证书
echo "步骤3: 检查SSL证书..."
if [ -f "docker/nginx/ssl/cert.pem" ] && [ -f "docker/nginx/ssl/key.pem" ]; then
    echo "✅ SSL证书已存在"
    echo "如需重新生成，请先删除现有证书文件"
else
    echo "🔐 生成自签名SSL证书..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout docker/nginx/ssl/key.pem \
        -out docker/nginx/ssl/cert.pem \
        -subj "/C=CN/ST=Beijing/L=Beijing/O=SF Express/CN=localhost" \
        2>/dev/null
    
    # 设置证书权限
    chmod 600 docker/nginx/ssl/*.pem
    echo "✅ SSL证书已生成"
fi
echo ""

# 步骤4: 验证证书文件
echo "步骤4: 验证证书文件..."
if [ -f "docker/nginx/ssl/cert.pem" ] && [ -f "docker/nginx/ssl/key.pem" ]; then
    echo "✅ 证书文件验证成功"
    ls -lh docker/nginx/ssl/
else
    echo "❌ 证书文件验证失败"
    exit 1
fi
echo ""

# 步骤5: 停止现有服务
echo "步骤5: 停止现有Docker服务..."
if docker-compose --env-file .env.production ps | grep -q "Up"; then
    docker-compose --env-file .env.production down
    echo "✅ 服务已停止"
else
    echo "ℹ️  没有运行中的服务"
fi
echo ""

# 步骤6: 清理旧容器和镜像（可选）
echo "步骤6: 清理旧容器..."
docker-compose --env-file .env.production rm -f 2>/dev/null || true
echo "✅ 清理完成"
echo ""

# 步骤7: 重新构建镜像
echo "步骤7: 重新构建Docker镜像（这可能需要几分钟）..."
docker-compose --env-file .env.production build --no-cache
echo "✅ 镜像构建完成"
echo ""

# 步骤8: 启动服务
echo "步骤8: 启动Docker服务..."
docker-compose --env-file .env.production up -d
echo "✅ 服务已启动"
echo ""

# 步骤9: 等待服务启动
echo "步骤9: 等待服务启动（30秒）..."
for i in {1..30}; do
    echo -n "."
    sleep 1
done
echo ""
echo "✅ 等待完成"
echo ""

# 步骤10: 检查服务状态
echo "步骤10: 检查服务状态..."
echo ""
docker-compose --env-file .env.production ps
echo ""

# 步骤11: 检查容器健康状态
echo "步骤11: 检查容器健康状态..."
echo ""

# 检查应用容器
if docker ps | grep -q "express-tracking-app.*Up"; then
    echo "✅ 应用容器运行正常"
else
    echo "❌ 应用容器未运行"
    echo "查看日志: docker-compose --env-file .env.production logs app"
fi

# 检查数据库容器
if docker ps | grep -q "express-tracking-db.*Up"; then
    echo "✅ 数据库容器运行正常"
else
    echo "❌ 数据库容器未运行"
    echo "查看日志: docker-compose --env-file .env.production logs db"
fi

# 检查Nginx容器
if docker ps | grep -q "express-tracking-nginx.*Up"; then
    echo "✅ Nginx容器运行正常"
else
    echo "❌ Nginx容器未运行"
    echo "查看日志: docker-compose --env-file .env.production logs nginx"
fi

# 检查Redis容器
if docker ps | grep -q "express-tracking-redis.*Up"; then
    echo "✅ Redis容器运行正常"
else
    echo "⚠️  Redis容器未运行（可选服务）"
fi

echo ""

# 步骤12: 测试应用访问
echo "步骤12: 测试应用访问..."
echo ""

# 等待几秒让应用完全启动
sleep 5

# 测试健康检查端点
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 应用健康检查通过"
    echo "   访问地址: http://localhost:8000/health"
else
    echo "⚠️  应用健康检查失败（应用可能还在启动中）"
    echo "   请稍后手动测试: curl http://localhost:8000/health"
fi

# 测试前端访问
if curl -s http://localhost > /dev/null 2>&1; then
    echo "✅ 前端页面可访问"
    echo "   访问地址: http://localhost"
else
    echo "⚠️  前端页面访问失败"
    echo "   请检查Nginx配置"
fi

echo ""
echo "=========================================="
echo "  修复完成！"
echo "=========================================="
echo ""
echo "📋 后续步骤："
echo ""
echo "1. 查看所有日志："
echo "   docker-compose --env-file .env.production logs"
echo ""
echo "2. 查看特定服务日志："
echo "   docker-compose --env-file .env.production logs app"
echo "   docker-compose --env-file .env.production logs nginx"
echo "   docker-compose --env-file .env.production logs db"
echo ""
echo "3. 实时查看日志："
echo "   docker-compose --env-file .env.production logs -f"
echo ""
echo "4. 访问应用："
echo "   前端: http://your-server-ip"
echo "   API: http://your-server-ip:8000"
echo "   管理后台: http://your-server-ip/admin/login.html"
echo ""
echo "5. 如果还有问题，请查看详细日志并检查配置文件"
echo ""
echo "=========================================="

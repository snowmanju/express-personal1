-- MySQL初始化脚本
-- 创建数据库和用户

-- 设置字符集
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS express_tracking 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE express_tracking;

-- 创建应用用户（如果不存在）
CREATE USER IF NOT EXISTS 'express_user'@'%' IDENTIFIED BY 'express_password';

-- 授予权限
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER ON express_tracking.* TO 'express_user'@'%';

-- 刷新权限
FLUSH PRIVILEGES;

-- 创建基础表结构（如果Alembic迁移未运行）
-- 这些表会被Alembic管理，这里只是备用

-- 理货单表
CREATE TABLE IF NOT EXISTS cargo_manifest (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    tracking_number VARCHAR(50) NOT NULL UNIQUE,
    manifest_date DATE NOT NULL,
    transport_code VARCHAR(20) NOT NULL,
    customer_code VARCHAR(20) NOT NULL,
    goods_code VARCHAR(20) NOT NULL,
    package_number VARCHAR(50),
    weight DECIMAL(10,3),
    length DECIMAL(8,2),
    width DECIMAL(8,2),
    height DECIMAL(8,2),
    special_fee DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_tracking_number (tracking_number),
    INDEX idx_package_number (package_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 管理员用户表
CREATE TABLE IF NOT EXISTS admin_users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- API配置表
CREATE TABLE IF NOT EXISTS api_config (
    id INT PRIMARY KEY AUTO_INCREMENT,
    config_key VARCHAR(50) NOT NULL UNIQUE,
    config_value VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_config_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入默认API配置
INSERT IGNORE INTO api_config (config_key, config_value, description) VALUES
('kuaidi100_key', 'fypLxFrg3636', '快递100 API授权key'),
('kuaidi100_customer', '3564B6CF145FA93724CE18C1FB149036', '快递100客户标识'),
('kuaidi100_secret', '8fa1052ba57e4d9ca0427938a77e2e30', '快递100密钥'),
('kuaidi100_userid', 'a1ffc21f3de94cf5bdd908faf3bbc81d', '快递100用户ID');

-- 创建默认管理员用户（密码: admin123）
-- 注意：生产环境中应该修改默认密码
INSERT IGNORE INTO admin_users (username, password_hash) VALUES
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6QJb.2Qe4W');
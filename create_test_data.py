"""
创建测试数据文件
用于测试CSV上传功能
"""

import csv
from datetime import datetime, timedelta
import random

def create_valid_test_file(filename='test_valid.csv', rows=10):
    """创建有效的测试数据文件"""
    print(f"创建有效测试文件: {filename} ({rows}行)")
    
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        # 写入标题行
        writer.writerow([
            '理货日期', '快递单号', '集包单号', '长度', '宽度', 
            '高度', '重量', '货物代码', '客户代码', '运输代码'
        ])
        
        # 写入数据行
        base_date = datetime.now()
        for i in range(rows):
            date = (base_date - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d')
            tracking = f'TEST{i:08d}'
            package = f'PKG{i:05d}'
            length = round(random.uniform(10, 100), 2)
            width = round(random.uniform(10, 80), 2)
            height = round(random.uniform(5, 50), 2)
            weight = round(random.uniform(0.5, 30), 2)
            goods_code = f'G{random.randint(1, 10):03d}'
            customer_code = f'C{random.randint(1, 20):03d}'
            transport_code = f'T{random.randint(1, 5):03d}'
            
            writer.writerow([
                date, tracking, package, length, width, 
                height, weight, goods_code, customer_code, transport_code
            ])
    
    print(f"✓ 创建成功: {filename}")
    return filename


def create_invalid_test_file(filename='test_invalid.csv'):
    """创建包含无效数据的测试文件"""
    print(f"创建无效数据测试文件: {filename}")
    
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow([
            '理货日期', '快递单号', '集包单号', '长度', '宽度', 
            '高度', '重量', '货物代码', '客户代码', '运输代码'
        ])
        
        # 有效行
        writer.writerow([
            '2024-01-01', 'VALID001', 'PKG001', 30, 20, 10, 5.5, 'G001', 'C001', 'T001'
        ])
        
        # 缺少必填字段（快递单号为空）
        writer.writerow([
            '2024-01-02', '', 'PKG002', 30, 20, 10, 5.5, 'G001', 'C001', 'T001'
        ])
        
        # 无效的数值（长度为负数）
        writer.writerow([
            '2024-01-03', 'INVALID003', 'PKG003', -30, 20, 10, 5.5, 'G001', 'C001', 'T001'
        ])
        
        # 无效的日期格式
        writer.writerow([
            'invalid-date', 'INVALID004', 'PKG004', 30, 20, 10, 5.5, 'G001', 'C001', 'T001'
        ])
        
        # 缺少必填字段（运输代码为空）
        writer.writerow([
            '2024-01-05', 'INVALID005', 'PKG005', 30, 20, 10, 5.5, 'G001', 'C001', ''
        ])
    
    print(f"✓ 创建成功: {filename}")
    return filename


def create_large_test_file(filename='test_large.csv', rows=1000):
    """创建大量数据的测试文件"""
    print(f"创建大文件测试: {filename} ({rows}行)")
    print("这可能需要几秒钟...")
    
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow([
            '理货日期', '快递单号', '集包单号', '长度', '宽度', 
            '高度', '重量', '货物代码', '客户代码', '运输代码'
        ])
        
        base_date = datetime.now()
        for i in range(rows):
            if i % 100 == 0:
                print(f"  进度: {i}/{rows}")
            
            date = (base_date - timedelta(days=i % 365)).strftime('%Y-%m-%d')
            tracking = f'LARGE{i:08d}'
            package = f'PKG{i:05d}'
            length = round(random.uniform(10, 100), 2)
            width = round(random.uniform(10, 80), 2)
            height = round(random.uniform(5, 50), 2)
            weight = round(random.uniform(0.5, 30), 2)
            goods_code = f'G{random.randint(1, 10):03d}'
            customer_code = f'C{random.randint(1, 20):03d}'
            transport_code = f'T{random.randint(1, 5):03d}'
            
            writer.writerow([
                date, tracking, package, length, width, 
                height, weight, goods_code, customer_code, transport_code
            ])
    
    print(f"✓ 创建成功: {filename}")
    return filename


def create_chinese_test_file(filename='test_chinese.csv'):
    """创建包含中文数据的测试文件"""
    print(f"创建中文数据测试文件: {filename}")
    
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow([
            '理货日期', '快递单号', '集包单号', '长度', '宽度', 
            '高度', '重量', '货物代码', '客户代码', '运输代码'
        ])
        
        # 中文货物代码和客户代码
        writer.writerow([
            '2024-01-01', 'CN001', '包裹001', 30, 20, 10, 5.5, '电子产品', '北京客户', '顺丰快递'
        ])
        
        writer.writerow([
            '2024-01-02', 'CN002', '包裹002', 40, 30, 15, 8.0, '服装鞋帽', '上海客户', '圆通快递'
        ])
        
        writer.writerow([
            '2024-01-03', 'CN003', '包裹003', 25, 15, 8, 3.5, '食品饮料', '广州客户', '中通快递'
        ])
    
    print(f"✓ 创建成功: {filename}")
    return filename


def create_duplicate_test_file(filename='test_duplicate.csv'):
    """创建包含重复快递单号的测试文件"""
    print(f"创建重复数据测试文件: {filename}")
    
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow([
            '理货日期', '快递单号', '集包单号', '长度', '宽度', 
            '高度', '重量', '货物代码', '客户代码', '运输代码'
        ])
        
        # 第一次出现
        writer.writerow([
            '2024-01-01', 'DUP001', 'PKG001', 30, 20, 10, 5.5, 'G001', 'C001', 'T001'
        ])
        
        # 重复的快递单号（应该更新而不是插入）
        writer.writerow([
            '2024-01-02', 'DUP001', 'PKG002', 35, 25, 12, 6.0, 'G002', 'C002', 'T002'
        ])
        
        # 另一个唯一的
        writer.writerow([
            '2024-01-03', 'DUP002', 'PKG003', 40, 30, 15, 7.5, 'G003', 'C003', 'T003'
        ])
    
    print(f"✓ 创建成功: {filename}")
    return filename


def main():
    """主函数"""
    print("=" * 60)
    print("CSV测试数据生成器")
    print("=" * 60)
    print()
    
    print("选择要创建的测试文件:")
    print("1. 小量有效数据 (10行)")
    print("2. 中量有效数据 (100行)")
    print("3. 大量有效数据 (1000行)")
    print("4. 包含无效数据的文件")
    print("5. 包含中文数据的文件")
    print("6. 包含重复数据的文件")
    print("7. 创建所有测试文件")
    print("0. 退出")
    print()
    
    choice = input("请输入选项 (0-7): ").strip()
    print()
    
    if choice == '1':
        create_valid_test_file('test_valid_10.csv', 10)
    elif choice == '2':
        create_valid_test_file('test_valid_100.csv', 100)
    elif choice == '3':
        create_large_test_file('test_large_1000.csv', 1000)
    elif choice == '4':
        create_invalid_test_file('test_invalid.csv')
    elif choice == '5':
        create_chinese_test_file('test_chinese.csv')
    elif choice == '6':
        create_duplicate_test_file('test_duplicate.csv')
    elif choice == '7':
        print("创建所有测试文件...")
        print()
        create_valid_test_file('test_valid_10.csv', 10)
        print()
        create_valid_test_file('test_valid_100.csv', 100)
        print()
        create_large_test_file('test_large_1000.csv', 1000)
        print()
        create_invalid_test_file('test_invalid.csv')
        print()
        create_chinese_test_file('test_chinese.csv')
        print()
        create_duplicate_test_file('test_duplicate.csv')
    elif choice == '0':
        print("退出")
        return
    else:
        print("❌ 无效的选项")
        return
    
    print()
    print("=" * 60)
    print("✓ 测试文件创建完成！")
    print()
    print("使用方法:")
    print("1. 启动服务器: python run.py")
    print("2. 登录管理后台: http://localhost:8000/admin/login.html")
    print("3. 在文件上传页面选择生成的测试文件")
    print("4. 测试预览和保存功能")
    print("=" * 60)


if __name__ == '__main__':
    main()

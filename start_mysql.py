"""
查找并启动MySQL服务
"""

import subprocess
import sys

print("=" * 60)
print("查找MySQL服务...")
print("=" * 60)
print()

# 查找MySQL服务
try:
    result = subprocess.run(
        ['powershell', '-Command', 'Get-Service | Where-Object {$_.Name -like "*mysql*" -or $_.DisplayName -like "*mysql*"} | Select-Object Name, DisplayName, Status | Format-Table -AutoSize'],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    if result.stdout:
        print("找到的MySQL服务:")
        print(result.stdout)
        
        # 提取服务名
        lines = result.stdout.strip().split('\n')
        if len(lines) > 2:  # 跳过表头
            for line in lines[2:]:
                parts = line.split()
                if parts:
                    service_name = parts[0]
                    print(f"\n尝试启动服务: {service_name}")
                    
                    try:
                        start_result = subprocess.run(
                            ['net', 'start', service_name],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        
                        if start_result.returncode == 0:
                            print(f"✓ 服务 {service_name} 启动成功！")
                            sys.exit(0)
                        else:
                            error_msg = start_result.stderr or start_result.stdout
                            if '已经启动' in error_msg or 'already' in error_msg.lower():
                                print(f"✓ 服务 {service_name} 已经在运行")
                                sys.exit(0)
                            else:
                                print(f"⚠ 启动失败: {error_msg}")
                    except Exception as e:
                        print(f"⚠ 启动出错: {e}")
    else:
        print("✗ 未找到MySQL服务")
        print()
        print("可能的原因:")
        print("1. MySQL未安装")
        print("2. MySQL服务名称不同")
        print()
        print("解决方案:")
        print("1. 打开服务管理器 (Win+R 输入 services.msc)")
        print("2. 查找MySQL相关服务")
        print("3. 右键点击 -> 启动")
        
except subprocess.TimeoutExpired:
    print("✗ 查询超时")
except Exception as e:
    print(f"✗ 查询失败: {e}")

print()
print("=" * 60)
print("如果MySQL服务无法启动，请:")
print("1. 打开服务管理器: Win+R 输入 services.msc")
print("2. 找到MySQL服务并手动启动")
print("3. 或者重新安装MySQL")
print("=" * 60)

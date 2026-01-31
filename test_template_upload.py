"""
测试理货单模板上传
"""
import requests
import os

def test_template_upload():
    """测试上传模板文件"""
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("测试理货单模板上传")
    print("=" * 60)
    
    # 1. 登录获取token
    print("\n1. 登录获取Token...")
    login_response = requests.post(
        f"{base_url}/api/v1/admin/login",
        json={"username": "admin", "password": "admin123"}
    )
    
    if login_response.status_code != 200:
        print(f"   ✗ 登录失败: {login_response.status_code}")
        return
    
    token = login_response.json()["access_token"]
    print(f"   ✓ 登录成功，获取Token")
    
    # 2. 测试上传模板文件
    print("\n2. 测试上传模板文件...")
    template_path = "static/templates/理货单上传模板.csv"
    
    if not os.path.exists(template_path):
        print(f"   ✗ 模板文件不存在: {template_path}")
        return
    
    print(f"   模板文件: {template_path}")
    
    # 读取文件
    with open(template_path, 'rb') as f:
        file_content = f.read()
    
    print(f"   文件大小: {len(file_content)} 字节")
    
    # 显示文件内容（前200字符）
    print(f"   文件内容预览:")
    print(f"   {file_content[:200].decode('utf-8', errors='ignore')}")
    
    # 3. 上传文件（预览模式）
    print("\n3. 上传文件（预览模式）...")
    
    files = {
        'file': ('理货单上传模板.csv', file_content, 'text/csv')
    }
    data = {
        'preview_only': 'true'
    }
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    upload_response = requests.post(
        f"{base_url}/api/v1/admin/manifest/upload",
        files=files,
        data=data,
        headers=headers
    )
    
    print(f"   响应状态码: {upload_response.status_code}")
    
    if upload_response.status_code == 200:
        result = upload_response.json()
        print(f"   ✓ 上传成功！")
        print(f"\n   上传结果:")
        print(f"   - 成功: {result.get('success')}")
        print(f"   - 总行数: {result.get('statistics', {}).get('total_rows', 0)}")
        print(f"   - 有效行数: {result.get('statistics', {}).get('valid_rows', 0)}")
        print(f"   - 错误行数: {result.get('statistics', {}).get('invalid_rows', 0)}")
        
        if result.get('preview_data'):
            print(f"\n   预览数据（前3行）:")
            for i, row in enumerate(result['preview_data'][:3], 1):
                print(f"   行 {row['row_number']}: {row['data']}")
                if not row['valid']:
                    print(f"      错误: {row.get('errors', [])}")
    else:
        print(f"   ✗ 上传失败")
        try:
            error = upload_response.json()
            print(f"   错误详情: {error}")
        except:
            print(f"   响应内容: {upload_response.text}")
    
    # 4. 测试实际保存
    print("\n4. 测试实际保存...")
    
    files = {
        'file': ('理货单上传模板.csv', file_content, 'text/csv')
    }
    data = {
        'preview_only': 'false'
    }
    
    upload_response = requests.post(
        f"{base_url}/api/v1/admin/manifest/upload",
        files=files,
        data=data,
        headers=headers
    )
    
    print(f"   响应状态码: {upload_response.status_code}")
    
    if upload_response.status_code == 200:
        result = upload_response.json()
        print(f"   ✓ 保存成功！")
        print(f"\n   保存结果:")
        print(f"   - 插入: {result.get('statistics', {}).get('inserted', 0)}")
        print(f"   - 更新: {result.get('statistics', {}).get('updated', 0)}")
        print(f"   - 跳过: {result.get('statistics', {}).get('skipped', 0)}")
    else:
        print(f"   ✗ 保存失败")
        try:
            error = upload_response.json()
            print(f"   错误详情: {error}")
        except:
            print(f"   响应内容: {upload_response.text}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_template_upload()

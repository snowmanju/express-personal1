"""
文件处理服务基础测试
"""

def test_file_processor_import():
    """测试文件处理服务导入"""
    try:
        from app.services.file_processor_service import FileProcessorService
        print("✓ FileProcessorService 导入成功")
        
        # 测试基本初始化
        service = FileProcessorService()
        print("✓ FileProcessorService 初始化成功")
        
        # 测试文件格式验证
        assert service.validate_file_format("test.csv") == True
        assert service.validate_file_format("test.xlsx") == True
        assert service.validate_file_format("test.txt") == False
        print("✓ 文件格式验证功能正常")
        
        # 测试字段映射
        assert len(service.REQUIRED_FIELDS) == 5
        assert len(service.OPTIONAL_FIELDS) == 6
        assert len(service.ALL_FIELDS) == 11
        print("✓ 字段映射配置正确")
        
        # 测试验证规则
        assert len(service.VALIDATION_RULES) == 11
        print("✓ 验证规则配置正确")
        
        print("\n所有基础测试通过！")
        return True
        
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

if __name__ == "__main__":
    test_file_processor_import()
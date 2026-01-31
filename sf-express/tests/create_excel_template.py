"""
创建Excel格式的理货单模板
"""
import pandas as pd

def create_excel_template():
    """创建Excel模板"""
    
    # 创建示例数据
    data = {
        '理货日期': ['2024-01-26', '2024-01-26', '2024-01-26'],
        '快递单号': ['YT1234567890', 'ZT9876543210', 'SF3456789012'],
        '集包单号': ['PKG001', 'PKG002', 'PKG003'],
        '长度': [20.5, 25.0, 15.0],
        '宽度': [15.0, 20.0, 10.0],
        '高度': [10.0, 15.0, 8.0],
        '重量': [1.5, 2.0, 0.8],
        '货物代码': ['GOODS001', 'GOODS002', 'GOODS003'],
        '客户代码': ['CUST001', 'CUST002', 'CUST003'],
        '运输代码': ['TRANS001', 'TRANS002', 'TRANS003']
    }
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 保存为Excel
    output_path = 'static/templates/理货单上传模板.xlsx'
    df.to_excel(output_path, index=False, engine='openpyxl')
    
    print(f"✓ Excel模板已创建: {output_path}")
    print(f"  行数: {len(df)}")
    print(f"  列数: {len(df.columns)}")
    print(f"\n列名:")
    for col in df.columns:
        print(f"  - {col}")

if __name__ == "__main__":
    try:
        create_excel_template()
    except ImportError as e:
        print("错误：需要安装openpyxl库")
        print("请运行：pip install openpyxl")
    except Exception as e:
        print(f"错误：{str(e)}")

# 输入验证器 (Input Validator)

## 概述

输入验证器是一个综合性的输入验证和安全过滤服务，提供快递单号格式验证、输入清理和安全防护功能。该模块实现了需求 1.5、6.1 和 6.5 中规定的输入验证和安全要求。

## 主要功能

### 1. 快递单号验证
- 支持多种快递公司的单号格式验证
- 包括顺丰、EMS、圆通、申通、中通、韵达、京东、中国邮政等
- 通用格式验证（6-30位字母数字组合）

### 2. 安全过滤
- SQL注入攻击检测和防护
- XSS（跨站脚本）攻击检测和防护
- 恶意字符过滤
- 输入长度限制

### 3. 输入清理
- HTML实体转义
- 控制字符移除
- 空白字符处理
- 空字节移除

### 4. 文件上传验证
- 文件名安全验证
- 文件扩展名检查
- 文件大小限制
- 路径遍历攻击防护

## 使用方法

### 基本使用

```python
from app.services.input_validator import validate_tracking_number, validate_and_clean_input

# 验证快递单号
result = validate_tracking_number("SF1234567890123")
if result.is_valid:
    print(f"验证通过，清理后的值: {result.cleaned_value}")
else:
    print(f"验证失败，错误: {result.errors}")

# 通用输入验证
result = validate_and_clean_input("用户输入", "字段名")
if result.is_valid:
    print(f"输入安全，清理后的值: {result.cleaned_value}")
else:
    print(f"输入不安全，错误: {result.errors}")
```

### 在API中使用

```python
from fastapi import HTTPException
from app.services.input_validator import validate_tracking_number

@app.post("/api/tracking/query")
async def query_tracking(tracking_number: str):
    # 验证输入
    validation_result = validate_tracking_number(tracking_number)
    if not validation_result.is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"输入验证失败: {'; '.join(validation_result.errors)}"
        )
    
    # 使用清理后的值
    cleaned_number = validation_result.cleaned_value
    # ... 继续处理
```

### 文件上传验证

```python
from app.services.input_validator import InputValidator

validator = InputValidator()
result = validator.validate_file_upload(
    filename="manifest.csv",
    file_size=1024000,  # 1MB
    allowed_extensions=["csv", "xlsx", "xls"]
)

if result.is_valid:
    print(f"文件验证通过: {result.cleaned_value}")
else:
    print(f"文件验证失败: {result.errors}")
```

## 支持的快递单号格式

| 快递公司 | 格式模式 | 示例 |
|---------|---------|------|
| 顺丰速运 | SF + 12位数字 | SF123456789012 |
| EMS | 2字母 + 9数字 + 2字母 | EA123456789CN |
| 圆通速递 | YT + 13位数字 | YT1234567890123 |
| 申通快递 | STO + 12位数字 | STO123456789012 |
| 中通快递 | ZTO + 12位数字 | ZTO123456789012 |
| 韵达快递 | YD + 13位数字 | YD1234567890123 |
| 京东快递 | JD + 15位数字 | JD123456789012345 |
| 中国邮政 | 13位数字 | 1234567890123 |
| 通用格式 | 6-30位字母数字 | ABC123456789 |

## 安全防护功能

### SQL注入防护
检测并阻止以下模式：
- SQL关键字（SELECT, INSERT, UPDATE, DELETE等）
- SQL注释符（--, #, /* */）
- 逻辑操作符组合（OR...=...OR, AND...=...AND）
- 字符串引号（单引号、双引号）
- 系统存储过程（xp_cmdshell, sp_executesql）

### XSS防护
检测并阻止以下模式：
- Script标签
- Iframe标签
- Object和Embed标签
- Link和Meta标签
- JavaScript和VBScript协议
- 事件处理器（onload, onerror, onclick等）

### 输入清理
- HTML实体转义（< > & " '）
- 移除空字节（\x00）
- 移除控制字符（除换行符和制表符外）
- 去除首尾空白字符

## 错误处理

验证结果通过 `ValidationResult` 对象返回：

```python
@dataclass
class ValidationResult:
    is_valid: bool                    # 验证是否通过
    cleaned_value: Optional[str]      # 清理后的值
    errors: List[str]                 # 错误信息列表
```

常见错误信息：
- "快递单号不能为空"
- "快递单号长度不能少于6位"
- "快递单号长度不能超过30位"
- "快递单号只能包含字母和数字"
- "输入包含可疑的SQL代码"
- "输入包含可疑的脚本代码"
- "输入包含不允许的特殊字符"
- "输入长度超出限制"

## 性能考虑

- 使用预编译的正则表达式提高匹配性能
- 输入长度限制防止DoS攻击
- 批量验证时建议分批处理
- 缓存验证结果以提高重复查询性能

## 配置选项

可以通过修改 `InputValidator` 类的常量来调整验证规则：

```python
# 修改最大输入长度
MAX_INPUT_LENGTH = 1000

# 添加新的快递公司格式
TRACKING_PATTERNS['new_company'] = r'^NC\d{10}$'

# 添加新的安全检测模式
SQL_INJECTION_PATTERNS.append(r'new_pattern')
```

## 集成示例

### 与智能查询服务集成

输入验证器已经集成到 `IntelligentQueryService` 中：

```python
# 在查询前自动验证输入
result = await query_service.query_tracking("SF1234567890123")
# 验证失败时会在结果中包含错误信息
```

### 与API端点集成

```python
# 在API层面进行额外验证
@router.post("/query")
async def query_tracking(request: TrackingQueryRequest):
    # 输入验证在服务层已处理
    # API层可以进行额外的业务逻辑验证
    pass
```

## 测试

运行测试以验证功能：

```bash
# 运行基本功能测试
python test_input_validator.py

# 运行集成测试
python test_input_validation_integration.py

# 运行完整测试套件
python -m pytest test_input_validator.py -v
```

## 日志记录

输入验证器会记录以下事件：
- 安全验证失败（WARNING级别）
- 验证错误（INFO级别）
- 系统异常（ERROR级别）

日志格式示例：
```
2024-01-01 10:00:00 WARNING Security validation failed for input: <script>al...
2024-01-01 10:00:01 INFO 快递单号验证通过: SF1234567890123
```

## 扩展性

### 添加新的快递公司格式

```python
# 在TRACKING_PATTERNS中添加新格式
TRACKING_PATTERNS['custom_express'] = r'^CE\d{8}$'
```

### 添加新的安全检测规则

```python
# 添加新的SQL注入模式
SQL_INJECTION_PATTERNS.append(r'new_sql_pattern')

# 添加新的XSS模式
XSS_PATTERNS.append(r'new_xss_pattern')
```

### 自定义验证逻辑

```python
class CustomValidator(InputValidator):
    def custom_validation(self, input_str: str) -> ValidationResult:
        # 实现自定义验证逻辑
        pass
```

## 最佳实践

1. **始终验证用户输入**：在处理任何用户输入前都应进行验证
2. **使用清理后的值**：验证通过后使用 `cleaned_value` 而不是原始输入
3. **记录安全事件**：记录所有安全验证失败的事件用于监控
4. **定期更新规则**：根据新的安全威胁更新检测规则
5. **分层验证**：在API层和服务层都进行适当的验证
6. **用户友好的错误信息**：提供清晰的错误信息帮助用户纠正输入

## 相关需求

该模块实现了以下需求：

- **需求 1.5**：当用户输入无效或空白快递单号时，快递查询系统应阻止查询请求并显示错误提示信息
- **需求 6.1**：当接收用户输入时，快递查询系统应验证快递单号格式的有效性
- **需求 6.5**：当系统处理请求时，快递查询系统应实施输入清理以防止安全漏洞
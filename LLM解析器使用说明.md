# LLM解析器使用说明

## 概述

LLM解析器是MAGIC到UNIPIC转译系统的重要组成部分，专门用于解析复杂的MAGIC MCL命令。它采用按命令类型分组的批量解析策略，提高解析准确性和效率。

## 核心特性

### 1. 按命令类型分组解析
- 将同类型的命令分组处理，避免不同命令类型之间的干扰
- 为每种命令类型提供专门的解析指导
- 提高解析的一致性和准确性

### 2. 智能批量处理
- 根据命令复杂度自动选择批量大小
- 支持大批量命令的分批处理
- 自动回退机制：批量失败时回退到单条解析

### 3. 灵活的配置系统
- 支持环境变量配置
- 可自定义模型参数、批量大小等
- 支持调试模式和日志记录

### 4. 多层错误处理
- 批量解析失败自动回退
- 详细的错误诊断信息
- 单个命令失败不影响其他命令

## 快速开始

### 基本使用

```python
from src.core_cac.mcl_llmparser import create_llm_parser

# 创建解析器
parser = create_llm_parser()

# 解析单条命令
result = parser.parse_command("ASSIGN VOLTAGE 500000.0 VOLT", 1)
print(f"解析结果: {result.ok}")
print(f"参数: {result.payload}")
```

### 批量解析

```python
# 准备命令列表
commands = [
    {'text': 'ASSIGN VOLTAGE 500000.0 VOLT', 'lineno': 1, 'command': 'ASSIGN'},
    {'text': 'ASSIGN CURRENT 10.0 AMP', 'lineno': 2, 'command': 'ASSIGN'},
    {'text': 'POINT P1 0.0 0.0 METER', 'lineno': 3, 'command': 'POINT'},
]

# 批量解析
results = parser.parse_batch_commands(commands)
for result in results:
    print(f"行{result.lineno}: {result.command} - {'成功' if result.ok else '失败'}")
```

## 配置说明

### 环境变量配置

```bash
# API配置
export DASHSCOPE_API_KEY="your-api-key"
export LLM_MODEL_NAME="qwen-turbo"
export LLM_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"

# 解析配置
export LLM_BATCH_SIZE_LIMIT="10"
export LLM_ENABLE_BATCH="true"
export LLM_ENABLE_FALLBACK="true"

# 调试配置
export LLM_DEBUG_MODE="false"
export LLM_LOG_REQUESTS="false"

# 重试配置
export LLM_MAX_RETRIES="3"
export LLM_RETRY_DELAY="1.0"
export LLM_REQUEST_TIMEOUT="30"
```

### 代码配置

```python
from src.core_cac.llm_config import LLMConfig
from src.core_cac.mcl_llmparser import create_llm_parser

# 自定义配置
config = LLMConfig(
    model_name="qwen-turbo",
    batch_size_limit=5,
    enable_batch_parsing=True,
    debug_mode=True,
    max_retries=2
)

parser = create_llm_parser(config)
```

## 支持的命令类型

### 简单命令 (Simple)
- **ASSIGN** - 变量赋值
- **POINT** - 点定义
- 建议批量大小: 15

### 中等复杂度命令 (Medium)
- **LINE** - 线定义
- **CONDUCTOR** - 导体定义
- **INDUCTOR** - 电感定义
- 建议批量大小: 10

### 复杂命令 (Complex)
- **AREA** - 区域定义
- **PORT** - 端口定义
- **EMISSION** - 发射定义
- **EMIT** - 发射设置
- **OBSERVE** - 观测设置
- **FUNCTION** - 函数定义
- 建议批量大小: 5

## 解析结果格式

```python
@dataclass
class ParseResult:
    lineno: int              # 行号
    command: str             # 命令类型
    payload: Dict[str, Any]  # 解析出的参数
    parser_kind: str         # 解析器类型 ("LLM")
    ok: bool                 # 是否解析成功
    errors: List[str]        # 错误信息列表
    text: str               # 原始命令文本
```

### 成功解析示例

```json
{
    "lineno": 1,
    "command": "ASSIGN",
    "payload": {
        "name": "VOLTAGE",
        "value": 500000.0,
        "unit": "VOLT"
    },
    "parser_kind": "LLM",
    "ok": true,
    "errors": [],
    "text": "ASSIGN VOLTAGE 500000.0 VOLT"
}
```

### 失败解析示例

```json
{
    "lineno": 2,
    "command": "UNKNOWN",
    "payload": {},
    "parser_kind": "LLM",
    "ok": false,
    "errors": ["无法识别命令类型"],
    "text": "INVALID_COMMAND"
}
```

## 集成到转译系统

### 路由配置

```python
from src.core_symbol.rules import RouteRule

# 创建包含LLM路由的规则
route_rule = RouteRule.create_default_route()

# 复杂命令会自动路由到LLM解析器
# 简单命令使用PLY或REGEX解析器
```

### 主解析器集成

```python
from src.core_symbol.muti_flows.mcl_allparser import MCLAllParser
from src.core_symbol.muti_flows.mclparser.parser_classifier import ParserClassifier

# 创建主解析器
route_rule = RouteRule.create_default_route()
parser_classifier = ParserClassifier(route_rule)
all_parser = MCLAllParser(parser_classifier)

# 解析命令
test_items = [
    {"lineno": 1, "command": "ASSIGN", "text": "ASSIGN VOLTAGE 500000.0 VOLT"},
    {"lineno": 2, "command": "EMISSION", "text": "EMISSION EXPLOSIVE NUMBER 10"},
]

results = all_parser.mclparser_in_memory(test_items)
```

## 性能优化建议

### 1. 批量大小调优
- 简单命令可以使用较大的批量大小 (10-15)
- 复杂命令建议使用较小的批量大小 (3-5)
- 根据API响应时间调整批量大小

### 2. 缓存策略
- 相同命令的解析结果可以缓存
- 避免重复解析相同的命令模式

### 3. 错误处理
- 启用回退机制，确保系统稳定性
- 记录解析失败的命令，用于规则优化

### 4. 成本控制
- 合理设置批量大小，减少API调用次数
- 优先使用PLY/REGEX解析器处理简单命令
- 只对复杂命令使用LLM解析器

## 故障排除

### 常见问题

1. **API密钥未设置**
   ```
   错误: LLM解析器初始化失败
   解决: 设置DASHSCOPE_API_KEY环境变量
   ```

2. **批量解析失败**
   ```
   现象: 所有命令都解析失败
   解决: 检查网络连接和API配额，启用回退机制
   ```

3. **解析结果不准确**
   ```
   现象: 参数提取错误
   解决: 检查命令格式，考虑使用单条解析模式
   ```

### 调试模式

```python
# 启用调试模式
config = LLMConfig(debug_mode=True, log_requests=True)
parser = create_llm_parser(config)

# 查看详细的解析过程
result = parser.parse_command("ASSIGN VOLTAGE 500000.0 VOLT", 1)
```

## 扩展开发

### 添加新命令类型

1. 在 `llm_config.py` 中添加命令配置
2. 在 `PromptTemplates` 中添加专用提示词
3. 在路由规则中配置命令路由

### 自定义解析逻辑

```python
class CustomLLMParser(MCLLLMParser):
    def _get_batch_system_prompt(self, command_type: str) -> str:
        # 自定义批量解析提示词
        return super()._get_batch_system_prompt(command_type)
    
    def _parse_batch_response(self, response_text: str, commands: List[Dict[str, Any]]) -> List[ParseResult]:
        # 自定义响应解析逻辑
        return super()._parse_batch_response(response_text, commands)
```

## 更新日志

### v1.0.0 (2025-12-17)
- 初始版本发布
- 支持按命令类型分组的批量解析
- 集成到主转译系统
- 完整的配置和错误处理机制
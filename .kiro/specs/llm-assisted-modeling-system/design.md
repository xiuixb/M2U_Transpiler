# LLM辅助建模系统设计文档

## 概述

LLM辅助建模系统是一个基于大语言模型的等离子体器件仿真软件转译系统，旨在解决传统规则转译器在复杂建模语义处理中的规则爆炸问题。系统通过引入LLM技术，实现从MAGIC建模脚本到UNIPIC配置文件的智能转换，并提供统一的中间语义文本作为转换桥梁。

## 架构

### 整体架构

系统采用分层架构设计，包含以下核心层次：

```
┌─────────────────────────────────────────────────────────────┐
│                    服务层                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  LLM转译服务    │  │  智能建模服务   │  │  配置管理服务   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                    核心处理层                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  LLM解析器      │  │  LLM转换器      │  │  规则转译器     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                    数据层                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  中间语义文本    │  │ 规则库(路由+映射)│  │  缓存存储       │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 数据流架构

```
MAGIC脚本(.m2d) 
    ↓ [预处理]
预处理文本
    ↓ [解析路由]
┌─────────────────┬─────────────────┬─────────────────┐
│   PLY解析器      │  REGEX解析器    │   LLM解析器     │
└─────────────────┴─────────────────┴─────────────────┘
    ↓ [ParseResult统一格式]
解析结果列表
    ↓ [LLM转换器/规则转换器]
中间语义文本(JSON)
    ↓ [UNIPIC生成器]
UNIPIC配置文件(.in文件集合)
```

## 组件和接口

### 核心组件

#### 1. LLM解析器 (LLMParser)

**职责**: 使用大语言模型解析复杂的MAGIC命令，处理传统语法分析器无法覆盖的命令类型。

**接口**:
```python
class LLMParser:
    def parse_cmd(self, model_name: str, cmd_name: str, input_list: List[dict], batch_size: int = 7) -> List[dict]
    def _parse_batch_with_json_retry(self, model_name: str, cmd_name: str, batch: List[dict], batch_index: int) -> List[dict]
    def _post_process_llm_results(self, llm_results: List[dict], original_batch: List[dict]) -> List[dict]
```

**关键特性**:
- 支持批量处理（5-8条同类型命令）
- 并发API调用优化
- 智能重试和错误处理机制
- 与PLY解析器相同的输出格式

#### 2. LLM转换器 (LLMConverter)

**职责**: 将ParseResult转换为中间语义文本，处理复杂的语义依赖关系和映射规则。

**接口**:
```python
class LLMConverter:
    def convert_to_intermediate(self, parse_results: List[ParseResult]) -> IntermediateSemanticText
    def build_context_block(self, element: ParseResult, dependencies: List[ParseResult]) -> ContextBlock
    def find_mapping_rules(self, element_type: str, target_field: str) -> MappingRule
    def process_concurrent_elements(self, elements: List[ParseResult]) -> List[ConversionResult]
```

#### 3. 中间语义文本管理器 (IntermediateTextManager)

**职责**: 管理统一的中间语义文本格式，提供语义元素的存储、查询和转换功能。

**接口**:
```python
class IntermediateTextManager:
    def create_intermediate_text(self) -> IntermediateSemanticText
    def add_semantic_element(self, element_type: str, element_data: dict) -> None
    def resolve_dependencies(self, element_id: str) -> List[str]
    def export_to_unipic(self) -> Dict[str, Any]
```

#### 4. 解析路由器 (ParserRouter)

**职责**: 智能路由MAGIC命令到合适的解析器，支持动态路由策略。

**接口**:
```python
class ParserRouter:
    def route_command(self, command: dict) -> str  # 返回 "PLY", "REGEX", "LLM"
    def update_routing_rules(self, rules: Dict[str, str]) -> None
    def get_parser_statistics(self) -> Dict[str, int]
```

## 数据模型

### 中间语义文本格式

基于对PIC软件建模流程的分析，中间语义文本采用以下JSON结构：

```json
{
  "meta": {
    "version": "1.0",
    "source_file": "example.m2d",
    "target_format": "unipic2.5d",
    "creation_time": "2025-12-17T10:00:00Z",
    "device_type": "BWO"
  },
  "variables": {
    "var_name1": {
      "var_expr": "2.5 * mm",
      "var_num": 2.5,
      "var_unit": "mm",
      "dependencies": []
    }
  },
  "functions": {
    "func_name1": {
      "func_params": ["x", "y", "t"],
      "func_expr": "x * sin(2*pi*f*t)",
      "func_vars": {"f": {"value": 1e9, "unit": "Hz"}},
      "dependencies": ["f"]
    }
  },
  "geometry": {
    "POINT": {
      "geom_name1": {
        "geom_type": "POINT",
        "geom_expr": "[0.0, 25.0]",
        "geom_params": {"x": 0.0, "y": 25.0, "unit": "mm"},
        "dependencies": []
      }
    },
    "LINE": {
      "geom_name1": {
        "geom_type": "LINE",
        "geom_expr": "P1 P2",
        "geom_params": {"points": ["P1", "P2"]},
        "dependencies": ["P1", "P2"]
      }
    },
    "AREA": {
      "geom_name1": {
        "geom_type": "AREA",
        "geom_expr": "RECTANGULAR P1 P2",
        "geom_params": {
          "area_type": "RECTANGULAR",
          "points": ["P1", "P2"]
        },
        "dependencies": ["P1", "P2"]
      }
    },
    "SELECTION": [
      {
        "selection_type": "INPUTMURPORT",
        "ref_geometry": "geom_name1",
        "ref_point": [0.0, 17.5, 0.0],
        "mask": 2
      }
    ]
  },
  "materials": {
    "definitions": [
      {
        "mat_name": "CONDUCTOR",
        "mat_type": "PEC",
        "mat_params": {"conductivity": "infinite"}
      }
    ],
    "assignments": [
      {
        "geom_name": "geom_name1",
        "mat_name": "CONDUCTOR"
      }
    ]
  },
  "mesh": {
    "dx": {"value": 0.1, "unit": "mm"},
    "dy": {"value": 0.1, "unit": "mm"},
    "dz": {"value": 0.1, "unit": "mm"},
    "wave_resolution_ratio": 200
  },
  "sources": {
    "excitation": [
      {
        "source_type": "MurVoltagePort",
        "geometry_ref": "port1",
        "function_ref": "voltage_func",
        "parameters": {"mask": 2}
      }
    ],
    "emission": [
      {
        "emission_type": "GaussEmitter",
        "geometry_ref": "cathode1",
        "parameters": {
          "field_enhancement": 1.0,
          "threshold": 2.3e7,
          "mask_vector": [4, 5]
        }
      }
    ]
  },
  "boundaries": {
    "PEC": [
      {"geometry_ref": "conductor_area1"}
    ],
    "PML": [
      {
        "parameters": {
          "power_order": 3,
          "alpha": 0.0,
          "kappa_max": 40.0,
          "sigma_ratio": 7.5
        }
      }
    ],
    "OpenPort": [
      {"geometry_ref": "port2", "mask": 3}
    ]
  },
  "diagnostics": [
    {
      "diagnostic_type": "VoltageDgn",
      "name": "Vin1",
      "parameters": {
        "line_dir": "r",
        "org": "[0.01, 0.01]",
        "end": "[0.01, 0.025]"
      }
    },
    {
      "diagnostic_type": "PoyntingDgn",
      "name": "Poutout1",
      "parameters": {
        "dir": "z",
        "lower_bounds": "[0.01, 0.01]",
        "upper_bounds": "[0.01, 0.025]"
      }
    }
  ],
  "global": {
    "simulation_time": {"value": 3e-8, "unit": "s"},
    "cfl_scale": 0.9,
    "thread_num": 2,
    "em_solver": "picMode",
    "material_lib": "material.xml"
  }
}
```

### ParseResult扩展

为支持LLM解析，扩展现有的ParseResult结构：

```python
@dataclass
class ParseResult:
    lineno: int
    command: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    parser_kind: str = ""  # "PLY", "REGEX", "LLM"
    ok: bool = False
    errors: str = "no"  # 统一为字符串格式
    text: str = ""
    confidence: float = 1.0  # LLM解析置信度
    dependencies: List[str] = field(default_factory=list)  # 依赖的其他元素
    context_used: bool = False  # 是否使用了上下文信息
```

## 正确性属性

*一个属性是一个特征或行为，应该在系统的所有有效执行中保持为真-本质上，是关于系统应该做什么的正式陈述。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*

基于需求分析，系统应满足以下正确性属性：

### 属性 1: 解析器路由一致性
*对于任何*未在PLY语法中定义的MAGIC命令，系统应该自动路由到LLM解析器进行处理
**验证需求: 1.1**

### 属性 2: 输出格式一致性  
*对于任何*MAGIC命令，无论使用哪种解析器处理，返回的ParseResult结构都应该包含相同的必需字段
**验证需求: 1.2**

### 属性 3: 并发处理性能提升
*对于任何*批量命令处理（5-8条同类型命令），并发API调用的处理时间应该显著少于顺序调用
**验证需求: 1.3**

### 属性 4: 错误处理完整性
*对于任何*LLM解析失败或格式错误的情况，系统应该提供清晰的错误信息并成功回退到其他解析器
**验证需求: 1.4**

### 属性 5: 中间文本语义完整性
*对于任何*MAGIC建模脚本，生成的中间语义文本应该包含所有必要的建模语义信息
**验证需求: 2.1**

### 属性 6: 变量信息保存完整性
*对于任何*包含变量定义的中间语义文本，都应该保存变量名、表达式、数值和单位信息
**验证需求: 2.2**

### 属性 7: 几何类型支持完整性
*对于任何*几何实体类型（POINT、LINE、AREA、SELECTION），中间语义文本都应该支持其完整描述
**验证需求: 2.3**

### 属性 8: 转换round-trip一致性
*对于任何*中间语义文本，基于它生成的UNIPIC配置文件应该包含所有必需的.in文件和参数
**验证需求: 2.5**

### 属性 9: 依赖关系识别完整性
*对于任何*具有依赖关系的建模元素，系统应该自动识别并包含所有依赖的前置元素
**验证需求: 3.1**

### 属性 10: 上下文构建完整性
*对于任何*语义元素，LLM转换器处理时应该构建包含必要上下文信息的完整语义块
**验证需求: 3.2**

### 属性 11: 并发处理正确性
*对于任何*需要并发处理的多个语义元素，不同元素的转换过程应该能够并行执行且结果正确
**验证需求: 3.4**

### 属性 12: 缓存机制有效性
*对于任何*相同的LLM API调用输入，系统应该复用缓存结果而不进行重复调用
**验证需求: 4.2**

### 属性 13: 容错机制可靠性
*对于任何*LLM API调用失败或超时的情况，系统应该提供有效的重试机制和降级策略
**验证需求: 4.3**

### 属性 14: 错误日志详细性
*对于任何*系统运行过程中出现的错误，都应该提供详细的错误日志和调试信息
**验证需求: 4.5**

### 属性 15: LLM泛化能力优越性
*对于任何*新器件类型，LLM方法应该展现出比纯规则方法更好的泛化能力
**验证需求: 5.2**

### 属性 16: 规则数量减少有效性
*对于任何*面临规则爆炸的场景，LLM方法应该显著减少所需的显式规则数量
**验证需求: 5.3**

### 属性 17: 配置化扩展能力
*对于任何*需要修改的转换规则，系统应该支持通过配置文件或数据库更新而无需修改代码
**验证需求: 6.2**

### 属性 18: LLM接口统一性
*对于任何*需要集成的新LLM模型，都应该能够通过统一的接口进行使用和切换
**验证需求: 6.3**

## 错误处理

### 错误分类

1. **解析错误**
   - LLM API调用失败
   - 返回格式不正确
   - 语义解析失败

2. **转换错误**
   - 依赖关系循环
   - 映射规则缺失
   - 数据类型不匹配

3. **系统错误**
   - 网络连接问题
   - 资源不足
   - 配置错误

### 错误处理策略

```python
class ErrorHandler:
    def handle_llm_api_error(self, error: Exception) -> FallbackStrategy
    def handle_parsing_error(self, command: str, error: str) -> ParseResult
    def handle_conversion_error(self, element: dict, error: str) -> ConversionResult
    def log_error_with_context(self, error: Exception, context: dict) -> None
```

### 降级策略

1. **解析器降级**: LLM → REGEX → 手动标记
2. **模型降级**: GPT-4 → GPT-3.5 → 本地模型
3. **功能降级**: 完整转换 → 部分转换 → 错误报告

## 测试策略

### 双重测试方法

系统采用单元测试和属性测试相结合的策略：

**单元测试**覆盖：
- 具体的解析器功能验证
- 特定器件类型的转换测试
- 错误处理边界情况
- API接口集成测试

**属性测试**覆盖：
- 使用Hypothesis库进行属性测试
- 每个属性测试运行最少100次迭代
- 测试通用的正确性属性，验证系统在各种输入下的行为一致性

### 测试框架选择

- **单元测试**: pytest
- **属性测试**: Hypothesis
- **集成测试**: pytest + docker-compose
- **性能测试**: pytest-benchmark
- **LLM测试**: 专用的mock框架模拟API调用

### 测试标记格式

每个属性测试使用以下格式标记：
```python
# **Feature: llm-assisted-modeling-system, Property 1: 解析器路由一致性**
def test_parser_routing_consistency():
    # 测试实现
```

### 测试数据管理

- 使用真实的器件配置文件作为测试数据
- 建立标准的测试数据集，包含6种器件类型
- 实现测试数据的版本控制和自动更新机制
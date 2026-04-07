# M2U_Transpiler

这是一个将 MAGIC 的 MCL 脚本转成 UNIPIC `.in` 文件组的本地转译器。  
项目已经从“单脚本试验代码”逐步整理成“预处理 -> 解析 -> 一轮符号处理 -> 二轮差异转换 -> UNI 生成”的流水线，但仍然保留了一些历史包袱。  
这份 README 不是用户手册，而是给新 Agent / 新维护者的交接文档。

## 1. 项目目标

输入：
- MAGIC / MCL 脚本文本文件，例如 `data/BWO/BWO.m2d`

输出：
- UNIPIC 仿真目录 `Simulation/`
- 典型文件包括：
  - `build.in`
  - `FaceBnd.in`
  - `PtclSources.in`
  - `FieldsDgn.in`
  - `PML.in`
  - `Species.in`
  - `GlobalSetting.in`
  - 可选 `StaticNodeFLds.in` / `CircuitModel.in` / `FoilModel.in`

## 2. 当前目录结构

当前主结构：

```text
src/
├── api
├── application
├── domain
├── infrastructure
└── presentation
```

其中真正核心的是：

- `src/application/`
  流水线入口、菜单入口、service 层

- `src/domain/mclparse/`
  预处理、PLY lexer/parser、AST visitor、多解析器流转

- `src/domain/mclconv/`
  MCL -> Mid 中间表示的一轮符号处理，以及 Mid 二轮差异转换

- `src/domain/unigenerate/`
  Mid -> UNI 符号与 `.in` 文件生成

- `src/domain/core/`
  几何计算、布尔运算、几何工具

- `src/domain/config/`
  命令词典、提示词、常量、符号表定义、路由配置

- `src/infrastructure/`
  系统级配置，如 `src/sys_config.json`

## 3. 主入口

### 3.1 纯 PLY 流水线

文件：
- [src/application/magic2unipic.py](D:/AAA_PIC/Parser/M2U_Transpiler/src/application/magic2unipic.py)

特点：
- 只走 PLY 预处理和 PLY parser
- 适合规则链路调试

### 3.2 LLM / 混合解析流水线

文件：
- [src/application/m2u_llm.py](D:/AAA_PIC/Parser/M2U_Transpiler/src/application/m2u_llm.py)

特点：
- 走 `LLMPreprocess + ParserClassifier + MCLParseFlow`
- 一轮符号处理使用 `MCL2MIDST_LLMConv`

### 3.3 菜单版 LLM 流水线

文件：
- [src/application/m2u_llm_menu.py](D:/AAA_PIC/Parser/M2U_Transpiler/src/application/m2u_llm_menu.py)

特点：
- 支持按步骤执行
- 适合调试中间产物
- 当前分阶段定义：
  - Step 1: 预处理
  - Step 2: 解析
  - Step 3: 符号处理 / 一轮符号处理
  - Step 4: 差异转换 / 二轮转换
  - Step 5: 文件生成
  - Step 9: 全流程

## 4. 当前流水线分层

### Step 1: 预处理

输出：
- `workdir/preprocessed.jsonl`

位置：
- `src/domain/mclparse/mcl_plypreprocess.py`
- `src/domain/mclparse/mcl_llmpreprocess.py`

职责：
- 注释过滤
- 命令展平
- 宏展开
- 默认单位补全

注意：
- 现在“数字+单位”的主识别已经尽量下沉到 lexer
- 但 `POINT/LINE/AREA` 的裸数字默认单位补全仍在预处理里

### Step 2: 解析

输出：
- `workdir/parsed_result.json`

位置：
- `src/domain/mclparse/plyparser/mcl_lexer.py`
- `src/domain/mclparse/plyparser/mcl_grammar.py`
- `src/domain/mclparse/mcl_ast_visit.py`
- `src/domain/mclparse/mcl_parseflow.py`

职责：
- PLY / regex / LLM 路由解析
- 产出统一的解析结果序列

解析结果基本格式：

```json
{
  "lineno": 1,
  "command": "ASSIGN",
  "payload": {...},
  "parser_kind": "PLY",
  "ok": true,
  "errors": "no",
  "text": "..."
}
```

### Step 3: 一轮符号处理

输出：
- `workdir/mid_round1.json`
- `workdir/llmconv.json`（LLM 路径）

位置：
- `src/domain/mclconv/mcl2midsT_plyconv.py`
- `src/domain/mclconv/mcl2midsT_llmconv.py`

职责：
- 解析结果 -> Mid `sT`
- 建立变量、函数、几何、材料绑定、边界、诊断、物理实体等

### Step 4: 二轮差异转换

输出：
- `workdir/mid_round2.json`

位置：
- `src/domain/mclconv/mid_sTconv.py`

职责：
- 网格汇总
- 材料绑定排序处理
- 金属建模
- 金属转真空
- 发射参考点等几何二次计算

### Step 5: UNI 生成

输出：
- `workdir/mid_symbols.json`
- `workdir/uni_symbols.json`
- `Simulation/*.in`

位置：
- `src/domain/unigenerate/mid2uni_sTconv.py`
- `src/domain/unigenerate/uni2Files.py`
- `src/domain/unigenerate/uni2inFiles.py`

职责：
- Mid `sT` -> UNI 符号结构
- UNI 符号 -> `.in` 文件

## 5. 当前中间表示约定

项目目前统一使用 `sT` 作为 Mid 中间表示。  
不要再往回依赖早期的平铺旧结构。

重点节点：

- `sT["variable"]`
- `sT["function"]`
- `sT["geometry"]["point"]`
- `sT["geometry"]["line"]`
- `sT["geometry"]["area"]`
- `sT["materials"]["material_assign"]`
- `sT["mesh"]["mark"]`
- `sT["diagnostic"]`
- `sT["boundaries"]["port"]`
- `sT["physics_entities"]`
- `sT["geometry"]["area_cac_result"]`

几个重要约定：

### 5.1 几何

点 / 线 / 面都走 `cac_result["geom_num"]`

例如：

- 点：
```python
sT["geometry"]["point"][name]["cac_result"]["geom_num"] == [x_mm, y_mm]
```

- 线：
```python
sT["geometry"]["line"][name]["cac_result"]["geom_num"] == [(x1, y1), (x2, y2), ...]
```

- 面：
```python
sT["geometry"]["area"][name]["cac_result"]["geom_num"] == [(x1, y1), ...]
```

历史旧字段如 `para` 不应再被新代码依赖。

### 5.2 材料绑定

材料绑定统一放在：

```python
sT["materials"]["material_assign"]
```

格式核心字段：
- `geom_name`
- `mat_name`
- `lineno`

注意：
- 一轮符号处理不要把材料直接塞到 area 本体里
- 二轮差异转换再统一做材料绑定和建模

### 5.3 网格 MARK

现在采用 `version2` 风格：

- 一轮符号处理只记录每条 `MARK`
```python
sT["mesh"]["mark"] = [
  {
    "geom_name": "...",
    "axis": "X1",
    "size_num": 0.05,
    "size_unit": "mm"
  }
]
```

- 二轮转换再汇总：
```python
sT["mesh"]["X1"]
sT["mesh"]["X2"]
```

不要在一轮直接覆盖 `mesh["X1"]/["X2"]`。

### 5.4 诊断

诊断对象当前在一轮符号处理后存放于：

```python
sT["diagnostic"]
```

生成侧目前按 `sys_name` 读，再映射到输出 `name`。

## 6. 二轮差异转换的真实顺序

目前二轮转换的几何核心逻辑是：

1. 读取 area 几何
2. 按 `material_assign.lineno` 顺序处理材料绑定
3. 建模得到金属区域 `metal_area_entities`
4. 从建模结果中拆出多个连通 PEC 区域
5. 再把建好的金属区域喂给 `Cond2Void`

实现文件：
- [src/domain/mclconv/mid_sTconv.py](D:/AAA_PIC/Parser/M2U_Transpiler/src/domain/mclconv/mid_sTconv.py)
- [src/domain/core/get_geometry_results.py](D:/AAA_PIC/Parser/M2U_Transpiler/src/domain/core/get_geometry_results.py)

### 6.1 当前已有调试输出

- 材料绑定开始：
```text
[info] 材料绑定......
```

- 每条材料绑定日志
- 建模后的 PEC 连通域打印
- `Cond2Void` 中打印 `"上包络 + y=0"外壳`

### 6.2 当前算法局限

`Cond2Void` 目前是“上包络 + y=0 外壳 -> 做差集”的方法。  
它不是严格的拓扑 flood fill / outside-inside 判断。

已知问题：
- 对于与外界连通的开口空腔，算法可能失效
- `RKLYS` 暴露了这个问题

如果未来重构，建议改成：
- `OuterBox - PEC`
- 再按是否与外边界连通区分 `outside` 和 `inner void`

## 7. 已经明确修过的关键坑

下面这些问题已经在当前代码里被修过，新的维护者不要再重复走回头路。

### 7.1 词法层

- 支持科学计数法 `1.2566e-6`
- 支持 `0.05e-2cm`
- 支持 `60_NANOSECONDS`
- 支持带点变量名：
  - `RF.FREQUENCY`
  - `CATHODE.OUTER.RADIUS`

位置：
- [mcl_lexer.py](D:/AAA_PIC/Parser/M2U_Transpiler/src/domain/mclparse/plyparser/mcl_lexer.py)

### 7.2 预处理层

- 不再把所有“数字+单位”强行主路径改写成 `num * unit`
- 但仍会对 `POINT/LINE/AREA` 做默认单位补全

### 7.3 一轮符号处理

- `MARK` 现在不再被硬 `return`
- `MARK` 已切到 `mesh["mark"]` 列表
- `CONFORMAL/RECTANGULAR` 的对角点会先做 `xmin/xmax/ymin/ymax` 归一化
- 材料绑定统一记为 `material_assign`

### 7.4 生成层

- `FieldsDgn` 生成端统一按 `sys_name` 读
- `mid_round1.json / mid_round2.json / mid_symbols.json` 命名已经统一

## 8. 当前最重要的文件

如果是新 Agent，优先看这些：

- [src/application/m2u_llm_menu.py](D:/AAA_PIC/Parser/M2U_Transpiler/src/application/m2u_llm_menu.py)
- [src/application/m2u_llm.py](D:/AAA_PIC/Parser/M2U_Transpiler/src/application/m2u_llm.py)
- [src/application/magic2unipic.py](D:/AAA_PIC/Parser/M2U_Transpiler/src/application/magic2unipic.py)
- [src/domain/config/symbolBase.py](D:/AAA_PIC/Parser/M2U_Transpiler/src/domain/config/symbolBase.py)
- [src/domain/mclparse/plyparser/mcl_lexer.py](D:/AAA_PIC/Parser/M2U_Transpiler/src/domain/mclparse/plyparser/mcl_lexer.py)
- [src/domain/mclparse/plyparser/mcl_grammar.py](D:/AAA_PIC/Parser/M2U_Transpiler/src/domain/mclparse/plyparser/mcl_grammar.py)
- [src/domain/mclconv/mcl2midsT_llmconv.py](D:/AAA_PIC/Parser/M2U_Transpiler/src/domain/mclconv/mcl2midsT_llmconv.py)
- [src/domain/mclconv/mcl2midsT_plyconv.py](D:/AAA_PIC/Parser/M2U_Transpiler/src/domain/mclconv/mcl2midsT_plyconv.py)
- [src/domain/mclconv/mid_sTconv.py](D:/AAA_PIC/Parser/M2U_Transpiler/src/domain/mclconv/mid_sTconv.py)
- [src/domain/unigenerate/mid2uni_sTconv.py](D:/AAA_PIC/Parser/M2U_Transpiler/src/domain/unigenerate/mid2uni_sTconv.py)
- [src/domain/core/get_geometry_results.py](D:/AAA_PIC/Parser/M2U_Transpiler/src/domain/core/get_geometry_results.py)

## 9. workdir 产物约定

每个器件目录下的 `workdir/` 现在典型包含：

- `preprocessed.jsonl`
- `parsed_result.json`
- `mid_round1.json`
- `mid_round2.json`
- `mid_symbols.json`
- `uni_symbols.json`
- `llmconv.json`
- `m2u_config.json`

推荐把调试建立在这些产物上，而不是每次都从头阅读整条日志。

## 10. 测试与验证

已有 service 级测试：

- [src/test/test_bwo1_services.py](D:/AAA_PIC/Parser/M2U_Transpiler/src/test/test_bwo1_services.py)
- [src/test/test_bwo1_services_stepwise.py](D:/AAA_PIC/Parser/M2U_Transpiler/src/test/test_bwo1_services_stepwise.py)
- [src/test/test_bwo1_services_additional.py](D:/AAA_PIC/Parser/M2U_Transpiler/src/test/test_bwo1_services_additional.py)

常用回归器件：

- `BWO`
  最稳定，适合冒烟测试

- `BWO1`
  已用来做 service 测试

- `RKLYS`
  能暴露几何、单位、诊断、材料绑定顺序问题

- `MILO_new`
  暴露电感、几何与 LLM 一轮符号处理问题

## 11. 给新 Agent 的建议

### 11.1 不要做的事

- 不要再把旧平铺字段当主结构恢复回来
- 不要在一轮符号处理里直接把材料塞进 area
- 不要把 `MARK` 再改回“直接覆盖 X1/X2”
- 不要把广义“数字+单位”识别重新塞回大规模预处理主链

### 11.2 优先遵守的约定

- 词法边界优先放 lexer
- 默认单位补全放预处理或语义层
- 一轮符号处理负责“记账”
- 二轮转换负责“汇总 / 建模 / 差异转换”
- 生成层只消费当前 `sT`，不要偷偷兼容过多旧格式

### 11.3 调试顺序建议

如果某个器件跑崩了，建议按这个顺序查：

1. `preprocessed.jsonl`
2. `parsed_result.json`
3. `mid_round1.json`
4. `mid_round2.json`
5. `mid_symbols.json`
6. `uni_symbols.json`
7. `Simulation/*.in`

不要一上来就盯最终 `.in` 文件。

## 12. 当前缺口

项目可以运行，但离“完全稳定的工业级编译器”还有距离。当前主要缺口：

- `Cond2Void` 对开口空腔的拓扑判断仍不可靠
- 一些复杂诊断命令还可能存在字段不统一问题
- LLM / PLY 两条一轮符号处理链虽然大体收敛，但仍有少量实现分叉
- 部分日志仍保留历史调试风格，未完全统一


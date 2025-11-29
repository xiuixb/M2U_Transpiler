# 文件模块导入方法
在根目录下创建空白的.project_mark文件

current_dir = os.path.dirname(os.path.abspath(__file__))
while not os.path.exists(os.path.join(current_dir, ".project_mark")):
    parent_dir = os.path.dirname(current_dir)
    if    parent_dir != current_dir: current_dir = parent_dir
    else: raise FileNotFoundError("未找到项目根目录，检查.project_mark文件")
project_root = current_dir
sys.path.append(project_root)

# 项目介绍
给两款等离子体器件仿真领域的工业软件做转译器，
第一款名字是MAGIC, 使用的是一款MCL脚本语言编写的代码作为输入文件,
第二款名字是UNIPIC, 使用类似xml风格的配置文件作为输入文件。
我开发的转译器使用PLY框架，方便快捷地解析MAGIC的MCL脚本语言为json文件,
并考虑两种文件的存储逻辑差异，将解析出的json文件转换成UNIPIC的类似xml风格的配置文件.

等离子体器件仿真工业软件的项目一般包括：
变量定义、函数定义，几何建模，材料定义，网格剖分，设置注入端口/阴极发射/开放端口，电磁场定义，诊断参数，仿真全局参数等过程；
转译器的主要工作是将MAGIC的MCL脚本语言转换为UNIPIC的配置文件。

# 开发需求
PLY规则转译器
LLM转译器

# 项目开发进度与计划
PLY规则转译器已经基本完成，
LLM转译器的开发还在进行中。
正在基于PLY规则转译器代码进行整体系统架构重构。

# 项目架构模板
思想参考
1. 后端采用fastapi，
2. 前端采用vue3，先用streamlit实现简单的前端
3. 数据库采用sqlite3
4. 架构设计思路参考 \架构设计文档.md
整体分为三大层，八小层
一、模块复用层 core
实体层  Entity
单实体变化层 flows
多实体事件层 events
二、系统后端层 src
系统配置层 config
系统服务层 services
系统接口层 controllers
API层(可能没有)   api
三、系统前端层(可能没有)
streamlit/Vue3

总结：该架构以本体论方法构建领域模型，以事件驱动方式组织业务逻辑，以整洁架构原则确保分层独立，最终实现底层代码可复用、业务逻辑可扩展、AI 工作流可适配的现代化软件体系。

Onto-Driven Architecture：核心架构特点
1. 本体论驱动的领域建模（Ontological Modeling）
实体层（Entities）采用本体论方法进行“存在模式”建模。
每个实体自封闭、不依赖外部模块、仅包含属性与原子状态变化。
实体具有明确的语义边界，有利于跨项目复用与形式化理解。

2. 分层明确，依赖方向严格控制（Clean Architecture）
架构分为 Entities → Flows → Events → Services → Controller → API → Frontend 多层。
上层依赖下层，下层不依赖上层，实现高内聚、低耦合。
底层三层可跨项目直接复用，业务差异通过上层注入。

3. 单实体变化与多实体事件分离（DDD Tactical Patterns）
Flows 层：描述单实体的内部状态变化过程。
Events 层：描述跨实体、跨上下文的业务事实（Domain Events）。
清晰区分局部内在变化与全局业务响应，提高结构化表达能力。

4. 服务层承载业务规则（Application Services）
所有业务逻辑、状态持久化、AI 调用、数据库读写均封装在 Service 层。
保持领域层（entities/flows/events）纯净，使其可以跨项目迁移与重用。

5. 事件驱动体系实现业务扩展性（Event-Driven Architecture）
底层 flows/events 负责发布事件，不包含业务细节。
上层 service 提供事件监听器，实现知识库更新、图数据库同步、RAG 索引更新等业务扩展。
新业务仅需增加监听器，无需修改底层代码（开放封闭原则）。

6. 插件化与可组合性（Plugin-Ready Structure）
Service 层事件监听器可按需组合，天然支持插件机制。
能够根据项目需求加载不同功能模块，实现灵活的系统裁剪。

7. 适配 AI 工作流与现代应用场景（AI-Native Architecture）

架构天生适合 AI 工作流（信息抽取、向量化、图构建、RAG 索引）。
强事件驱动结构匹配多阶段推理链、数据转换链路。
实体/事件/服务三层组合可表达复杂 AI 业务逻辑。

以上所有的名称可以根据项目需求进行修改，但核心架构思想不变。


# 系统设计
## 概览
规则转译器架构分析：
### 分析符号域
纯信息域
### 梳理实体层
字符名{
字符域(可省略)
字符形式(即内容)
字符解释规则
字符语义()
}
语义计算(){}

符号基础类         symbolBase.py
1源文本            magic_mcl   magic_m2d  
2清洗文本          magic_cmd  magic_txt
3中间文本        
31源符号表         magic_symTable
32中间符号表       mid_symTable
33目标符号表       unipic25d_symTable
4目标文本          unipic25d_InFiles
实体类             entity.py
llmEntity
fileEntity
dbEntity
infoEnyity

### 梳理单实体流程
即一些符号内部计算工具

文件读写方法都有
1源文本

2清洗文本
词法 语法分析


### 梳理多实体流程
即符号计算方法
mcl_preprocess
mcl_symTable_builder
mcl_plyparser
mcl_llmparser


mcl2mid_sTconv.py
mid2uni_sTconv.py
mcl_ruleconv.py
mcl_llmconv.py
### 分析超参数
系统超参数配置文件，类的实例化对象

### 定义service/功能层
转译流程服务
magic2unipic.py
### 定义controller/系统层
unipic_help_system.py

## 目录结构

## 模块细节
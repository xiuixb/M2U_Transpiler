# 项目介绍
## 总背景
这是一个电子工程学院与软件学院联培的软件工程硕士生毕业设计。  
主题是：等离子体器件仿真领域-粒子模拟软件辅助建模系统  
应用领域：高功率微波器件仿真领域  
毕业设计的主要内容是：

1. 基于PLY框架开发MAGIC到UNIPIC的规则转译器
2. 基于LLM开发UNIPIC软件的智能辅助建模系统

## 规则转译器背景
给两款等离子体器件仿真领域的工业软件做转译器，  
第一款名字是MAGIC, 使用的是一款MCL脚本语言编写的代码作为输入文件, 是一种纯文本文件，  
第二款名字是UNIPIC, 使用类似xml/ini混合风格的配置文件作为输入文件，是一系列后缀为.in的文本文件夹。  
具体为：  
Simulation  
├── build.in  
├── FaceBnd.in  
├── PtclSources.in  
├── StaticNodeFLds.in(可省略)  
├── CircuitModel.in(可省略)  
├── FoilModel.in(可省略)  
├── FieldsDgn.in  
├── PML.in  
├── Species.in  
├── GlobalSetting.in  
...  
我开发的规则转译器的解析器部分使用PLY框架。

首先m2d文件经过预处理器被处理各种格式，  
再经过解析路由选择PLY/正则方法来解析参数，方便灵活地将MAGIC的MCL脚本语言解析为json文件，  
并考虑两种文件的存储逻辑差异，将解析出的json文件经过三轮转换得到UNIPIC符号表，

第一轮是magic命令处理，即mcl2mid_conv

第二轮是中间符号处理，即mid_conv

第三轮是中间符号到unipic符号，即mid2uni_conv  
最终由.in文件生成器生成UNIPIC的类似xml/ini混合风格的配置文件.

等离子体器件仿真软件的项目文件一般包括如下语义元素：  
变量定义、函数定义，几何建模，材料定义，网格剖分，设置注入端口/阴极发射/开放端口，电磁场定义，诊断参数，仿真全局参数等过程；

## 智能辅助建模系统
给UNIPIC软件开发一个智能辅助建模系统，  
使用UNIPIC软件构建仿真模型分为以下几个步骤：

1. 选择项目参数 ProjectConfig
2. 导入点集 points->构建几何图形
3. 网格参数 GridCtrlConfig
4. 参考点选择（注入波、端口）SelectionConfig
5. 端口参数 FaceBndConfig
6. 粒子源参数 PtclSourcesConfig
7. 静磁场参数 （可跳过）StaticNodeFLdsConfig
8. 电感参数（可跳过）CircuitModelConfig
9. 薄膜参数（可跳过）FoilModelConfig
10. 诊断参数 FieldsDgnConfig
11. 粒子参数 SpeciesConfig
12. PML参数 PMLConfig
13. 仿真流程参数 GlobalSettingConfig



智能辅助建模系统可以考虑实现一些相关的功能，现在需求还未明确，创新点还没想好，一切应该服务于研究生毕设开发以及论文写作。



# 文件模块导入方法
在根目录下创建空白的.project_mark文件  
在其它文件中：

import os  
import sys  
current_dir = os.path.dirname(os.path.abspath(**file**))  
while not os.path.exists(os.path.join(current_dir, ".project_mark")):  
    parent_dir = os.path.dirname(current_dir)  
    if    parent_dir != current_dir: current_dir = parent_dir  
    else: raise FileNotFoundError("未找到项目根目录，检查.project_mark文件")  
project_root = current_dir  
sys.path.append(project_root)

# 开发需求
PLY规则转译器  
智能辅助建模系统

# 项目开发进度与计划
PLY规则转译器已经基本完成

# 项目架构模板
思想参考UKCS知识范畴思想、采用分层方法设计

  
src  
├── api  
│   └── controller  
├── core_cac  
│   ├── cac_entity.py  
│   ├── cac_flows.py  
│   ├── db_entity.py  
│   ├── gemo_conv.py  
│   ├── get_geometry_results.py  
│   └── prompt.py  
├── core_symbol  
│   ├── symbolBase.py  
│   ├── rules.py  
│   ├── single_flows  
│   ├── muti_flows  
├── m2u_transpiler  
│   ├── magic2unipic.py  
│   ├── model_builder.py  
│   └── sys_config  
└── uni_modeling

调用关系是：

严格单向调用  
m2u_transpiler/uni_modeling为服务层，可以调用core_cac、core_symbol模块。

core_symbol可以调用core_cac

  
简单来说  
core_symbol层中定义基本数据类、及其简单符号表征、模拟方法、时序变化逻辑；

单一实体的时序变化逻辑放到single_flows子文件夹，多个实体交互的时序变化逻辑放到muti_flows子文件夹中。  
core_cac层中定义一些不涉及业务逻辑实体状态的符号演算方法、模型、算法等，如字符处理，排序，几何算法等等。  
最终由对应的system层调用，封装为一个业务service  
api层中由controller层调用service层，service层调用complex_cac、core_cac、core_symbol模块，向外部提供接口

这样一来，核心的业务逻辑代码只需要定义到system层，api层，底层的symbol层和cac层都可以通用

## 规则转译器系统设计
规则转译器架构分析：

### 分析知识范畴
纯符号范畴，符号语义指向的是

粒子模拟软件描述的模拟过程

### 梳理S1符号层
字符名{  
字符域(可省略)  
字符形式(即内容)  
字符解释规则  
字符语义()  
}  
简单演算(){}

符号基础类         symbolBase.py  
1源文本            magic_mcl   magic_m2d  
2清洗文本          magic_cmd  magic_txt  
3中间文本  
31源符号表         magic_symTable  
32中间符号表       mid_symTable  
33目标符号表       unipic25d_symTable  
4目标文本          unipic25d_InFiles

符号系统实体类      entity.py  
llmEntity  
fileEntity  
dbEntity  
infoEnyity

### 梳理简单演算流程
即一些符号内部计算工具

文件读写方法都有  
1源文本  
2清洗文本  
词法 语法分析

mcl_ast.py  
mcl_grammar.py  
mcl_lexer.py

### 梳理复杂演算流程
预处理mcl_preprocess

ply解析mcl_plyparser  
llm解析mcl_llmparser  
正则解析mcl_regex_parser.py  
解析路由parser_route.py  
解析主模块mcl_allparser.py  
ast访问/符号搜集mcl_ast_visit.py

几何处理geom_conv.py

一轮转换mcl2mid_sTconv.py  
二轮转换mid_sTconv.py  
三轮转换mid2uni_sTconv.py  
中间符号保存mid2Files.py  
unipic符号保存uni2Files.py  
unipic符号生成.in文件 uni2inFiles.py

### 分析系统运行参数
系统参数配置文件，类的实例化对象

### 定义软件系统功能层 service/
转译流程服务  
magic2unipic.py

### 定义软件系统对外接口 controller/
暂无

## 智能辅助建模系统

### 需求分析
1.从自然语言/需求文档中抽取关键配置项
基于大模型的自然语言建模信息抽取方法

2.给出参数建议值或合理范围
面向 UNIPIC 的参数自动推荐与缺省补全机制

3.自动生成 UNIPIC 配置文件并串成一个可运行工程
基于工作流的半自动/自动建模系统




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



## UNIPIC器件示例
1.BWO

```markdown
==build.in==
unitScale = -3
backGround = PEC
geomAlgoTol = 1.0e-12

<GeomCtrl theGeomCtrl>
  <GeomBuilder vectorBuilder>
    nameid = vectorBuilder
    kind = vector
    name = axis
    type = Dim
    value = [0.0 0.0 100.0]
  </GeomBuilder>

  <GeomBuilder polyBuilder>
    kind = polygon
    nameid = polyBuilder
    name = voidarea
    type = polygon
    material = FREESPACE
    pnts = [0.0 25.0 60.0 0.0 23.0 60.0 0.0 23.0 70.0 0.0 11.0 82.0 0.0 11.0 124.0 0.0 17.0 124.0 0.0 17.0 126.0 0.0 13.0 130.0 0.0 13.0 134.0 0.0 17.0 138.0 0.0 17.0 142.0 0.0 13.0 146.0 0.0 13.0 150.0 0.0 17.0 154.0 0.0 17.0 158.0 0.0 13.0 162.0 0.0 13.0 166.0 0.0 17.0 170.0 0.0 17.0 174.0 0.0 13.0 178.0 0.0 13.0 182.0 0.0 17.0 186.0 0.0 17.0 190.0 0.0 13.0 194.0 0.0 13.0 198.0 0.0 17.0 202.0 0.0 17.0 206.0 0.0 13.0 210.0 0.0 13.0 214.0 0.0 17.0 218.0 0.0 17.0 222.0 0.0 13.0 226.0 0.0 13.0 230.0 0.0 17.0 234.0 0.0 17.0 238.0 0.0 13.0 242.0 0.0 13.0 246.0 0.0 17.0 250.0 0.0 17.0 254.0 0.0 13.0 258.0 0.0 13.0 262.0 0.0 15.0 265.0 0.0 15.0 267.0 0.0 23.0 321.0 0.0 23.0 331.0 0.0 25.0 331.0 0.0 25.0 600.0 0.0 0.0 600.0 0.0 0.0 0.0 0.0 9.0 0.0 0.0 9.499122807017544 56.9 0.0 9.5 57.0 0.0 10.0 57.0 0.0 10.0 56.9 0.0 10.0 0.0 0.0 25.0 0.0 0.0 25.0 60.0]
  </GeomBuilder>

  <GeomBuilder faceBuilder>
    nameid = faceBuilder
    kind = face
    name = polyFace
    wireName = voidarea
    isPlanar = 1
  </GeomBuilder>

  <GeomBuilder revolutionBuilder>
    nameid = revolutionBuilder
    kind = revolution
    name = revolModel
    base = polyFace
    mask = 1
    vector = axis
    material = FREESPACE
    type = oneWay
    angle = 360.0
  </GeomBuilder>

  <GeomBuilder selectionBuilder1>
    contextNodeName = revolModel
    kind = subFaceSelection
    mask = 2
    name = selection1
    refPnt = [0.0 17.5 0.0]
    materialType = INPUTMURPORT
  </GeomBuilder>

  <GeomBuilder selectionBuilder2>
    contextNodeName = revolModel
    kind = subFaceSelection
    mask = 3
    name = selection2
    refPnt = [0.0 12.5 600.0]
    materialType = OPENPORT
  </GeomBuilder>

  <GeomBuilder selectionBuilder3>
    contextNodeName = revolModel
    kind = subFaceSelection
    mask = 4
    name = selection3
    refPnt = [0.0 9.75 57.0]
    materialType = EMITTER
  </GeomBuilder>

  <GeomBuilder selectionBuilder4>
    contextNodeName = revolModel
    kind = subFaceSelection
    mask = 5
    name = selection4
    refPnt = [0.0 10.0 56.95]
    materialType = EMITTER
  </GeomBuilder>
</GeomCtrl>

<GridCtrl theGC>
  margin = 1
  waveLength = 0.1
  axis = z
  org = [0.0000,0.0000,0.0000]
  rDir = y
  <GridDefine gd1>
    dir = y
    kind = uniformGrid
    waveResolutionRatio = 200
  </GridDefine>

  <GridDefine gd2>
    dir = z
    kind = uniformGrid
    waveResolutionRatio = 200
  </GridDefine>
</GridCtrl>


==FaceBnd.in==
<FieldSrc MurVoltagePort>
  mask = 2
  kind = MurVoltagePort
  fileName = Default.h5
  <Function Vin>
    VOLTAGE_MAX = 500000.0
    TRISE = 1e-09
    kind = tFunc
    result = VOLTAGE_MAX*max(0.0,min(1.0,t/TRISE))
  </Function>
</FieldSrc>


==PtclSources.in==
<ParticleSource Emitter>
  <Emitter Emitter>
    field_enhancement = 1.0
    threshold = 2.3e+07
    kind = GaussEmitter
    outPtcl = Species
    maskVector = [4 5]
    applyTimes = [0.0 1e-05]
  </Emitter>
</ParticleSource>


==StaticNodeFLds.in==
<StaticNodeFLd ZRExpressionModel>
  axis = 2
  rDir = 1
  rMax = 0.6
  kind = ZRExpressionModel
  target = mag
  startCenter = [0.0 0.0 0.0]
  <Function Bz>
    component = 0
    kind = zrFunc
    result = 2.8/(1+exp((z-0.29)/0.02))
  </Function>

  <Function Br>
    component = 1
    kind = zrFunc
    result = 2.8/(2*0.02)*r*exp((z-0.29)/0.02)/((1+exp((z-0.29)/0.02))^2)
  </Function>
</StaticNodeFLd>


==FieldsDgn.in==
<FieldsDgn Dgn1>
  kind = VoltageDgn
  name = Vin1
  lineDir = r
  org = [0.01 0.01]
  end = [0.01 0.025]
</FieldsDgn>

<FieldsDgn Dgn2>
  kind = PoyntingDgn
  dir = z
  name = Poutout1
  lowerBounds = [0.01 0.01]
  upperBounds = [0.01 0.025]
</FieldsDgn>

<FieldsDgn Dgn3>
  kind = CurrentDgn
  name = Iz1
  dir = r
  lowerBounds = [0.06 0]
  upperBounds = [0.06 0.025]
</FieldsDgn>

<FieldsDgn Dgn4>
  kind = PoyntingDgn
  dir = z
  name = Poutout2
  lowerBounds = [0.49 0]
  upperBounds = [0.49 0.025]
</FieldsDgn>

<FieldsDgn Dgn5>
  kind = MagDgn
  component = dynamic
  dir = phi
  name = Bphi1
  location = [0.45 0.02]
</FieldsDgn>




==PML.in==
<PML PMLSetting>
  key = 1
  powerOrder = 3
  alpha = 0.0
  kappaMax = 40.0
  sigmaRatio = 7.5
</PML>


==Species.in==
<Species Species>
  charge = -1.6022e-19
  mass = 9.109e-31
  ptclCreationRate = 3.0
  kind = electron
  name = Species
</Species>


==GlobalSetting.in==
FilterMask = 0
InterpolateType = 1
emAdvanceOrder = 1
ptclTrackNum = 1
threadnum = 2
CFLScale = 9.0e-01
LangdonMarderDivParam = 0.0
chiParam = 1.0
emDamping = 1.0e-01
parabolicDamping = 2.0e-01
simulationTime = 3e-08
EMSolver = picMode
dynEMkind = SI_SC_PHM_Matrix
emDumpSwitch = ON
jDumpSwitch = ON
materialLib = D:\UNIPIC\Unipic2.5D_Training\UNIPIC20240819\bin\pic\MyRBWO\Material\material.xml
ptclDensityDumpSwitch = OFF
ptclDumpSwitch = ON
ptclTrackSwitch = OFF
rhoDumpSwitch = OFF
dumpStepVec = [1.0e-09 ]
dumpTimeNode = [1.0e-05 ]
ptclTrackProb = [ ]
ptclTrackTypes = [ ]


```

2.MILO

```markdown
==build.in==
unitScale = -3
backGround = PEC
geomAlgoTol = 1.0e-12

<GeomCtrl theGeomCtrl>
  <GeomBuilder vectorBuilder>
    nameid = vectorBuilder
    kind = vector
    name = axis
    type = Dim
    value = [0.0 0.0 100.0]
  </GeomBuilder>

  <GeomBuilder polyBuilder>
    kind = polygon
    nameid = polyBuilder
    name = voidarea
    type = polygon
    material = FREESPACE
    pnts = [0.0 76.0 358.4 0.0 76.0 371.2 0.0 143.0 371.2 0.0 143.0 400.0 0.0 76.0 400.0 0.0 76.0 412.8 0.0 143.0 412.8 0.0 143.0 441.6 0.0 76.0 441.6 0.0 76.0 454.4 0.0 143.0 454.4 0.0 143.0 483.2 0.0 86.0 483.2 0.0 86.0 496.0 0.0 143.0 496.0 0.0 143.0 524.8 0.0 86.0 524.8 0.0 86.0 537.6 0.0 143.0 537.6 0.0 143.0 566.4 0.0 86.0 566.4 0.0 86.0 579.2 0.0 143.0 579.2 0.0 143.0 608.0 0.0 96.5 608.0 0.0 96.5 620.8 0.0 143.0 620.8 0.0 143.0 998.4 0.0 96.5 998.4 0.0 96.5 672.0 0.0 86.0 672.0 0.0 86.0 960.0 0.0 0.0 960.0 0.0 0.0 764.8 0.0 50.0 764.8 0.0 57.5 764.8 0.0 57.5 750.0 0.0 57.5 441.6 0.0 57.5 0.0 0.0 143.0 0.0 0.0 143.0 358.4 0.0 76.0 358.4]
  </GeomBuilder>

  <GeomBuilder faceBuilder>
    nameid = faceBuilder
    kind = face
    name = polyFace
    wireName = voidarea
    isPlanar = 1
  </GeomBuilder>

  <GeomBuilder revolutionBuilder>
    nameid = revolutionBuilder
    kind = revolution
    name = revolModel
    base = polyFace
    mask = 1
    vector = axis
    material = FREESPACE
    type = oneWay
    angle = 360.0
  </GeomBuilder>

  <GeomBuilder selectionBuilder1>
    contextNodeName = revolModel
    kind = subFaceSelection
    mask = 2
    name = selection1
    refPnt = [0.0 100.25 0.0]
    materialType = INPUTMURPORT
  </GeomBuilder>

  <GeomBuilder selectionBuilder2>
    contextNodeName = revolModel
    kind = subFaceSelection
    mask = 3
    name = selection2
    refPnt = [0.0 119.75 998.4]
    materialType = OPENPORT
  </GeomBuilder>

  <GeomBuilder selectionBuilder3>
    contextNodeName = revolModel
    kind = subFaceSelection
    mask = 4
    name = selection3
    refPnt = [0.0 57.5 757.4]
    materialType = EMITTER
  </GeomBuilder>

  <GeomBuilder selectionBuilder4>
    contextNodeName = revolModel
    kind = subFaceSelection
    mask = 5
    name = selection4
    refPnt = [0.0 57.5 595.8]
    materialType = EMITTER
  </GeomBuilder>
</GeomCtrl>

<GridCtrl theGC>
  margin = 1
  waveLength = 0.1
  axis = z
  org = [0.0000,0.0000,0.0000]
  rDir = y
  <GridDefine gd1>
    dir = y
    kind = uniformGrid
    waveResolutionRatio = 25
  </GridDefine>

  <GridDefine gd2>
    dir = z
    kind = uniformGrid
    waveResolutionRatio = 25
  </GridDefine>
</GridCtrl>



==FaceBnd.in==
<FieldSrc MurVoltagePort>
  mask = 2
  kind = MurVoltagePort
  fileName = Default.h5
  <Function Vin>
    VOLTAGE_MAX = 1800000.0
    TRISE = 5e-09
    kind = tFunc
    result = VOLTAGE_MAX*max(0.0,min(1.0,t/TRISE))
  </Function>
</FieldSrc>



==PtclSources.in==
<ParticleSource Emitter>
  <Emitter Emitter>
    field_enhancement = 1.0
    threshold = 2.3e+07
    kind = GaussEmitter
    outPtcl = Species
    maskVector = [4 5]
    applyTimes = [0.0 1e-05]
  </Emitter>
</ParticleSource>



==CircuitModel.in==
<CircuitModel inductor1>
  name = inductor1
  kind = Inductor
  L = 100e-9
  dir = r
  lowerBounds = [0.8 0.0965]
  upperBounds = [0.8 0.143]
</CircuitModel>



==FieldsDgn.in==
<FieldsDgn Dgn1>
  kind = VoltageDgn
  name = Vin1
  lineDir = r
  org = [0.01 0.0575]
  end = [0.01 0.143]
</FieldsDgn>

<FieldsDgn Dgn2>
  kind = PoyntingDgn
  dir = z
  name = Poutout1
  lowerBounds = [0.01 0.0575]
  upperBounds = [0.01 0.143]
</FieldsDgn>

<FieldsDgn Dgn3>
  kind = VoltageDgn
  name = Vin2
  lineDir = r
  org = [0.34 0.0575]
  end = [0.34 0.143]
</FieldsDgn>

<FieldsDgn Dgn4>
  kind = PoyntingDgn
  dir = z
  name = Poutout2
  lowerBounds = [0.34 0.0575]
  upperBounds = [0.34 0.143]
</FieldsDgn>

<FieldsDgn Dgn5>
  kind = VoltageDgn
  name = Vin3
  lineDir = r
  org = [0.7 0.086]
  end = [0.7 0.143]
</FieldsDgn>

<FieldsDgn Dgn6>
  kind = VoltageDgn
  name = Vin4
  lineDir = r
  org = [0.7 0.0575]
  end = [0.7 0.086]
</FieldsDgn>

<FieldsDgn Dgn7>
  kind = CurrentDgn
  name = Iz1
  dir = r
  lowerBounds = [0.4 0.066]
  upperBounds = [0.8 0.066]
</FieldsDgn>

<FieldsDgn Dgn8>
  kind = CurrentDgn
  name = Iz2
  dir = r
  lowerBounds = [0.6654 0.084]
  upperBounds = [0.96 0.084]
</FieldsDgn>

<FieldsDgn Dgn9>
  kind = PoyntingDgn
  dir = z
  name = Poutout3
  lowerBounds = [0.9984 0.0965]
  upperBounds = [0.9984 0.143]
</FieldsDgn>

<FieldsDgn Dgn10>
  kind = ElecDgn
  dir = r
  name = Er1
  location = [0.9984 0.14]
</FieldsDgn>

<FieldsDgn Dgn11>
  kind = ElecDgn
  dir = z
  name = Ez1
  location = [0.9984 0.14]
</FieldsDgn>



==PML.in==
<PML PMLSetting>
  key = 1
  powerOrder = 3
  alpha = 0.0
  kappaMax = 40.0
  sigmaRatio = 7.5
</PML>


==Species.in==
<Species Species>
  charge = -1.6022e-19
  mass = 9.109e-31
  ptclCreationRate = 3.0
  kind = electron
  name = Species
</Species>


==GlobalSetting.in==
FilterMask = 0
InterpolateType = 1
emAdvanceOrder = 1
ptclTrackNum = 1
threadnum = 2
CFLScale = 9.0e-01
LangdonMarderDivParam = 0.0
chiParam = 1.0
emDamping = 1.0e-01
parabolicDamping = 2.0e-01
simulationTime = 6e-08
EMSolver = picMode
dynEMkind = SI_SC_PHM_Matrix
emDumpSwitch = ON
jDumpSwitch = ON
materialLib = D:\UNIPIC\Unipic2.5D_Training\UNIPIC20240819\bin\pic\MyRBWO\Material\material.xml
ptclDensityDumpSwitch = OFF
ptclDumpSwitch = ON
ptclTrackSwitch = OFF
rhoDumpSwitch = OFF
dumpStepVec = [1.0e-09 ]
dumpTimeNode = [1.0e-05 ]
ptclTrackProb = [ ]
ptclTrackTypes = [ ]

```

3.vir100_25

```markdown
暂时省略
```

## 补充两款软件的业务逻辑
### 新建工程
1.统一界面操作

<font style="color:rgb(0,0,0);">新建工程->选择工程类型为2.5D->选择工作平面如YZ平面</font>

2.UNIPIC文件

直接编辑.in文件

3.MAGIC命令

直接编辑.m2d文件

### 全局元素-变量、几何体、函数
1.统一界面操作

无

2.UNIPIC文件

无

3.MAGIC命令

变量定义命令 ASSIGN/缺省 ......

几何体定义命令 POINT LINE AREA VOLUME(3D)

函数定义命令 FUNCTION

4.MAGIC命令到UNIPIC文件转换方法

处理定义中的依赖问题，将所有元素导入到转换方法的总作用域中，用于后续传参



### 几何建模
1.统一界面操作

方法1：草图建模：从点集txt导入->绕转

方法2：选择基本几何体/进行基本几何操作

2.UNIPIC文件--build.in

注：UNIPIC默认背景材料为PEC，材料为VOID

2D几何体、旋转轴、绕转体

3.MAGIC命令

注：给全局变量中的几何体定义材料，有材料属性的为模型，模型一般为CONDUCTOR

材料定义 CONDUCTOR

4.MAGIC命令到UNIPIC文件转换方法

将材料属性加入到对应的几何体参数列表中，将视情况进行一些几何算法，将建模用到的几何体单独保存

根据UNIPIC目标格式调整点坐标的次序、单位，以及几何体定义方式等等



### 参考点选择
1.统一界面操作

不需要提前操作，在具体需要设置端口时候再手动选择参考点

2.UNIPIC文件--build.in

参考点选择(即selectionBuilder，类型参数 kind 包括INPUTMURPORT、OPENPORT、EMITTER)

3.MAGIC命令

无，通过全局几何体名来直接指定参考点/线/面

### 网格参数
1.统一界面操作

点击Meshes->Mesh2D->设置网格属性

2.UNIPIC文件--build.in

网格参数 

3.MAGIC命令

网格定义 GRID

4.MAGIC命令到UNIPIC文件转换方法

将网格命令中的参数？？？填到build.in中

### 注入波
1.统一界面操作

端口设置->选择注入波->选择参考点->注入波(MurVoltagePort)->注入波参数（函数等）

2.UNIPIC文件--FaceBnd.in``

参数：参考点(类型INPUTMURPORT)对应mask

参数：类型(默认MurVoltagePort)

参数：函数定义

3.MAGIC命令

PORT命令(POSITIVE, 且有INCOMING参数)

4.MAGIC命令到UNIPIC文件转换方法

将端口参考点定义在build.in

将注入波参数填入FaceBnd.in

### 开放端口
1.统一界面操作

端口设置->开放端口->选择参考点

2.UNIPIC文件--build.in

定义端口参考点即可，无须单独定义开放端口参数

3.MAGIC命令

PORT命令(NEGTIVE, 无参数)

4.MAGIC命令到UNIPIC文件转换方法

将端口参考点定义在build.in

### 发射
1.统一界面操作

端口设置->粒子发射->选择参考点->阴极发射->选择发射类型(如：高斯发射)->阴极发射参数

**2.UNIPIC文件**--PtclSources.in

参数：kind(类型有：BeamEmitter、CLEmitter、CylGyroEmitter、FNEmitter、Furman、GaussEmitter、TEmitter、ConstantSEY、Vaughan)

参数：场增强因子(默认field_enhancement = 1.0)，<font style="color:rgba(0, 0, 0, 0.9);">模拟表面微观突起（如金属毛刺）导致局部电场增强</font>

参数：阈值电场(典型值threshold = 1e+7)

参数：粒子种类（如电子、离子，默认outPtcl = Species，Species在其它文件定义）

参数：参考点标记列表 maskVector = [ ]

参数：发射时间窗口，如 applyTimes = [0.0 7.0e-08]

......(不同类型的参数不同)

**3.MAGIC命令**

EMISSION命令

EMIT命令

直接指定发射点/线/面

例如：

EMISSION EXPLOSIVE NUMBER 10 ;

EMIT EXPLOSIVE CATHODE EXCLUDE NO_EMISSION ;

4.MAGIC命令到UNIPIC文件转换方法

将端口参考点定义在build.in

选择对应的阴极发射类型

将阴极发射参数写入PtclSources.in



### 引导磁场
1.统一界面操作

静场加载->选择磁场类型（如ZRExpressionModel）->设置引导磁场参数

2.UNIPIC文件--StaticNodeFlds.in

默认参数：

  axis = 2

  rDir = 1

  rMax = 0.0

  kind = ZRExpressionModel

  target = mag

  startCenter = [0.0 0.0 0.0]

<Function Br>标签

      <Function Bz>标签

3.MAGIC命令

未知

4.MAGIC命令到UNIPIC文件转换方法

未知

### 诊断参数
1.统一界面操作

电磁场诊断->点击诊断类型->设置诊断参数

2.UNIPIC文件--FieldsDgn.in

常见诊断类型的模板：

 <FieldsDgn fieldDiagnosis001>

  dir = z

  kind = ElecDgn

  name = ElecDgn

  location = [5.50000000000000044e-01 1.29999999999999994e-02 ]

  </FieldsDgn>

  <FieldsDgn fieldDiagnosis003>

  kind = VoltageDgn

  lineDir = phi

  name = VoltageDgn

  end = [0.00000000000000000e+00 0.00000000000000000e+00 ]

  org = [0.00000000000000000e+00 0.00000000000000000e+00 ]

  </FieldsDgn>

  <FieldsDgn fieldDiagnosis004>

  dir = phi

  kind = CurrentDgn

  name = CurrentDgn

  lowerBounds = [0.00000000000000000e+00 0.00000000000000000e+00 ]

  upperBounds = [0.00000000000000000e+00 0.00000000000000000e+00 ]

  </FieldsDgn>

3.MAGIC命令

<font style="color:black;">OBSERVE命令</font>

4.MAGIC命令到UNIPIC文件转换方法

将OBSERVE命令的参数解析后，映射并填入FieldsDgn.in

### 仿真参数
1.统一界面操作

<font style="color:rgb(0,0,0);">EngineController</font>->设置全局仿真参数->点击Run

2.UNIPIC文件--GlobalSetting.in

默认即可

3.MAGIC命令

未知

4.MAGIC命令到UNIPIC文件转换方法

未知



## UKCS知识范畴思想简介
一套知识描述体系，可以用来指导代码开发、知识表示等领域

将知识按照描述对象的本体划分为十大范畴  
具体细节不重要



## 文件模块导入方法
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



# 论文行文逻辑梳理
##  第一次梳理

工作不是“通用程序语言翻译（program-to-program translation）”，  
而是“领域建模语言到配置空间的语义映射（semantic mapping from DSL to configuration space）  

### 1️⃣ 转译目标不同：执行语义 vs 建模语义
**传统高级语言转译器（C → C++ / Python → C++ 等）**

+ 输入：可执行程序
+ 输出：可执行程序
+ 核心目标：

**保持控制流、数据流和执行语义等价**

+ 因此必须：
    - 构建完整 AST
    - 保留语句结构
    - 严格处理表达式、作用域、控制结构

---

**你的转译器（MAGIC → UNIPIC）**

+ 输入：仿真建模脚本（DSL）
+ 输出：仿真工程配置文件
+ 核心目标：

**保持建模意图与物理/工程语义一致**

+ 因此你只需要：
    - 抽取关键参数
    - 理解对象间的语义关系
    - 在目标系统中重组这些关系

👉 **你不关心“语句怎么执行”，只关心“模型在仿真系统中代表什么”。**

---

### 2️⃣ AST 在你这里的角色发生了“功能降级”
这是你提到的关键点。

在经典转译器中：

AST = 程序的核心语义载体

在你的系统中：

AST = **信息抽取的中间工具**

你使用 AST / PLY 的目的不是：

+ 重写语句
+ 变换控制结构

而是：

+ **定位参数**
+ **解析命令结构**
+ **辅助构建符号表**

学术上，这可以明确表述为：

_AST is used as an intermediate representation for semantic information extraction rather than structural program transformation._

这是一个**非常标准、非常安全的学术说法**。

---

### 3️⃣ 转换逻辑的位置不同：语法驱动 vs 规则驱动
你已经意识到一个非常重要的点：

**真正的“转译”并不发生在 AST 层，而发生在后续的规则映射模块。**

在你这里：

+ 解析阶段：
    - 目的：**获得足够完整、无歧义的语义信息**
+ 转换阶段：
    - 目的：**根据目标软件的建模规范，人工设计映射规则**

这在学术上被称为：

**rule-based semantic reconstruction**  
或  
**domain-specific rule-driven transformation**

而不是传统的：

syntax-directed translation



### ✦ 表述模板 1（方法定位型，强烈推荐）
与通用程序语言之间的翻译任务不同，本文所研究的转译问题并不以保持程序执行语义为目标，而是面向特定仿真领域的建模语义映射。  
MAGIC 输入脚本本质上是一种领域特定建模语言，其语句用于描述仿真对象、物理参数及其相互关系；而 UNIPIC 目标文件则以配置文件形式组织仿真模型。因此，本文在解析阶段仅利用语法分析手段抽取关键建模信息，而不对源语言的语句结构进行逐语句转换，真正的转译过程发生在后续基于领域规则的语义重构阶段。

---

### ✦ 表述模板 2（AST 角色差异型）
在传统高级语言转译器中，抽象语法树通常作为程序结构与执行语义的核心表示，用于指导后续的语句级重写与代码生成。相比之下，本文中 AST 的作用主要体现在建模信息的结构化提取上，其目标并非保持语句级结构一致性，而是为领域语义的识别与重组提供可靠的中间表示。

---

### ✦ 表述模板 3（规则驱动转换型）
本文采用基于规则的语义映射策略，将解析得到的中间语义表示映射为 UNIPIC 系统所需的配置项。该策略强调人工可控的领域规则设计，以适应不同器件类型与建模约束的差异，避免将复杂的工程语义隐式地编码于语法结构转换之中。





第四章或第三章的**方法论总论断**：

**由于源语言与目标语言在表达层级、语义粒度以及建模范式上的本质差异，本文所研究的问题不适合采用传统基于 AST 的语句级转译流程；在规则数量与语义组合呈指数增长的情况下，引入具备语义泛化能力的大语言模型成为一种结构上必要的解决方案。**

### 1️⃣** 传统转译器隐含了一个前提，而你的问题不满足**
**经典编译 / 转译器设计****，隐含了一个非常重要的前提：**

**源语言与目标语言共享“相似的抽象层级”**

**比如：**

+ **C **↔** C++**
+ **MATLAB **↔** Julia**
+ **Python **↔** Java**

**它们都有：**

+ **控制流**
+ **数据流**
+ **表达式**
+ **作用域**
+ **语句执行顺序**

**所以：**

+ **AST 是“程序语义的主要载体”**
+ **转换是“结构保持 + 语义替换”**

---

**而你的问题中：**

+ **MAGIC：**
    - **是****命令式 + 过程式 + 建模 DSL**
    - **强调“描述如何构建模型”**
+ **UNIPIC：**
    - **是****声明式 + 配置驱动**
    - **强调“模型是什么样”**

👉** ****抽象层级不对齐，导致 AST 失效为主语义载体。**

**学术表达上，这是：**

_There is a semantic level mismatch between the source DSL and the target configuration language._

---

### 2️⃣** AST 在你这里无法承载“真正的转译复杂度”**
**你已经意识到：**

+ **AST 能解决：**
    - **命令结构**
    - **参数绑定**
+ **AST 无法解决：**
    - **跨命令依赖**
    - **物理建模约束**
    - **器件类型差异**
    - **参数隐含语义**

**也就是说：**

**语法复杂度是线性的，  
****语义复杂度是组合爆炸的。**

**传统转译器设计的是：**

+ **“语法主导的复杂性”**

**而你面对的是：**

+ **“语义主导的复杂性”**

**这在学术上是一个非常清晰的分界线。**

---

### 3️⃣** 你的转译问题本质是“语义重构”，不是“语法变换”**
**你不是在做：**

**statement → statement**

**而是在做：**

**modeling intent → configuration realization**

**也就是说：**

+ **输入不是“程序”**
+ **输出不是“程序”**
+ **中间也不应该是“程序 AST”**

**而是：**

+ **参数空间**
+ **对象关系**
+ **物理意义映射**

**这决定了：**

+ **规则一定是“跨结构的”**
+ **规则一定是“上下文相关的”**
+ **规则无法被局部语法触发完全覆盖**

---

为什么说“规则爆炸”在你的问题中是不可避免的？

**这是你引入 LLM 的****真正、硬核的理由****。**

---

### 1️⃣** 规则爆炸不是工程实现问题，而是组合复杂性问题**
**我们把你面对的规则类型拆开：**

+ **器件类型：BWO / MILO / Vir / …**
+ **建模阶段：几何 / 网格 / 端口 / 发射 / 诊断 / …**
+ **参数约束：范围 / 单位 / 依赖关系**
+ **目标系统限制：UNIPIC 支持方式差异**

**如果你****纯规则化****，规则数量是：**

**O(器件 × 模块 × 参数 × 约束)**

**这是****指数级组合空间****。**

**关键点是：**

**这些规则不是彼此独立的。**

**例如：**

+ **同一个端口参数，在不同器件中含义不同**
+ **同一个发射模型，在不同几何上下文中合法性不同**

---

### 2️⃣** 传统转译器为什么“天生不擅长”解决这类爆炸？**
**传统转译器规则有两个特征：**

1. **局部触发**
    - **一个语法模式 → 一个转换规则**
2. **确定性输出**
    - **同样输入 → 同样输出**

**但你这里的规则：**

+ **依赖全局上下文**
+ **依赖历史建模步骤**
+ **依赖目标系统隐含规范**

**这会导致：**

+ **规则链极长**
+ **维护成本指数增长**
+ **稍微扩展就整体崩塌**

---

### 3️⃣** 你真正需要的不是“更多规则”，而是“规则的泛化能力”**
**这是引入 LLM 的****决定性原因****。**

**你需要的是：**

**在有限显式规则基础上，对未覆盖组合进行合理推断**

**而这正是：**

+ **统计学习**
+ **语义泛化**
+ **上下文推理**

**所擅长的。**

---

为什么“引入 LLM”在你这里是“结构必然”，而不是“技术潮流”

**这一点你一定要写清楚，否则会被误解为“跟风”。**

---

### 1️⃣** LLM 在你系统中的角色是“语义压缩器”**
**你并没有让 LLM：**

+ **随意生成配置**
+ **直接输出 .in 文件**

**你让它做的是：**

+ **在规则缺失处补全**
+ **在规则冲突处选择**
+ **在规则组合爆炸处泛化**

**学术上可以这样说：**

_LLM is introduced as a semantic generalization component to mitigate rule explosion in domain-specific transformation._

**这是****非常高级、而且非常正当的表述****。**

---

### 2️⃣** 你的系统实际上是“规则 + LLM”的混合推理系统**
**从 AI 角度看，你的系统是：**

+ **Symbolic system（规则转译器）**
+ **Statistical system（LLM）**

**这正是当前 AI 研究里非常重要的一条路线：**

**Neuro-symbolic / Hybrid AI**

**你不是“用 LLM 替代规则”，  
****而是“用 LLM 托底规则”。**

---

### 3️⃣** 如果不引入 LLM，会发生什么？（这是个反证）**
**你可以非常理直气壮地写：**

+ **不引入 LLM：**
    - **规则数量不可控**
    - **系统可扩展性迅速下降**
    - **新器件引入成本过高**
+ **引入 LLM：**
    - **显式规则数量受控**
    - **隐式规则由模型泛化**
    - **工程维护成本显著下降**

## 第二次梳理

从全电磁 PIC软件架构角度出发，重新对任务进行表述，与通用计算进行区分

软件 = 数据 + 对数据的操作过程

示意图如下：

\```

​    			   state_1(data) --------(calculate)----------> state_2(data)

概念层	|  状态1语义                                                 | 状态2语义

逻辑层    |  数据1结构                                                 | 数据2结构 

存储层         存储方式

\```

模拟软件是通过数据的概念建模、逻辑设计，以及对数据的操作算法，来达到对另一变化过程的模拟预测

从这个视角对全电磁 PIC软件架构进行分析

全电磁 PIC软件可以分为以下几个流程和数据：

工程文件---建模操作--->输入文本  [---前处理---> 描述性参数 ---求解---> 计算结果 ---数据后处理]---> 处理结果

[]里面的是内核处理过程

### 每个数据节点、数据操作的具体分析

#### 工程文件 + 建模操作

打开软件创建的工程文件，可能是前端操作，生成内核可以解析的输入文本

也可能是编写脚本文件，编译后生成内核可以解析的文本

概念上，描述了粒子模拟过程所需要的文本参数构建过程

逻辑上，包含了一些有时序关系的文本列表

存储上，往往是一个计算机文件

#### 输入文本

描述性的文本，未必是一个外部可打开的文件

是建模完成后形成的完整输入文本，描述了模拟过程所需要的完整模型、参数等等

概念上，描述了软件模拟内核需要的输入参数

逻辑上，是一个结构化的文本

存储上，可以是一个计算机文件，也可以是计算机内存中的数据结构

#### 前处理(内核)

子模块1：输入解析与一致性校验

- 解析配置；校验 CFL（Δt 与 Δx/Δy/Δz）、Yee 网格错位一致性、粒子权重与密度量纲、边界互斥（PML vs 周期等）；生成 `input_hash`。

子模块2：网格与 Yee 结构初始化

- 分配 Ex/Ey/Ez、Bx/By/Bz、J/ρ；构造 Yee 错位索引；初始化 ghost 区；若启用 PML，分配并初始化辅助变量。

子模块3：边界条件对象装配

- 建立场边界算子（导体/开边界/周期/PML/注入边界）；建立粒子边界（吸收/反射/SEE）；形成统一的边界处理接口。

子模块4：粒子初始化与空间索引

- 按分布生成粒子（位置与速度/动量）；构建 cell binning/tile；初始化 RNG（若需要），保证可复现。

子模块5：诊断与输出管线初始化

- 注册探针/截面/谱分析任务；设定采样频率与统计窗口；建立 HDF5/Zarr 数据集与 chunk 策略。

#### 描述性参数

前处理后形成的，在进程内存空间中定义的变量数据，描述了模拟过程所需要的完整模型、参数等等

概念上，描述了软件模拟内核后续求解和后处理需要的输入参数

逻辑上，是一个结构化的文本

存储上，因为模拟进程而定义在计算机内存中的数据结构

#### 求解(内核)

> EM-PIC 主循环的算子序列（离散实现可略有差异）：

1. **J 沉积（守恒）**
2. **Maxwell 更新（E/B）**
3. **E/B 插值到粒子**
4. **粒子推进（pusher）**
5. **粒子边界/碰撞**
6. **诊断采样**
7. **检查点/快照（按策略）**

子模块1：电流沉积（Current Deposition, charge-conserving）

- 将粒子运动产生的电流沉积到 Yee 网格；推荐使用**电流守恒沉积**（如 Esirkepov 类方法）以满足离散连续性方程，降低数值发散与噪声。

子模块2：场更新（Maxwell FDTD on Yee grid）

- 按离散 Maxwell 方程推进：
  - `B^{n+1/2} = B^{n-1/2} - Δt * curl(E^n)`
  - `E^{n+1} = E^n + Δt * (curl(B^{n+1/2}) - J^{n+1/2}/ε0)`
     并施加 PML/导体/周期/注入等边界条件。

子模块3：必要时的电荷/场清洗（Charge/Field Cleaning，可选但常用）

- 在数值误差累积导致 Gauss 约束偏离时，执行 divergence cleaning（如 GLM / Poisson-based correction）以控制数值电荷积累。

子模块4：场插值（Gather：Grid → Particles）

- 按与沉积一致的形函数将 E/B 插值到粒子位置；保证“沉积—插值”的一致性以减少自力与噪声。

子模块5：粒子推进（Particle Pusher）

- 使用 Boris（非相对论常用）或 Vay（相对论/强磁场更稳）推进粒子动量与位置；更新 `cell_id` 并处理跨 cell 迁移。

子模块6：粒子边界相互作用

- 处理越界粒子（吸收/反射/周期映射）；二次电子发射（SEE）或再注入；更新壁面通量诊断。

子模块7：碰撞与反应（PIC-MCC，可选）

- 执行 Monte Carlo 碰撞（弹性/激发/电离等）；生成/删除粒子；更新能量分布与种类标记。

子模块8：诊断采样与在线统计

- 采样能量守恒项（粒子动能+场能+边界功），电流/电荷谱，密度/温度空间分布，频谱（FFT 窗口）等；支持滑动窗口平均与方差。

子模块9：检查点/快照写入（按策略）

- 写入一致性检查点用于断点续算；按需写快照（避免每步写造成 IO 瓶颈）；支持原子写/双文件切换保证可靠恢复。

> EM-PIC 主循环的算子序列（离散实现可略有差异）：

1. **J 沉积（守恒）**
2. **Maxwell 更新（E/B）**
3. **E/B 插值到粒子**
4. **粒子推进（pusher）**
5. **粒子边界/碰撞**
6. **诊断采样**
7. **检查点/快照（按策略）**

#### 计算结果

经过求解器完整模拟过程后得到的结果

概念上，描述了软件模拟内核求解结果，以及后处理需要的输入参数

逻辑上，是一个结构化的文本

存储上，因为模拟进程而定义在计算机内存中的数据结构

#### 后处理

子模块1：统计量与器件指标生成

- 输出放电电流、电压功率、能量耦合效率、粒子/能量通量、空间均匀性、谱密度等器件级指标；对稳态段做时间平均/相位平均（RF 常用）。

子模块2：空间场与粒子分布可视化数据准备

- 重建剖面、截面、等值面；对粒子分布生成相空间投影与能谱；可做下采样/多分辨率以支撑交互可视化。

子模块3：导出与报告

- 导出标准格式（VTK/CSV）；生成关键曲线图与报告结构（摘要、设定、守恒性与误差评估、主要结论）

#### 处理结果

经过求解器完整模拟过程后得到的结果

概念上，描述了软件模拟内核求解结果的后处理结果

逻辑上，是一个结构化的文本

存储上，因为模拟进程而定义在计算机内存中的数据结构，可能通过文件读写模块生成了结果文件

### 问题背景重述

MAGIC的工程文件是文件形式的，所有的文件都保存在.m2d同级的文件夹下面。

.m2d描述的是建模过程，经过MCL语言的编译器解析后，生成一系列文件，

继而直接开始前处理->求解->后处理流程

UNIPIC的工程文件是.FCStd格式，承载着所有的项目数据，可以被软件的前端读取展示、并进行编辑

.FCStd格式文件可以生成内核可以读取的Simulation文件夹，里面有所有的.in文件，描述了内核运行需要的模型和所有流程需要的参数。

将MAGIC项目文件转译到UNIPIC中，可行的语义对齐点是建模结束后生成的输入文本。

但MAGIC的输入文本是封闭的，无法拿到，只能从工程文件开始转译；

而UNIPIC的输入文本是Simulation文件夹中的.in文件。

这样一来，将.m2d文件转换到Simulation文件夹中的.in文件，本质上包括了两个环节，第一个环节是m2d文件的语义解析，将建模脚本映射到输入文本，第二个环节是将MAGIC的输入文本语义映射到UNIPIC的输入文本。

由于不存在MAGIC的输入文本格式，可以构建一个通用的输入文本语义中介，关于输入文本的语义中介，

概念上，描述了软件模拟内核需要的所有输入参数，包括模型、前处理参数、求解参数、后处理参数，也可能存在一些软件运行环境、软件系统相关的参数
逻辑上，是一个结构化的文本
存储上，是计算机内存中的数据结构，但也需要保存为文件

可以将其命名为建模完成时语义中介文本

### 解决方案

建模完成时语义中介文本设计方案：
概念上，描述了软件模拟内核需要的所有输入参数，包括模型、前处理参数、求解参数、后处理参数，也可能存在一些软件运行环境、软件系统相关的参数
逻辑上，是一个结构化的文本，选择json
存储上，是计算机内存中的json对象和json文件


## 第三次梳理(论文章节安排)
第三章提出问题与方法边界；
第四章构建确定性的规则转译基线；
即完整的规则转译器
第五章通过引入 LLM，实现对复杂建模语义的泛化补全与系统扩展。
5.1 引入LLM做解析，将m2d文件解析为ParserResult，后半部分的转译还继续走规则转译器，这样可以省去预处理、词法分析、语法分析
5.2 引入LLM做转换，将ParserResult转换为中间语义文本，这样可以省略掉复杂的命令处理阶段，后面的逻辑映射、字符映射都可以继续走规则方法

5.1已经开发好了，在解析器前面加了一个分类器做路由，可以在新增命令时候，根据命令类型，路由到LLM解析器，用于快速验证
5.2还没解决，目前考虑的是，需要根据语义，找到每个语义元素所依赖的上下文块(考虑字符匹配)，同时要知道映射规则(考虑通过语义检索、手动修改、LLM推荐等多种方法)，LLM翻译前后的字段逻辑(只能手动设计，考虑代码逻辑)


# 开发需求
PLY规则转译器  
智能辅助建模系统

# 项目进度与时间节点
开发进度：

2025.7 PLY规则转译器已经基本完成

2025.9 规则转译器开发基本完成



硕士毕业进度：  
2025.11 完成规则转译器部分小论文撰写，参加学术会议汇报

2025.12.17 现在



未来节点：  
2025.12.19 课题组组会

2026.1.4 第二次组会

2026.1.31 放假前完成大部分开发

春节期间完成全部开发任务、论文第一二章

2026.3.1 开学后开始撰写论文

2026.3.31 交初稿

# 规则转译器项目文档
## 规则转译器需求分析
需求很明确，  
在业务逻辑方便，开发一款稳定可用的规则转译器，实现一些基本功能；  
在个人硕士毕业论文方面，作为PIC软件辅助建模系统的一个核心功能，是第一个工作内容，作为论文第三章

## 规则转译器系统的整体分析
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



## 规则转译器开发迭代记录
### 迭代周期1：3个月
完整开发第一版预处理器、词法、语法分析器、基础的转换逻辑

### 迭代周期2：2个月
根据仿真验证中存在的问题，重构代码、修复逻辑、梳理完善代码结构

### 迭代周期3：1个月
配合未来的仿真建模系统，做代码流程拆解、梳理  
整理总结文档

## 规则转译器设计思路总结
转译器采用“预处理—解析—转换”的流水线式架构，其目标是在保证跨平台语义一致性的前提下，实现对 MAGIC 输入文件的自动化与高效处理。

整体流程被进一步划分为多个子模块：

预处理器负责将输入.m2d文件格式标准化；

解析路由选择PLY/正则方法来解析参数，方便灵活地将MAGIC的MCL脚本命令解析为json文件

规则解析器承担词法与语法分析任务；正则解析器利用正则表达式提取简单命令的参数；二者通过符号搜集模块汇合为一个List[Dict]列表。

转换器负责将解析出的json文件进行三轮转换得到UNIPIC符号表，具体来说是在上下文环境下完成命令处理、符号表构建、几何处理、符号映射等等。

第一轮是magic命令处理，即mcl2mid_conv

第二轮是中间符号处理，即mid_conv

第三轮是中间符号到unipic符号，即mid2uni_conv  
最终由.in文件生成器生成UNIPIC的类似xml/ini混合风格的配置文件.



## 规则转译器代码设计总结
架构设计思想参考UKCS知识范畴思想、采用分层方法设计  


```markdown
src  
├── api  
│   └── controller/     //这个项目没用到  
├── core_cac  
│   ├── cac_entity.py  
│   ├── cac_flows.py  
│   ├── gemo_conv.py  
│   ├── get_geometry_results.py  
├── core_symbol  
│   ├── symbolBase.py  
│   ├── rules.py  
│   ├── single_flows/
│   │   ├── mcl_ast.py
│   │   ├── mcl_grammar.py
│   │   ├── mcl_lexer.py  
│   ├── muti_flows/
│   │   ├── mcl_allparser.py
│   │   ├── mcl_preprocess.py
│   │   ├── mclparser/
│   │   │   ├── mcl_ast_visit.py
│   │   │   ├── mcl_plyparser.py
│   │   │   ├── mcl_regex_parser.py
│   │   │   ├── parser_classifier.py
│   │   │   └── mcl_llmparser.py
│   │   ├── conv/
│   │   │   ├── mcl2mid_sTconv.py
│   │   │   ├── mid2Files.py
│   │   │   ├── mid2uni_sTconv.py
│   │   │   ├── mid_sTconv.py
│   │   │   ├── uni2Files.py
│   │   │   └── uni2inFiles.py
│   │   └── utils  
├── m2u_transpiler  
│   ├── magic2unipic.py  
│   ├── model_builder.py  
│   └── m2u_config  
└── mn2u_modeling
```

调用关系是：

严格单向调用  
m2u_transpiler/mn2u_modeling为服务层，可以调用core_cac、core_symbol模块。

core_symbol可以调用core_cac


简单来说  
core_symbol层中定义基本数据类、及其简单符号表征、模拟方法、时序变化逻辑；

单一实体的时序变化逻辑放到single_flows子文件夹，多个实体交互的时序变化逻辑放到muti_flows子文件夹中。  
core_cac层中定义一些不涉及业务逻辑实体状态的符号演算方法、模型、算法等，如字符处理，排序，几何算法等等。  
最终由对应的system层调用，封装为一个业务service  
api层中由controller层调用service层，service层调用complex_cac、core_cac、core_symbol模块，向外部提供接口

这样一来，核心的业务逻辑代码只需要定义到system层，api层，底层的symbol层和cac层都可以通用



## 规则转译器的规则细节
### 预处理阶段
输入.m2d文本

流程1：

1.注释过滤

2.跨多行命令合并为一行

流程2：

1.不支持命令/命令参数的过滤

2.POINT变量表， LINE/AREA命令中展开POINT变量

流程3：

1.识别命令名

2.命令字符处理：FUNCTION命令中+-*/)(符号前后加空格、

3.输出结构化数据（加上行号、命令名）

流程4：

1.单位处理：ASSIGN、POINT、LINE、AREA命令中默认单位补充、单位解析、单位格式统一

2.ASSIGN、POINT、LINE、AREA命令变量名识别

流程5：

处理 SYS$xxx 引用：去掉直接依赖/链式依赖SYS$xxx变量的ASSIGN、POINT、LINE、AREA命令

### 解析阶段
流程1：解析路由阶段

解析路由是一个字典，用于将命令名映射到解析器名称["ply","regex","llm"]

流程2：解析阶段

1.拿到预处理、路由后的命令行，逐行执行解析命令

2.1 ply解析器

词法分析

语法分析

语法树访问（符号收集）：将语法树节点信息输出到json

2.2 regex解析器

正则提取参数，输出到json

2.3 llm解析器

还没开发  
3.将解析结果汇总

```python
@dataclass
class ParseResult:
    """
    解析器统一返回的内部对象（仅在内存流转；最终会被转换为对外 dict）。
    属性字段：
        lineno     : 过滤后行号（预处理/路由决定）
        command     : 命令关键字（如 "LINE"/"AREA"/"EMISSION"...）
        payload     : 语义结果（供转换器使用）
        parser_kind : 解析器名（"PLY"|"REGEX"|"LLM" 或自定义）
        ok          : 是否成功解析出语义结果
        errors      : 错误/告警信息列表
        text        : 原始单行命令文本（规范化后的）
    """
    lineno: int
    command: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    parser_kind: str = ""
    ok: bool = False
    errors: List[str] = field(default_factory=list)
    text: str = ""
```

### 转换阶段
流程1：一轮转换 mcl2mid_sTconv.py

1.输入的是List[Dict]，对于每一条命令的解析结果，根据命令名调用对应的处理方法，对解析出来的结果进行初步处理，映射到统一语义表中，即中间符号表（mid_symbolTable->）

中间符号的具体：

```python
class MidSymbolTable():
    """
    中间符号表类，表示MAGIC符号表一轮转换后的符号表
    """
    def __init__(self):
        self.props = {}
        self.symbol_table = {}
        self.functions = {}
        self.geom: Dict[str, Dict[str, Any]] = {
            "points": {},    # name -> (qx, qy)
            "lines": {},     # name -> [(qx, qy), ...]
            "areas": {},     # name -> {"type": a_type, "points": [(qx,qy),...], ...}
        }
        self.grid = {'X1': -1.0, 'X2': -1.0, 'X3': -1.0}
        self.ports = {}
        self.emits = []
        self.observes = []
        self.presets = {}
        self.inductor = []
        self.FieldsDgn = []
        self.FoilModel = []

        self.area_entities = {}
        self.void_area = {}
        self.geom_other_entity = {}
        self.result = {}
```

流程2：二轮转换 mid_sTconv.py

1.AREA区域转换:金属区域List 计算所围出来真空空腔区域

2.输入真空空腔区域、金属区域、发射命令参数，计算发射区域，以及发射区域的参考点



流程3：三轮转换 mid_sTconv.py

输入处理后的中间符号

生成UNIPIC软件的符号表的json，格式为Dict[str,List]

在此过程中给一些list中的元素标序号

依次生成：  
buildIn

FaceBndIn

PtclSourcesIn

PMLIn

SpeciesIn

FieldsDgnIn

StaticNodeFLdsIn

CircuitModelIn

FoilModelIn

GlobalSettingIn



流程4：生成.in文件 uni2inFiles.py

根据UNIPIC符号表（json）构造ini/xml混合格式的.in文件

## 依赖的Python包总结
argparse

pathlib

re

ply

pint

sympy

shapely

# 智能辅助建模系统项目文档
## 智能辅助建模系统需求分析
以硕士论文撰写为核心，指导业务逻辑的确定，指导代码的开发。  
以前想到的硕士论文需求方向：

1.证明LLM方法在转译场景的价值，  
如LLM可以用于快速扩充解析、转换规则，可以方便地修改背景知识达成规则的变化，可以拿出几个器件作为例子来证明，只要LLM方法可以用于快速扩充/修改规则方法即可
2.LLM可以用于理解自然语言输入，输入/修改/推荐对应的器件参数，用于智能辅助器件建模

参考第二次、第三次梳理的内容
首先考虑需求：LLM用于MAGIC到UNIPIC转译器的扩充/替换
全电磁 PIC软件可以分为以下几个流程和数据：工程文件---建模操作--->输入文本  [---前处理---> 描述性参数 ---求解---> 计算结果 ---数据后处理]---> 处理结果
将.m2d文件转换到Simulation文件夹中的.in文件，本质上包括了两个环节，第一个环节是m2d文件的语义解析，将建模脚本映射到输入文本，第二个环节是将MAGIC的输入文本语义映射到UNIPIC的输入文本。由于不存在MAGIC的输入文本格式，可以构建一个建模完成时语义中介，作为MAGIC建模脚本输入文件到UNIPIC模型描述文件翻译的中间文本。

第二个环节是确定的，固定的过程，甚至可以考虑写死规则
我们来看第一个环节的开发，即MAGIC建模脚本输入文件到建模完成时语义中介的转译
经过分析包括以下难点：
1.需要保证不同语义元素翻译过程之间可以并发处理，以缩小等待时间
2.每个语义元素(有语义的MAGIC命令)翻译时，通过字符匹配、规则找到该语义元素所依赖的其他元素，构建完整的语义元素上下文块
3.找到要映射的建模完成时语义中介的对应字段，通过字段查找对应的字段规则，拼接到prompt，如果没有的话就需要在后端代码补全规则
4.送到LLM等待返回结果，对结果后处理


## 智能辅助建模系统的整体分析
### 核心功能
给UNIPIC软件开发整个智能辅助建模系统，具备两个核心功能：  
1.LLM转译（输入全部/部分magic命令，输出对UNIPIC项目文件的编辑/操作）
2.LLM辅助建模（输入自然语言/文档，输出对UNIPIC项目文件的编辑/操作）
现在打算都通过建模完成时语义中介来实现，现在先不着急自然语言的事情

### 应用范围
考虑需要验证的器件范围：  
目前只需要考虑：  
BWO、MILO、Vir、Mitl、TM03_60GHz、XCB_PB  
其中BWO、MILO、Vir已经在小论文中用于验证规则转译器的有效性了  
其余几个器件可以用于说明LLM方法的必要性、有效性

### 符号分析
根据PIC软件构建仿真模型的流程步骤，

建模完成时语义中介的模式设计为：
{
  "meta": {},
  "variables": {},
  "functions": {},
  "geometry": {},        #几何实体 POINT\LINE\AREA\SELECTION
  "materials": {},        #材料参数 定义与应用 definition and assignment
  "mesh": {},       #网格参数
  "sources": {},     #粒子发射和注入波
  "boundaries": {},     #各种边界条件
  "couplings": {},      #耦合条件
  "diagnostics": [],      #物理量诊断
  "global": {},     内核运行模拟过程的全局参数
}

每个标签对应的模式：
"variables": {
  "var_name1":{
  "var_expr":...,
  "var_num":...,
  "var_unit":...,
  },
  "var_name2":{
  "var_expr":...,
  "var_num":...,
  "var_unit":...,
  },
  ...
},

"functions": {
  "func_name1":{
    "func_params":...,
    "func_expr":...,
  },
  "func_name2":{
    "func_params":...,
    "func_expr":...,
  },
  ...
}

"geometry": {
  "POINT":{
    "geom_name1":{
      "geom_type":"POINT",
      "geom_expr":...,
      "geom_params":...,
    },
    ...
  },
  "LINE":{
    "geom_name1":{
      "geom_type":"LINE",
      "geom_expr":...,
      "geom_params":...,
    },
    ...
  },
  "AREA":{
    "geom_name1":{
      "geom_type":"AREA",
      "geom_expr":...,
      "geom_params":...,
    },
    ...
  },
  "SELECTION":[{...}]
}

"materials":{
  "definitions": [
    {
      "mat_name1":{
        "mat_type":"...",
        "mat_expr":...,
        "mat_params":...,
      },
      ...
    },
    {
      "mat_name2":{
        "mat_type":"...",
        "mat_expr":...,
        "mat_params":...,
      },
      ...
    },
    ...
  ]
  "assignments": [
    {
      "geom_name1":...,
      "mat_name":...,
    },
    {
      "geom_name2":...,
      "mat_name":...,
    },
    ...
  ]
}

"mesh": {
  "dx": ...,
  "dy": ...,
  "dz": ...,
}, 

"sources": {
  "excitation":{...},
  "emission":{...},
  "beam_injection":{...},
}

"boundaries": {
  "PEC": [{...}],
  "PML": [{...}],
  "OpenPort": [{...}],
  "Mur": [{...}],
}

"couplings": {
  "transmission_line": [{...}],
}

"diagnostics":[]

"global": {}



### 流程分析

第五章通过引入 LLM，实现对复杂建模语义的泛化补全与系统扩展。
5.1 引入LLM做解析，将m2d文件解析为ParserResult，后半部分的转译还继续走规则转译器，这样可以省去预处理、词法分析、语法分析
5.2 引入LLM做转换，将ParserResult转换为中间语义文本，这样可以省略掉复杂的命令处理阶段，后面的逻辑映射、字符映射都可以继续走规则方法

5.1 LLM解析方法：在解析器前面加了一个分类器做路由，可以在新增命令时候，根据命令类型，路由到LLM解析器，用于快速验证

参考规则转译器的代码总结，我们来思考LLM转译的切入思路
LLM转译应该分为两个阶段：LLM解析和LLM转换
我认为LLM解析的输入应该是
解析路由后输出的单条命令，或者同类型的5-10条命令
LLM解析的输出应该是
与ply/regex解析器同样的格式

5.2 LLM转换方法的需求：
1.需要保证不同语义元素翻译过程之间可以并发处理，以缩小等待时间
2.每个语义元素(有语义的MAGIC命令)翻译时，通过字符匹配、规则找到该语义元素所依赖的其他元素，构建完整的语义元素上下文块
3.找到要映射的建模完成时语义中介的对应字段，通过字段查找对应的字段规则，拼接到prompt，如果没有的话就需要在后端代码补全规则
4.送到LLM等待返回结果，对结果后处理

流程设计：
1.输入m2d文件，进行简单预处理，去掉注释、空行、空格等，合并为一行
2.对于每一行命令，识别其命令类型
3.



## 智能辅助建模系统的迭代计划
还没定好  
目前在第一轮迭代，只产生了第一轮想法讨论的demo交付  
只完成了基础的数据配置类、基础的模版（最简单的，没按照上面分析来）  
LLM转译部分还没做

LLM用于辅助建模也还没做




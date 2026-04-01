"""
==========================
src/domain/config/prompt.py
==========================
定义了转译流程中需要的一些提示词，包括：
- 解析提示词
- 转换提示词
"""

m2u_task_dict = {
    "parse": """
    现在请你来完成解析部分，将命令预处理后的文本解析为json格式的中间文件。
    解析的注意事项:
    1.保留预处理的命令行数、命令名标记,若不存在这两个字段，行号填写为0，报错。
    2.如果输入的命令不符合预期，如格式不对，不是指定的命令类型，残缺等等，在"errors"字段中描述具体错误类型
    3.解析的参数放到payload字段中
    4.整个输出是一个json数组，每个元素对应一条命令的json项，不要有多余的描述
    """,
    "mcl_midconv":"""
    现在请你来完成转换部分，将输入的参数解析为json格式的中间表示。
    解析的注意事项:
    整个输出是一个json数组，每个元素对应一条命令的json项，不要有多余的描述
    """
}


parse_cmd_dict = {
    "ASSIGN": """
    解析ASSIGN命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    ASSIGN命令的规则:
    1.ASSIGN命令的格式为：ASSIGN 变量名 = {数值} 或 {数值}{单位} 或 {表达式}
    2.ASSIGN关键字本身可以省略，也可以出现
    3.对于定义的变量，
    若为纯数值无单位，不要补充单位，格式为{num}；
    若有数值与单位，统一格式为{num} * {unit}，单位去掉末尾复数标记s，其它保持原样统一小写；
    若为一个表达式，将表达式原封不动作为结果，两边加上括号，即({expr})
    """,

    "FUNCTION": """
    解析FUNCTION命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    FUNCTION命令的规则:
    1.FUNCTION命令的格式为：FUNCTION 函数名(参数列表) = 表达式 或 FUNCTION 函数名 = 表达式
    2.函数参数可以有多个（用逗号分隔），也可能没有参数
    3.参数列表用括号包围，如果没有参数则可以省略括号
    4.表达式可以包含常量、变量、内在函数、数学运算符（+、-、*、/、**）和布尔运算符
    5.将表达式原封不动保存，去掉多余的空格但保持运算符和操作数的分隔
    """,

    "POINT": """
    解析POINT命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    POINT命令的规则:
    1.POINT命令用于定义空间中的一个点
    2.POINT命令的格式为：POINT 点名 x1坐标 x2坐标 [x3坐标]
    3.坐标可以是数值、表达式或带单位的数值
    4.2D仿真只需要两个坐标，3D仿真需要三个坐标
    """,

    "LINE": """
    解析LINE命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    LINE命令的规则:
    1.LINE命令用于定义空间中的线
    2.LINE命令的格式为：LINE 线名 线类型 参数列表
    3.线类型包括：CONFORMAL、OBLIQUE、CIRCULAR、ELLIPTICAL等
    4.参数列表根据线类型不同而不同
    """,

    "AREA": """
    解析AREA命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    AREA命令的规则:
    1.AREA命令用于定义空间中的区域
    2.AREA命令的格式为：AREA 区域名 区域类型 参数列表
    3.区域类型包括：CONFORMAL、RECTANGULAR、FUNCTIONAL、POLYGONAL等
    4.参数列表根据区域类型不同而不同
    """,

    "VOLUME": """
    解析VOLUME命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    VOLUME命令的规则:
    1.VOLUME命令用于定义空间中的体积（仅3D仿真）
    2.VOLUME命令的格式为：VOLUME 体积名 体积类型 参数列表
    3.体积类型包括：CONFORMAL、CYLINDRICAL、SPHERICAL、ANNULAR等
    4.参数列表根据体积类型不同而不同
    """,

    "MARK": """
    解析MARK命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    MARK命令的规则:
    1.MARK命令用于标记几何对象用于后续网格剖分
    2.MARK命令的格式为：MARK 对象名 [坐标轴] [位置选项] [SIZE 单元大小]
    3.坐标轴可以是X1、X2、X3
    4.位置选项包括：MINIMUM、MIDPOINT、MAXIMUM
    5.SIZE指定标记位置处的单元大小
    """,

    "CONDUCTOR": """
    解析CONDUCTOR命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    CONDUCTOR命令的规则:
    1.CONDUCTOR命令用于定义导体材料
    2.CONDUCTOR命令的格式为：CONDUCTOR 对象名 [导率]
    3.对象名是要设为导体的几何对象
    4.导率是可选参数，指定导体的导率值
    """,

    "DIELECTRIC": """
    解析DIELECTRIC命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    DIELECTRIC命令的规则:
    1.DIELECTRIC命令用于定义介电材料
    2.DIELECTRIC命令的格式为：DIELECTRIC 对象名 介电常数 [损耗角正切]
    3.对象名是要设为介电体的几何对象
    4.介电常数和损耗角正切是材料参数
    """,

    "PORT": """
    解析PORT命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    PORT命令的规则:
    1.PORT命令用于定义端口边界条件
    2.PORT命令的格式为：PORT 几何对象 方向 [选项列表]
    3.方向为POSITIVE或NEGATIVE
    4.选项可能包括：INCOMING、NORMALIZATION、PHASE_VELOCITY等
    5.INCOMING后面跟函数名和相关参数
    6.NORMALIZATION指定归一化方式
    """,

    "PRESET": """
    解析PRESET命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    PRESET命令的规则:
    1.PRESET命令用于预设场分量的初始值
    2.PRESET命令的格式为：PRESET 场分量 初始化方式 参数
    3.场分量包括：E1、E2、E3、B1、B2、B3、B1ST、B2ST、B3ST等
    4.初始化方式包括：FUNCTION、READ、PANDIRA等
    5.参数根据初始化方式不同而不同
    """,

    "EMISSION": """
    解析EMISSION命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    EMISSION命令的规则:
    1.EMISSION命令用于定义粒子发射过程
    2.EMISSION命令的格式为：EMISSION 发射类型 [参数列表]
    3.发射类型包括：EXPLOSIVE、BEAM、GYRO、HIGH_FIELD、PHOTOELECTRIC、SECONDARY、THERMIONIC等
    4.参数可能包括SPECIES、NUMBER、THRESHOLD、MODEL等选项
    5.每个选项后面跟相应的值或函数
    """,

    "EMISSION EXPLOSIVE": """
    解析EMISSION EXPLOSIVE命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    EMISSION EXPLOSIVE命令的规则:
    1.EMISSION EXPLOSIVE用于定义爆炸发射过程
    2.格式为：EMISSION EXPLOSIVE [THRESHOLD 阈值] [SPECIES 粒子种类] [NUMBER 数量] 等
    3.THRESHOLD指定击穿阈值电场
    4.SPECIES指定发射的粒子种类（如ELECTRON）
    5.NUMBER指定发射粒子数量
    """,

    "EMIT": """
    解析EMIT命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    EMIT命令的规则:
    1.EMIT命令用于在指定对象上启用粒子发射
    2.EMIT命令的格式为：EMIT 发射模型名 对象名 [EXCLUDE/INCLUDE 选项]
    3.发射模型名是在EMISSION命令中定义的模型
    4.对象名是要启用发射的几何对象
    5.EXCLUDE/INCLUDE用于排除或包含特定区域的发射
    """,

    "OBSERVE": """
    解析OBSERVE命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    OBSERVE命令的规则:
    1.OBSERVE命令用于观测和记录仿真变量
    2.OBSERVE命令的格式为：OBSERVE 观测类型 [参数] 对象名 [选项]
    3.观测类型包括：FIELD、FIELD_POWER、FIELD_INTEGRAL、COLLECTED、EMITTED等
    4.参数根据观测类型不同而不同
    5.对象名是要观测的几何对象或变量
    6.选项包括数据处理选项如FFT、FILTER等
    """,

    "OBSERVE FIELD": """
    解析OBSERVE FIELD命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    OBSERVE FIELD命令的规则:
    1.OBSERVE FIELD用于观测电磁场分量
    2.格式为：OBSERVE FIELD 场分量 对象名 [选项]
    3.场分量包括：E1、E2、E3、B1、B2、B3等
    4.对象名是要观测的空间对象（点、线、面、体积）
    5.选项包括数据处理选项
    """,

    "OBSERVE FIELD_INTEGRAL": """
    解析OBSERVE FIELD_INTEGRAL命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    OBSERVE FIELD_INTEGRAL命令的规则:
    1.OBSERVE FIELD_INTEGRAL用于观测场的积分量
    2.格式为：OBSERVE FIELD_INTEGRAL 积分类型 对象名 [选项]
    3.积分类型包括：E.DL（电压）、H.DL（电流）、J.DA（电流）、Q.DV（电荷）等
    4.对象名是要积分的空间对象
    5.选项包括数据处理选项
    """,

    "OBSERVE FIELD_POWER": """
    解析OBSERVE FIELD_POWER命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    OBSERVE FIELD_POWER命令的规则:
    1.OBSERVE FIELD_POWER用于观测功率相关量
    2.格式为：OBSERVE FIELD_POWER 功率变量 对象名 [选项]
    3.功率变量包括：S.DA（坡印廷矢量）、E.J_PARTICLE.DV等
    4.对象名是要测量功率的空间对象
    5.选项包括数据处理选项
    """,

    "OBSERVE COLLECTED": """
    解析OBSERVE COLLECTED命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    OBSERVE COLLECTED命令的规则:
    1.OBSERVE COLLECTED用于观测收集的粒子变量
    2.格式为：OBSERVE COLLECTED 对象名 粒子种类 变量类型 [选项]
    3.对象名是收集粒子的对象（导体、介电体等）
    4.粒子种类如ELECTRON或ALL
    5.变量类型包括：CHARGE、CURRENT、ENERGY、POWER、VOLTAGE
    """,

    "OBSERVE EMITTED": """
    解析OBSERVE EMITTED命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    OBSERVE EMITTED命令的规则:
    1.OBSERVE EMITTED用于观测发射的粒子变量
    2.格式为：OBSERVE EMITTED 对象名 粒子种类 变量类型 [选项]
    3.对象名是发射粒子的对象
    4.粒子种类如ELECTRON或ALL
    5.变量类型包括：CHARGE、CURRENT、ENERGY、POWER、VOLTAGE
    """,

    "DURATION": """
    解析DURATION命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    DURATION命令的规则:
    1.DURATION命令用于指定仿真的时间跨度
    2.DURATION命令的格式为：DURATION 时间跨度
    3.时间跨度可以是数值、表达式或带时间单位的数值
    4.单位可以是秒、纳秒、微秒等
    """,

    "TIMER": """
    解析TIMER命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    TIMER命令的规则:
    1.TIMER命令用于定义时间触发器
    2.TIMER命令的格式为：TIMER 计时器名 类型 参数列表
    3.类型包括：PERIODIC（周期性）、DISCRETE（离散）
    4.参数列表根据类型不同而不同
    5.可选INTEGRATE选项用于积分测量
    """,

    "SYSTEM": """
    解析SYSTEM命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    SYSTEM命令的规则:
    1.SYSTEM命令用于指定坐标系
    2.SYSTEM命令的格式为：SYSTEM 坐标系类型
    3.坐标系类型包括：CARTESIAN（笛卡尔）、CYLINDRICAL（柱坐标）、POLAR（极坐标）
    4.坐标系的选择影响后续几何定义和场计算
    """,

    "GRID": """
    解析GRID命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    GRID命令的规则:
    1.GRID命令用于定义空间网格
    2.GRID命令的格式为：GRID 网格类型 坐标轴 参数列表
    3.网格类型包括：ORIGIN、UNIFORM、QUADRATIC、PADE、EXPLICIT等
    4.坐标轴为X1、X2或X3
    5.参数列表根据网格类型不同而不同
    """,

    "AUTOGRID": """
    解析AUTOGRID命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    AUTOGRID命令的规则:
    1.AUTOGRID命令用于根据标记自动生成网格
    2.AUTOGRID命令的格式为：AUTOGRID [坐标轴] [选项]
    3.坐标轴可以是X1、X2、X3
    4.选项包括：REPLACE、EXTEND等
    5.如果不指定坐标轴，则为所有坐标轴生成网格
    """,

    "INDUCTOR": """
    解析INDUCTOR命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    INDUCTOR命令的规则:
    1.INDUCTOR命令用于定义电感元件
    2.INDUCTOR命令的格式为：INDUCTOR 线名 直径 [INDUCTANCE 电感值] [其他选项]
    3.线名是在LINE命令中定义的线对象
    4.直径是导线的直径
    5.INDUCTANCE用于指定电感值
    6.其他选项包括材料属性、电阻等
    """,

    "FREESPACE": """
    解析FREESPACE命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    FREESPACE命令的规则:
    1.FREESPACE命令用于定义自由空间边界条件
    2.FREESPACE命令的格式为：FREESPACE 对象名 方向 坐标轴 场分量 [选项]
    3.对象名是要应用边界的区域或体积
    4.方向为POSITIVE或NEGATIVE
    5.坐标轴为X1、X2或X3
    6.场分量包括：TRANSVERSE、ALL、E1、E2等
    7.选项包括导电率函数等
    """,

    "PHASESPACE": """
    解析PHASESPACE命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    PHASESPACE命令的规则:
    1.PHASESPACE命令用于绘制粒子相空间图
    2.PHASESPACE命令的格式为：PHASESPACE AXES 坐标1 坐标2 计时器 [选项]
    3.坐标可以是X1、X2、X3、P1、P2、P3、Q、KE、GAMMA等
    4.计时器是在TIMER命令中定义的触发器
    5.选项包括轴范围、窗口、粒子种类等
    """,

    "RANGE": """
    解析RANGE命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    RANGE命令的规则:
    1.RANGE命令用于绘制场变量沿空间线的分布
    2.RANGE命令的格式为：RANGE FIELD 场变量 线名 计时器 [选项]
    3.场变量是要绘制的场分量
    4.线名是在LINE命令中定义的共形线
    5.计时器指定绘制时间
    6.选项包括处理选项等
    """,

}


json_dict = {
    "ASSIGN": """
    ASSIGN命令对应的json项的json模式为：
    {   
        "lineno": {保持原来的lineno},
        "command": "ASSIGN",
        "parser_kind": "LLM",
        "payload": {
            "kind": "variable",
            "sys_name": "{name}",
            "value": "{num} * {unit}"
        },        
        "errors": "no或者具体错误类型"
    }
    
    ##示例输入：
    {"lineno": "43", "command": "ASSIGN", "text": "ZP1 = 0.6 * mm ;"}
    {"lineno": "", "command": "ASSIGN", "text": ""}
    {"lineno": "53", "command": "ASSIGN", "text": "ZS1 = Z_ANODE_RR + ZP1 ;"}
    ##示例输出：
    [
        {
            "lineno": "43",
            "command": "ASSIGN",
            "parser_kind": "LLM",
            "payload": {
                "kind": "variable",
                "sys_name": "ZP1",
                "value": "0.6 * mm"
            },
            "errors": "no"
        },
        {
            "lineno": "0",
            "command": "ASSIGN",
            "parser_kind": "LLM",
            "payload": {},
            "errors": "输入文本不完整"
        },
        {
            "lineno": "53",
            "command": "ASSIGN",
            "parser_kind": "LLM",
            "payload": {
                "kind": "variable",
                "sys_name": "ZS1",
                "value": "(Z_ANODE_RR + ZP1)"
            },
            "errors": "no"
        }
    ]""",

    "FUNCTION": """
    FUNCTION命令对应的json项的json模式为：
    {   
        "lineno": {保持原来的lineno},
        "command": "FUNCTION",
        "parser_kind": "LLM",
        "payload": {
            "kind": "function",
            "sys_name": "{函数名}",
            "params": ["{参数1}", "{参数2}", ...] 或 [],
            "body": "{表达式内容}"
        },        
        "errors": "no或者具体错误类型"
    }
    
    ##示例输入：
    {"lineno": "64", "command": "FUNCTION", "text": "FUNCTION FIN ( T )  = VOLTAGE.MAX * MAX ( 0.0 , MIN ( 1.0 , T / TRISE )  )  ;"}
    {"lineno": "65", "command": "FUNCTION", "text": "FUNCTION G1 ( Z , R )  = 1 / R ;"}
    {"lineno": "66", "command": "FUNCTION", "text": "FUNCTION G2 = 0.0 ;"}
    ##示例输出：
    [
        {
            "lineno": "64",
            "command": "FUNCTION",
            "parser_kind": "LLM",
            "payload": {
                "kind": "function",
                "sys_name": "FIN",
                "params": ["T"],
                "body": "VOLTAGE.MAX * MAX ( 0.0 , MIN ( 1.0 , T / TRISE )  )"
            },
            "errors": "no"
        },
        {
            "lineno": "65",
            "command": "FUNCTION",
            "parser_kind": "LLM",
            "payload": {
                "kind": "function",
                "sys_name": "G1",
                "params": ["Z", "R"],
                "body": "1 / R"
            },
            "errors": "no"
        },
        {
            "lineno": "66",
            "command": "FUNCTION",
            "parser_kind": "LLM",
            "payload": {
                "kind": "function",
                "sys_name": "G2",
                "params": [],
                "body": "0.0"
            },
            "errors": "no"
        }
    ]""",

    "POINT": """
    POINT命令对应的json项的json模式为：
    {   
        "lineno": {保持原来的lineno},
        "command": "POINT",
        "parser_kind": "LLM",
        "payload": {
            "kind": "POINT",
            "sys_name": "{点名}",
            "point": "{坐标表示}"
        },        
        "errors": "no或者具体错误类型"
    }
    
    ##示例输入：
    {"lineno": "7", "command": "POINT", "text": "POINT POINTS1 0 * mm , 143 * mm ;"}
    {"lineno": "89", "command": "POINT", "text": "POINT ED2 998.4 * mm , 140 * mm ;"}
    ##示例输出：
    [
        {
            "lineno": "7",
            "command": "POINT",
            "parser_kind": "LLM",
            "payload": {
                "kind": "POINT",
                "sys_name": "POINTS1",
                "point": "<(0 * mm)|(143 * mm)>"
            },
            "errors": "no"
        },
        {
            "lineno": "89",
            "command": "POINT",
            "parser_kind": "LLM",
            "payload": {
                "kind": "POINT",
                "sys_name": "ED2",
                "point": "<(998.4 * mm)|(140 * mm)>"
            },
            "errors": "no"
        }
    ]""",

    "LINE": """
    LINE命令对应的json项的json模式为：
    {   
        "lineno": {保持原来的lineno},
        "command": "LINE",
        "parser_kind": "LLM",
        "payload": {
            "kind": "LINE",
            "sys_name": "{线名}",
            "line_type": "{线类型}",
            "points": ["{点坐标列表}"]
        },        
        "errors": "no或者具体错误类型"
    }
    
    ##示例输入：
    {"lineno": "62", "command": "LINE", "text": "LINE GAP CONFORMAL 0.80 * m 0.0965 * m 0.80 * m 0.143 * m ;"}
    {"lineno": "67", "command": "LINE", "text": "LINE INLET CONFORMAL 0.0 * m , 0.0575 * m 0.0 * m 0.143 * m ;"}
    ##示例输出：
    [
        {
            "lineno": "62",
            "command": "LINE",
            "parser_kind": "LLM",
            "payload": {
                "kind": "LINE",
                "sys_name": "GAP",
                "line_type": "CONFORMAL",
                "points": [
                    "<(0.8 * m)|(0.0965 * m)>",
                    "<(0.8 * m)|(0.143 * m)>"
                ]
            },
            "errors": "no"
        },
        {
            "lineno": "67",
            "command": "LINE",
            "parser_kind": "LLM",
            "payload": {
                "kind": "LINE",
                "sys_name": "INLET",
                "line_type": "CONFORMAL",
                "points": [
                    "<(0.0 * m)|(0.0575 * m)>",
                    "<(0.0 * m)|(0.143 * m)>"
                ]
            },
            "errors": "no"
        }
    ]""",

    "AREA": """
    AREA命令对应的json项的json模式为：
    {   
        "lineno": {保持原来的lineno},
        "command": "AREA",
        "parser_kind": "LLM",
        "payload": {
            "kind": "AREA",
            "sys_name": "{区域名}",
            "area_type": "{区域类型}",
            "params": {
                "points": ["{点坐标列表}"]
            }
        },        
        "errors": "no或者具体错误类型"
    }
    
    ##示例输入：
    {"lineno": "6", "command": "AREA", "text": "AREA SIMULATION CONFORMAL 0.0 * mm , 0.0 * mm , 998.40 * mm , 150.0 * mm ;"}
    {"lineno": "47", "command": "AREA", "text": "AREA CATHODE CONFORMAL 0 * mm , 0 * mm , 764.8 * mm , 57.5 * mm ;"}
    ##示例输出：
    [
        {
            "lineno": "6",
            "command": "AREA",
            "parser_kind": "LLM",
            "payload": {
                "kind": "AREA",
                "sys_name": "SIMULATION",
                "area_type": "CONFORMAL",
                "params": {
                    "points": [
                        "<(0.0 * mm)|(0.0 * mm)>",
                        "<(998.4 * mm)|(150.0 * mm)>"
                    ]
                }
            },
            "errors": "no"
        },
        {
            "lineno": "47",
            "command": "AREA",
            "parser_kind": "LLM",
            "payload": {
                "kind": "AREA",
                "sys_name": "CATHODE",
                "area_type": "CONFORMAL",
                "params": {
                    "points": [
                        "<(0 * mm)|(0 * mm)>",
                        "<(764.8 * mm)|(57.5 * mm)>"
                    ]
                }
            },
            "errors": "no"
        }
    ]""",

    "PRESET": """
    PRESET命令对应的json项的json模式为：
    {   
        "lineno": {保持原来的lineno},
        "command": "PRESET",
        "parser_kind": "LLM",
        "payload": {
            "kind": "preset",
            "preset_name": "{场分量名称}",
            "func_name": "{函数名称}"
        },        
        "errors": "no或者具体错误类型"
    }
    
    ##示例输入：
    {"lineno": "90", "command": "PRESET", "text": "PRESET B1ST FUNCTION B_Z ;"}
    {"lineno": "92", "command": "PRESET", "text": "PRESET B2ST FUNCTION B_R ;"}
    {"lineno": "94", "command": "PRESET", "text": "PRESET B3ST FUNCTION B_PHI ;"}
    ##示例输出：
    [
        {
            "lineno": "90",
            "command": "PRESET",
            "parser_kind": "LLM",
            "payload": {
                "kind": "preset",
                "preset_name": "B1ST",
                "func_name": "B_Z"
            },
            "errors": "no"
        },
        {
            "lineno": "92",
            "command": "PRESET",
            "parser_kind": "LLM",
            "payload": {
                "kind": "preset",
                "preset_name": "B2ST",
                "func_name": "B_R"
            },
            "errors": "no"
        },
        {
            "lineno": "94",
            "command": "PRESET",
            "parser_kind": "LLM",
            "payload": {
                "kind": "preset",
                "preset_name": "B3ST",
                "func_name": "B_PHI"
            },
            "errors": "no"
        }
    ]""",

    "EMISSION": """
    EMISSION命令对应的json项的json模式为：
    {   
        "lineno": {保持原来的lineno},
        "command": "EMISSION",
        "parser_kind": "LLM",
        "payload": {
            "kind": "emission",
            "emission_type": "{发射类型}",
            "species": "{粒子种类}",
            "parameters": {
                "number": "{数量}",
                "threshold": "{阈值}",
                "其他参数": "{值}"
            }
        },        
        "errors": "no或者具体错误类型"
    }
    
    ##示例输入：
    {"lineno": "72", "command": "EMISSION", "text": "EMISSION EXPLOSIVE SPECIES ELECTRON NUMBER 1 ;"}
    ##示例输出：
    [
        {
            "lineno": "72",
            "command": "EMISSION",
            "parser_kind": "LLM",
            "payload": {
                "kind": "emission",
                "emission_type": "EXPLOSIVE",
                "species": "ELECTRON",
                "parameters": {
                    "number": "1"
                }
            },
            "errors": "no"
        }
    ]""",

    "EMIT": """
    EMIT命令对应的json项的json模式为：
    {   
        "lineno": {保持原来的lineno},
        "command": "EMIT",
        "parser_kind": "LLM",
        "payload": {
            "kind": "emit",
            "model": "{发射模型名}",
            "mobject": "{材料对象名}",
            "ex_in": ["{EXCLUDE/INCLUDE选项列表}"]
        },        
        "errors": "no或者具体错误类型"
    }
    
    ##示例输入：
    {"lineno": "73", "command": "EMIT", "text": "EMIT EXPLOSIVE CATHODE EXCLUDE NOEMIT EXCLUDE NOEMIT2 INCLUDE EMITTER ;"}
    ##示例输出：
    [
        {
            "lineno": "73",
            "command": "EMIT",
            "parser_kind": "LLM",
            "payload": {
                "kind": "emit",
                "model": "EXPLOSIVE",
                "mobject": "CATHODE",
                "ex_in": [
                    "EXCLUDE",
                    "NOEMIT",
                    "EXCLUDE", 
                    "NOEMIT2",
                    "INCLUDE",
                    "EMITTER"
                ]
            },
            "errors": "no"
        }
    ]""",


    "INDUCTOR": """
    INDUCTOR命令对应的json项的json模式为：
    {   
        "lineno": {保持原来的lineno},
        "command": "INDUCTOR",
        "parser_kind": "LLM",
        "payload": {
            "kind": "INDUCTOR",
            "line_name": "{线名}",
            "diameter": "{直径}",
            "inductance": "{电感值或null}",
            "other_params": {}
        },        
        "errors": "no或者具体错误类型"
    }
    
    ##示例输入：
    {"lineno": "63", "command": "INDUCTOR", "text": "INDUCTOR GAP 1e-3 INDUCTANCE   100e-9 ;"}
    ##示例输出：
    [
        {
            "lineno": "63",
            "command": "INDUCTOR",
            "parser_kind": "LLM",
            "payload": {
                "kind": "INDUCTOR",
                "line_name": "GAP",
                "diameter": "1e-3",
                "inductance": "100e-9"
            },
            "errors": "no"
        }
    ]""",

    "MARK": """
    MARK命令对应的json项的json模式为：
    {   
        "lineno": {保持原来的lineno},
        "command": "MARK",
        "parser_kind": "LLM",
        "payload": {
            "kind": "mark",
            "geom_name": "{对象名}",
            "axis": "{坐标轴}",
            "position": "{位置选项或空字符串}",
            "size": "{单元大小或空字符串}"
        },        
        "errors": "no或者具体错误类型"
    }
    
    ##示例输入：
    {"lineno": "51", "command": "MARK", "text": "MARK SIMULATION X1 SIZE DZ ;"}
    {"lineno": "53", "command": "MARK", "text": "MARK CATHODE X1 SIZE DZ ;"}
    ##示例输出：
    [
        {
            "lineno": "51",
            "command": "MARK",
            "parser_kind": "LLM",
            "payload": {
                "kind": "mark",
                "geom_name": "SIMULATION",
                "axis": "X1",
                "position": "",
                "size": "DZ"
            },
            "errors": "no"
        },
        {
            "lineno": "53",
            "command": "MARK",
            "parser_kind": "LLM",
            "payload": {
                "kind": "mark",
                "geom_name": "CATHODE",
                "axis": "X1",
                "position": "",
                "size": "DZ"
            },
            "errors": "no"
        }
    ]""",

    "CONDUCTOR": """
    CONDUCTOR命令对应的json项的json模式为：
    {   
        "lineno": {保持原来的lineno},
        "command": "CONDUCTOR",
        "parser_kind": "LLM",
        "payload": {
            "kind": "material_assign",
            "mtype": "CONDUCTOR",
            "geom_name": "{几何对象名}",
            "spec": "{导率值或空字符串}"
        },        
        "errors": "no或者具体错误类型"
    }
    
    ##示例输入：
    {"lineno": "59", "command": "CONDUCTOR", "text": "CONDUCTOR CATHODE ;"}
    {"lineno": "60", "command": "CONDUCTOR", "text": "CONDUCTOR ANODE ;"}
    ##示例输出：
    [
        {
            "lineno": "59",
            "command": "CONDUCTOR",
            "parser_kind": "LLM",
            "payload": {
                "kind": "material_assign",
                "mtype": "CONDUCTOR",
                "geom_name": "CATHODE",
                "spec": ""
            },
            "errors": "no"
        },
        {
            "lineno": "60",
            "command": "CONDUCTOR",
            "parser_kind": "LLM",
            "payload": {
                "kind": "material_assign",
                "mtype": "CONDUCTOR",
                "geom_name": "ANODE",
                "spec": ""
            },
            "errors": "no"
        }
    ]""",

    "PORT": """
    PORT命令对应的json项的json模式为：
    {   
        "lineno": {保持原来的lineno},
        "command": "PORT",
        "parser_kind": "LLM",
        "payload": {
            "kind": "PORT",
            "geom_name": "{几何对象名}",
            "direction": "{方向}",
            "options": [
                {
                    "port_opt_name": "{选项名称}",
                    "incoming_func": "{函数名}",
                    "incoming_opt": ["{组件列表}"]
                },
                {
                    "port_opt_name": "{选项名称}",
                    "norm_type": "{归一化类型}",
                    "geom_type": "{几何类型}",
                    "peak_value": ["{峰值对象}"]
                }
            ]
        },        
        "errors": "no或者具体错误类型"
    }
    
    ##示例输入：
    {"lineno": "86", "command": "PORT", "text": "PORT INLET POSITIVE INCOMING FIN FUNCTION E2 G1 E3 G2 NORMALIZATION VOLTAGE INLET ;"}
    {"lineno": "88", "command": "PORT", "text": "PORT OUTLET NEGATIVE ;"}
    ##示例输出：
    [
        {
            "lineno": "86",
            "command": "PORT",
            "parser_kind": "LLM",
            "payload": {
                "kind": "PORT",
                "geom_name": "INLET",
                "direction": "POSITIVE",
                "options": [
                    {
                        "port_opt_name": "INCOMING",
                        "incoming_func": "FIN",
                        "incoming_opt": [
                            "E2",
                            "G1",
                            "E3",
                            "G2"
                        ]
                    },
                    {
                        "port_opt_name": "NORMALIZATION",
                        "norm_type": "VOLTAGE",
                        "geom_type": "line",
                        "peak_value": [
                            "INLET"
                        ]
                    }
                ]
            },
            "errors": "no"
        },
        {
            "lineno": "88",
            "command": "PORT",
            "parser_kind": "LLM",
            "payload": {
                "kind": "PORT",
                "geom_name": "OUTLET",
                "direction": "NEGATIVE",
                "options": []
            },
            "errors": "no"
        }
    ]""",

    "OBSERVE": """
    OBSERVE命令对应的json项的json模式为：
    {   
        "lineno": {保持原来的lineno},
        "command": "OBSERVE",
        "parser_kind": "LLM",
        "payload": {
            "kind": "observe_{观测类型}",
            "observe_type": "{观测类型}",
            "field_component": "{场分量}",
            "object_name": "{对象名}",
            "options": {}
        },        
        "errors": "no或者具体错误类型"
    }
    
    ##示例输入：
    {"lineno": "75", "command": "OBSERVE", "text": "OBSERVE FIELD_INTEGRAL E.DL INLET ;"}
    {"lineno": "90", "command": "OBSERVE", "text": "OBSERVE FIELD E2 ED2 ;"}
    ##示例输出：
    [
        {
            "lineno": "75",
            "command": "OBSERVE",
            "parser_kind": "LLM",
            "payload": {
                "kind": "observe_field_integral",
                "observe_type": "FIELD_INTEGRAL",
                "field_component": "E.DL",
                "object_name": "INLET",
                "options": {}
            },
            "errors": "no"
        },
        {
            "lineno": "90",
            "command": "OBSERVE",
            "parser_kind": "LLM",
            "payload": {
                "kind": "observe_field",
                "observe_type": "FIELD",
                "field_component": "E2",
                "object_name": "ED2",
                "options": {}
            },
            "errors": "no"
        }
    ]"""
}




mcl2mid_mclcontext_dict = {
    "MARK": "MARK命令在MCL中用于标记AREA区域的网格精度",
    "CONDUCTOR": "CONDUCTOR对应PEC材料，用于定义AREA区域的材料属性",
    "PORT": "PORT对应端口，用于定义各种边界条件",
    "EMISSION": "EMISSION命令用于定义发射模型",
    "EMIT": "EMIT命令用于定义发射模型的应用位置",
    "PRESET": "PRESET命令用于定义静电磁场",
    "INDUCTOR": "INDUCTOR命令用于定义电感",
    "RESISTOR": "RESISTOR命令用于定义电阻",
    "FOIL": "FOIL命令用于定义foil模型",
    "OBSERVE": "OBSERVE对应粒子推进过程中的物理量观测，如电压降、电流、功率、粒子数等"
}


mcl2mid_midcontext_dict = {
    "mark": "中间符号中mark元素用于记录网格精度参数",
    "material_assign": "中间符号中material_assign元素用于定义AREA区域的各种材料属性",
    "geom_cac_result": "中间符号中geom_cac_result元素用于记录几何区域的整体参数，如内部真空空腔参数、外部PEC外径等",  # 几何区域计算结果可能依赖面
    "selection": "中间符号中selection元素用于表示对点、线、面等几何元素的选择，可能用于绑定一些端口、场激励等物理元素的几何位置",  # 选择可能依赖点、线、面、几何计算结果
    
    # 材料命令
    "material_library": "中间符号中material_library元素用于表示材料库中材料的属性参数",  # 材料库无依赖
    "material_assign": "中间符号中material_assign元素用于定义AREA区域的材料属性",  # 材料应用依赖面、材料
    
    # 边界命令
    "port": "中间符号中port元素用于定义端口，可能用于绑定一些场激励、开放端口等物理元素的几何位置",  # 边界定义依赖几何选择
    
    # 物理实体命令
    "particle_library": "中间符号中particle_library元素用于表示粒子库中粒子的属性参数",
    "field_excitation": "中间符号中field_excitation元素用于定义场激励",  # 场激励依赖端口
    "emission_model": "中间符号中emission_model元素用于定义发射模型",  # 发射依赖区域
    "emission_apply": "中间符号中emission_apply元素用于定义发射模型的应用位置",  # 发射应用依赖区域
    "secondary_electron_emitter": "中间符号中secondary_electron_emitter元素用于定义次电子发射模型",  # 次电子发射依赖区域
    "electromagnetic_field": "中间符号中electromagnetic_field元素用于定义电磁场",  # 电磁场依赖函数
    "inductor": "中间符号中inductor元素用于定义电感",  # 电感依赖选择
    "resistor": "中间符号中resistor元素用于定义电阻",  # 电阻依赖选择
    "foil_model": "中间符号中foil_model元素用于定义 foil模型",  #  foil模型依赖选择

    # 诊断命令
    "diagnostic": "中间符号中diagnostic元素用于标记粒子推进过程中对某些空间位置上的物理量进行的诊断、观测"

}


mcl2mid_json_dict = {
"CONDUCTOR": """CONDUCTOR对应PEC材料，对应中间符号中的material_assign，
单个CONDUCTOR材料应用命令对应的json项的json模式为：
{"geom_name": "XXXX", "mat_name": "PEC"}

### 示例输入：
{'kind': 'material_assign', 'mat_type': 'CONDUCTOR', 'geom_name': 'CATHODE', 'spec': None}
{'kind': 'material_assign', 'mat_type': 'CONDUCTOR', 'geom_name': 'AREA1', 'spec': None}
### 示例输出：
{
    "material_assign": [
        {"geom_name": "CATHODE", "mat_name": "PEC"},
        {"geom_name": "AREA1", "mat_name": "PEC"}
    ]
}
""",

"MARK": """MARK命令在MCL中用于标记AREA区域的网格精度，对应中间符号中的mark元素，
MARK命令对应的json项的json模式为：
{"geom_name": "XXXX", "axis": "X1/2/3", "size_num": "{num}", "size_unit": "{unit}"}

### 示例输入：
[
    {'kind': 'mark', 'geom_name': 'geom_name1', 'axis': 'X1', 'position': '', 'size': 'DZ', 'dependency': [{'DZ': '[varible value] 0.5 millimeter'}]},
    {'kind': 'mark', 'geom_name': 'geom_name2', 'axis': 'X2', 'position': '', 'size': 'DR', 'dependency': [{'DR': '[varible value] 1.0 millimeter'}]}
]
### 示例输出：
{
    "mark": [
        {"geom_name": "geom_name1", "axis": "X1", "size_num": "0.5", "size_unit": "mm"},
        {"geom_name": "geom_name2", "axis": "X2", "size_num": "1.0", "size_unit": "mm"}
    ]
}
""",

"PORT": """PORT命令在MCL中用于定义端口，以及端口对应的几何位置、端口参数等等，对应中间符号中的port, field_excitation元素，互相之间以port_no为关联键
PORT命令对应的json项的json模式为：
外部激励，即'direction' = 'POSITIVE':
{
    "port":[{
        "PORT_type": "INPUTMURPORT",
        "sys_no": "{cmd_no}",
        "parameters": {
          "PORT_type": "INPUTMURPORT",
          "kind": "MurVoltagePort",
          "geom_name": "XXXX",
          "geom_value": [[0.0,Y1,Z1],[0.0,Y2,Z2]],
          "direction": "POSITIVE",
          "norm_type": "VOLTAGE",
          "norm_geom_name": "INLET",
          "norm_geom_value": [[0.0,Y1,Z1],[0.0,Y2,Z2]]
        },
        "dependencies": [],
        "cac_result": {}
      }
    ],
    "field_excitation":[{
        "port_no": "{cmd_no}",
        "parameters": {
            "incoming_func_body": "VOLTAGE_MAX*max(0.0,min(1.0,t/TRISE))",
            "incoming_func_vars": [
                {"VOLTAGE_MAX": "500000"},
                {"TRISE": "1e-9"}
            ],
            "incoming_opt": {
                "E2": "G1",
                "E3": "G2"
            }
        },
        "dependencies": [
            {"G1": "[FUNCTION value] G1 ( Z , R )  = 1 / R"},
            {"G2": "[FUNCTION value] G2 = 0.0"}
        ],
        "cac_result": {}
    }]
}
开放端口，即'direction' = 'NEGATIVE':
{
    "port":[{
        "PORT_type": "OPENPORT",
        "parameters": {
          "PORT_type": "OPENPORT",
          "kind": "OPENPORT",
          "geom_name": "XXXX",
          "geom_value": [[0.0,Y1,Z1],[0.0,Y2,Z2]],
          "direction": "NEGATIVE"
        },
        "cac_result": {},
        "dependencies": []
    }],
    "field_excitation":[]
}

### 示例输入：
[
    {
        "kind": "PORT",
        "geom_name": "LINE_IN",
        "direction": "POSITIVE",
        "options": [
            {
                "port_opt_name": "INCOMING",
                "incoming_func": "FIN",
                "incoming_opt": [
                    "E2",
                    "G1",
                    "E3",
                    "G2"
                ]
            },
            {
                "port_opt_name": "NORMALIZATION",
                "norm_type": "VOLTAGE",
                "geom_type": "line",
                "peak_value": [
                    "LINE_IN"
                ]
            }
        ],
        "cmd_no": 1,
        "dependency": [
            {
                "VOLTAGE.MAX": "600000"
            },
            {
                "TRISE": "1e-9"
            },
            {
                "sys_name": "FIN",
                "command": "FUNCTION",
                "text": "FUNCTION FIN ( T )  = VOLTAGE.MAX * MAX ( 0.0 , MIN ( 1.0 , T / TRISE )  )  ;"
            },
            {
                "sys_name": "G1",
                "command": "FUNCTION",
                "text": "FUNCTION G1 ( Z , R )  = 1 / R ;"
            },
            {
                "sys_name": "G2",
                "command": "FUNCTION",
                "text": "FUNCTION G2 = 0.0 ;"
            },
            {
                "LINE_IN": "[line value] [(5.0, 10.0), (5.0, 25.0)] (mm)"
            }
        ]
    },
    {
        "kind": "PORT",
        "geom_name": "LINE_OUT",
        "direction": "NEGATIVE",
        "options": [],
        "cmd_no": 2,
        "dependency": [
            {
                "LINE_OUT": "[line value] [(600.0, 0.0), (600.0, 25.0)] (mm)"
            }
        ]
    }
]
### 示例输出：
{
    "port":[
        {
            "PORT_type": "INPUTMURPORT",
            "sys_no": "1",
            "parameters": {
            "PORT_type": "INPUTMURPORT",
            "kind": "MurVoltagePort",
            "geom_name": "LINE_IN",
            "geom_value": [[0.0,10.0,5.0],[0.0,25.0,5.0]],
            "direction": "POSITIVE",
            "norm_type": "VOLTAGE",
            "norm_geom_name": "LINE_IN",
            "norm_geom_value": [[0.0,10.0,5.0],[0.0,25.0,5.0]]
            },
            "dependencies": [],
            "cac_result": {}
        },
        {
            "PORT_type": "OPENPORT",
            "sys_no": "2",
            "parameters": {
            "PORT_type": "OPENPORT",
            "kind": "OPENPORT",
            "geom_name": "LINE_OUT",
            "geom_value": [[0.0,0.0,600.0],[0.0,25.0,600.0]],
            "direction": "NEGATIVE"
            },
            "cac_result": {},
            "dependencies": []
        }
    ],
    "field_excitation":[{
        "port_no": "1",
        "parameters": {
            "incoming_func_body": "VOLTAGE_MAX*max(0.0,min(1.0,t/TRISE))",
            "incoming_func_vars": [
                {"VOLTAGE_MAX": "600000"},
                {"TRISE": "1e-9"}
            ],
            "incoming_opt": {
                "E2": "G1",
                "E3": "G2"
            }
        },
        "dependencies": [
            {"G1": "[FUNCTION value] G1 ( Z , R )  = 1 / R"},
            {"G2": "[FUNCTION value] G2 = 0.0"}
        ],
        "cac_result": {}
    }]
}
""", 



"EMISSION EXPLOSIVE": """EMISSION命令在MCL中用于定义发射模型，对应中间符号中的emission_model元素，
其中EMISSION EXPLOSIVE代表爆炸式发射模型，
EMISSION命令对应的json项的json模式为：
{"sys_type": "emission_model", "sys_name": "XXXX", "species_opt": "ELECTRON", "number_opt": "1.0"}

### 示例输入：
[
    {
        "kind": "emission",
        "emission_type": "EXPLOSIVE",
        "species": "ELECTRON",
        "parameters": {
            "number": "1"
        },
        "cmd_no": 1,
        "dependency": []
    }
]
### 示例输出：
{
    "emission_model": [
        {
            "sys_type": "emission_model",
            "sys_name": "EXPLOSIVE",
            "parameters": {
                "model_opt": null,
                "species_opt": "ELECTRON",
                "number_opt": "1.0"
            }
        }
    ]
}
""",



"EMIT": """EMIT命令在MCL中用于定义发射模型的应用位置，对应中间符号中的emit_apply元素，
EMIT命令对应的json项的json模式为：
{"sys_type": "emit_apply", "emission_name": "XXXX", "mobject": "YYYY", "ex_in": ["EXCLUDE", "obj1", "INCLUDE", "obj2"]}

### 示例输入：
[
    {
        "kind": "emit",
        "model": "EXPLOSIVE",
        "mobject": "CATHODE",
        "ex_in": [
            "EXCLUDE",
            "CATHODE1",
            "INCLUDE",
            "EMITTER"
        ],
        "cmd_no": 1,
        "dependency": [
            {
                "CATHODE": "[area value] muti-polygon, details omitted"
            },
            {
                "CATHODE1": "[area value] [(-1.0, 8.0), (57.0, 8.0), (57.0, 11.0), (-1.0, 11.0), (-1.0, 8.0)] (mm)"
            },
            {
                "EMITTER": "[area value] [(56.9, 8.0), (57.2, 8.0), (57.2, 11.0), (56.9, 11.0), (56.9, 8.0)] (mm)"
            }
        ]
    }
]
### 示例输出：
{
    "emit_apply": [
        {
            "sys_type": "emit_apply",
            "emission_name": "EXPLOSIVE",
            "parameters": {
                "mobject": "CATHODE",
                "ex_in": [
                    "EXCLUDE",
                    "CATHODE1",
                    "INCLUDE",
                    "EMITTER"
                ]
            },
            "cac_result": {}
        }
    ]
}
""",



"PRESET": """PRESET命令在MCL中用于定义静电磁场，对应中间符号中的electromagnetic_field元素，
PRESET命令对应的json项的json模式为：
{"sys_name": "XXXX", "component": "0/1/2", "func_name": "YYYY", "kind": "zrFunc"}

### 示例输入：
[
    {
        "kind": "preset",
        "preset_name": "B1ST",
        "func_name": "B_Z",
        "cmd_no": 1,
        "dependency": [
            {
                "sys_name": "B_Z",
                "command": "FUNCTION",
                "text": "FUNCTION B_Z ( Z , R )   =  2.8 /  ( 1 + EXP (  ( Z - 0.29 )  / 0.02 )  )    ;"
            }
        ]
    },
    {
        "kind": "preset",
        "preset_name": "B2ST",
        "func_name": "B_R",
        "cmd_no": 2,
        "dependency": [
            {
                "sys_name": "B_R",
                "command": "FUNCTION",
                "text": "FUNCTION B_R ( Z , R )   =  2.8 /  ( 2 * 0.02 )  * R * EXP (  ( Z - 0.29 )  / 0.02 )  /  (  ( 1 + EXP (  ( Z - 0.29 )  / 0.02 )  )  ** 2 )   ;"
            }
        ]
    }
]
### 示例输出：
{
    "electromagnetic_field": [
        {
            "sys_name": "B1ST",
            "parameters": {
                "component": "0",
                "func_name": "B_Z",
                "kind": "zrFunc"
            },
            "cac_result": {
                "func_body": "2.8/(1+exp((z-0.29)/0.02))",
                "func_vars": {}
            }
        },
        {
            "sys_name": "B2ST",
            "parameters": {
                "component": "1",
                "func_name": "B_R",
                "kind": "zrFunc"
            },
            "cac_result": {
                "func_body": "2.8/(2*0.02)*r*exp((z-0.29)/0.02)/((1+exp((z-0.29)/0.02))^2)",
                "func_vars": {}
            }
        }
    ]
}
""",




"INDUCTOR": """INDUCTOR命令在MCL中用于定义电感，对应中间符号中的inductor元素，
INDUCTOR命令对应的json项的json模式为：
{"kind": "INDUCTOR", "line_name": "XXXX", "diameter": "YYYY", "inductance": "ZZZZ"}

### 示例输入：
[
    {
        "kind": "INDUCTOR",
        "line_name": "GAP",
        "diameter": "1e-3",
        "inductance": "100e-9",
        "cmd_no": 1,
        "dependency": [
            {
                "GAP": "[line value] [(0.8, 0.0965), (0.8, 0.143)] (m)"
            }
        ]
    }
]
### 示例输出：
{
    "inductor": [
        {
            "kind": "INDUCTOR",
            "line_name": "GAP",
            "diameter": "1e-3",
            "inductance": "100e-9",
            "other_params": {}
        }
    ]
}
""",




"RESISTOR": """
""",




"FOIL": """FOIL命令在MCL中用于定义foil模型，对应中间符号中的foil_model元素，
FOIL命令对应的json项的json模式为：
{"kind": "FOIL", "geom_name": "XXXX", "thickness": "YYYY", "material": "ZZZZ"}

### 示例输入：
[
    {
        "kind": "FOIL",
        "geom_name": "FOIL_AREA",
        "thickness": "1e-6",
        "material": "ALUMINUM",
        "cmd_no": 1,
        "dependency": [
            {
                "FOIL_AREA": "[area value] [(0.1, 0.01), (0.2, 0.01), (0.2, 0.02), (0.1, 0.02), (0.1, 0.01)] (m)"
            }
        ]
    }
]
### 示例输出：
{
    "foil_model": [
        {
            "kind": "FOIL",
            "geom_name": "FOIL_AREA",
            "thickness": "1e-6",
            "material": "ALUMINUM",
            "other_params": {}
        }
    ]
}
""",
"OBSERVE": """OBSERVE命令在MCL中用于观测粒子推进过程中的物理量，对应中间符号中的diagnostic元素，
OBSERVE命令对应的json项的json模式为：
{"kind": "observe_XXXX", "observe_type": "FIELD/FIELD_INTEGRAL/...", "field_component": "E2/B1/...", "object_name": "YYYY"}

### 示例输入：
[
    {
        "kind": "observe_field_integral",
        "observe_type": "FIELD_INTEGRAL",
        "field_component": "E.DL",
        "object_name": "INLET",
        "options": {},
        "cmd_no": 1,
        "dependency": [
            {
                "INLET": "[line value] [(0.0, 10.0), (0.0, 25.0)] (mm)"
            }
        ]
    },
    {
        "kind": "observe_field",
        "observe_type": "FIELD",
        "field_component": "E2",
        "object_name": "ED2",
        "options": {},
        "cmd_no": 2,
        "dependency": [
            {
                "ED2": "[point value] (998.4, 140.0) (mm)"
            }
        ]
    }
]
### 示例输出：
{
    "diagnostic": [
        {
            "kind": "observe_field_integral",
            "observe_type": "FIELD_INTEGRAL",
            "field_component": "E.DL",
            "object_name": "INLET",
            "options": {}
        },
        {
            "kind": "observe_field",
            "observe_type": "FIELD",
            "field_component": "E2",
            "object_name": "ED2",
            "options": {}
        }
    ]
}
"""
}



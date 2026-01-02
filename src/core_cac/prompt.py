

m2u_task_dict = {
    "parse": """
    现在请你来完成解析部分，将命令预处理后的文本解析为json格式的中间文件。
    解析的注意事项:
    1.保留预处理的命令行数、命令名标记,若不存在这两个字段，行号填写为0，报错。
    2.如果输入的命令不符合预期，如格式不对，不是指定的命令类型，残缺等等，在"errors"字段中描述具体错误类型
    3.解析的参数放到payload字段中
    4.整个输出是一个json数组，每个元素对应一条命令的json项，不要有多余的描述
    """,
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

    "PRESET": """
    解析PRESET命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    PRESET命令的规则:
    1.PRESET命令用于预设场分量的函数
    2.PRESET命令的格式为：PRESET field FUNCTION function_name
    3.field是要初始化的场分量，支持：B1ST、B2ST、B3ST（静态磁场）
    4.FUNCTION是关键字，表示使用函数进行预设
    5.function_name是已定义的函数名称
    6.命令以分号结尾
    """,

    "EMISSION": """
    解析EMISSION命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    EMISSION命令的规则:
    1.EMISSION命令的格式为：EMISSION 发射类型 [参数列表]
    2.发射类型包括：EXPLOSIVE、BEAM、GYRO、HIGH_FIELD、PHOTOELECTRIC、SECONDARY、THERMIONIC等
    3.参数可能包括SPECIES、NUMBER、THRESHOLD等选项
    4.每个选项后面跟相应的值
    """,

    "OBSERVE": """
    解析OBSERVE命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    OBSERVE命令的规则:
    1.OBSERVE命令的格式为：OBSERVE 观测类型 [参数] 对象名 [选项]
    2.观测类型包括：FIELD、FIELD_POWER、FIELD_INTEGRAL等
    3.FIELD后面可以跟场分量（如E1、E2、B1等）
    4.对象名是要观测的几何对象
    5.可能包含其他选项如FFT、TIME_FREQUENCY等
    """,

    "PORT": """
    解析PORT命令，每行命令输出一个json项，包含命令行号、命令名、参数等字段。
    PORT命令的规则:
    1.PORT命令的格式为：PORT 几何对象 方向 [选项列表]
    2.方向为POSITIVE或NEGATIVE
    3.选项可能包括：INCOMING、NORMALIZATION、PHASE_VELOCITY等
    4.INCOMING后面跟函数名和相关参数
    5.NORMALIZATION指定归一化方式
    """
    


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
            "name": "{name}",
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
                "name": "ZP1",
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
                "name": "ZS1",
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
            "name": "{函数名}",
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
                "name": "FIN",
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
                "name": "G1",
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
                "name": "G2",
                "params": [],
                "body": "0.0"
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
                    "option_type": "{选项类型}",
                    "parameters": {}
                }
            ]
        },        
        "errors": "no或者具体错误类型"
    }
    
    ##示例输入：
    {"lineno": "68", "command": "PORT", "text": "PORT INLET POSITIVE INCOMING FIN FUNCTION E2 G1 E3 G2 NORMALIZATION VOLTAGE INLET ;"}
    {"lineno": "71", "command": "PORT", "text": "PORT OUTLET NEGATIVE ;"}
    ##示例输出：
    [
        {
            "lineno": "68",
            "command": "PORT",
            "parser_kind": "LLM",
            "payload": {
                "kind": "PORT",
                "geom_name": "INLET",
                "direction": "POSITIVE",
                "options": [
                    {
                        "option_type": "INCOMING",
                        "parameters": {
                            "function": "FIN",
                            "components": ["E2", "G1", "E3", "G2"]
                        }
                    },
                    {
                        "option_type": "NORMALIZATION",
                        "parameters": {
                            "type": "VOLTAGE",
                            "object": "INLET"
                        }
                    }
                ]
            },
            "errors": "no"
        },
        {
            "lineno": "71",
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
    ]"""

}


m2u_task_dict = {
    "parse": """
    现在请你来完成解析部分，将命令预处理后的文本解析为json格式的中间文件。
    解析的注意事项:
    1.保留预处理的命令行数、命令名标记,若不存在这两个字段，行号填写为0，报错。
    2.如果输入的命令不符合预期，如格式不对，不是指定的命令类型，残缺等等，在"errors"字段中描述具体错误类型
    3.整个输出是一个json数组，每个元素对应一条命令的json项，不要有多余的描述
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
    {"linen}
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
    }
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

}


class LLMRouteConfig:
    ###################
    # LLM解析路由参数配置(默认使用PLY解析器)
    ###################
    # 哪些命令可能是"复合前缀"（两词命令名）
    multiword_prefixes: set = {"OBSERVE", "EMISSION"}
    
    # REGEX解析器处理的命令（简单、结构化的命令）
    regexparse_commands: set = {
        "INDUCTOR",
    }

    # LLM解析器处理的命令（复杂、开放式的命令）
    llmparse_commands: set = {
        #"ASSIGN",
        #"FUNCTION",   #函数定义

        #"POINT",
        #"LINE",
        #"AREA",

        
        #"MARK",
        #"CONDUCTOR",

        #"PORT",
        #"PRESET",
        #"EMISSION", 
        #"EMIT",
        #"INDUCTOR",
        

        #"OBSERVE", "OBSERVE FIELD", "OBSERVE FIELD_POWER", "OBSERVE FIELD_INTEGRAL"
    }

    # LLM解析器处理的前缀（所有以这些词开头的命令）
    llmparse_prefixes: set = {"   ",
        #"OBSERVE",  # 所有OBSERVE开头的命令
    }

    # LLM解析器处理的正则模式（包含特定模式的命令）
    llmparse_patterns: list = [
        #r".*COMPLEX.*",  # 包含复杂表达式的命令
        #r".*\$.*",       # 包含变量引用的命令
    ]

    ###################
    # LLM转换器路由参数配置
    ###################

    # mcl2mid转换器的命令类型(kind)
    mcl2mid_llmconv_commands: tuple = (
            #"ASSIGN", "PARAMETER", "CHARACTER", "REAL", "INTEGER",

            #"FUNCTION",

            #"POINT","LINE", "AREA",

            "MARK",

            #"CONDUCTOR", "VOID",

            #"PORT", "FREESPACE",

            #"EMISSION", "EMIT",
            #"INDUCTOR",
            #"RESISTOR",
            #"FOIL",
            #"PRESET",

            #"OBSERVE"

    )

llm_route_config = LLMRouteConfig()
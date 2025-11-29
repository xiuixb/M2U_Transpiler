import re
from dataclasses import dataclass
from typing import List, Iterable, Literal


class PreprocessRules:
    ## 第一次循环用到的
    # 1. 整条命令跳过
    commands_to_skip = [

    # 1. 变量和函数
    "CONTROL",
    "MCLDIALOG",

    # 2. 逻辑命令
    "CALL",
    "RETURN",
    "$namelist$",

    # 3. I/O Utilities
    "BLOCK",
    "ENDBLOCK",
    "COMMENT",
    "C",
    "Z",
    "!",
    "DELIMITER",
    "ECHO",
    "NOECHO",

    # 4. 执行控制
    
    "START",
    "STOP",
    "TERMINATE",
    "COMMAND",
    "KEYBOARD",
    

    # 5. OBJECTS
    
    "SYSTEM",
    "VOLUME",
    "LIST",
    

    # 6. 网格
    
    "DURATION",
    "TIMER",
    #"MARK",
    "AUTOGRID",
    "GRID",
    

    # 7. Outer Boundries
    
    "SYMMETRY",
    #"PORT",
    "RESONANT_PORT",
    #"OUTGOING",
    #"FREESPACE",
    "MATCH",
    "IMPORT",
    

    # 8. 传输线
    
    "TRAMLINE",
    "JOIN",
    "LOOKBACK",
    "VOLTAGE",
    

    # 9. 材料属性
    
    #"CONDUCTANCE",
    #"CONDUCTOR",
    #"DIELECTRIC",
    #"INDUCTOR",
    "FILM",
    "FOIL",
    "GAS_CONDUCTIVITY",
    "MATERIAL",
    "SURFACE_LOSS",
    #"VOID",
    

    # 10. 发射过程
    #"EMISSION",
    #"EMIT",
    "PHOTON",
    "IONIZATION",

    # 11. 算法
    
    "TIME_STEP",
    "MODE",
    "MAXWELL",
    "SPECIES",
    "LORENTZ",
    "CONTINUITY",
    "CIRCUIT",
    "POISSON",
    "POPULATE",
    "COILS",
    "CURRENT_SOURCE",
    "DRIVER",
    "EIGENMODE",
    #"PRESET",
    

    # 12. 输出控制
    
    "GRAPHICS",
    "HEADER",
    "DUMP",
    "EXPORT",
    "PARAMETER",
    "STATISTICS",
    "TABLE",
    "OBSERVE FIELD_INTEGRAL",
    #"OBSERVE",
    "RANGE",
    "DISPLAY",
    "DISPLAY_2D", 
    "CONTOUR",
    "VECTOR",
    "PHASESPACE",
    "TAGGING",
    "VIEWER",
    ]

    # 2. 命令 + 特定选项 整条命令跳过
    commands_to_skip_byOptions = {
        "PORT": [],
        "OBSERVE": ["FILTER"],
        "LINE": ["SYS$"]
    }

    # 3. 命令 + 特定选项仅丢弃参数
    options_to_skip = {
        "PORT": ["PHASE_VELOCITY"],
        "EMISSION": ["THRESHOLD", "SURFACE_SPACING", "TIMING"],
        "OBSERVE": ["FFT", "TIME_FREQUENCY"],
    }

    # 4. 命令对应的所有可能选项（用来切分）
    options_of_command = {
        "PORT": ["INLET", "OUTLET", "INCOMING", "FUNCTION", "NORMALIZATION", "PHASE_VELOCITY"],
        "OBSERVE": ["FIELD_POWER", "FIELD_INTEGRAL", "FILTER", "FIELD", "FFT", "TIME_FREQUENCY"],
        "EMISSION": ["SPECIES", "THRESHOLD", "NUMBER", "SURFACE_SPACING", "TIMING"],
    }

    # ---------- 正则 ----------
    float_e_exp = r"([0-9]+([.][0-9]*)?[eE][+-]?[0-9]+|[.][0-9]+[eE][+-]?[0-9]+)"
    float_exp = r"[+-]?([0-9]+([.][0-9]*)?([eE][+-]?[0-9]+)?|[.][0-9]+([eE][+-]?[0-9]+)?)"
    float_ext_exp = r"[+-]?([0-9]+([.][0-9]*)?([eE][+-]?[0-9]+)?|[.][0-9]+([eE][+-]?[0-9]+)?)[_A-Za-z]*"
    identity_exp = r"[\.%\&\<\>\?_\~\`@#\^|{}\[\]a-zA-Z][\.%\&\<\>\?_\~\`@#\^|{}\[\]a-zA-Z0-9]*"


@dataclass
class RuleBucket:
    exact: set[str]
    prefix: List[str]
    regex: List[re.Pattern]

    @classmethod
    def from_patterns(cls, exact: Iterable[str] = (), prefix: Iterable[str] = (), regex: Iterable[str] = ()):
        return cls(
            exact=set([s.upper() for s in exact]),
            prefix=[s.upper() for s in prefix],
            regex=[re.compile(r, flags=re.IGNORECASE) for r in regex],
        )

    def match(self, key: str, text: str) -> bool:
        K = key.upper()
        if K in self.exact:
            return True
        for p in self.prefix:
            if K.startswith(p):
                return True
        for rgx in self.regex:
            if rgx.search(text):
                return True
        return False


class RouteRule:
    RouteType = Literal["PLY", "REGEX", "LLM"]

    def __init__(self, regex_rules: RuleBucket, llm_rules: RuleBucket, MULTIWORD_PREFIXES: set[str]):
        self.regex_rules = regex_rules
        self.llm_rules = llm_rules
        self.MULTIWORD_PREFIXES = MULTIWORD_PREFIXES

    def extract_command_key(self, command: str, text: str) -> str:
        """
        生成路由用 key：
        - 若命令在 MULTIWORD_PREFIXES，尝试取 text 的前两个 token 联合作为 key（如 "OBSERVE FIELD"）
        - 否则用单词命令（如 "LINE"、"AREA"）
        """
        tokens = text.split()
        if tokens and tokens[0] in self.MULTIWORD_PREFIXES and len(tokens) >= 2:
            # 第二词只保留字母/下划线，避免括号、符号干扰
            head2 = re.sub(r"[^A-Z_]+", "", tokens[1])
            if head2:
                return f"{tokens[0]} {head2}"
        return command.upper()

    def pick_route(self, command: str, text: str) -> RouteType:
        key = self.extract_command_key(command, text)
        if self.regex_rules.match(key, text):
            return "REGEX"
        if self.llm_rules.match(key, text):
            return "LLM"
        return "PLY"
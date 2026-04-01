# src/domain/config/cmd_dic.py
# ============================================================
# MAGIC MCL command dictionary
# - CMD_KEYWORDS_SINGLE: single-token commands
# - CMD_KEYWORDS_MULTI: multi-token commands
# ============================================================

class MCLParse_CmdDict:
    def __init__(self):
        self.MCL2Kind = {
            "ASSIGN": ["variable"],
            "PARAMETER": ["variable"],
            "CHARACTER": ["variable"],
            "REAL": ["variable"],
            "INTEGER": ["variable"],

            "FUNCTION": ["function"],

            "POINT": ["point"],
            "LINE": ["line"],
            "AREA": ["area"],

            "MARK": ["mark"],

            "CONDUCTOR": ["material_assign"],
            "VOID": ["material_assign"],

            "PORT": ["port"],
            "FREESPACE": ["freespace"],

            "EMISSION": ["emission_model"],
            "EMIT": ["emission_apply"],
            "INDUCTOR": ["inductor"],
            "RESISTOR": ["resistor"],
            "FOIL": ["foil_model"],

            "PRESET": ["electromagnetic_field"],

            "OBSERVE": ["observe"]
        }

class MCL2MID_CmdDict:
    def __init__(self):
        self.MCL_dependency_dict = {
            "ASSIGN": ["ASSIGN"],
            "FUNCTION": ["ASSIGN"],
            "POINT": ["ASSIGN"],
            "LINE": ["ASSIGN", "POINT"],
            "AREA": ["ASSIGN", "POINT"],
            "MARK": ["ASSIGN"],
            "CONDUCTOR": [],
            "PORT": ["FUNCTION", "LINE"],
            "EMISSION": [],
            "EMIT": ["EMISSION", "AREA"],
            "PRESET": ["FUNCTION"],
            "INDUCTOR": ["LINE"],
            "RESISTOR": ["LINE"],
            "FOIL": ["LINE","AREA"],
            "OBSERVE": ["POINT", "LINE"]
        }
        
        self.MID_dict = {
            "ASSIGN": ["variable"],
            "FUNCTION": ["function"],
            "POINT": ["point"],
            "LINE": ["line"],
            "AREA": ["area"],
            "MARK": ["mark"],
            "CONDUCTOR": ["material_assign"],
            "PORT": ["port", "field_excitation"],
            "EMISSION": ["emission_model"],
            "EMIT": ["emission_apply"],
            "PRESET": ["electromagnetic_field"],
            "INDUCTOR": ["inductor"],
            "RESISTOR": ["resistor"],
            "FOIL": ["foil_model"],
            "OBSERVE": ["diagnostic"]
        }

        self.MCL2MID_llmconv_List = {
            "MARK": [],
            "CONDUCTOR": [],
            "PORT": [],
            "EMISSION": [],
            "EMIT": [],
            "PRESET": [],
            "INDUCTOR": [],
            "RESISTOR": [],
            "FOIL": [],
            "OBSERVE": []
        }

        


        # 中间语义的依赖关系
        self.MID_dependency_dict = {
            # 基础命令
            "variable": ["variable"],  # 变量可能依赖其他变量
            "function": ["variable"],  # 函数可能依赖变量
            
            # 几何命令
            "point": ["variable"],  # 点可能依赖变量
            "line": ["variable", "point"],  # 线可能依赖变量和点
            "area": ["variable", "point"],  # 面可能依赖变量、点、线
            "geom_cac_result": ["area"],  # 几何区域计算结果可能依赖面
            "selection": ["point", "line", "area", "geom_cac_result"],  # 选择可能依赖点、线、面、几何计算结果
            
            # 材料命令
            "material_library": [],  # 材料库无依赖
            "material_assign": ["area", "material_library"],  # 材料应用依赖面、材料
            
            # 边界命令
            "port": ["selection"],  # 边界定义依赖几何选择
            
            # 物理实体命令
            "particle_library":[],
            "field_excitation": ["port", "function"],
            "emission_model": [],
            "emission_apply": ["selection"],

            "secondary_electron_emitter":[],
            "electromagnetic_field": ["function"],
            "inductor": ["selection"],
            "resistor": ["selection"],
            "foil_model": ["selection"],

            # 诊断命令
            "diagnostic": []
        }


class PreprocessCmd:
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


CMD_KEYWORDS_SINGLE = {
    # Script control flow
    "BLOCK",
    "ENDBLOCK",
    "CALL",
    "RETURN",
    "DO",
    "ENDDO",
    "IF",
    "ELSEIF",
    "ELSE",
    "ENDIF",

    # Script text formatting
    "COMMENT",
    "C",
    "Z",
    "!",
    "DELIMITER",
    "ECHO",
    "NOECHO",

    # Script runtime control
    "KEYBOARD",
    "START",
    "STOP",
    "TERMINATE",

    # Variables, functions, types
    "ASSIGN",
    "CHARACTER",
    "CONTROL",
    "FUNCTION",
    "INTEGER",
    "MCLDIALOG",
    "REAL",
    "PARAMETER",

    # Geometry
    "AREA",
    "LINE",
    "POINT",
    "SYSTEM",
    "VOLUME",

    # Mesh and time
    "MARK",
    "AUTOGRID",
    "DURATION",
    "TIMER",
    "PARALLEL_GRID",

    # Ports and boundaries
    "PORT",
    "RESONANT_PORT",
    "FREESPACE",
    "IMPORT",
    "MATCH",
    "OUTGOING",
    "SYMMETRY",

    # Tramline / transmission-line model
    "JOIN",
    "LOOKBACK",
    "TRAMLINE",
    "VOLTAGE",

    # Basic materials
    "CONDUCTOR",
    "FILM",
    "FOIL",
    "CONDUCTANCE",
    "DIELECTRIC",
    "GAS_CONDUCTIVITY",
    "MATERIAL",
    "SURFACE_LOSS",
    "VOID",

    # Lumped / special devices
    "INDUCTOR",
    "POLARIZER",
    "RESISTOR",
    "SHIM",

    # Emission and collision processes
    "EMISSION",
    "EMIT",
    "IONIZATION",
    "PHOTON",

    # Initial fields and static structures
    "CIRCUIT",
    "COILS",
    "EIGENMODE",
    "POISSON",
    "PRESET",

    # Initial particles and drivers
    "CURRENT_SOURCE",
    "DRIVER",
    "POPULATE",

    # Diagnostics
    "OBSERVE",
    "RANGE",
    "CONTOUR",
    "PHASESPACE",
    "TAGGING",
    "VECTOR",

    # Solver
    "MODE",
    "TIME_STEP",
    "CONTINUITY",
    "LORENTZ",
    "SPECIES",

    # Data output
    "DISPLAY",
    "DUMP",
    "EXPORT",
    "GRAPHICS",
    "HEADER",
    "STATISTICS",
    "VIEWER",
    "TABLE",
}


CMD_KEYWORDS_MULTI = {
    # Mesh and time
    "GRID EXPLICIT",
    "GRID ORIGIN",
    "GRID PADE",
    "GRID QUADRATIC",
    "GRID UNIFORM",

    # Emission model definitions
    "EMISSION BEAM",
    "EMISSION EXPLOSIVE",
    "EMISSION GYRO",
    "EMISSION HIGH_FIELD",
    "EMISSION PHOTOELECTRIC",
    "EMISSION SECONDARY",
    "EMISSION THERMIONIC",

    # Observe diagnostics
    "OBSERVE CIRCUIT",
    "OBSERVE COLLECTED",
    "OBSERVE EMITTED",
    "OBSERVE FIELD",
    "OBSERVE FIELD_ENERGY",
    "OBSERVE FIELD_INTEGRAL",
    "OBSERVE FIELD_POWER",
    "OBSERVE FILE",
    "OBSERVE IMPEDANCE",
    "OBSERVE INDUCTOR",
    "OBSERVE INTERVAL",
    "OBSERVE IONIZATION",
    "OBSERVE NEUTRAL_GAS",
    "OBSERVE PARTICLE_STATISTICS",
    "OBSERVE RESISTOR",
    "OBSERVE RESONANT_PORT",
    "OBSERVE SECONDARY",
    "OBSERVE SMATRIX",
    "OBSERVE SPACE_HARMONIC",
    "OBSERVE TRAMLINE",
    "OBSERVE TRANSFORM",

    # Range diagnostics
    "RANGE FIELD",
    "RANGE FIELD_INTEGRAL",
    "RANGE FIELD_POWER",
    "RANGE HISTOGRAM",
    "RANGE NEUTRAL_GAS",
    "RANGE PARTICLE",
    "RANGE TRAMLINE",

    # Contour diagnostics
    "CONTOUR FIELD",
    "CONTOUR HISTOGRAM",
    "CONTOUR NEUTRAL_GAS",

    # Maxwell solver modes
    "MAXWELL BIASED",
    "MAXWELL CENTERED",
    "MAXWELL FIXED",
    "MAXWELL HIGH_Q",
    "MAXWELL QUASI_STATIC",
    "MAXWELL QUASI_NEUTRAL",

    # Table output
    "TABLE FIELD",
    "TABLE PARTICLES",
}

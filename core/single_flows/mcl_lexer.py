#######################
# core\single_flows\mcl_lexer.py
#######################

import os
import sys

# 获取项目根目录路径
current_dir = os.path.dirname(os.path.abspath(__file__))
while not os.path.exists(os.path.join(current_dir, ".project_mark")):
    parent_dir = os.path.dirname(current_dir)
    if    parent_dir != current_dir: current_dir = parent_dir
    else: raise FileNotFoundError("未找到项目根目录，检查.project_mark文件")
project_root = current_dir
sys.path.append(project_root)

import ply.lex as lex


states = (
    ('functiondef', 'inclusive'),  # 函数定义状态（允许继承基础规则）
    ('funcbody', 'exclusive')     # 函数体捕获状态（独占模式）
    #('presetdef', 'inclusive')    # 预设定义状态（允许继承基础规则）
)

# 关键字列表
reserved = {
    'ASSIGN': 'K_ASSIGN',
    'CHARACTER': 'K_CHARACTER',
    'INTEGER': 'K_INTEGER',
    'REAL': 'K_REAL',
    'FUNCTION': 'FUNCTION',
    'DO': 'K_DO',
    'ENDDO': 'K_ENDDO',
    'IF': 'K_IF',
    'THEN': 'K_THEN',
    'ELSEIF': 'K_ELSEIF',
    'ELSE': 'K_ELSE',
    'ENDIF': 'K_ENDIF',
    'HEADER': 'C_HEADER',
    'POINT': 'C_POINT',
    'LINE': 'C_LINE',
    'AREA': 'C_AREA',
    'MARK': 'C_MARK',
    #'AUTOGRID': 'C_AUTOGRID',
    #'GRAPHICS': 'C_GRAPHICS',
    #'ECHO': 'C_ECHO',
    #'NOECHO': 'C_NOECHO',
    #'START': 'C_START',
    #'STOP': 'C_STOP',
    #'TERMINATE': 'C_TERMINATE',
    
    #几何建模参数
    'STRAIGHT': 'K_STRAIGHT',
    'CONFORMAL': 'K_CONFORMAL',
    'OBLIQUE': 'K_OBLIQUE',
    'CIRCULAR': 'K_CIRCULAR',
    'ELLIPTICAL': 'K_ELLIPTICAL',
    'RECTANGULAR': 'K_RECTANGULAR',
    'FUNCTIONAL': 'K_FUNCTIONAL',
    'POLYGONAL': 'K_POLYGONAL',
    'FILLET': 'K_FILLET',
    'QUARTERROUND': 'K_QUARTERROUND',
    'SINUSOID': 'K_SINUSOID',

    #材料参数
    'CONDUCTANCE': 'K_CONDUCTANCE',
    'CONDUCTOR': 'K_CONDUCTOR',
    'DIELECTRIC': 'K_DIELECTRIC',
    'VOID':'K_VOID',
    'MATERIAL':'K_MATERIAL',

    #材料属性
    'ATOMIC_NUMBER': 'K_ATOMIC_NUMBER',
    'ATOMIC_MASS': 'K_ATOMIC_MASS',
    'MOLECULAR_CHARGE': 'K_MOLECULAR_CHARGE',
    'MOLECULAR_MASS': 'K_MOLECULAR_MASS',
    'CONDUCTIVITY': 'K_CONDUCTIVITY',
    'MASS_DENSITY': 'K_MASS_DENSITY',
    'PERMITTIVITY': 'K_PERMITTIVITY',

    #端口
    'PORT': 'K_PORT',
    'OUTGOING': 'K_OUTGOING',
    #'FREESPACE': 'K_FREESPACE',

    #端口参数
    'POSITIVE': 'K_POSITIVE',
    'NEGATIVE': 'K_NEGATIVE',
    'TE': 'K_TE',
    'TM': 'K_TM',
    'ALL': 'K_ALL',
    'INCOMING': 'K_INCOMING',
    'NORMALIZATION':'K_NORMALIZATION',
    'PEAK_FIELD': 'K_PEAK_FIELD',
    'VOLTAGE': 'K_VOLTAGE',

    #发射
    'EMISSION': 'K_EMISSION',
    'EMIT': 'K_EMIT',
    'MODEL': 'K_MODEL',
    'SPECIES': 'K_SPECIES',
    'NUMBER': 'K_NUMBER',
    'BEAM': 'K_BEAM',
    'EXPLOSIVE': 'K_EXPLOSIVE',
    #'GYRO': 'K_GYRO',
    #'HIGH_FIELD': 'K_HIGH_FIELD',
    #'PHOTOELECTRIC': 'K_PHOTOELECTRIC',
    #'THERMIONIC': 'K_THERMIONIC',
    #'FIXED_CHARGE_SIZE': 'K_FIXED_CHARGE_SIZE',
    #'TIMING': 'K_TIMING',
    #'RANDOM_TIMING': 'K_RANDOM_TIMING',
    #'SURFACE_SPACING': 'K_SURFACE_SPACING',
    #'OUTWARD_SPACING': 'K_OUTWARD_SPACING',
    #'RANDOM': 'K_RANDOM',
    #'UNIFORM': 'K_UNIFORM',
    #'FIXED': 'K_FIXED',
    'EXCLUDE': 'K_EXCLUDE',
    'INCLUDE': 'K_INCLUDE',

    #静磁场
    'PRESET': 'K_PRESET',

    #定时器
    'TIMER': 'K_TIMER',
    'PERIODIC': 'K_PERIODIC',
    'DISCRETE':'K_DISCRETE',
    'INTEGRATE': 'K_INTEGRATE',

    #MARK参数
    'MINIMUM':'K_MINIMUM',
    'MIDPOINT': 'K_MIDPOINT',
    'MAXIMUM': 'K_MAXIMUM',
    'SIZE': 'K_SIZE',


    #诊断
    'OBSERVE': 'K_OBSERVE',
    'EMITTED': 'K_EMITTED',
    'CHARGE': 'K_CHARGE',
    'CURRENT': 'K_CURRENT',
    'ENERGY': 'K_ENERGY',
    'POWER': 'K_POWER',

    'FIELD': 'K_FIELD',
    'FIELD_POWER': 'K_FIELD_POWER',
    'FIELD_ENERGY': 'K_FIELD_ENERGY',
    "FIELD_INTEGRAL": 'K_FIELD_INTEGRAL',


    'FFT': 'K_FFT',
    'MAGNITUDE': 'K_MAGNITUDE',
    'COMPLEX': 'K_COMPLEX',
    'WINDOW': 'K_WINDOW',
    'FREQUENCY': 'K_FREQUENCY',
    'TIME_FREQUENCY': 'K_TIME_FREQUENCY',
    'SPECTROGRAM': 'K_SPECTROGRAM',
    'WIGNER-VILLE': 'K_WIGNER_VILLE',
    'REDUCED_INTERFERENCE': 'K_REDUCED_INTERFERENCE',
    #'E.DL': 'K_E.DL',
    
    'TIME': 'K_TIME',
    'RANGE': 'K_RANGE',

    'SYSTEM': 'C_SYSTEM'
}

# 定义所有的 tokens，包括 reserved
tokens = [
    # 关键字
    'K_COMMENT',
    'K_ASSIGN',
    'K_CHARACTER',
    'K_INTEGER',
    'K_REAL',
    'K_DO',
    'K_ENDDO',
    'K_IF',
    'K_THEN',
    'K_ELSEIF',
    'K_ELSE',
    'K_ENDIF',
    'C_SYSTEM',
    'C_HEADER',
    'C_POINT',
    'C_LINE',
    'C_AREA',
    
    'C_MARK',
    #'C_AUTOGRID',
    #'C_GRAPHICS',
    #'C_ECHO',
    #'C_NOECHO',
    #'C_START',
    #'C_STOP',
    #'C_TERMINATE',
    

    'O_GT',
    'O_LT',
    'O_LE',
    'O_GE',
    'O_EQ',
    'O_NE',

    # 标识符和字面量
    'IDENTITY',
    'INTEGER_LITERAL',
    'FLOAT_LITERAL',
    'STRING_LITERAL',
    # 'STRING',
    
    'FUNCTION',
    # 函数体状态
    'FUNCTION_BODY',

    #命令参数
    'K_STRAIGHT',
    'K_CONFORMAL',
    'K_OBLIQUE',
    'K_CIRCULAR',
    'K_ELLIPTICAL',
    'K_RECTANGULAR',
    'K_FUNCTIONAL',
    'K_POLYGONAL',
    'K_FILLET',
    'K_QUARTERROUND',
    'K_SINUSOID',

    #材料参数
    'K_CONDUCTANCE',
    'K_CONDUCTOR',
    'K_DIELECTRIC',
    'K_VOID',
    'K_MATERIAL',

    #材料属性
    'K_ATOMIC_NUMBER',
    'K_ATOMIC_MASS',
    'K_MOLECULAR_CHARGE',
    'K_MOLECULAR_MASS',
    'K_CONDUCTIVITY',
    'K_MASS_DENSITY',
    'K_PERMITTIVITY',

    #端口
    'K_PORT',
    'K_OUTGOING',
    #'K_FREESPACE',

    #端口参数
    'K_POSITIVE',
    'K_NEGATIVE',
    'K_TE',
    'K_TM',
    'K_ALL',
    'K_INCOMING',
    'K_NORMALIZATION',
    'K_PEAK_FIELD',
    'K_VOLTAGE',

    #发射
    'K_EMISSION',
    'K_EMIT',
    'K_MODEL',
    'K_SPECIES',
    'K_NUMBER',
    'K_BEAM',
    'K_EXPLOSIVE',
    #'K_GYRO',
    #'K_HIGH_FIELD',
    #'K_PHOTOELECTRIC',
    #'K_THERMIONIC',
    #'K_FIXED_CHARGE_SIZE',
    #'K_TIMING',
    #'K_RANDOM_TIMING',
    #'K_SURFACE_SPACING',
    #'K_OUTWARD_SPACING',
    #'K_RANDOM',
    #'K_UNIFORM',
    #'K_FIXED',
    'K_EXCLUDE',
    'K_INCLUDE',

    'K_PRESET',

    #诊断
    'K_TIMER',
    'K_PERIODIC',
    'K_DISCRETE',
    'K_INTEGRATE',
    'K_OBSERVE',
    'K_EMITTED',
    'K_CHARGE',
    'K_CURRENT',
    'K_ENERGY',
    'K_POWER',

    'K_FIELD',
    'K_FIELD_POWER',
    'K_FIELD_ENERGY',
    'K_FIELD_INTEGRAL',

    'K_FFT',
    'K_MAGNITUDE',
    'K_COMPLEX',
    'K_WINDOW',
    'K_FREQUENCY',
    'K_TIME_FREQUENCY',
    'K_SPECTROGRAM',
    'K_WIGNER_VILLE',
    'K_REDUCED_INTERFERENCE',

    'K_TIME',

    'K_RANGE',

    #MARK
    'K_MINIMUM',
    'K_MIDPOINT',
    'K_MAXIMUM',
    'K_SIZE',

    # 运算符和分隔符（多字符运算符）
    'EXPONENT'
    #'ENTER_IN',
]

# 也可以定义单字符字面符号
literals = ['=', '+', '-', '*', '/', '(', ')', ';', ',', ':', '$']

# 定义忽略的字符
t_ignore = ' \t\v\r\f'

# 定义操作符的正则表达式（多字符运算符）

t_O_GT        = r'>'
t_O_LT        = r'<'
t_O_LE        = r'<='
t_O_GE        = r'>='
t_O_EQ        = r'=='
t_O_NE        = r'!='


def t_K_COMMENT(t):
    r'COMMENT'
    #print(f"Found COMMENT: {t.value}")
    return t

def t_FUNCTION(t):
    r'FUNCTION\b'  # 精确匹配关键字
    # 当其不在基础状态时，将其视为普通标识符
    if t.lexer.current_state() != 'INITIAL':
        t.type = 'IDENTITY'
    else:
        t.lexer.push_state('functiondef')  # 推入函数定义状态
    return t

def t_functiondef_EQUAL(t):
    r'='
    t.type = '='
    t.lexer.push_state('funcbody')    # 推入函数体状态
    t.lexer.func_body_start = t.lexer.lexpos  # 记录起始位置
    return t

def t_functiondef_SEMI(t):
    r';'
    while t.lexer.current_state() != 'INITIAL':
        t.lexer.pop_state() # 退出functiondef状态
    t.type = ';'         # 保持token类型
    return t

# 当在functiondef状态下遇到换行时退出
def t_functiondef_newline(t):
    r'\n+'
    t.lexer.pop_state()  # 退出functiondef状态
    t.lexer.lineno += len(t.value)

def t_funcbody_SEMI(t):
    r';'
    # 计算函数体范围
    start = t.lexer.func_body_start
    end = t.lexer.lexpos-1  # 分号前的位置
    t.value = t.lexer.lexdata[start:end].strip()
    
    # 状态管理
    while t.lexer.current_state() != 'INITIAL':
        t.lexer.pop_state()
    
    t.type = 'FUNCTION_BODY'
    t.lexer.lexpos = end
    return t

# 修改3：防止状态泄漏的保障机制
def t_funcbody_ANY(t):
    r'.'  # 匹配任意单个字符（除了换行符）
    t.lexer.lexpos += 1  # 手动推进指针
    return None  # 不生成token

def t_funcbody_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    t.lexer.lexpos += len(t.value)  # 手动处理换行

t_funcbody_ignore = ' \t'  # 忽略空格和tab

# 添加错误处理规则
def t_funcbody_error(t):
    print(f"Illegal character in function body: '{t.value[0]}' at line {t.lineno}")
    t.lexer.skip(1)


# 定义多字符运算符，如 '**'
def t_EXPONENT(t):
    r'\*\*'
    t.value = '**'
    return t


def t_STRING_LITERAL(t):
    r'\"[^\"]*\"'  # 匹配双引号包围的字符串
    t.value = t.value[1:-1]  # 去除引号
    # print(f"Found STRING_LITERAL: {t.value}")  # 调试信息
    return t


def t_FLOAT_LITERAL(t):
    r'[+-]?([0-9]+([.][0-9]*)?([eE][+-]?[0-9]+)?|[.][0-9]+([eE][+-]?[0-9]+)?)'
    try:
        t.value = float(t.value)
    except ValueError:
        print(f"Float value too large {t.value}")
        t.value = 0.0
    return t

def t_INTEGER_LITERAL(t):
    r'[+-]?([0-9])+'
    try:
        t.value = int(t.value)
    except ValueError:
        print(f"Integer value too large {t.value}")
        t.value = 0
    return t

def t_IDENTITY(t):
    r'[\.\_a-zA-Z][\.\$\%\&\<\>\?\_\~\`\@\#\^\|\{\}\[\]a-zA-Z0-9]*'
    t.type = reserved.get(t.value.upper(), 'IDENTITY')  # 检查是否为关键字
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# 错误处理
def t_error(t):
    print(f"Illegal character '{t.value[0]}' at line {t.lineno}")
    t.lexer.skip(1)



# 构建词法分析器
lexer = lex.lex()

# 测试词法分析器
if __name__ == "__main__":
    data = '''
        ON = 1 ;
        OFF = 0 ;
        RUNTIME = 60*nano*seconds ;
        DR = 0.5*mm ;
        DZ = 0.5*mm ;
    '''
    lexer.input(data)
    for tok in lexer:
        if tok.type == 'FUNCTION_BODY':
            print(f"FUNCTION_BODY at line {tok.lineno}: {tok.value!r}")
        else:
            if tok.type == 'FLOAT_LITERAL':
                print(f"LexToken({tok.type}, {tok.value})")
            else:
                print(f"LexToken({tok.type}, {tok.value!r})")

        """if tok.type == 'FLOAT_LITERAL':
                print(f"LexToken({tok.type}, {tok.value})")
            else:
                print(f"LexToken({tok.type}, {tok.value!r})")"""

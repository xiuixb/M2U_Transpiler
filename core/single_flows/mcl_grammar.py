###########################
# core\single_flows\mcl_grammar.py
###########################

import os
import sys
import re

# 获取项目根目录路径
current_dir = os.path.dirname(os.path.abspath(__file__))
while not os.path.exists(os.path.join(current_dir, ".project_mark")):
    parent_dir = os.path.dirname(current_dir)
    if    parent_dir != current_dir: current_dir = parent_dir
    else: raise FileNotFoundError("未找到项目根目录，检查.project_mark文件")
project_root = current_dir
sys.path.append(project_root)

import ply.yacc as yacc
from core.single_flows.mcl_lexer import lexer, tokens
from core.single_flows.mcl_ast import *



# -------------------
# 语法优先级和结合性
# -------------------
precedence = (
    ('left', 'O_GT', 'O_LT', 'O_LE', 'O_GE', 'O_EQ', 'O_NE'), # 比较运算符
    ('left', '+', '-'),
    ('left', '*', '/'),
    ('right', 'EXPONENT'),
    ('right', 'UMINUS'),
)

# 语法规则
# ===================
# 基础语法结构
# ===================
def p_program(p):
    """program : statements"""
    p[0] = ProgramNode(p[1])

def p_statements(p):
    """statements : statement
                  | statements statement"""
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]

def p_statement(p):
    """statement : command
                 | assignment
                 | if_statement
                 | do_loop
                 | function
                 """
    p[0] = p[1]

# -------------------
# IF 语句（支持 ELSEIF 链）
# -------------------
def p_if_statement(p):
    """if_statement : K_IF expr K_THEN statements elseif_clauses opt_else K_ENDIF"""
    # 结构：IF条件 + THEN块 + [ELSEIF块列表] + [ELSE块]
    clauses = [(p[2], p[4])] + p[5]  # 初始IF条件+THEN块，合并ELSEIF列表
    p[0] = IfStatementNode(clauses, p[6], lineno=p.lineno(1))

def p_elseif_clauses(p):
    """elseif_clauses : empty
                     | elseif_clauses K_ELSEIF expr K_THEN statements"""
    if len(p) == 1:
        p[0] = []  # 无 ELSEIF
    else:
        p[0] = p[1] + [(p[3], p[5])]  # 追加 ELSEIF 条件+块

def p_opt_else(p):
    """opt_else : empty
                | K_ELSE statements"""
    p[0] = p[2] if len(p) > 1 else None  # ELSE 块或空

# ===================
# DO 循环
# ===================
def p_do_loop(p):
    """
    do_loop : K_DO IDENTITY '=' expr ',' expr statements K_ENDDO
               | K_DO IDENTITY '=' expr ',' expr ',' expr statements K_ENDDO
    """
    if len(p) == 9:
        p[0] = DoLoopNode(VariableNode(p[2]), p[4], p[6], None, p[7], lineno=p.lineno(1))  # 无步长
    else:
        p[0] = DoLoopNode(VariableNode(p[2]), p[4], p[6], p[8], p[9], lineno=p.lineno(1))  # 有步长


# ===================
# 命令体系结构
# ===================
def p_command(p):
    """command : system_command
               | geometry_command
               | header_command
               | material_application_command
               | ports_command
               | emission_command
               | emit_command
               | preset_command
               | timer_command
               | observe_command
               | range_command
               | mark_command
               """
    p[0] = p[1]
# ===================
# 系统命令
# ===================
def p_system_command(p):
    """system_command : C_SYSTEM IDENTITY ';' """
    if ((p[2] == 'CARTESIAN') or (p[2] == 'CYLINDRICAL') or (p[2] == '')):
        p[0] = SystemCommandNode(p[2])
    else:
        print(f"Unsupported system command parameter: {p[2]}")
    

# ===================
# 几何命令体系
# ===================
def p_geometry_command(p):
    """geometry_command : point_command
                        | line_command
                        | area_command"""
    p[0] = p[1]

# -------------------
# POINT 命令
# -------------------
def p_point_command(p):
    """point_command : C_POINT IDENTITY point_coords ';'"""
    p[0] = PointCommandNode(p[2], p[3], p.lineno(1))

def p_point_coords(p):
    """point_coords : expr sep expr
                    | expr sep expr sep expr"""
    if len(p) == 4:
        p[0] = [p[1], p[3]]  # 二维坐标
    else:
        p[0] = [p[1], p[3], p[5]]  # 三维坐标

# -------------------
# LINE 命令
# -------------------
def p_line_command(p):
    """line_command : C_LINE IDENTITY line_type ';'"""
    p[0] = LineCommandNode(p[2], p[3], p.lineno(1))

def p_line_type(p):
    """line_type : K_CONFORMAL point_list
                 | K_OBLIQUE point_list
                 | K_STRAIGHT point_ref point_ref
                 | K_CIRCULAR point_ref point_ref point_ref
                 | K_ELLIPTICAL point_ref expr expr expr expr"""
    #print("识别到line命令：", p[1], p[2])
    if p[1] in ('CONFORMAL', 'OBLIQUE'):
        p[0] = (p[1], {'points': p[2]})
    elif p[1] == 'STRAIGHT':
        p[0] = (p[1], {'start': p[2], 'end': p[3]})
    elif p[1] == 'CIRCULAR':
        p[0] = (p[1], {'center': p[2], 'start': p[3], 'end': p[4]})
    else:  # ELLIPTICAL
        p[0] = (p[1], {
            'center': p[2],
            'x_radius': p[3],
            'y_radius': p[4],
            'start_angle': p[5],
            'end_angle': p[6]
        })

def p_point_ref(p):
    """point_ref : expr sep expr
                 """
    #print("识别到point_ref：", p[1], p[3])
    if len(p) == 4:
        p[0] = CoordPointNode((p[1], p[3]))  # 直接构造坐标对节点
    else:
        p[0] = NamedPointNode(p[1])          # 点变量节点

def p_point_list(p):
    """point_list : point_ref
                  | point_list sep point_ref"""  # 支持换行分隔
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_polygon_points(p):
    """polygon_points : point_ref
                      | polygon_points sep point_ref"""  # 支持换行分隔
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

# 添加sep规则以支持逗号和空格分隔符
def p_sep(p):
    """sep : ','
           | empty"""
    p[0] = None

# -------------------
# AREA 命令
# -------------------
def p_area_command(p):
    """area_command : C_AREA IDENTITY area_type ';'"""
    p[0] = AreaCommandNode(p[2], p[3], p.lineno(1))

def p_area_type(p):
    """area_type : K_CONFORMAL point_ref sep point_ref
                 | K_RECTANGULAR point_ref sep point_ref
                 | K_POLYGONAL polygon_points
                 | K_FUNCTIONAL IDENTITY
                 | K_FILLET point_ref sep point_ref IDENTITY IDENTITY IDENTITY
                 | K_QUARTERROUND IDENTITY point_ref IDENTITY
                 | K_SINUSOID axis_spec point_ref sep  point_ref sep point_ref"""
    if p[1] == 'CONFORMAL':
        #print("识别到area命令：", p[1], p[2], p[4])
        p[0] = (p[1], {'p1': p[2], 'p2': p[4]})
    elif p[1] == 'RECTANGULAR':
        p[0] = (p[1], {'p1': p[2], 'p2': p[4]})
    elif p[1] == 'POLYGONAL':
        p[0] = (p[1], {'points': p[2]})
    elif p[1] == 'FUNCTIONAL':
        p[0] = (p[1], {'function': p[2]})
    elif p[1] == 'FILLET':
        p[0] = (p[1], {'p1': p[2], 'p2': p[4], 'radius': p[5], 'start_angle': p[6], 'end_angle': p[7]})
    elif p[1] == 'QUARTERROUND':
        p[0] = (p[1], {'iquadrant': p[2], 'point': p[3], 'radius': p[4]})
    else:  # SINUSOID
        p[0] = (p[1], {
            'axis': p[2],
            'p1': p[3],
            'p2': p[5],
            'p3': p[7]
        })

def p_axis_spec(p):
    """axis_spec : '{' IDENTITY ',' IDENTITY '}'"""
    p[0] = (p[2], p[4])

# -------------------
# 材料属性与模型操作
# -------------------


def p_material_application(p):
    """material_application_command : conductance_command
              | dielectric_command
              | conductor_command
              | void_command"""
    p[0] = p[1]

def p_conductance_command(p):
    """conductance_command : K_CONDUCTANCE IDENTITY ';'"""
    p[0] = MaterialApplicationNode('CONDUCTANCE', p[2], None, p.lineno(1))

def p_dielectric_command(p):
    """dielectric_command : K_DIELECTRIC IDENTITY ';'"""
    p[0] = MaterialApplicationNode('DIELECTRIC', p[2], None, p.lineno(1))

def p_conductor_command(p):
    """conductor_command : K_CONDUCTOR IDENTITY ';'
                         | K_CONDUCTOR IDENTITY IDENTITY ';'
                         """                     
    if len(p) == 5:
        p[0] = MaterialApplicationNode('CONDUCTOR', p[2], p[3], p.lineno(1))
    else:
        p[0] = MaterialApplicationNode('CONDUCTOR', p[2], None, p.lineno(1))

def p_void_command(p):
    """void_command : K_VOID IDENTITY ';'"""
    p[0] = MaterialApplicationNode('VOID', p[2], None, p.lineno(1))


# ===================
# 端口命令
# ===================
def p_port_commands(p):
    """ports_command : port_command
                     | outgoing_command

    """
    p[0] = p[1]

# PORT命令
def p_port_command(p):
    """port_command : K_PORT IDENTITY direction port_options ';'"""
    p[0] = PortCommandNode(geom_name=p[2], direction=p[3], options=p[4], lineno=p.lineno(1))

# 方向参数
def p_direction(p):
    '''direction : K_POSITIVE
                 | K_NEGATIVE'''
    p[0] = p[1]

# 可选参数聚合
def p_port_options(p):
    """
    port_options : port_options port_option
                | empty
    """
    if len(p) == 3:
        # 当已有选项列表时直接扩展
        if isinstance(p[1], list):
            p[0] = p[1] + [p[2]]  # 更安全的列表合并方式
        else:
            # 处理意外情况（理论上不会出现）
            p[0] = [p[2]] if p[1] is None else [p[1], p[2]]
    else:
        # 空选项时返回空列表
        p[0] = []

# 各可选参数定义
def p_port_option(p):
    """
    port_option : incoming_portopt
                | normalization_portopt
    """
    p[0] = p[1]

# port_options

def p_incoming_portopt(p):
    """
    incoming_portopt : K_INCOMING IDENTITY incoming_option 
    """
    p[0] = {
        "port_opt_name": 'INCOMING',
        "incoming_func": p[2],
        "incoming_opt": p[3]
    }

def p_incoming_option(p):
    """
    incoming_option : FUNCTION IDENTITY IDENTITY 
                    | FUNCTION IDENTITY IDENTITY IDENTITY IDENTITY
    """
    if len(p) == 4:
        p[0] = [p[2], p[3]]
    elif len(p) == 6:
        p[0] = [p[2], p[3], p[4], p[5]]
    else:
        raise SyntaxError(f"Unexpected incoming option: {p[1]}")

def p_normalization_portopt(p):
    """
    normalization_portopt : K_NORMALIZATION K_PEAK_FIELD IDENTITY IDENTITY
                          | K_NORMALIZATION K_VOLTAGE IDENTITY
    """
    if p[2] == 'PEAK_FIELD':
        p[0] = {
            "port_opt_name": 'NORMALIZATION',
            "norm_type": 'PEAK_FIELD',
            "geom_type": "point",
            "peak_value" : [p[3], p[4]]
        }
    elif p[2] == 'VOLTAGE':
        p[0] = {
            "port_opt_name": 'NORMALIZATION',
            "norm_type": 'VOLTAGE',
            "geom_type": "line",
            "peak_value" : [p[3]]
        }
    else:
        raise SyntaxError(f"Unexpected normalization option: {p[2]}")

#=============
# OUTGOING命令
#=============
def p_outgoing_command(p):
    """outgoing_command : K_OUTGOING IDENTITY direction outgoing_mode ';' """
    p[0] = OutgoingCommandNode(geom_name=p[2], direction=p[3], mode=p[4], lineno=p.lineno(1))

# 模式参数
def p_outgoing_mode(p):
    '''outgoing_mode : K_TE
            | K_TM
            | K_ALL'''
    p[0] = p[1]


# ===================
# 发射命令
# ===================
# EMISSION命令规则
def p_emission_command(p):
    """emission_command : K_EMISSION emission_process_args emission_options ';'"""
    process_args = p[2]
    model_opt = None
    species_opt = None
    number_opt = None
    opts = p[3]
    # print("opts:", opts)
    for opt in opts:
        if opt:
            if opt[0] == 'MODEL':
                model_opt = opt[1]
            elif opt[0] == 'SPECIES':
                species_opt = opt[1]
            elif opt[0] == 'NUMBER':
                number_opt = opt[1]
    p[0] = EmissionCommandNode(process_args, model_opt, species_opt, number_opt, p.lineno(1))

def p_emission_process_args(p):
    """emission_process_args : K_BEAM IDENTITY IDENTITY
                        | K_EXPLOSIVE
                        """
    if p[1] == 'BEAM':
        p[0] = {"process": "BEAM", "current_density": p[2], "beam_voltag": p[3]}
    elif p[1] == 'EXPLOSIVE':
        p[0] = {"process": "EXPLOSIVE"}
    else:
        raise SyntaxError(f"Unexpected emission process: {p[1]}")

def p_emission_options(p):
    """emission_options : emission_option
                        | emission_options emission_option
                        | empty"""
    p[0] = [] if len(p) == 1 else ([p[1]] if len(p) == 2 else p[1] + [p[2]])

def p_emission_option(p):
    """emission_option : K_MODEL IDENTITY
                       | K_SPECIES IDENTITY
                       | K_NUMBER expr
                       | K_NUMBER IDENTITY
                       """
    p[0] = (p[1], p[2])

# EMIT命令规则
def p_emit_command(p):
    """emit_command : K_EMIT emit_process IDENTITY emit_excludes_includes_opt ';'"""
    model = p[2]
    mobject = p[3]
    ex_in = p[4] if p[4] is not None else []
    p[0] = EmitCommandNode(model, mobject, ex_in, p.lineno(1))

def p_emit_process(p):
    """emit_process : K_BEAM
                    | K_EXPLOSIVE"""
    p[0] = p[1]

def p_emit_excludes_includes_opt(p):
    """emit_excludes_includes_opt : emit_excludes_includes
                                  | empty"""
    p[0] = p[1]

def p_emit_excludes_includes(p):
    """emit_excludes_includes : emit_exclude_include emit_excludes_includes
                              | emit_exclude_include"""
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[1] + p[2]


def p_emit_exclude_include(p):
    """emit_exclude_include : K_EXCLUDE IDENTITY
                            | K_INCLUDE IDENTITY
                            """
    p[0] = [p[1], p[2]]


# ===================
# PRESET命令
# ===================
def p_preset_command(p):
    """preset_command : K_PRESET IDENTITY FUNCTION IDENTITY ';' """
    preset_name = p[2]
    func_name = p[4]
    p[0] = PresetCommandNode(preset_name, func_name, p.lineno(1))

# ===================
# TIMER命令
# ===================
def p_timer_command(p):
    """timer_command : K_TIMER IDENTITY timer_mode timer_type timer_options timer_integrate_opt ';' """
    timer_name = p[2]
    mode = p[3]
    timer_type = p[4]
    opts = p[5]
    integrate_opt = p[6]
    p[0] = TimerCommandNode(timer_name, mode, timer_type, opts, integrate_opt, p.lineno(1))

def p_timer_mode(p):
    """timer_mode : K_PERIODIC
                  | K_DISCRETE
                  """
    p[0] = p[1]

def p_timer_type(p):
    """timer_type : K_INTEGER
                  | K_REAL
                  """
    p[0] = p[1]

def p_timer_options(p):
    """timer_options : timer_option timer_options
                     | timer_option
                     """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[2]

def p_timer_option(p):
    """timer_option : expr
                    | IDENTITY
                    """
    if isinstance(p[1], str):  # 标识符
        p[0] = p[1]
    else:  # 表达式
        p[0] = p[1].to_expression()

def p_timer_integrate_opt(p):
    """timer_integrate_opt : K_INTEGRATE IDENTITY ';'
                           | empty
                           """
    if len(p) == 3:
        p[0] = p[2]
    else:
        p[0] = None

# ===================
# OBSERVES命令
# ===================
def p_observe_command(p):
    """observe_command : ObserveEmittedCommand
                        | ObserveFieldCommand
                        | ObserveFieldPowerCommand
                        | ObserveFieldEnergyCommand
                        | ObserveIntegralCommand
    """
    p[0] = p[1]

def p_observe_emitted_command(p):
    """ObserveEmittedCommand : K_OBSERVE K_EMITTED IDENTITY IDENTITY observe_emit_kind observe_opts ';' """
    
    p[0] = ObserveEmittedCommandNode(p[3], p[4], p[5], p[6], p.lineno(1))

def p_observe_emit_kind(p):
    """observe_emit_kind : K_CHARGE
                         | K_CURRENT
                         | K_ENERGY
                         | K_POWER
                         | K_VOLTAGE"""
    p[0] = p[1]

def p_observe_field_command(p):
    """ObserveFieldCommand : K_OBSERVE K_FIELD IDENTITY IDENTITY observe_opts ';' """
    p[0] = ObserveFieldCommandNode(p[3], p[4], p[5], p.lineno(1))

def p_observe_field_power_command(p):
    """ObserveFieldPowerCommand : K_OBSERVE K_FIELD_POWER IDENTITY IDENTITY observe_opts ';' """
    p[0] = ObserveFieldPowerCommandNode(p[3], p[4], p[5], p.lineno(1))

def p_observe_field_energy_command(p):
    """ObserveFieldEnergyCommand : K_OBSERVE K_FIELD_ENERGY IDENTITY IDENTITY observe_opts ';' """
    p[0] = ObserveFieldEnergyCommandNode(p[3], p[4], p[5], p.lineno(1))

def p_observe_Integral_command(p):
    """ObserveIntegralCommand : K_OBSERVE K_FIELD_INTEGRAL IDENTITY IDENTITY observe_opts ';' """
    p[0] = ObserveIntegralCommandNode(p[3], p[4], p[5], p.lineno(1))

def p_observe_opts(p):
    """observe_opts : observe_opt observe_opts
                    | observe_opt"""
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = {**p[1], **p[2]}

def p_observe_opt(p):
    """observe_opt : K_FFT K_MAGNITUDE
                   | K_FFT K_COMPLEX
                   | K_WINDOW K_TIME expr expr
                   | K_WINDOW K_FREQUENCY expr expr
                   | K_TIME_FREQUENCY time_frequency_kind expr expr expr
                   | empty
    """
    if p[1] == "FFT":  # 处理 K_FFT 选项
        p[0] = {p[1]: {"observe_opt_kind": p[1], "fft_kind": p[2]}}
    elif p[1] == "WINDOW":  # 处理 K_WINDOW 选项
        p[0] = {p[1]+'_'+p[2]: {"observe_opt_kind": p[1], "window_kind": p[2], "start": p[3].to_expression(), "end": p[4].to_expression()}}
    elif p[1] == "TIME_FREQUENCY":  # 处理 K_TIME_FREQUENCY 选项
        p[0] = {p[1]: {"observe_opt_kind": p[1], "time_frequency_kind": p[2], "start": p[3].to_expression(), "end": p[4].to_expression(), "step": p[5].to_expression()}}
    else:  # 处理空选项
        p[0] = {}

def p_time_frequency_kind(p):
    """time_frequency_kind : K_SPECTROGRAM
                           | K_WIGNER_VILLE
                           | K_REDUCED_INTERFERENCE"""
    p[0] = p[1]

# ===================
# RANGE诊断命令
# ===================
def p_range_command(p):
    """range_command : range_field_command """
    p[0] = p[1]

def p_range_field_command(p):
    """range_field_command : K_RANGE K_FIELD IDENTITY IDENTITY IDENTITY range_opts ';' """
    p[0] = RangeFieldCommandNode(p[3], p[4], p[5], p[6], p.lineno(1))

def p_range_opts(p):
    """range_opts : range_opt range_opts
                  | range_opt"""
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = {**p[1], **p[2]}

def p_range_opt(p):
    """range_opt : K_FFT K_MAGNITUDE
                 | empty"""
    if len(p) == 3:  # 处理 K_FFT 选项
        p[0] = {p[1]: {"range_opt_kind": p[1], "fft_kind": p[2]}}  
    else:  # 处理空选项
        p[0] = {}

# ===================
# MARK命令
# ===================
def p_mark_command(p):
    """mark_command : C_MARK mark_target mark_tail_opt ';'"""
    # mark_tail_opt -> 可能为空；若不为空包含 axis/position/size
    target = p[2]
    tail = p[3] or {}
    p[0] = MarkCommandNode(
        target=target,
        axis=tail.get("axis"),
        position=tail.get("position"),
        size=tail.get("size"),
        lineno=p.lineno(1)
    )

def p_mark_target(p):
    """mark_target : IDENTITY"""
    p[0] = p[1]

def p_mark_tail_opt(p):
    """mark_tail_opt : mark_axis mark_options_opt
                     | empty"""
    if len(p) == 2:
        p[0] = {}
    else:
        axis = p[1]
        opts = p[2] or {}
        p[0] = {"axis": axis, **opts}

def p_mark_axis(p):
    """mark_axis : IDENTITY"""
    # 允许 x1/x2/x3 或 X1/X2/X3，其他一律报错
    axis = p[1].upper() if isinstance(p[1], str) else str(p[1]).upper()
    if axis not in ('X1', 'X2', 'X3'):
        # 用 SyntaxError 抛出清晰报错
        # 小贴士：若你希望带行号，可用 p.lineno(1)；但这里 axis 只是个子片段，
        # 行号一般在上层 rule（mark_command）里统一处理
        raise SyntaxError(f"MARK axis must be X1/X2/X3, got '{p[1]}'")
    p[0] = axis

# 选项聚合：可能出现 [MINIMUM] [MIDPOINT] [MAXIMUM] [SIZE cell_size]
def p_mark_options_opt(p):
    """mark_options_opt : mark_options
                        | empty"""
    p[0] = p[1] if len(p) == 2 else {}

def p_mark_options(p):
    """mark_options : mark_options mark_option
                    | mark_option"""
    if len(p) == 2:
        p[0] = p[1]
    else:
        # 合并字典；position 如果重复，后者覆盖前者
        p[0] = {**p[1], **p[2]}

def p_mark_option(p):
    """mark_option : K_MINIMUM
                   | K_MIDPOINT
                   | K_MAXIMUM
                   | K_SIZE mark_size_value"""
    if p.slice[1].type == 'K_SIZE':
        p[0] = {"size": p[2]}
    else:
        # 三选一的定位关键字
        p[0] = {"position": p[1]}

# SIZE 后的值既可能是表达式，也可能是一个标识符（如 DZ / DR / DRC）
def p_mark_size_value(p):
    """mark_size_value : expr
                       | IDENTITY"""
    if isinstance(p[1], str):
        p[0] = p[1]
    else:
        p[0] = p[1].to_expression()


# ===================
# 其他命令类型
# ===================
def p_header_command(p):
    """header_command : C_HEADER IDENTITY STRING_LITERAL ';' """
    p[0] = HeaderCommandNode(p[2], p[3])

"""
def p_graphics_command(p):
    graphics_command : C_GRAPHICS IDENTITY ';' 
    p[0] = GraphicsCommandNode(p[2])
"""

# ===================
# 变量、表达式体系
# ===================

# -------------------
# 函数定义
# -------------------
# 有参数函数
def p_function_with_params(p):
    """function : FUNCTION IDENTITY '(' param_list ')' '=' FUNCTION_BODY ';'"""
    p[0] = FunctionNode(p[2], p[4], p[7], p.lineno(1))

# 无参数函数（常量函数）
def p_function_no_params(p):
    """function : FUNCTION IDENTITY '=' FUNCTION_BODY ';'"""
    p[0] = FunctionNode(p[2], [], p[4], p.lineno(1))

def p_param_list(p):
    """
    param_list : IDENTITY
                  | param_list ',' IDENTITY
    """
    if len(p) == 2:
        p[0] = [VariableNode(p[1])]
    else:
        p[0] = p[1] + [VariableNode(p[3])]


#暂时弃用
def p_function_call(p):
    """function_call : IDENTITY '(' argument_list ')'"""
    p[0] = FunctionCallNode(p[1], p[3])  # 例如：func(1, 2+3)

def p_argument_list(p):
    """argument_list : expr
                     | argument_list ',' expr"""
    if len(p) == 2:
        p[0] = [p[1]]  # 单个参数
    else:
        p[0] = p[1] + [p[3]]  # 多个参数


# -------------------
# 赋值、变量定义
# -------------------

# assignment
def p_assignment(p):
    """assignment : IDENTITY '=' expr ';'
                  | K_ASSIGN IDENTITY '=' expr ';'
                  | K_REAL IDENTITY '=' expr ';'
                  | K_INTEGER IDENTITY '=' expr ';'
                  | K_CHARACTER IDENTITY '=' STRING_LITERAL ';'"""
    if len(p) == 5:  # 处理 IDENTITY = expr;
        var_name = p[1]
        value = p[3]
        decl_type = None
        p[0] = AssignmentNode(VariableNode(var_name), value, decl_type , p.lineno(1))
    else:  # 处理其他情况（长度6）
        keyword = p[1]
        if keyword == 'ASSIGN':  # K_ASSIGN的情况
            var_name = p[2]
            value = p[4]
            decl_type = None
        elif keyword in ('REAL', 'INTEGER'):
            var_name = p[2]
            value = p[4]
            decl_type = keyword
        elif keyword == 'CHARACTER':
            var_name = p[2]
            value = StringNode(p[4])  # 假设STRING_LITERAL已被正确处理
            decl_type = 'CHARACTER'
        else:
            raise SyntaxError(f"Unexpected keyword: {keyword}")
        p[0] = AssignmentNode(VariableNode(var_name), value, decl_type , p.lineno(1))

# -------------------
# 表达式
# -------------------


def p_expr(p):
    """expr : comparison"""
    p[0] = p[1]

def p_comparison(p):
    """comparison : arith_expr COMPARE_OP arith_expr
                  | arith_expr"""
    if len(p) == 4:
        p[0] = CompareOpNode(p[2], p[1], p[3])  # 例如：a + b > c * d
    else:
        p[0] = p[1]
def p_COMPARE_OP(p):
    """COMPARE_OP : O_GT
                  | O_LT
                  | O_LE
                  | O_GE
                  | O_EQ
                  | O_NE"""
    p[0] = p[1]


def p_arith_expr(p):
    """arith_expr : arith_expr '+' term
                  | arith_expr '-' term
                  | term"""
    if len(p) == 4:
        p[0] = BinaryOpNode(p[2], p[1], p[3])  # 例如：a + b - c
    else:
        p[0] = p[1]
def p_term(p):
    """term : term '*' factor
            | term '/' factor
            | factor"""
    if len(p) == 4:
        p[0] = BinaryOpNode(p[2], p[1], p[3])  # 例如：a * b / c
    else:
        p[0] = p[1]


def p_factor(p):
    """factor : power
              | '-' factor %prec UMINUS"""  # 单目负号，优先级高于乘除
    if len(p) == 3:
        p[0] = UnaryOpNode('-', p[2])      # 例如：-3, -(a + b)
    else:
        p[0] = p[1]

def p_power(p):
    """power : primary EXPONENT factor
             | primary"""  # 指数右结合：a**b**c = a**(b**c)
    if len(p) == 4:
        p[0] = BinaryOpNode('**', p[1], p[3])
    else:
        p[0] = p[1]

def p_primary(p):
    """primary : '(' expr ')'
               | function_call
               | IDENTITY
               | FLOAT_LITERAL
               | INTEGER_LITERAL"""
    if len(p) == 4:
        p[0] = p[2]  # 括号表达式，直接返回内部表达式
    elif isinstance(p[1], str) and re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', p[1]):
        p[0] = VariableNode(p[1])       # 变量名
    elif isinstance(p[1], (int, float)):
        p[0] = LiteralNode(p[1])          # 数字字面量
    else:
        p[0] = p[1]                       # 函数调用

# 显式定义 empty 规则
def p_empty(p):
    """empty :"""
    p[0] = []  # 可选：传递空值

# ===================
# 错误处理
# ===================
def p_error(p):
    if p:
        print(f"Syntax error at line {p.lineno}: Unexpected token '{p.value}'")
    else:
        print("Syntax error: Unexpected end of input")

# 构建语法分析器
ply_parser = yacc.yacc()
#######################
# core\single_flows\mcl_ast.py
#######################

class ASTNode:
    """抽象语法树节点基类"""
    def __repr__(self):
        kv = ", ".join(f"{k}={v!r}" for k, v in vars(self).items())
        return f"{self.__class__.__name__}({kv})"


class ProgramNode(ASTNode):
    def __init__(self, statements, lineno=0):
        self.statements = statements
        self.lineno = lineno

# 语句节点基类
class StatementNode(ASTNode):
    pass

class IfStatementNode(ASTNode):
    def __init__(self, clauses, else_body=None, lineno=0):
        self.clauses = clauses
        self.else_body = else_body or []
        self.lineno = lineno

class DoLoopNode(ASTNode):
    def __init__(self, var, start, end, step, body, lineno=0):
        self.var = var
        self.start = start
        self.end = end
        self.step = step
        self.body = body
        self.lineno = lineno

# ===================
# 命令体系结构
# ===================

# 系统命令节点
class SystemCommandNode(ASTNode):
    def __init__(self, name):
        self.name = name

# 头信息命令节点
class HeaderCommandNode(ASTNode):
    def __init__(self, name, value):
        self.name = name
        self.value = value

# 图形命令节点
class GraphicsCommandNode(ASTNode):
    def __init__(self, name):
        self.name = name

# 终止命令节点
class TerminateCommandNode(ASTNode):
    def __init__(self, name):
        self.name = name

# =====================
# 几何命令
# =====================

class GeometryNode(ASTNode):
    pass

class NamedPointNode(ASTNode):
    def __init__(self, name, lineno=0):
        self.name = name
        self.lineno = lineno

class CoordPointNode(ASTNode):
    def __init__(self, coords, lineno=0):
        self.coords = coords
        self.lineno = lineno

class PointCommandNode(GeometryNode):
    def __init__(self, name, coords, lineno=0):
        self.name = name
        self.coords = coords
        self.lineno = lineno

    def to_expression(self):
        parts = []
        for c in self.coords:
            if hasattr(c, "to_expression"):
                parts.append(str(c.to_expression()))
            else:
                parts.append(str(c))
        return f"({', '.join(parts)})"

class LineCommandNode(GeometryNode):
    def __init__(self, name, line_type, lineno=0):
        self.name = name
        self.line_type, self.params = line_type
        self.lineno = lineno

class AreaCommandNode(GeometryNode):
    def __init__(self, name, area_type, lineno=0):
        self.name = name
        self.area_type, self.params = area_type
        self.lineno = lineno

    def to_expression(self):
        return self.params

# =====================
# 材料命令
# =====================

class MaterialDefinitionNode(ASTNode):
    def __init__(self, name, properties, lineno=0):
        self.name = name
        self.properties = properties
        self.lineno = lineno

class MaterialApplicationNode(ASTNode):
    def __init__(self, mtype, geom_name, spec, lineno=0):
        self.mtype = mtype
        self.geom_name = geom_name
        self.spec = spec
        self.lineno = lineno
        print(f"[info] MaterialApplicationNode...{self.mtype}:{self.geom_name}")
    
    def __repr__(self):
        #print("MaterialApplicationNode......\n")
        return f"[info] MaterialApplicationNode({self.mtype}:{self.geom_name})"

    def to_expression(self):
        #print("MaterialApplicationNode......\n")
        if hasattr(self, 'spec') and self.spec:
            return f"'mtype': '{self.mtype}', 'geom_name': '{self.geom_name}', 'spec': '{self.spec[0]}', 'name': '{self.name}'"
        return f"'mtype': '{self.mtype}', 'geom_name': '{self.geom_name}', 'name': '{self.name}'"

    
# 端口
class PortCommandNode(ASTNode):
    def __init__(self, geom_name, direction, options, lineno):
        self.geom_name = geom_name
        self.direction = direction
        self.options = options
        self.lineno = lineno

class OutgoingCommandNode(ASTNode):
    def __init__(self, geom_name, direction, mode, lineno):
        self.geom_name = geom_name
        self.direction = direction
        self.mode = mode
        self.lineno = lineno

class FreespaceCommandNode(ASTNode):
    def __init__(self, geom_type, geom_name, direction, axes, fields, lineno):
        self.geom_type = geom_type
        self.geom_name = geom_name
        self.direction = direction
        self.axes = axes
        self.fields = fields
        self.lineno = lineno

# 发射命令
# 添加发射相关节点
class EmissionCommandNode(ASTNode):
    def __init__(self, process_args, model_opt=None, species_opt=None, number_opt=None, lineno=0):
        self.process_args = process_args
        self.model_opt = model_opt
        self.species_opt = species_opt
        self.number_opt = number_opt
        self.lineno = lineno

class EmitCommandNode(ASTNode):
    def __init__(self, model, mobject, ex_in, lineno=0):
        self.model = model
        self.mobject = mobject
        self.ex_in = ex_in
        self.lineno = lineno


class PresetCommandNode(ASTNode):
    def __init__(self, preset_name, func_name, lineno=0):
        self.preset_name = preset_name
        self.func_name = func_name
        self.lineno = lineno


class TimerCommandNode(ASTNode):
    def __init__(self, name, mode, time_type, timer_opt, integrate_opt, lineno=0):
        self.name = name
        self.mode = mode
        self.time_type = time_type
        self.timer_opt = timer_opt
        self.integrate_opt = integrate_opt
        self.lineno = lineno

# 诊断命令
class ObserveEmittedCommandNode(ASTNode):
    def __init__(self, object_kind, species_kind, observe_emit_kind, observe_opt, lineno=0):
        self.object_kind = object_kind
        self.species_kind = species_kind
        self.observe_emit_kind = observe_emit_kind
        self.observe_opt = observe_opt
        self.lineno = lineno

class ObserveFieldCommandNode(ASTNode):
    def __init__(self, field_kind, object_kind, observe_opt, lineno=0):
        self.field_kind = field_kind
        self.object_kind = object_kind
        self.observe_opt = observe_opt
        self.lineno = lineno

class ObserveFieldPowerCommandNode(ASTNode):
    def __init__(self, power_variable, object_kind, observe_opt, lineno=0):
        self.power_variable = power_variable
        self.object_kind = object_kind
        self.observe_opt = observe_opt
        self.lineno = lineno

class ObserveFieldEnergyCommandNode(ASTNode):
    def __init__(self, energy_variable, object_kind, observe_opt, lineno=0):
        self.energy_variable = energy_variable
        self.object_kind = object_kind
        self.observe_opt = observe_opt
        self.lineno = lineno

class ObserveIntegralCommandNode(ASTNode):
    def __init__(self, Integral_kind, geom_name, observe_opt = None, lineno=0):
        self.Integral_kind = Integral_kind
        self.geom_name = geom_name
        self.observe_opt = observe_opt
        self.lineno = lineno


class RangeFieldCommandNode(ASTNode):
    def __init__(self, field_name, line_name, timer_name, range_opt, lineno = 0):
        self.field_name = field_name
        self.line_name = line_name
        self.timer_name = timer_name
        self.range_opt = range_opt
        self.lineno = lineno

# 标记命令节点
class MarkCommandNode(ASTNode):
    def __init__(self, target, axis=None, position=None, size=None, lineno=0):
        self.target = target        # 变量名或对象名（POINT/LINE/AREA/VOLUME 名 或 ASSIGN 定义变量）
        self.axis = axis            # 'X1' | 'X2' | 'X3' | None
        self.position = position    # 'MINIMUM' | 'MIDPOINT' | 'MAXIMUM' | None
        self.size = size            # 表达式字符串 或 标识符（如 DZ/DR） 或 None
        self.lineno = lineno

    def __repr__(self):
        return f"MarkCommandNode(target={self.target}, axis={self.axis}, position={self.position}, size={self.size}, lineno={self.lineno})"


# 函数定义节点
class FunctionNode(ASTNode):
    def __init__(self, name, params, body, lineno):
        """
        :param name: 函数名 (str)
        :param params: 参数节点列表 (List[VariableNode])
        :param body: 函数体原始字符串 (str) 或表达式节点
        """
        self.name = name
        self.params = params or []
        self.body = body
        self.lineno = lineno

    def __repr__(self):
        return f"FunctionNode(name={self.name}, params={self.params}, body={self.body})"

    def to_expression(self):
        if self.params:
            return f"{self.name}({', '.join(p.name for p in self.params)})"
        else:
            if hasattr(self.body, "to_expression"):
                return self.body.to_expression()
            return str(self.body)

class FunctionCallNode(ASTNode):
    def __init__(self, func_name, args):
        self.func_name = func_name  # 函数名
        self.args = args            # 参数列表 (列表)

    def __repr__(self):
        return f"FunctionCall({self.func_name}, {self.args})"
    
    def to_expression(self):
        args_str = ", "
        for arg in self.args:
            if isinstance(arg, str):
                args_str += f'"{arg}", '
            else:
                args_str += arg.to_expression() + ", "

        return f"{self.func_name}({args_str[:-2]})"

        #return f"{self.func_name}({args_str})"

class AssignmentNode(StatementNode):
    def __init__(self, target, value, decl_type=None ,lineno = 0):
        self.target = target
        self.value = value
        self.decl_type = decl_type  # 新增类型字段
        self.lineno = lineno

class VariableNode(ASTNode):
    # 变量(标识符)节点
    def __init__(self, name):
        self.name = name  # 变量名

    def __repr__(self):
        return f"Identifier({self.name})"

    def to_expression(self):
        return self.name

class LiteralNode(ASTNode):
    # 数字或字符串字面值节点
    def __init__(self, value):
        self.value = value  # 值: int, float

    def __repr__(self):
        return f"Literal({self.value})"
    
    def to_expression(self):
        return str(self.value)

class StringNode(ASTNode):
    # 字符串字面量节点
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"StringNode({self.value})"



class CompareOpNode(ASTNode):
    # 比较符：'==', '!=', '>', '<', '>=', '<='
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        return f"CompareOp({self.left}, {self.op}, {self.right})"

    def to_expression(self):
        if isinstance(self.left, str):
            left_str = f'"{self.left}"'
        else:
            left_str = self.left.to_expression()
        if isinstance(self.right, str):
            right_str = f'"{self.right}"'
        else:
            right_str = self.right.to_expression()
        return f"({left_str} {self.op} {right_str})"


class BinaryOpNode(ASTNode):
    # 二元运算符：'+', '-', '*', '/', '**'
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        return f"BinaryOp({self.left}, {self.op}, {self.right})"

    def to_expression(self):
        if isinstance(self.left, str):
            left_str = f'"{self.left}"'
        else:
            left_str = self.left.to_expression()
        if isinstance(self.right, str):
            right_str = f'"{self.right}"'
        else:
            right_str = self.right.to_expression()
        return f"({left_str} {self.op} {right_str})"

class UnaryOpNode(ASTNode):
    # 一元运算符节点（负号）
    def __init__(self, op, operand):
        self.op = op     # 运算符：'-' (负号)
        self.operand = operand

    def __repr__(self):
        return f"UnaryOp({self.op}, {self.operand})"

    def to_expression(self):
        if isinstance(self.operand, str):
            operand_str = self.operand
        else:
            operand_str = self.operand.to_expression()
        return f"{self.op}{operand_str}"

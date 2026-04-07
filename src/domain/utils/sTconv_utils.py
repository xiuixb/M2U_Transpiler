import re
from math import log, sin, cos, tan, exp

from sympy import field
from typing import Dict, List, Any, Tuple, Iterable
from pint import UnitRegistry, Quantity
ureg = UnitRegistry()

for alias, canonical in {
    "hz": "hertz",
    "khz": "kilohertz",
    "mhz": "megahertz",
    "ghz": "gigahertz",
    "thz": "terahertz",
    "kv": "kilovolt",
}.items():
    try:
        ureg.define(f"{alias} = {canonical}")
    except Exception:
        pass

VAR_RE = re.compile(r'(?<![A-Za-z0-9_])([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)*)(?![A-Za-z0-9_])')
POINT_TOKEN_RE = re.compile(
    r'^\s*<\s*([^>|]+)\s*(?:\|\s*([^>|]+)\s*(?:\|\s*([^>]+)\s*)?)?>\s*$'
)
FUNCTION_NAME_RE = re.compile(r'\b(LOG|SQRT|SIN|COS|TAN|EXP|ABS)\b', re.IGNORECASE)
BROKEN_FUNC_CALL_RE = re.compile(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*,')

def convert_to_xy_pairs(points: Iterable[Tuple], nd: int = 10) -> List[Tuple[float, float]]:
    """
    将 [(qx, qy), ...] 转为以毫米为单位的数值点列 [(x_mm, y_mm), ...]。
    - qx, qy 推荐为 pint.Quantity；如是纯数则按 mm 解释。
    - nd: 保留小数位，默认 10。
    """
    def to_qty(v) -> Quantity:
        # 已是 Quantity
        if hasattr(v, "to"):
            return v
        # 纯数，按 mm 解释
        if isinstance(v, (int, float)):
            return v * ureg.mm
        # 其它（字符串/表达式），尝试 pint 解析
        return ureg.parse_expression(str(v))

    out: List[Tuple[float, float]] = []
    for i, pt in enumerate(points):
        if not (isinstance(pt, (list, tuple)) and len(pt) == 2):
            raise TypeError(f"第 {i} 个点不是二元组：{pt!r}")
        qx = to_qty(pt[0])
        qy = to_qty(pt[1])
        x_mm = round(qx.to(ureg.mm).magnitude, nd)
        y_mm = round(qy.to(ureg.mm).magnitude, nd)
        out.append((x_mm, y_mm))
    return out

def substitute_variables(expr_str: str, symbol_table: Dict[str, Dict[str, Any]]) -> str:
    def repl(m):
        v = m.group(1)
        if v in symbol_table:
            info = symbol_table[v].get("cac_result", {})
            var_num = info.get("var_num")
            var_unit = info.get("var_unit")
            if var_num is not None and var_unit:
                return f"({var_num} * {var_unit})"
        return v
    return VAR_RE.sub(repl, expr_str)

def normalize_expression(expr_str: str) -> str:
    expr = str(expr_str).strip()
    expr = BROKEN_FUNC_CALL_RE.sub(r"\1(", expr)

    def normalize_func(m):
        name = m.group(1).upper()
        mapping = {
            "LOG": "log",
            "SQRT": "sqrt",
            "SIN": "sin",
            "COS": "cos",
            "TAN": "tan",
            "EXP": "exp",
            "ABS": "Abs",
        }
        return mapping.get(name, name.lower())

    return FUNCTION_NAME_RE.sub(normalize_func, expr)

def _to_dimensionless_number(value):
    if hasattr(value, "to_base_units") and hasattr(value, "magnitude"):
        base = value.to_base_units()
        if str(base.units) != "dimensionless":
            raise ValueError(f"函数要求无量纲输入: {value}")
        return float(base.magnitude)
    return float(value)

def _safe_log(value):
    return log(_to_dimensionless_number(value)) * ureg.dimensionless

def _safe_sqrt(value):
    return value ** 0.5

def _safe_sin(value):
    return sin(_to_dimensionless_number(value)) * ureg.dimensionless

def _safe_cos(value):
    return cos(_to_dimensionless_number(value)) * ureg.dimensionless

def _safe_tan(value):
    return tan(_to_dimensionless_number(value)) * ureg.dimensionless

def _safe_exp(value):
    return exp(_to_dimensionless_number(value)) * ureg.dimensionless

def _safe_abs(value):
    return abs(value)

class _EvalNamespace(dict):
    def __missing__(self, key):
        try:
            return getattr(ureg, key)
        except Exception as exc:
            raise NameError(key) from exc

def eval_quantity_expression(expr_str: str):
    namespace = _EvalNamespace({
        "log": _safe_log,
        "sqrt": _safe_sqrt,
        "sin": _safe_sin,
        "cos": _safe_cos,
        "tan": _safe_tan,
        "exp": _safe_exp,
        "Abs": _safe_abs,
        "abs": _safe_abs,
        "__builtins__": {},
    })
    return eval(expr_str, {"__builtins__": {}}, namespace)

def eval_qty(
    expr_str: str,
    symbol_table: Dict[str, Dict[str, Any]],
    unit_lr,
    str2qty_debug: bool = False,
    allow_dimensionless: bool = False,
):
    """
    将字符串表达式 -> pint.Quantity（带单位）
    允许 expr_str 中出现已声明变量。
    """
    normalized = normalize_expression(expr_str)
    s = substitute_variables(normalized, symbol_table)
    q = eval_quantity_expression(s)
    
    if str2qty_debug:
        #print(f"[info] 原始表达式: {expr_str}  规范化-> {normalized}  替换变量-> {s} \n       解析结果: {q}")
        pass

    # 若无单位，强制抛错（几何坐标必须有单位，除非是 0）
    if isinstance(q, (int, float)) or (hasattr(q, "units") and str(q.units) == "dimensionless"):
        if allow_dimensionless:
            return q
        # 允许 0 作为“0 * target_unit”
        if float(q) == 0.0:
            return 0.0 * unit_lr
        raise ValueError(f"几何表达式缺少单位: {expr_str}")
    return q

def parse_point_token(
    token: str,
    symbol_table: Dict[str, Dict[str, Any]],
    points_store: Dict[str, Tuple[Any, Any]],
    unit_lr
) -> Tuple[Any, Any]:
    """
    token: "<x|y>" 或 "<Name>" 或 "<x|y|z>"（第三分量忽略）。
    返回 (qx, qy) 两个 pint.Quantity。
    """
    m = POINT_TOKEN_RE.match(token)
    if not m:
        raise ValueError(f"非法点记号: {token}")

    a, b, c = m.groups()
    # 引用形式：<Name>
    if b is None:
        name = a.strip()
        if name not in points_store:
            raise KeyError(f"点引用未定义: {name}")
        return points_store[name]

    x_str, y_str = a.strip(), b.strip()
    qx = eval_qty(x_str, symbol_table, unit_lr)
    qy = eval_qty(y_str, symbol_table, unit_lr)
    #print(f"qx: {qx}, qy: {qy}")
    return qx, qy

def qty_to_unit_str(q, unit=None, unit_lr=None, digits=10) -> str:
    """
    将 pint.Quantity 格式化为 'value unit' 字符串。
    默认使用 constants.unit_lr（例如 mm）。
    """
    unit = unit or unit_lr
    qn = q.to(unit)
    return f"{round(float(qn.magnitude), digits)} {str(unit)}"

def q_to_mag(q, unit=None, unit_lr=None, nd=10):
    """Quantity -> 指定单位下的 magnitude（四舍五入，不转 float）"""
    unit = unit or unit_lr
    return round(q.to(unit).magnitude, nd)

def format_point(qx, qy, unit=None) -> str:
    return f"({qty_to_unit_str(qx, unit)}, {qty_to_unit_str(qy, unit)})"

def format_line(points: List[Tuple[Any, Any]], unit=None) -> str:
    return "[" + ", ".join(format_point(x, y, unit) for x, y in points) + "]"

# ====== 基础映射 ======
dir_dic  = {"E1":"z","E2":"r","E3":"phi","B1":"z","B2":"r","B3":"phi"}
name_dic = {"E1":"Ez","E2":"Er","E3":"Ephi","B1":"Bz","B2":"Br","B3":"Bphi"}

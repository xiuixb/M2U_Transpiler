import os
import sys
import re
import traceback

from sympy import field, parse_expr
from typing import Dict, List, Any, Tuple, Iterable
from pint import UnitRegistry, Quantity
ureg = UnitRegistry()


VAR_RE = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b')
POINT_TOKEN_RE = re.compile(
    r'^\s*<\s*([^>|]+)\s*(?:\|\s*([^>|]+)\s*(?:\|\s*([^>]+)\s*)?)?>\s*$'
)

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
            info = symbol_table[v]["cac_result"]
            return f"({info['var_num']} * {info['var_unit']})"
        return v
    return VAR_RE.sub(repl, expr_str)

def eval_qty(expr_str: str, symbol_table: Dict[str, Dict[str, Any]], unit_lr, str2qty_debug: bool = False):
    """
    将字符串表达式 -> pint.Quantity（带单位）
    允许 expr_str 中出现已声明变量。
    """
    s = substitute_variables(str(expr_str), symbol_table)
    # Sympy 先做代数规范化，再交给 pint
    sym = parse_expr(s, evaluate=False)
    q = ureg.parse_expression(str(sym))
    
    if str2qty_debug:
        print(f"[info] 原始表达式: {expr_str}  替换变量-> {s} \n       解析结果: {q}")

    # 若无单位，强制抛错（几何坐标必须有单位，除非是 0）
    if isinstance(q, (int, float)) or (hasattr(q, "units") and str(q.units) == "dimensionless"):
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
#########################
# core\muti_flows\mclparser\mcl_ast_visit.py
#########################
"""
AST Visitor -> 顺序列表导出
--------------------------
用途：
  - 替代旧的 SymbolTableBuilder
  - 对每条语句节点生成一条“转换器可用”的结果记录（按行号升序）
"""

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


from typing import Any, Dict, List, Optional

from src.core_symbol.single_flows.mcl_ast import *
from src.core_symbol.symbolBase import ParseResult


class ASTVisitor:
    """访问 AST，将每条命令节点转为统一结构"""
    def build_sequence(
        self,
        program: ProgramNode,
        *,
        parser_name: str,
        line_index: Optional[Dict[int, Dict[str, str]]] = None,
    ) -> List[ParseResult]:
        """
        class ParseResult:
        属性字段：
        lineno     : 过滤后行号（预处理/路由决定）
        command     : 命令关键字（如 "LINE"/"AREA"/"EMISSION"...）
        payload     : 语义结果（供转换器使用），建议沿用 SymbolTable 的字段组织
        parser_kind : 解析器名（"PLY"|"REGEX"|"LLM" 或自定义）
        ok          : 是否成功解析出语义结果
        errors      : 错误/告警信息列表
        text        : 原始单行命令文本（规范化后的）
        将 ProgramNode 转为结果列表：
          - 每条语句转化为 {"lineno","command","payload","parser_kind","ok","errors","text"}
        """
        results: List[ParseResult] = []

        if not isinstance(program, ProgramNode) or not getattr(program, "statements", None):
            return results

        for stmt in program.statements:
            lineno = getattr(stmt, "lineno", 0)
            meta = line_index.get(lineno, {}) if line_index else {}
            command = meta.get("command", "")
            text = meta.get("text", "")

            try:
                payload = self._visit_payload_for(stmt)
                results.append(
                    ParseResult(
                        lineno=lineno,
                        command=command,
                        payload=payload,
                        parser_kind=parser_name,
                        ok=True,
                        errors="no",
                        text=text,
                    )
                )
            except Exception as e:
                results.append(
                    ParseResult(
                        lineno=lineno,
                        command=command,
                        payload={},
                        parser_kind=parser_name,
                        ok=False,
                        errors=str(e),
                        text=text,
                    )
                )

        results.sort(key=lambda r: r.lineno)
        return results

    # ============================ 分派 ============================

    def _visit_payload_for(self, node: ASTNode) -> Dict[str, Any]:
        """根据节点类型调用对应 _visit_* 方法"""
        method = getattr(self, f"_visit_{node.__class__.__name__}", None)
        if method:
            return method(node)

        # fallback：递归找子节点
        for _, value in vars(node).items():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ASTNode):
                        p = self._visit_payload_for(item)
                        if p: return p
            elif isinstance(value, ASTNode):
                p = self._visit_payload_for(value)
                if p: return p
        
        return {
            "kind": "UNKNOWN",
            "raw": self._safe_repr(node)
            #"location": getattr(node, "lineno", 0),
        }

    # ============================ visit_* 系列 ============================
    # ---- 基础语句 ----
    def _visit_AssignmentNode(self, node: AssignmentNode):
        return {
            "kind": node.decl_type or "variable",
            "sys_name": getattr(getattr(node, "target", None), "name", ""),
            "value": self._expr(node.value)
            #"location": node.lineno,
        }

    def _visit_FunctionNode(self, node: FunctionNode):
        params = [p.name for p in getattr(node, "params", [])]
        return {
            "kind": "function",
            "sys_name": node.name,
            "params": params,
            "body": self._expr(node.body)
            #"location": node.lineno,
        }

    def _visit_FunctionCallNode(self, node: FunctionCallNode):
        args = [self._expr(a) for a in getattr(node, "args", [])]
        return {
            "kind": "function_call",
            "sys_name": node.func_name,
            "args": args
            #"location": node.lineno,
        }

    # ---- 几何命令 ----
    def _visit_PointCommandNode(self, node: PointCommandNode):
        x = str(self._expr(node.coords[0]))
        y = str(self._expr(node.coords[1]))
        return {
            "kind": "POINT",
            "sys_name": node.name,
            "point": f"<{x}|{y}>",
        }

    def _visit_LineCommandNode(self, node: LineCommandNode):
        params = node.params or {}
        points: List[str] = []
        for _, v in params.items():
            if isinstance(v, list):
                points.extend([self._point_token(p) for p in v])
            else:
                points.append(self._point_token(v))
        return {
            "kind": "LINE",
            "sys_name": node.name,
            "line_type": node.line_type,
            "points": points,  # 统一为 ["<...>", "<...>", ...]
            # "location": node.lineno,
        }

    def _visit_AreaCommandNode(self, node: AreaCommandNode):
        a_type = node.area_type
        params = node.params or {}
        res: Dict[str, Any] = {}

        if a_type in ("CONFORMAL", "RECTANGULAR"):
            # 统一为 points: [对角点1, 对角点2]
            res["points"] = [
                self._point_token(params.get("p1")),
                self._point_token(params.get("p2")),
            ]
        elif a_type == "POLYGONAL":
            res["points"] = [ self._point_token(p) for p in params.get("points", []) ]
        elif a_type == "FUNCTIONAL":
            res["function"] = self._expr(params.get("function"))
        elif a_type == "FILLET":
            # 仍需保留几何专有参数，但点也统一为 <...>
            res.update({
                "points": [
                    self._point_token(params.get("p1")),
                    self._point_token(params.get("p2")),
                ],
                "radius": self._expr(params.get("radius")),
                "start_angle": self._expr(params.get("start_angle")),
                "end_angle": self._expr(params.get("end_angle")),
            })
        elif a_type == "QUARTERROUND":
            res.update({
                "center": self._point_token(params.get("center")),
                "radius": self._expr(params.get("radius")),
                "quadrant": self._expr(params.get("quadrant")),
            })
        elif a_type == "SINUSOID":
            res.update({
                "axis": self._expr(params.get("axis")),
                "points": [
                    self._point_token(params.get("p1")),
                    self._point_token(params.get("p2")),
                    self._point_token(params.get("p3")),
                ],
            })

        return {
            "kind": "AREA",
            "sys_name": node.name,
            "area_type": a_type,  # 最少结构信号：转换器据此决定解释方式
            "params": res,
            # "location": node.lineno,
        }

    # ---- 材料 ----
    def _visit_MaterialDefinitionNode(self, node: MaterialDefinitionNode):
        props = {prop: self._expr(expr) for prop, expr in node.properties}
        return {
            "kind": "material_def",
            "sys_name": node.name,
            "properties": props
            #"location": node.lineno,
        }

    def _visit_MaterialApplicationNode(self, node: MaterialApplicationNode):
        return {
            "kind": "material_assign",
            "mtype": node.mtype,
            "geom_name": node.geom_name,
            "spec": node.spec
            #"location": node.lineno,
        }

    # ---- 边界/端口 ----
    def _visit_PortCommandNode(self, node: PortCommandNode):
        return {
            "kind": "PORT",
            "geom_name": node.geom_name,
            "direction": node.direction,
            "options": node.options
            #"location": node.lineno,
        }

    def _visit_OutgoingCommandNode(self, node: OutgoingCommandNode):
        return {
            "kind": "OUTGOING",
            "geom_name": node.geom_name,
            "direction": node.direction,
            "mode": node.mode
            #"location": node.lineno,
        }

    def _visit_FreespaceCommandNode(self, node: FreespaceCommandNode):
        return {
            "kind": "FREESPACE",
            "geom_type": node.geom_type,
            "geom_name": node.geom_name,
            "direction": node.direction,
            "axes": node.axes,
            "fields": node.fields
            #"location": node.lineno,
        }

    # ---- 发射命令 ----
    def _visit_EmissionCommandNode(self, node: EmissionCommandNode):
        number_opt = getattr(node, "number_opt", None)
        if number_opt is not None:
            if hasattr(number_opt, "value"):
                number_opt = str(number_opt.value)
            else:
                number_opt = str(number_opt)
        return {
            "kind": "emission",
            "process_args": node.process_args,
            "model_opt": node.model_opt,
            "species_opt": node.species_opt,
            "number_opt": number_opt
            #"location": node.lineno,
        }

    def _visit_EmitCommandNode(self, node: EmitCommandNode):
        return {
            "kind": "emit",
            "model": node.model,
            "mobject": node.mobject,
            "ex_in": node.ex_in
            #"location": node.lineno,
        }

    # ---- 预设与计时 ----
    def _visit_PresetCommandNode(self, node: PresetCommandNode):
        return {
            "kind": "preset",
            "preset_name": node.preset_name,
            "func_name": node.func_name
            #"location": node.lineno,
        }

    def _visit_TimerCommandNode(self, node: TimerCommandNode):
        return {
            "kind": "timer",
            "sys_name": node.name,
            "mode": node.mode,
            "time_type": node.time_type,
            "timer_opt": node.timer_opt
            #"location": node.lineno,
        }

    # ---- 诊断 ----
    def _visit_ObserveEmittedCommandNode(self, node: ObserveEmittedCommandNode):
        return {
            "kind": "observe_emitted",
            "object_kind": node.object_kind,
            "species_kind": node.species_kind,
            "observe_emit_kind": node.observe_emit_kind,
            "observe_opt": node.observe_opt
            #"location": node.lineno,
        }

    def _visit_ObserveFieldCommandNode(self, node: ObserveFieldCommandNode):
        return {
            "kind": "observe_field",
            "field_kind": node.field_kind,
            "object_kind": node.object_kind,
            "observe_opt": node.observe_opt
            #"location": node.lineno,
        }

    def _visit_ObserveFieldPowerCommandNode(self, node: ObserveFieldPowerCommandNode):
        return {
            "kind": "observe_field_power",
            "power_variable": node.power_variable,
            "object_kind": node.object_kind,
            "observe_opt": node.observe_opt
            #"location": node.lineno,
        }

    def _visit_ObserveFieldEnergyCommandNode(self, node: ObserveFieldEnergyCommandNode):
        return {
            "kind": "observe_field_energy",
            "energy_variable": node.energy_variable,
            "object_kind": node.object_kind,
            "observe_opt": node.observe_opt
            #"location": node.lineno,
        }

    def _visit_ObserveIntegralCommandNode(self, node: ObserveIntegralCommandNode):
        return {
            "kind": "observe_field_integral",
            "integral_kind": node.Integral_kind,
            "geom_name": node.geom_name,
            "observe_opt": node.observe_opt
            #"location": node.lineno,
        }

    def _visit_RangeFieldCommandNode(self, node: RangeFieldCommandNode):
        return {
            "kind": "range",
            "field_name": node.field_name,
            "line_name": node.line_name,
            "timer_name": node.timer_name,
            "range_opt": node.range_opt
            #"location": node.lineno,
        }

    def _visit_MarkCommandNode(self, node: MarkCommandNode):
        return {
            "kind": "mark",
            "geom_name": node.target,
            "axis": node.axis,
            "position": node.position if node.position is not None else "",
            "size": node.size
            #"location": node.lineno,
        }

    # ============================ 工具 ============================

    def _expr(self, node: Any):
        if hasattr(node, "to_expression"):
            return str(node.to_expression())
        if isinstance(node, list):
            return [self._expr(x) for x in node]
        return str(node)

    def _point_token(self, node: Any) -> str:
        """
        统一返回点记号：
        - NamedPointNode  -> "<P1>"
        - CoordPointNode  -> "<exprX|exprY(|exprZ)>"
        - 其它（容错）     -> "<...>" 包裹后的字符串
        """
        if isinstance(node, NamedPointNode):
            return f"<{node.name}>"
        if isinstance(node, CoordPointNode):
            coords = [self._expr(c) for c in node.coords]
            if len(coords) == 2:
                return f"<{coords[0]}|{coords[1]}>"
            elif len(coords) == 3:
                return f"<{coords[0]}|{coords[1]}|{coords[2]}>"
            else:
                raise ValueError(f"无效坐标维度: {coords}")
        # 兜底：将任意表达式包成一个“引用式点”
        return f"<{self._expr(node)}>"

    @staticmethod
    def _safe_repr(node: Any) -> str:
        try:
            return repr(node)
        except Exception:
            return f"<{node.__class__.__name__}>"

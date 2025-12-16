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

from src.core_symbol.symbolBase import MagicSymbolTable, MidSymbolTable
from src.core_symbol.muti_flows.utils.sTconv_utils import *
from src.core_symbol.muti_flows.utils.get_geom_num import geo_counter

from pint import Quantity, UnitRegistry



class MCL2MID_STConv:
    def __init__(self,
                 magic_symbols: MagicSymbolTable,
                 mid_symbols: MidSymbolTable,
                 ):
        self.magic_symbols = magic_symbols
        self.mid_symbols = mid_symbols

    def load_list(self, 
                  parsed_dicts: list,
                  unit_lr,
                  axis_mcl_dir: str,
                  geo_c: geo_counter,
                  area_debug: bool = False,
                  variable_debug: bool = False,
                  function_debug: bool = False,
                  port_debug: bool = False,
                  ):
        self.magic_symbols.load_list(parsed_dicts)
        self.unit_lr = unit_lr
        self.axis_mcl_dir = axis_mcl_dir
        self.geo_c = geo_c
        self.variable_debug = variable_debug
        self.area_debug = area_debug
        self.function_debug = function_debug
        self.port_debug = port_debug

    


    def mcl2mid_sTconv(self):
        """
        将MCL符号表转换为中间符号表
        """
        # ======================================================
        # 1️⃣ 过滤并排序有效条目
        # ======================================================
        valid_entries = [r for r in self.magic_symbols.cmds_list if r.get("ok") and "payload" in r]
        sorted_entries = sorted(valid_entries, key=lambda r: r.get("lineno", 0))
        print(f"[info] 有效解析条目数: {len(sorted_entries)}")

        # ======================================================
        # 2️⃣ 一次处理：主遍历
        # ======================================================
        print("[info] 转换器一轮处理……")

        for record in sorted_entries:
            payload = record["payload"]
            kind = payload.get("kind", "").upper()
            name = payload.get("name", "") or payload.get("geom_name", "")
            lineno = record.get("lineno", "?")

            print(f"[info] ====> @ Line {lineno}: {kind} {name}")

            try:
                self.process_entry(payload)
            except Exception as e:
                #print(f"[error] 条目处理失败 ({kind} {name}): {e}")
                pass

        return self.mid_symbols

    def process_entry(self, payload: dict):
        """
        处理单个条目
        """
        kind = payload.get("kind", "").lower()
        if not kind:
            print("[error] 无法识别条目 kind，已跳过。")
            return

        handler_name = f"_process_{kind}"
        handler = getattr(self, handler_name, None)
        if handler is None:
            print(f"[error] 未处理的条目类型: {kind}")
            return

        try:
            handler(payload)
        except Exception as e:
            print(f"[error] 处理 {kind} 时出错: {e}")
            traceback.print_exc()
            raise
        
    # ==========================
    # 工具方法
    # ==========================
    def _eval_length_in_meter(self, size_str: str, str2qty_debug) -> float:
        q = eval_qty(size_str, self.mid_symbols.symbol_table, self.unit_lr, str2qty_debug).to(ureg.meter)
        return float(q.magnitude)
    
    def get_point_str(self, name: str, unit=None) -> str:
        qx, qy = self.mid_symbols.geom["points"][name]
        return format_point(qx, qy, unit or self.unit_lr)

    def get_line_str(self, name: str, unit=None) -> str:
        pts = self.mid_symbols.geom["lines"][name]
        return format_line(pts, unit or self.unit_lr)

    def get_area_polygon_str(self, name: str, unit=None, close=True) -> str:
        info = self.mid_symbols.geom["areas"][name]
        if "points" not in info:
            raise ValueError(f"AREA {name} 不是点列表类型（{info['type']}），无法格式化为 polygon")
        pts = info["points"]
        if close and pts and pts[0] != pts[-1]:
            pts = pts + [pts[0]]
        return format_line(pts, unit or self.unit_lr)
    
    def _to_lr(self, v):
        """将 v 转到 constants.unit_lr 的数值；v 可以是 Quantity 或 float（已是 self.unit_lr）"""
        if hasattr(v, "to"):
            return float(v.to(self.unit_lr).magnitude)
        return float(v)

    def qty_mag_mm(self, q: Quantity, nd=10):
        """Quantity -> mm 数值"""
        return round(q.to(ureg.millimeter).magnitude, nd)

    def to_number_or_str(self, expr):
        """能转数字就转 float，转不了就保留为字符串"""
        try:
            v = float(parse_expr(str(expr)))
            return v
        except Exception:
            return str(expr)
        
    def _lr_pair_to_m_str(self, z_lr: float, r_lr: float, nd: int = 10) -> str:
        """把以 self.unit_lr 表示的 (z, r) 数值转为以米表示的字符串: '[z r]'"""
        lr_to_m = float(self.unit_lr.to(ureg.meter).magnitude)
        z_m = round(z_lr * lr_to_m, nd)
        r_m = round(r_lr * lr_to_m, nd)
        # 用 :g 避免 0.0000000000 这类冗长格式
        return f"[{z_m:g} {r_m:g}]"


    def _pt_to_unipic(self, qx, qy, axis_mcl_dir) -> tuple:
        """
        将几何平面点 (x,y) 转成 UNIPIC 三元组 (0, r, z)
        MCL 的轴向选择由 axis_mcl_dir 控制：
        - 'X'：x->z, y->r
        - 'Y'：x->r, y->z
        """
        x = self._to_lr(qx)
        y = self._to_lr(qy)
        if axis_mcl_dir == 'X':
            z, r = x, y
        else:  # 'Y'
            r, z = x, y
        return (0.0, r, z)
    
    # ==========================
    # 各类处理函数
    # ==========================
    def _process_variable(self, entry):

        variable_debug = self.variable_debug
        expr_str = entry.get("value", "")
        name = entry.get("name", "")
        try:
            #sym = parse_expr(str(expr_str))
            #if varible_debug:
            #    print(f"       变量 {name} 值表达式: {sym}")
            substituted_expr = substitute_variables(expr_str, self.mid_symbols.symbol_table)  # 替换变量名为符号表中对应的值和单位
            qty = ureg.parse_expression(substituted_expr)  # 解析表达式为数量
            

            # 纯数
            if isinstance(qty, (int, float)):
                value = round(float(qty), 10)
                unit = "dimensionless"
            else:
                # === 规范化到指定 SI/默认单位 ===
                q = qty
                dim = q.dimensionality
                try:
                    if dim == ureg.volt.dimensionality:
                        q = q.to(ureg.volt)                 # 电压 -> V
                    elif dim == ureg.second.dimensionality:
                        q = q.to(ureg.second)               # 时间 -> s
                    elif dim == ureg.hertz.dimensionality:
                        q = q.to(ureg.hertz)                # 频率 -> Hz
                    # 其它维度：保持原单位不变
                except Exception:
                    # 单位不可转换时，保持原样
                    q = qty

                value = round(float(q.magnitude), 10)
                unit = str(q.units)
                if variable_debug:
                    print(f"       变量 {name} 原始值: {expr_str} -> {value} {unit}")

            self.mid_symbols.symbol_table[name] = {"value": value, "unit": unit}

        except Exception as e:
            print(f"[error] 变量 {name} 处理失败: {e}")
            self.mid_symbols.symbol_table[name] = {"value": expr_str, "unit": "unknown"}


    def _process_point(self, entry):
        name = entry["name"]
        token = entry["point"]
        qx, qy = parse_point_token(token, self.mid_symbols.symbol_table, self.mid_symbols.geom["points"], self.unit_lr)
        # 保存成 mm 的纯浮点
        (x_mm, y_mm) = convert_to_xy_pairs([(qx, qy)])[0]
        self.mid_symbols.geom["points"][name] = (x_mm, y_mm)

    def _process_line(self, entry):
        name = entry["name"]
        pts_q = []
        for t in entry.get("points", []):
            qx, qy = parse_point_token(t, self.mid_symbols.symbol_table, self.mid_symbols.geom["points"], self.unit_lr)
            pts_q.append((qx, qy))
        # 保存成 mm 的纯浮点
        self.mid_symbols.geom["lines"][name] = convert_to_xy_pairs(pts_q)


    def _process_area(self, entry):
        """
        统一把面转成顶点序列（ZR 平面），内部存储为数量列表。
        RECTANGULAR/CONFORMAL：两个对角点 -> 四角闭合
        POLYGONAL：按顺序
        其它类型先存其专有参数，后续需要时再生成。
        """
        area_debug = self.area_debug

        name = entry["name"]
        a_type = entry["area_type"]
        params = entry.get("params", {})
        if area_debug:
            print(f"       {a_type} 原始点: {params}")
            print(f"[info] 符号表: {self.mid_symbols.symbol_table}")

        if a_type in ("CONFORMAL", "RECTANGULAR"):
            p_tokens = params.get("points") or [params.get("p1"), params.get("p2")]
            
            if len(p_tokens) != 2:
                raise ValueError(f"{a_type} 需要两个对角点")
            (x1, y1) = parse_point_token(p_tokens[0], self.mid_symbols.symbol_table, self.mid_symbols.geom["points"], self.unit_lr)
            (x2, y2) = parse_point_token(p_tokens[1], self.mid_symbols.symbol_table, self.mid_symbols.geom["points"], self.unit_lr)
            # 四角（闭合，首尾相接可按需要决定是否重复首点）
            p1 = (x1, y1)
            p2 = (x2, y1)
            p3 = (x2, y2)
            p4 = (x1, y2)
            poly = [p1, p2, p3, p4, p1]
            points = convert_to_xy_pairs(poly)
            self.mid_symbols.geom["areas"][name] = {"type": a_type, "points": points}

        elif a_type == "POLYGONAL":
            tokens = params.get("points", [])
            poly = [parse_point_token(t, self.mid_symbols.symbol_table, self.mid_symbols.geom["points"], self.unit_lr) for t in tokens]
            # 可选闭合：若首尾不同，可在生成时闭合
            if poly and poly[0] != poly[-1]:
                poly.append(poly[0])
            points = convert_to_xy_pairs(poly)
            self.mid_symbols.geom["areas"][name] = {"type": a_type, "points": points}

        elif a_type == "FUNCTIONAL":
            self.mid_symbols.geom["areas"][name] = {"type": a_type, "function": params.get("function")}

        elif a_type == "FILLET":
            p_tokens = params.get("points") or [params.get("p1"), params.get("p2")]
            (a1, b1) = parse_point_token(p_tokens[0], self.mid_symbols.symbol_table, self.mid_symbols.geom["points"], self.unit_lr)
            (a2, b2) = parse_point_token(p_tokens[1], self.mid_symbols.symbol_table, self.mid_symbols.geom["points"], self.unit_lr)
            rad_q = eval_qty(params["radius"], self.mid_symbols.symbol_table, self.unit_lr, area_debug)
            st  = self.to_number_or_str(params["start_angle"])
            ed  = self.to_number_or_str(params["end_angle"])
            self.mid_symbols.geom["areas"][name] = {
                "type": a_type,
                "points": convert_to_xy_pairs([(a1, b1), (a2, b2)]),  # 浮点(mm)
                "radius": self.qty_mag_mm(rad_q),                          # 浮点(mm)
                "start_angle": st,                                    # 数字或字符串
                "end_angle": ed,                                      # 数字或字符串
            }

        elif a_type == "QUARTERROUND":
            (cx, cy) = parse_point_token(params["center"], self.mid_symbols.symbol_table, self.mid_symbols.geom["points"], self.unit_lr)
            rad_q = eval_qty(params["radius"], self.mid_symbols.symbol_table, self.unit_lr, area_debug)
            quad = self.to_number_or_str(params["quadrant"])
            center = convert_to_xy_pairs([(cx, cy)])[0]
            self.mid_symbols.geom["areas"][name] = {
                "type": a_type,
                "center": center,                 # (x_mm, y_mm)
                "radius": self.qty_mag_mm(rad_q),      # 浮点(mm)
                "quadrant": quad,                 # 数字或字符串
            }

        elif a_type == "SINUSOID":
            p1 = parse_point_token(params["points"][0] if "points" in params else params["p1"], self.mid_symbols.symbol_table, self.mid_symbols.geom["points"], self.unit_lr)
            p2 = parse_point_token(params["points"][1] if "points" in params else params["p2"], self.mid_symbols.symbol_table, self.mid_symbols.geom["points"], self.unit_lr)
            p3 = parse_point_token(params["points"][2] if "points" in params else params["p3"], self.mid_symbols.symbol_table, self.mid_symbols.geom["points"], self.unit_lr)
            axis = str(params.get("axis"))
            self.mid_symbols.geom["areas"][name] = {"type": a_type, "points": convert_to_xy_pairs([p1, p2, p3]), "axis": axis}

        else:
            raise ValueError(f"未知 AREA 类型: {a_type}")

    def _process_material_apply(self, entry):
        geom_name = entry.get("geom_name", "")
        mtype = entry.get("mtype", "")
        area = self.mid_symbols.geom["areas"].get(geom_name)
        if not area:
            raise ValueError(f"[material_apply] 几何体不存在：{geom_name}")
        # 直接在 area 信息上挂材料
        area["material"] = mtype
        print(f"       已为几何体 {geom_name} 添加材料 {mtype}")


    ###############
    # cmd_func
    ###############
    # 系统函数大写转小写
    __func__ = ""

    def func_mcl2unipic(self, func_str:str):
        import re
        print("       func value:\n       ", func_str)
        func_str = func_str.replace(" T ", " t ")
        func_str = func_str.replace(" X ", " x ")
        func_str = func_str.replace(" Y ", " y ")
        func_str = func_str.replace(" Z ", " z ")
        func_str = func_str.replace(" EXP ( ", " exp ( ")
        func_str = func_str.replace(" * R * ", " * r * ")
        func_str = func_str.replace(" MIN ", " min ")
        func_str = func_str.replace(" MAX ", " max ")
        func_str = func_str.replace(" ABS ", " abs ")
        func_str = func_str.replace(" SIN ", " sin ")
        func_str = func_str.replace(" ", "")
        func_str = func_str.replace("**", "^")
        # 正则表达式匹配 字符.字符为 字符_字符
        func_str = re.sub(r'([A-Za-z]+)\.([A-Za-z]+)', r'\1_\2', func_str)

        print("       处理后:\n       ", func_str)
        return func_str

    def funcvars_mcl2unipic(self, func_vars_list):
        pattern = re.compile(r'([A-Za-z]+)\.([A-Za-z]+)')
        
        new_list: List[Dict[str, Any]] = []
        for entry in func_vars_list:
            new_entry = {}
            for key, value in entry.items():
                new_key = pattern.sub(r'\1_\2', key)
                new_entry[new_key] = value
            new_list.append(new_entry)
        
        return new_list

    def _process_function(self, entry):
        name = entry.get("name")
        params = entry.get("params", [])
        body = entry.get("body", "")
        func_vars = []
        for var_name, v in self.mid_symbols.symbol_table.items():
            if var_name in body:
                func_vars.append({var_name: v["value"]})
        self.mid_symbols.functions[name] = {
            "name": name, "params": params, "body": body, "vars": func_vars
        }
        if self.function_debug:
            print(f"       函数 {name} 定义成功")

    def _process_port(self, entry):
        port_debug = self.port_debug
        axis_mcl_dir = self.axis_mcl_dir

        if port_debug:
            print(f"[info] 端口解析: {entry.get('geom_name','')}")
        geom_name = entry["geom_name"]
        direction = entry["direction"]

        # 取几何（点/线都行）
        if geom_name in self.mid_symbols.geom["lines"]:
            pts = self.mid_symbols.geom["lines"][geom_name]
            geom_value = [self._pt_to_unipic(qx, qy, axis_mcl_dir) for (qx, qy) in pts]
        elif geom_name in self.mid_symbols.geom["points"]:
            qx, qy = self.mid_symbols.geom["points"][geom_name]
            geom_value = [self._pt_to_unipic(qx, qy, axis_mcl_dir)]
        else:
            raise ValueError(f"[port] 未找到几何：{geom_name}")

        incoming_func_body = None
        incoming_func_vars = []
        incoming_opt = {}
        norm_set = {}

        if direction == "POSITIVE":
            kind = "MurVoltagePort"
            for opt in entry.get("options", []):
                opt_name = opt.get("port_opt_name")
                if opt_name == "INCOMING":
                    incoming_func_name = opt["incoming_func"]
                    incoming_func = self.mid_symbols.functions.get(incoming_func_name)
                    if not incoming_func:
                        raise ValueError(f"[port] 未定义的入射函数：{incoming_func_name}")
                    incoming_func_body = self.func_mcl2unipic(incoming_func["body"])
                    incoming_func_vars = self.funcvars_mcl2unipic(incoming_func["vars"])

                    # 形如 ["E1", "value", "E2", "value2"]
                    incoming_opt_list = opt.get("incoming_opt", [])
                    for i in range(0, len(incoming_opt_list), 2):
                        comp = incoming_opt_list[i]
                        val  = incoming_opt_list[i+1] if i+1 < len(incoming_opt_list) else None
                        if comp not in ("E1", "E2", "E3"):
                            raise ValueError(f"[port] INCOMING 组件非法：{comp}")
                        incoming_opt[comp] = val

                elif opt_name == "NORMALIZATION":
                    norm_type = opt.get("norm_type")
                    peak_ref  = opt.get("peak_value", [None])[0]
                    # 支持点/线
                    if peak_ref in self.mid_symbols.geom["lines"]:
                        npts = self.mid_symbols.geom["lines"][peak_ref]
                        norm_geom_value = [self._pt_to_unipic(qx, qy, axis_mcl_dir) for (qx, qy) in npts]
                    elif peak_ref in self.mid_symbols.geom["points"]:
                        qx, qy = self.mid_symbols.geom["points"][peak_ref]
                        norm_geom_value = [self._pt_to_unipic(qx, qy, axis_mcl_dir)]
                    else:
                        raise ValueError(f"[port] 归一化参考几何不存在：{peak_ref}")
                    norm_set = {
                        "norm_type": norm_type,
                        "norm_geom_name": peak_ref,
                        "norm_geom_value": norm_geom_value
                    }

            self.mid_symbols.ports[geom_name] = {
                "kind": kind,
                "geom_name": geom_name,
                "geom_value": geom_value,
                "direction": direction,
                "result": incoming_func_body,
                "func_vars": incoming_func_vars,
                "incoming_opt": incoming_opt,
            }
            if norm_set:
                self.mid_symbols.ports[geom_name].update(norm_set)

            print(f"[info] 端口 {geom_name} 定义成功")

        elif direction == "NEGATIVE":
            kind = "OPENPORT"
            self.mid_symbols.ports[geom_name] = {
                "kind": kind,
                "geom_name": geom_name,
                "geom_value": geom_value,
                "direction": direction,
            }
        else:
            raise ValueError(f"[port] 方向不合法：{direction}")

    def _process_emit(self, entry):
        self.mid_symbols.emits.append(entry)

    def _process_emission(self, entry):
        self.mid_symbols.emits.append(entry)

    def _process_preset(self, entry):
        preset_name = entry["preset_name"]
        preset_func_name = entry["func_name"]

        if preset_name == "B1ST":
            component = "0"; func_kind = "Bz"
        elif preset_name == "B2ST":
            component = "1"; func_kind = "Br"
        else:
            raise ValueError(f"[preset] 未支持的预设：{preset_name}")

        preset_func = self.mid_symbols.functions.get(preset_func_name)
        if not preset_func:
            raise ValueError(f"[preset] 未定义函数：{preset_func_name}")

        preset_func_body = self.func_mcl2unipic(preset_func["body"])
        preset_func_vars_list = self.funcvars_mcl2unipic(preset_func["vars"])

        preset_func_vars = {k: v for d in preset_func_vars_list for k, v in d.items()}

        params = set(preset_func.get("params", []))
        if "T" in params:
            preset_func_kind = "tFunc"
        elif ("Z" in params) and ("R" in params):
            preset_func_kind = "zrFunc"
        else:
            raise ValueError(f"[preset] 函数参数不符合预期，应包含T或(Z,R)：{preset_func_name}")

        self.mid_symbols.presets[func_kind] = {
            "component": component,
            "func_vars": preset_func_vars,
            "kind": preset_func_kind,
            "result": preset_func_body,
        }
    
    def _process_timer(self, entry):
        timer_name = entry.get("timer_name") or entry.get("name")
        timer_mode = entry.get("timer_mode") or entry.get("mode")
        timer_type = entry.get("timer_type") or entry.get("time_type")
        timer_opts = list(entry.get("timer_opt", []))

        # 变量展开
        symbol_table = {n: f"{v['value']} * {v['unit']}" for n, v in self.mid_symbols.symbol_table.items()}
        for i, opt in enumerate(timer_opts):
            timer_opts[i] = symbol_table.get(opt, opt)

        self.mid_symbols.timers[timer_name] = {
            "timer_name": timer_name,
            "timer_mode": timer_mode,
            "timer_type": timer_type,
            "timer_opts": timer_opts,
        }

    def _process_observe_field_integral(self, entry):
        
        axis_mcl_dir = self.axis_mcl_dir
        geo_c = self.geo_c
        result_dic = {}
        ikind = entry["integral_kind"]
        gname = entry["geom_name"]

        if gname not in self.mid_symbols.geom["lines"]:
            raise ValueError(f"[observe_field_integral] 参考对象应为 LINE：{gname}")

        pts = [self._pt_to_unipic(qx, qy, axis_mcl_dir) for (qx, qy) in self.mid_symbols.geom["lines"][gname]]
        (_, r1, z1), (_, r2, z2) = pts[0], pts[-1]   # 这里 r1,z1 等仍是 self.unit_lr 下的数

        if ikind == "E.DL":
            # 电压：按 r 方向（写文件用米）
            org = self._lr_pair_to_m_str(z1, r1)
            end = self._lr_pair_to_m_str(z2, r2)
            result_dic.update({
                "observe_type": "observe_field_integral",
                "kind": "VoltageDgn",
                "name": f"Vin{geo_c.get_voltageDgn_count()}",
                "lineDir": "r",
                "org": org.replace("0 ", "0.01 "),
                "end": end.replace("0 ", "0.01 "),
            })
        elif ikind == "J.DA":
            # 电流：给一个上下界（沿 z），写文件用米
            lo = self._lr_pair_to_m_str(min(z1, z2), r1 if z1 <= z2 else r2)
            hi = self._lr_pair_to_m_str(max(z1, z2), r2 if z2 >= z1 else r1)
            result_dic.update({
                "observe_type": "observe_field_integral",
                "kind": "CurrentDgn",
                "name": f"Iz{geo_c.get_currentDgn_count()}",
                "dir": "r",
                "lowerBounds": lo.replace("0 ", "0.01 "),
                "upperBounds": hi.replace("0 ", "0.01 "),
            })
        else:
            raise ValueError(f"[observe_field_integral] 暂不支持：{ikind}")

        # 选项占位...
        observe_opts = entry.get("observe_opt", [])
        if result_dic:
            self.mid_symbols.FieldsDgn.append(result_dic)


    def _process_observe_field(self, entry):
        result_dic = {}
        field_kind = entry["field_kind"]
        obj = entry["object_kind"]

        if obj not in self.mid_symbols.geom["points"]:
            raise ValueError(f"[observe_field] 参考点不存在：{obj}")

        qx, qy = self.mid_symbols.geom["points"][obj]
        _, r_lr, z_lr = self._pt_to_unipic(qx, qy, self.axis_mcl_dir)   # self.unit_lr 下

        # 写文件用米
        loc = self._lr_pair_to_m_str(z_lr, r_lr)

        if field_kind in ("E1","E2","E3"):
            kind = "ElecDgn"; result_dic.update({"kind": kind})
        elif field_kind in ("B1","B2","B3"):
            kind = "MagDgn";  result_dic.update({"kind": kind, "component": "dynamic"})
        else:
            raise ValueError(f"[observe_field] 不支持的场分量：{field_kind}")

        result_dic.update({
            "observe_type": "observe_field",
            "field_kind": field_kind,
            "dir": dir_dic[field_kind],
            "name": name_dic[field_kind],
            "location": loc.replace("0 ", "0.01 "),
        })

        observe_opts = entry.get("observe_opt", [])
        if result_dic:
            self.mid_symbols.FieldsDgn.append(result_dic)


    def _process_observe_field_power(self, entry):
        result_dic = {}
        unit_lr = self.unit_lr
        axis_mcl_dir = self.axis_mcl_dir
        geo_c = self.geo_c

        if entry["power_variable"] != "S.DA":
            raise ValueError(f"[observe_field_power] 仅支持 S.DA")
        obj = entry["object_kind"]
        if obj not in self.mid_symbols.geom["lines"]:
            raise ValueError(f"[observe_field_power] 参考对象应为 LINE：{obj}")

        pts = [self._pt_to_unipic(qx, qy, axis_mcl_dir) for (qx, qy) in self.mid_symbols.geom["lines"][obj]]
        (_, r1, z1), (_, r2, z2) = pts[0], pts[-1]

        # 统一下界<上界（按 z），并转米
        lo = self._lr_pair_to_m_str(min(z1, z2), r1 if z1 <= z2 else r2)
        hi = self._lr_pair_to_m_str(max(z1, z2), r2 if z2 >= z1 else r1)

        result_dic.update({
            "observe_type": "observe_field_power",
            "kind": "PoyntingDgn",
            "dir": "z",
            "name": f"Poutout{geo_c.get_PoyntingDgn_count()}",
            "lowerBounds": lo.replace("0 ", "0.01 "),
            "upperBounds": hi.replace("0 ", "0.01 "),
        })

        observe_opts = entry.get("observe_opt", [])
        if result_dic:
            self.mid_symbols.FieldsDgn.append(result_dic)


   
    def _process_mark(self, entry):
        
        axis = entry.get("axis")
        size_token = entry.get("size")
        if not axis or not size_token:
            print("[error] MARK 缺少必要字段，已忽略。")
            return
        try:
            # eval_qty 返回带单位，转米
            size_m = float(eval_qty(size_token, self.mid_symbols.symbol_table, self.unit_lr).to(ureg.meter).magnitude)
            
            prev = self.mid_symbols.grid.get(axis) or -1.0
            
            if (prev <= 0.0) or (size_m < prev):
                self.mid_symbols.grid[axis] = size_m
                
            print(f"       Grid=> {axis} = {self.mid_symbols.grid[axis]} m")
        except Exception as e:
            print(f"[error] MARK 处理失败: {e}")

    def _process_inductor(self, entry):
        """
        entry (from REGEX_PARSER):
        {
        "kind": "INDUCTOR",
        "line_name": "GAP",
        "diameter": "1.5 * mm",        # 可选/必选, 字符串表达式（长度）
        "inductance": "1e-9",          # 可选，若提供视作 H/m（可不带单位）
        # 未来可扩展: material/frequency/resistivity/resistance/number ...
        }
        """
        unit_lr = self.unit_lr
        axis_mcl_dir = self.axis_mcl_dir
        line = entry.get("line_name")
        if not line or line not in self.mid_symbols.geom["lines"]:
            raise ValueError(f"[inductor] 目标线不存在：{line}")

        # 1) 线的几何（Quantity -> UNIPIC 三元组 -> 取首尾两点）
        pts_q = self.mid_symbols.geom["lines"][line]                 # [(qx,qy), ...] 仍是 Quantity
        if len(pts_q) < 2:
            raise ValueError(f"[inductor] 线 {line} 至少需要两个点")

        # 取首末两点（若是折线，我们按整体端点处理）
        (qx1, qy1) = pts_q[0]
        (qx2, qy2) = pts_q[-1]
        _, r1_lr, z1_lr = self._pt_to_unipic(qx1, qy1, axis_mcl_dir)   # 单位: self.unit_lr（如 mm）的 float
        _, r2_lr, z2_lr = self._pt_to_unipic(qx2, qy2, axis_mcl_dir)

        # 2) 方向与上下界（参考 UNIPIC 约定：位置写成 [z r]）
        #    - 根据变化量决定是沿 r 还是沿 z
        dr = r2_lr - r1_lr
        dz = z2_lr - z1_lr
        if abs(dr) >= abs(dz):
            direc = "r"
            # 按 r 升序排列下/上界
            if r1_lr <= r2_lr:
                lo = (z1_lr, r1_lr)
                hi = (z2_lr, r2_lr)
            else:
                lo = (z2_lr, r2_lr)
                hi = (z1_lr, r1_lr)
        else:
            direc = "z"
            if z1_lr <= z2_lr:
                lo = (z1_lr, r1_lr)
                hi = (z2_lr, r2_lr)
            else:
                lo = (z2_lr, r2_lr)
                hi = (z1_lr, r1_lr)

        # 3) 转成米（样例里是 0.2、0.025 这种量级，显然是 m）
        lr_to_m = float(unit_lr.to(ureg.meter).magnitude)  # e.g. mm -> m = 1e-3
        def to_bounds_str(z_lr, r_lr):
            z_m = round(z_lr * lr_to_m, 10)
            r_m = round(r_lr * lr_to_m, 10)
            # 使用尽量简洁的数字格式
            return f"[{z_m:g} {r_m:g}]"

        lower_bounds = to_bounds_str(*lo)
        upper_bounds = to_bounds_str(*hi)

        # 4) 直径表达式 & 强制电感（H/m）-> 总电感（H）
        diameter_expr = entry.get("diameter")     # 字符串表达式（不在此阶段强求值）
        inductance_pm = entry.get("inductance")   # 可能是 "1e-9"（H/m），无单位也接受

        # 线总长度（米）
        r1_m, z1_m = r1_lr * lr_to_m, z1_lr * lr_to_m
        r2_m, z2_m = r2_lr * lr_to_m, z2_lr * lr_to_m
        length_m = ( (r2_m - r1_m)**2 + (z2_m - z1_m)**2 )**0.5

        L_total = None
        if inductance_pm is not None and str(inductance_pm).strip() != "":
            try:
                # 支持纯数或带单位表达式；若无单位则视作 H/m
                # 先尝试 pint；失败则退化为纯 float
                try:
                    q = ureg.parse_expression(str(inductance_pm))
                    if hasattr(q, "to"):
                        Lp = float(q.to(ureg.henry/ureg.meter).magnitude)  # H/m
                    else:
                        Lp = float(q)  # 纯数
                except Exception:
                    Lp = float(str(inductance_pm))
                L_total = Lp * length_m
            except Exception:
                # 不终止流程，只是不给 L，总线写出其余信息
                print(f"[error] INDUCTOR 解析强制电感失败：{inductance_pm}")

        # 5) 缓存 JSON-safe 结果，留给 saveCircuitModelIn()
        self.mid_symbols.inductor.append({
            "name": line,                       # 以线名作为逻辑名（保存时会生成 inductor1/2/...）
            "kind": "Inductor",
            "L":  inductance_pm, #None if L_total is None else float(f"{L_total:.10g}"),  # H
            "dir": direc,                       # "r" 或 "z"
            "lowerBounds": lower_bounds,        # "[z r]" in meters
            "upperBounds": upper_bounds,        # "[z r]" in meters
            "length_m": float(f"{length_m:.10g}"),
            "diameter_expr": diameter_expr     # 留作后续需要时再数值化
            #"inductance_per_m": inductance_pm   # 原样保留（便于追溯）
        })
    
    def _process_freespace(self, entry):
        return None

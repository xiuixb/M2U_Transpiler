import os
import sys
import json

# 获取项目根目录路径
current_dir = os.path.dirname(os.path.abspath(__file__))
while not os.path.exists(os.path.join(current_dir, ".project_mark")):
    parent_dir = os.path.dirname(current_dir)
    if    parent_dir != current_dir: current_dir = parent_dir
    else: raise FileNotFoundError("未找到项目根目录，检查.project_mark文件")
project_root = current_dir
sys.path.append(project_root)

from src.domain.config.symbolBase import MagicSymbolTable, MidSymbolTable
from src.domain.utils.sTconv_utils import *
from src.domain.utils.get_geom_num import geo_counter
from src.domain.mclconv.llm_conv import LLMConv
from src.infrastructure.llm_config import llm_config
from src.domain.core.llm_flows import MCLPromptBuildFlow
from src.domain.config.cmd_dic import MCL2MID_CmdDict
from src.domain.config.llm_route_config import llm_route_config
from src.domain.core.dependency_retriever import DependencyRetriever
from src.domain.core.treeList_upserter import TreeListUpserter
from src.domain.core.unit_tool import UnitTool


class MCL2MID_STConv:
    def __init__(self,
                 magic_symbols: MagicSymbolTable,
                 mid_symbols: MidSymbolTable,
                 dependency_retriever: DependencyRetriever,
                 ):
        self.magic_symbols = magic_symbols        
        self.mid_symbols = mid_symbols
        self.dependency_retriever = dependency_retriever
        self.inserter = TreeListUpserter()
        self.mcl2mid_dict = MCL2MID_CmdDict()
        self.MCL2MID_dict = self.mcl2mid_dict.MID_dict
        self.llmconvlist = self.mcl2mid_dict.MCL2MID_llmconv_List
        self.cmd_no = {}
        for llmconv in self.llmconvlist.keys():
            self.cmd_no[llmconv] = 0
        self.llmconv = LLMConv()
        self.llmconv.load_entity(
            self.mcl2mid_dict,
            api_key = llm_config.api_key,
            prompt_flow = MCLPromptBuildFlow(),
        )
       

        

    def load_list(self, 
                  parsed_dicts: list,
                  unit_lr,
                  axis_mcl_dir: str,
                  geo_c: geo_counter,
                  area_debug: bool = False,
                  variable_debug: bool = False,
                  function_debug: bool = False,
                  port_debug: bool = False,
                  llmconv_debug: bool = False,
                  ):
        self.magic_symbols.load_list(parsed_dicts)
        self.unit_lr = unit_lr
        self.axis_mcl_dir = axis_mcl_dir
        self.geo_c = geo_c
        self.variable_debug = variable_debug
        self.area_debug = area_debug
        self.function_debug = function_debug
        self.port_debug = port_debug
        self.llmconv_debug = llmconv_debug



    def mcl2mid_sTconv(self):
        """
        将解析结果写入 sT 中间表示。
        """
        # ======================================================
        # 1️⃣ 过滤并排序有效条目
        # ======================================================
        valid_entries = [r for r in self.magic_symbols.cmds_list if r.get("ok") and "payload" in r]
        sorted_entries = sorted(valid_entries, key=lambda r: r.get("lineno", 0))
        self.magic_symbols.cmds_list = sorted_entries
        print(f"[info] 有效解析条目数: {len(sorted_entries)}")

        # ======================================================
        # 2️⃣ 一次处理：主遍历
        # ======================================================

        for idx, record in enumerate(sorted_entries):
            command_type = record["command"]
           
            payload = record["payload"]
            kind = payload.get("kind", "").upper()
            name = payload.get("sys_name", "") or payload.get("geom_name", "")
            lineno = record.get("lineno", "?")

            print(f"[info] ====> @ Line {lineno}: {kind} {name}")

            self.process_record(idx, record)

        # ======================================================
        # 3️⃣ 二次处理：LLM并发 + 后处理
        # ======================================================
        if self.llmconv_debug:
            print(f"[debug] 待处理LLM转换条目:")
            json.dump(self.llmconvlist, sys.stdout, ensure_ascii=False, indent=4)
        
        print(f"[debug] 二次处理llm_debug={self.llmconv_debug}")
        
        llm_results = self.llmconv.llmconv_mcl2mid(
            self.llmconvlist,
            'qwen-plus',
            self.llmconv_debug
        )
        #print(f"[debug] 处理LLM转换条目结果:", json.dumps(llm_results, ensure_ascii=False, indent=4))
        for llmconv_item in llm_results:
            
            # print(f"[debug] 处理LLM转换条目:", json.dumps(llmconv_item, ensure_ascii=False, indent=4))
            self.inserter.upsert_one(self.mid_symbols.sT, llmconv_item)

        return self.mid_symbols, self.llmconvlist

    def process_record(self, idx: int, record: dict):
        """
        处理单个条目
        """
        # print(f"[debug] 已处理 {idx} 条记录，当前索引标签: {self.treelist_upserter.list_unique_tags(self.mid_symbols.to_dict())}")
        kind = record.get("payload", "").get("kind", "").lower()
        cmd_type = record["command"]
        if not kind:
            print("[error] 无法识别条目 kind，已跳过。")
            return
        
        if not self.llmconv_debug:
            # 正式转换
            if kind in llm_route_config.mcl2mid_llmconv_commands:
                print(f"       loading dependency_retriever for {kind} {record['command']}")
                print(f"       LLM处理的条目类型: {cmd_type}")
                if cmd_type in self.cmd_no:
                    cmd_no = self.cmd_no[cmd_type] + 1
                    self.cmd_no[cmd_type] = cmd_no
                    record["payload"]["cmd_no"] = cmd_no
                cmd_type_single = cmd_type.split()[0]
                shouldConvert = cmd_type_single in self.MCL2MID_dict
                if shouldConvert:
                    self._process_llmconv(idx, record)
                return
            else:
                handler_name = f"_process_{kind}"
                handler = getattr(self, handler_name, None)
                if handler is None:
                    print(f"[error] 未处理的条目类型: {kind}")
                    return

                try:
                    handler(idx, record)
                except Exception as e:
                    print(f"[error] 处理 {kind} 时出错: {e}")
                    traceback.print_exc()
                    raise
            


    def _process_llmconv(self, idx: int, record: dict):
        """
        处理LLM转换的上下文
        """
        # print(f"[debug] _process_llmconv")
        
        # 命令依赖检索器加载数据
        self.dependency_retriever.load_data(
                self.magic_symbols, 
                self.mid_symbols
            )
        
        mcl_command_type = record["command"]
        mcl_command_type_single = mcl_command_type.split()[0]
        mcl_cmd_text = record["text"]     # 原始命令文本
        mcl_payload = record["payload"]


        # 查询此命令的依赖命令
        dependency = self.dependency_retriever.get_mcl_dependency_item(idx, mcl_command_type_single, mcl_cmd_text)
        self.magic_symbols.cmds_list[idx]["payload"]["dependency"] = dependency
        # mcl_dependency_text = str(dependency)

        # 入库
        llmconv_item = {
            "sys_type": mcl_command_type_single,
            "value":{
                "mcl_type": mcl_command_type,
                "mcl_cmd_text": mcl_cmd_text,
                "mcl_payload": mcl_payload
            }
        }
        self.inserter.upsert_one(self.llmconvlist, llmconv_item)

        
    # ==========================
    # 工具方法
    # ==========================
    def _eval_length_in_meter(self, size_str: str, str2qty_debug) -> float:
        q = eval_qty(size_str, self.mid_symbols.sT["variable"], self.unit_lr, str2qty_debug).to(ureg.meter)
        return float(q.magnitude)
    
    def get_point_str(self, name: str, unit=None) -> str:
        qx, qy = self.mid_symbols.sT["geometry"]["point"][name]
        return format_point(qx, qy, unit or self.unit_lr)

    def get_line_str(self, name: str, unit=None) -> str:
        pts = self.mid_symbols.sT["geometry"]["line"][name]
        return format_line(pts, unit or self.unit_lr)

    def get_area_polygon_str(self, name: str, unit=None, close=True) -> str:
        info = self.mid_symbols.sT["geometry"]["area"][name]
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
    def _process_variable(self, idx: int, record: dict):
        #print("[info] ====> @ variable:\n", record)
        variable_debug = self.variable_debug
        expr_str = record.get("payload", "").get("value", "")
        name = record.get("payload", "").get("sys_name", "")
        try:
            #sym = parse_expr(str(expr_str))
            #if varible_debug:
            #    print(f"       变量 {name} 值表达式: {sym}")
            substituted_expr = substitute_variables(expr_str, self.mid_symbols.sT["variable"])  # 用 sT 变量表展开表达式
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
                    elif dim == ureg.nanosecond.dimensionality:
                        q = q.to(ureg.nanosecond)               # 时间 -> ns
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

            # 存储到magic_symbols
            self.magic_symbols.cmds_list[idx]["payload"]["dependency"] = [
                { name: f"[varible value] {value} {unit}"}
            ]
            
            
            # 存储到variable（用于输出）
            self.mid_symbols.sT["variable"][name] = {
                "var_name": name,
                "parameters": {
                    "var_expr": expr_str
                },
                "cac_result": {
                    "var_num": value,
                    "var_unit": unit,
                    "text": f"{name} = {value} {unit}"
                },
                "dependencies": []
            }

        except Exception as e:
            print(f"[error] 变量 {name} 处理失败: {e}")
            # 存储到symbol_table（用于内部计算）
            self.mid_symbols.sT["variable"][name] = {"value": expr_str, "unit": "unknown"}
            
            # 存储到variable（用于输出）
            self.mid_symbols.sT["variable"][name] = {
                "var_name": name,
                "parameters": {
                    "var_expr": expr_str
                },
                "cac_result": {},
                "dependencies": []
            }


    def _process_point(self, idx: int, record):
        #print(record)
        
        entry = record.get("payload", "")
        name = entry["sys_name"]
        token = entry["point"]
        qx, qy = parse_point_token(token, self.mid_symbols.sT["variable"], self.mid_symbols.sT["geometry"]["point"], self.unit_lr)
        # 保存成 mm 的纯浮点
        (x_mm, y_mm) = convert_to_xy_pairs([(qx, qy)])[0]
        self.magic_symbols.cmds_list[idx]["payload"]["dependency"] = [
            { name: f"[point value] ({x_mm}, {y_mm}) (mm)"}
        ]
        self.mid_symbols.sT["geometry"]["point"][name] = {
            "geom_name": name,
            "parameters":{
                "geom_expr": f"{x_mm:.6f}mm, {y_mm:.6f}mm"
            },
            "cac_result":{
                "geom_num": [x_mm, y_mm],
                "geom_unit": "mm"
            }
        }

    def _process_line(self, idx: int, record):
        #print(record)
        
        entry = record.get("payload", "")
        name = entry["sys_name"]
        pts_q = []
        for t in entry.get("points", []):
            qx, qy = parse_point_token(t, self.mid_symbols.sT["variable"], self.mid_symbols.sT["geometry"]["point"], self.unit_lr)
            pts_q.append((qx, qy))

        def to_mm_value(q):
            # pint.Quantity
            if hasattr(q, "to") and hasattr(q, "magnitude"):
                return float(q.to("millimeter").magnitude)
            # astropy.units.Quantity
            if hasattr(q, "to") and hasattr(q, "value"):
                return float(q.to("mm").value)
            raise TypeError(f"Unsupported type: {type(q)}")
        
        data_mm = [(to_mm_value(a), to_mm_value(b)) for a, b in pts_q]
        
        self.magic_symbols.cmds_list[idx]["payload"]["dependency"] = [
            { name: f"[line value] {data_mm} (mm)"}
        ]
        self.mid_symbols.sT["geometry"]["line"][name] = {
            "geom_name": name,
            "parameters":{
                "geom_expr": entry.get("points", [])
            },
            "cac_result":{
                "geom_num": convert_to_xy_pairs(pts_q),
                "geom_unit": "mm"
            }
        }
        #print("_process_line:\n",self.mid_symbols.sT["geometry"]["line"][name])


    def _process_area(self, idx: int, record):
        """
        统一把面转成顶点序列（ZR 平面），内部存储为数量列表。
        RECTANGULAR/CONFORMAL：两个对角点 -> 四角闭合
        POLYGONAL：按顺序
        其它类型先存其专有参数，后续需要时再生成。
        """
        #print(record)
        area_debug = self.area_debug
        
        entry = record.get("payload", "")
        name = entry["sys_name"]
        a_type = entry["area_type"]
        params = entry.get("params", {})
        if area_debug:
            print(f"       {a_type} 原始点: {params}")
            print(f"[info] sT.variable: {self.mid_symbols.sT['variable']}")

        if a_type in ("CONFORMAL", "RECTANGULAR"):
            p_tokens = params.get("points") or [params.get("p1"), params.get("p2")]
            
            if len(p_tokens) != 2:
                raise ValueError(f"{a_type} 需要两个对角点")
            (x1, y1) = parse_point_token(p_tokens[0], self.mid_symbols.sT["variable"], self.mid_symbols.sT["geometry"]["point"], self.unit_lr)
            (x2, y2) = parse_point_token(p_tokens[1], self.mid_symbols.sT["variable"], self.mid_symbols.sT["geometry"]["point"], self.unit_lr)
            # 四角（闭合，首尾相接可按需要决定是否重复首点）
            p1 = (x1, y1)
            p2 = (x2, y1)
            p3 = (x2, y2)
            p4 = (x1, y2)
            poly = [p1, p2, p3, p4, p1]

            # 保存成 mm 的纯浮点
            geom_num = convert_to_xy_pairs(poly)
            self.magic_symbols.cmds_list[idx]["payload"]["dependency"] = [
                { name: f"[area value] {geom_num} (mm)"}
            ]

            self.mid_symbols.sT["geometry"]["area"][name] = {
                "area_type": a_type, 
                "parameters":{
                    "geom_expr": params.get("points", [])
                },
                "cac_result":{
                    "geom_num": geom_num,
                    "geom_unit": "mm"
                }  
            }

        elif a_type == "POLYGONAL":
            tokens = params.get("points", [])
            poly = [parse_point_token(t, self.mid_symbols.sT["variable"], self.mid_symbols.sT["geometry"]["point"], self.unit_lr) for t in tokens]
            # 可选闭合：若首尾不同，可在生成时闭合
            if poly and poly[0] != poly[-1]:
                poly.append(poly[0])
            geom_num = convert_to_xy_pairs(poly)
            self.magic_symbols.cmds_list[idx]["payload"]["dependency"] = [
                { name: f"[area value] muti-polygon, details omitted"}
            ]

            self.mid_symbols.sT["geometry"]["area"][name] = {
                "area_type": a_type,
                "parameters":{
                    "geom_expr": params.get("points", [])
                },
                "cac_result":{
                    "geom_num": geom_num,
                    "geom_unit": "mm"
                }  
            }

        elif a_type == "FUNCTIONAL":
            self.mid_symbols.sT["geometry"]["area"][name] = {
                "area_type": a_type,
                "parameters":{
                    "geom_expr": params.get("function")
                },
                "cac_result":{}
            }

        elif a_type == "FILLET":
            p_tokens = params.get("points") or [params.get("p1"), params.get("p2")]
            (a1, b1) = parse_point_token(p_tokens[0], self.mid_symbols.sT["variable"], self.mid_symbols.sT["geometry"]["point"], self.unit_lr)
            (a2, b2) = parse_point_token(p_tokens[1], self.mid_symbols.sT["variable"], self.mid_symbols.sT["geometry"]["point"], self.unit_lr)
            rad_q = eval_qty(params["radius"], self.mid_symbols.sT["variable"], self.unit_lr, area_debug)
            st  = self.to_number_or_str(params["start_angle"])
            ed  = self.to_number_or_str(params["end_angle"])
            self.mid_symbols.sT["geometry"]["area"][name] = {
                "area_type": a_type,
                "parameters":{
                    "geom_expr": params.get("points"),
                    "radius": UnitTool.qty_mag_mm(rad_q),                          # 浮点(mm)
                    "start_angle": st,                                    # 数字或字符串
                    "end_angle": ed
                },
                "cac_result":{
                    "geom_num": convert_to_xy_pairs([(a1, b1), (a2, b2)]),  # 浮点(mm)
                    "geom_unit": "mm"
                }  
            }

        elif a_type == "QUARTERROUND":
            (cx, cy) = parse_point_token(params["center"], self.mid_symbols.sT["variable"], self.mid_symbols.sT["geometry"]["point"], self.unit_lr)
            rad_q = eval_qty(params["radius"], self.mid_symbols.sT["variable"], self.unit_lr, area_debug)
            quad = self.to_number_or_str(params["quadrant"])
            center = convert_to_xy_pairs([(cx, cy)])[0]
            self.mid_symbols.sT["geometry"]["area"][name] = {
                "area_type": a_type,
                "parameters":{
                    "center": center,                 # (x_mm, y_mm)
                    "radius": UnitTool.qty_mag_mm(rad_q),      # 浮点(mm)
                    "quadrant": quad,                 # 数字或字符串
                },
                "cac_result":{}
            }

        elif a_type == "SINUSOID":
            raise ValueError(f"[sinusoid] 未实现")
            p1 = parse_point_token(params["points"][0] if "points" in params else params["p1"], self.mid_symbols.sT["variable"], self.mid_symbols.sT["geometry"]["point"], self.unit_lr)
            p2 = parse_point_token(params["points"][1] if "points" in params else params["p2"], self.mid_symbols.sT["variable"], self.mid_symbols.sT["geometry"]["point"], self.unit_lr)
            p3 = parse_point_token(params["points"][2] if "points" in params else params["p3"], self.mid_symbols.sT["variable"], self.mid_symbols.sT["geometry"]["point"], self.unit_lr)
            axis = str(params.get("axis"))
            self.mid_symbols.sT["geometry"]["area"][name] = {"type": a_type, "points": convert_to_xy_pairs([p1, p2, p3]), "axis": axis}

        else:
            raise ValueError(f"未知 AREA 类型: {a_type}")

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

    def _process_function(self, idx, record):

        entry = record["payload"]
        name = entry.get("sys_name")
        params = entry.get("params", [])
        body = entry.get("body", "")
        func_vars = []
        for var_name, var_record in self.mid_symbols.sT["variable"].items():
            if var_name in body:
                # print(f"variable {var_name} in function {name}, value: {var_record["cac_result"]["var_num"]}")
                var_num = var_record["cac_result"]["var_num"]
                var_unit = var_record["cac_result"]["var_unit"]

                var_si_num, var_si_unit = UnitTool.to_default_num(var_num, var_unit)
                #print(f"[info] var_si_num: {var_si_num}")

                func_vars.append({var_name: f"{var_si_num}"})
        self.magic_symbols.cmds_list[idx]["payload"]["dependency"] = func_vars
        # print(f"function print {idx}: {self.magic_symbols.cmds_list[idx]["payload"]}")
        
        self.mid_symbols.sT["function"][name] = {
            "func_name": name,
            "parameters": {
                "func_params": params,
                "func_body": body
            },
            "cac_result": {
                "func_vars": func_vars
            }
        }
        if self.function_debug:
            print(f"       函数 {name} 定义成功")


    ###############
    # other_cmd
    ###############



    def _process_material_assign(self, idx, record):
        entry = record["payload"]
        geom_name = entry.get("geom_name", "")
        mtype = entry.get("mtype", "")
        
        insert_cmd = {
            "sys_type": "material_assign",
            "value": {
                "geom_name": geom_name,
                "mat_name": mtype
            }
        }
        
        self.inserter.upsert_one(self.mid_symbols.sT, insert_cmd)
        
        print(f"[info] 已为几何体 {geom_name} 添加材料 {mtype}")
        print(self.mid_symbols.sT["materials"]["material_assign"])


    def _process_mark(self, idx, record):
        return
        entry = record["payload"]
        
        geom_name = entry.get("geom_name", "")
        axis = entry.get("axis")
        mesh_size = entry.get("size")


        if not axis or not mesh_size:
            print("[error] MARK 缺少必要字段，已忽略。")
            return
        try:
            # eval_qty 返回带单位，转米
            size_m = float(eval_qty(mesh_size, self.mid_symbols.sT["variable"], self.unit_lr).to(ureg.meter).magnitude)
            
            prev = self.mid_symbols.sT["mesh"]["mark"].get(axis) or -1.0
            
            if (prev <= 0.0) or (size_m < prev):
                self.mid_symbols.sT["mesh"][axis] = size_m
                
            print(f"       Grid=> {axis} = {self.mid_symbols.sT["mesh"][axis]} m")
        except Exception as e:
            print(f"[error] MARK 处理失败: {e}")


    def _process_port(self, idx, record):
        self.cmd_no["PORT"] += 1
        entry = record["payload"]
        port_debug = self.port_debug
        axis_mcl_dir = self.axis_mcl_dir

        if port_debug:
            print(f"[info] 端口解析: {entry.get('geom_name','')}")
        geom_name = entry["geom_name"]
        direction = entry["direction"]

        # 取几何（点/线都行）
        if geom_name in self.mid_symbols.sT["geometry"]["line"]:
            geom_num = self.mid_symbols.sT["geometry"]["line"][geom_name]["cac_result"]["geom_num"]
            geom_value = [(0.0, qy, qx) for (qx, qy) in geom_num]
        elif geom_name in self.mid_symbols.sT["geometry"]["point"]:
            qx, qy = self.mid_symbols.sT["geometry"]["point"][geom_name]["cac_result"]["geom_num"]
            geom_value = [(0.0, qy, qx)]
        else:
            raise ValueError(f"[port] 未找到几何：{geom_name}")

        #print(f"[info] debug\n{geom_name}:  {geom_value}")
        #raise ValueError(f"DEBUG...")
        incoming_func_body = None
        incoming_func_vars = []
        incoming_opt = {}
        norm_set = {}
        PORT_type = ""

        if direction == "POSITIVE":
            kind = "MurVoltagePort"
            PORT_type = "INPUTMURPORT"
            for opt in entry.get("options", []):
                opt_name = opt.get("port_opt_name")
                if opt_name == "INCOMING":
                    incoming_func_name = opt["incoming_func"]
                    incoming_func = self.mid_symbols.sT["function"].get(incoming_func_name)
                    if not incoming_func:
                        raise ValueError(f"[port] 未定义的入射函数：{incoming_func_name}")
                    incoming_func_body = self.func_mcl2unipic(incoming_func["parameters"]["func_body"])
                    incoming_func_vars = self.funcvars_mcl2unipic(incoming_func["cac_result"]["func_vars"])

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
                    if peak_ref in self.mid_symbols.sT["geometry"]["line"]:
                        npts = self.mid_symbols.sT["geometry"]["line"][peak_ref]["cac_result"]["geom_num"]
                        norm_geom_value = [(0.0, qy, qx) for (qx, qy) in npts]
                    elif peak_ref in self.mid_symbols.sT["geometry"]["point"]:
                        qx, qy = self.mid_symbols.sT["geometry"]["point"][peak_ref]["cac_result"]["geom_num"]
                        norm_geom_value = [(0.0, qy, qx)]
                    else:
                        raise ValueError(f"[port] 归一化参考几何不存在：{peak_ref}")
                    norm_set = {
                        "norm_type": norm_type,
                        "norm_geom_name": peak_ref,
                        "norm_geom_value": norm_geom_value
                    }

            self.mid_symbols.sT["boundaries"]["port"].append({
                "PORT_type": PORT_type,
                "sys_no": f"{self.cmd_no["PORT"]}",
                "parameters": {
                    "PORT_type": PORT_type,
                    "kind": kind,
                    "geom_name": geom_name,
                    "geom_value": geom_value,
                    "direction": direction,
                },
                "dependencies": [],
                "cac_result": {}
            })
            self.mid_symbols.sT["physics_entity"]["field_excitation"].append({
                "port_no": f"{self.cmd_no["PORT"]}",
                "parameters": {
                    "incoming_func_body": incoming_func_body,
                    "incoming_func_vars": incoming_func_vars,
                    "incoming_opt": incoming_opt,
                },
                "dependencies": [],
                "cac_result": {}
            })
            if norm_set:
                self.mid_symbols.sT["boundaries"]["port"][-1]["parameters"].update(norm_set)

            print(f"[info] 注入波端口 {geom_name} 定义成功")

        elif direction == "NEGATIVE":
            kind = "OPENPORT"
            PORT_type = "OPENPORT"
            self.mid_symbols.sT["boundaries"]["port"].append({
                "PORT_type": PORT_type,
                "sys_no": f"{self.cmd_no["PORT"]}",
                "parameters": {
                    "PORT_type": PORT_type,
                    "kind": kind,
                    "geom_name": geom_name,
                    "geom_value": geom_value,
                    "direction": direction,
                },
                "cac_result": {},
                "dependencies": []
            })
            print(f"[info] 开放端口 {geom_name} 定义成功")
        else:
            raise ValueError(f"[port] 方向不合法：{direction}")

    def _process_emit(self, idx, record):
        entry = record["payload"]
        self.mid_symbols.sT["physics_entities"]["emit_apply"].append({
            "sys_type": "emit_apply",
            "emission_name": entry["model"],
            "parameters": {
                "mobject": entry["mobject"],
                "ex_in": entry["ex_in"]
            },
            "cac_result": {}
        })

    def _process_emission(self, idx, record):
        entry = record["payload"]
        self.mid_symbols.sT["physics_entities"]["emission_model"].append({
            "sys_type": "emission_model",
            "sys_name": entry["process_args"]["process"],
            "parameters": {
                "model_opt": entry["model_opt"],
                "species_opt": entry["species_opt"],
                "number_opt": entry["number_opt"]
            }
        })

    def _process_preset(self, idx, record):

        entry = record["payload"]
        preset_name = entry["preset_name"]
        preset_func_name = entry["func_name"]

        if preset_name == "B1ST":
            component = "0"; func_kind = "Bz"
        elif preset_name == "B2ST":
            component = "1"; func_kind = "Br"
        else:
            raise ValueError(f"[preset] 未支持的预设：{preset_name}")

        preset_func = self.mid_symbols.sT["function"].get(preset_func_name)
        if not preset_func:
            raise ValueError(f"[preset] 未定义函数：{preset_func_name}")

        preset_func_body = self.func_mcl2unipic(preset_func["parameters"]["func_body"])
        preset_func_vars_list = self.funcvars_mcl2unipic(preset_func["cac_result"]["func_vars"])

        preset_func_vars = {k: v for d in preset_func_vars_list for k, v in d.items()}

        params = set(preset_func.get("parameters", {}).get("func_params", []))
        if "T" in params:
            preset_func_kind = "tFunc"
        elif ("Z" in params) and ("R" in params):
            preset_func_kind = "zrFunc"
        else:
            raise ValueError(f"[preset] 函数参数不符合预期，应包含T或(Z,R)：{preset_func_name}")


        self.mid_symbols.sT["physics_entities"]['electromagnetic_field'].append({
            "sys_name": preset_name,
            "parameters": {
                "component": component,
                "func_name": preset_func_name,
                "kind": preset_func_kind,
            },
            "cac_result": {
                "func_body": preset_func_body,
                "func_vars": preset_func_vars,
            },
        })
        
        print(f"[info] PRESET {preset_name}:  {self.mid_symbols.sT["physics_entities"]['electromagnetic_field']}")

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
        if not line or line not in self.mid_symbols.sT["geometry"]["line"]:
            raise ValueError(f"[inductor] 目标线不存在：{line}")

        # 1) 线的几何（Quantity -> UNIPIC 三元组 -> 取首尾两点）
        pts_q = self.mid_symbols.sT["geometry"]["line"][line]                 # [(qx,qy), ...] 仍是 Quantity
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
        self.mid_symbols.sT["physics_entities"]["inductor"].append({
            "sys_name": line,                       # 以线名作为逻辑名（保存时会生成 inductor1/2/...）
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
    
    def _process_timer(self, entry):
        timer_name = entry.get("timer_name") or entry.get("sys_name")
        timer_mode = entry.get("timer_mode") or entry.get("mode")
        timer_type = entry.get("timer_type") or entry.get("time_type")
        timer_opts = list(entry.get("timer_opt", []))

        # 变量展开
        variable_expr_map = {n: f"{v['cac_result']['var_num']} * {v['cac_result']['var_unit']}" for n, v in self.mid_symbols.sT["variable"].items()}
        for i, opt in enumerate(timer_opts):
            timer_opts[i] = variable_expr_map.get(opt, opt)

        self.mid_symbols.sT["global_settings"].setdefault("timers", {})[timer_name] = {
            "timer_name": timer_name,
            "timer_mode": timer_mode,
            "timer_type": timer_type,
            "timer_opts": timer_opts,
        }
    ##################
    # 处理 OBSERVE 命令
    ##################
    def _process_observe(self, idx, record):
        mcl_type = record["command"]
        
        if mcl_type == "OBSERVE FIELD_INTEGRAL":
            self._process_observe_field_integral(idx, record)
        elif mcl_type == "OBSERVE FIELD":
            self._process_observe_field(idx, record)
        elif mcl_type == "OBSERVE FIELD_POWER":
            self._process_observe_field_power(idx, record)
        else:
            raise ValueError(f"[observe] 未知命令：{mcl_type}")


    # 电压降、电流积分
    def _process_observe_field_integral(self, idx, record):
        entry = record["payload"]
        return
        axis_mcl_dir = self.axis_mcl_dir
        geo_c = self.geo_c
        result_dic = {}
        ikind = entry["integral_kind"]
        gname = entry["geom_name"]

        if gname not in self.mid_symbols.sT["geometry"]["line"]:
            raise ValueError(f"[observe_field_integral] 参考对象应为 LINE：{gname}")

        pts = [self._pt_to_unipic(qx, qy, axis_mcl_dir) for (qx, qy) in self.mid_symbols.sT["geometry"]["line"][gname]["para"]]
        (_, r1, z1), (_, r2, z2) = pts[0], pts[-1]   # 这里 r1,z1 等仍是 self.unit_lr 下的数

        if ikind == "E.DL":
            # 电压：按 r 方向（写文件用米）
            org = self._lr_pair_to_m_str(z1, r1)
            end = self._lr_pair_to_m_str(z2, r2)
            result_dic.update({
                "observe_type": "observe_field_integral",
                "kind": "VoltageDgn",
                "sys_name": f"Vin{geo_c.get_voltageDgn_count()}",
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
                "sys_name": f"Iz{geo_c.get_currentDgn_count()}",
                "dir": "r",
                "lowerBounds": lo.replace("0 ", "0.01 "),
                "upperBounds": hi.replace("0 ", "0.01 "),
            })
        else:
            raise ValueError(f"[observe_field_integral] 暂不支持：{ikind}")

        # 选项占位...
        observe_opts = entry.get("observe_opt", [])
        if result_dic:
            self.mid_symbols.sT["diagnostic"].append(result_dic)


    def _process_observe_field(self, idx, record):
        entry = record["payload"]
        return
        result_dic = {}
        field_kind = entry["field_kind"]
        obj = entry["object_kind"]

        if obj not in self.mid_symbols.sT["geometry"]["point"]:
            raise ValueError(f"[observe_field] 参考点不存在：{obj}")

        qx, qy = self.mid_symbols.sT["geometry"]["point"][obj]
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
            "sys_name": name_dic[field_kind],
            "location": loc.replace("0 ", "0.01 "),
        })

        observe_opts = entry.get("observe_opt", [])
        if result_dic:
            self.mid_symbols.sT["diagnostic"].append(result_dic)


    def _process_observe_field_power(self, idx, record):
        entry = record["payload"]
        return
        result_dic = {}
        unit_lr = self.unit_lr
        axis_mcl_dir = self.axis_mcl_dir
        geo_c = self.geo_c

        if entry["power_variable"] != "S.DA":
            raise ValueError(f"[observe_field_power] 仅支持 S.DA")
        obj = entry["object_kind"]
        if obj not in self.mid_symbols.sT["geometry"]["line"]:
            raise ValueError(f"[observe_field_power] 参考对象应为 LINE：{obj}")

        pts = [self._pt_to_unipic(qx, qy, axis_mcl_dir) for (qx, qy) in self.mid_symbols.sT["geometry"]["line"][obj]]
        (_, r1, z1), (_, r2, z2) = pts[0], pts[-1]

        # 统一下界<上界（按 z），并转米
        lo = self._lr_pair_to_m_str(min(z1, z2), r1 if z1 <= z2 else r2)
        hi = self._lr_pair_to_m_str(max(z1, z2), r2 if z2 >= z1 else r1)

        result_dic.update({
            "observe_type": "observe_field_power",
            "kind": "PoyntingDgn",
            "dir": "z",
            "sys_name": f"Poutout{geo_c.get_PoyntingDgn_count()}",
            "lowerBounds": lo.replace("0 ", "0.01 "),
            "upperBounds": hi.replace("0 ", "0.01 "),
        })

        observe_opts = entry.get("observe_opt", [])
        if result_dic:
            self.mid_symbols.sT["diagnostic"].append(result_dic)


   


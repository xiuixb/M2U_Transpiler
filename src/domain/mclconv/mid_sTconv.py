import os
import sys
import traceback
import json
from shapely.geometry import MultiPolygon, Polygon
from pint import Quantity

# 获取项目根目录路径
current_dir = os.path.dirname(os.path.abspath(__file__))
while not os.path.exists(os.path.join(current_dir, ".project_mark")):
    parent_dir = os.path.dirname(current_dir)
    if    parent_dir != current_dir: current_dir = parent_dir
    else: raise FileNotFoundError("未找到项目根目录，检查.project_mark文件")
project_root = current_dir
sys.path.append(project_root)

from src.domain.config.symbolBase import MidSymbolTable
from src.domain.core.geom_cac import GeomCac

class MID_STConv:
    def __init__(self,
                mid_symbols: MidSymbolTable,
                geom_conv: GeomCac
                ):
        self.mid_symbols = mid_symbols
        self.geom_conv = geom_conv

    def load_data(self, mid_symbols: MidSymbolTable):
        self.mid_symbols = mid_symbols

    def mid_sTconv(self,
                       IF_Conv2Void: bool = False,
                       conduct2void_debug: bool = False,
                       emit_debug: bool = False
                       ):
        print("[info] 网格计算......")
        self.calc_mesh_X1X2()
        
        ## 处理area实体的基本参数
        area_entities = self.get_area_entities(
            areas=self.mid_symbols.sT["geometry"]["area"],
            material_assigns=self.mid_symbols.sT["materials"]["material_assign"]
        )
        
        metal_area_entities = self.build_metal_area_entities(
            areas=self.mid_symbols.sT["geometry"]["area"],
            material_assigns=self.mid_symbols.sT["materials"]["material_assign"],
        )
        self.mid_symbols.sT["geometry"]["area_cac_result"]["metal_area_entities"] = metal_area_entities
        self.mid_symbols.sT["geometry"]["area_cac_result"]["pec_connected_components"] = self.build_pec_connected_components(
            metal_area_entities
        )


        ## 金属转真空
        if IF_Conv2Void:
            print("\n[info] 金属转真空......")
            self.mid_symbols.sT["geometry"]["area_cac_result"]["void_area"], self.mid_symbols.sT["geometry"]["area_cac_result"]["other_entity"] = self.geom_conv.conduct2void_utils(
                area_entities=metal_area_entities,
                conduct2void_debug=conduct2void_debug
            )



        emit_apply_idx = None
        for emit_idx, emit in enumerate(self.mid_symbols.sT["physics_entities"]["emit_apply"]):
            if emit["sys_type"] == "emit_apply":
                emit_apply_idx = emit_idx
                break

        if self.mid_symbols.sT["physics_entities"]["emit_apply"]:
            print("[info] 发射参考点计算......")
            self.mid_symbols.sT["geometry"]["area_cac_result"]["void_area"], self.mid_symbols.sT["physics_entities"]["emit_apply"][emit_apply_idx]["cac_result"] = self.geom_conv.get_emits_refPnts(
                self.mid_symbols.sT["physics_entities"]["emit_apply"],
                area_entities,
                self.mid_symbols.sT["geometry"]["area_cac_result"]["void_area"],
                emit_debug
            )

        return self.mid_symbols

    def calc_mesh_X1X2(self):
        """
        根据一轮转换记录的 MARK 列表，汇总得到各轴最小网格尺寸（单位：meter）。
        """
        mesh = self.mid_symbols.sT["mesh"]
        mark_list = mesh.get("mark", [])

        if not mark_list:
            print("\n[info] 未找到 MARK 记录，使用默认网格尺寸 0.001")
            mesh["X1"] = 0.001
            mesh["X2"] = 0.001
            print("[info] mesh X1: 0.001, X2: 0.001")
            return 0.001, 0.001

        axis_min = {}
        for mark in mark_list:
            axis = mark.get("axis")
            size_num = mark.get("size_num")
            size_unit = mark.get("size_unit", "mm")
            if axis not in ("X1", "X2"):
                continue
            size_m = float(Quantity(float(size_num), size_unit).to("meter").magnitude)
            if axis not in axis_min or size_m < axis_min[axis]:
                axis_min[axis] = size_m

        mesh["X1"] = axis_min.get("X1", 0.001)
        mesh["X2"] = axis_min.get("X2", 0.001)
        print(f"[info] mesh X1: {mesh['X1']}, X2: {mesh['X2']}")
        return mesh["X1"], mesh["X2"]
    
    def get_area_entities(self,
                          areas: dict,
                          material_assigns: list
                          ):
        """
        从 sT 面定义和材料绑定中构造几何计算输入。
        """
        area_entities = {}
        for name, entity in areas.items():
            area_entities[name] = {
                "area_type": entity["area_type"],
                "points": entity["cac_result"]["geom_num"]
            }
        for material_assign in material_assigns:
            geom_name = material_assign["geom_name"]
            mat_name = material_assign["mat_name"]
            area_entities[geom_name]["material"] = mat_name
        return area_entities

    def build_metal_area_entities(self, areas: dict, material_assigns: list):
        """
        按材料应用命令的出现顺序重放建模过程：
        - PEC 视为向金属区域并入
        - VOID 视为从金属区域扣除
        最终输出供 conduct2void 使用的 PEC 轮廓集合。
        """
        print("\n[info] 材料绑定......")
        area_polygons = {}
        for name, entity in areas.items():
            print(f"处理区域 {name}")
            points = entity.get("cac_result", {}).get("geom_num")
            if not points or len(points) < 4:
                print(f"[warn] 区域 {name} -> 未定义或点数不足4个，跳过")
                continue
            poly = Polygon(points).buffer(0)
            if poly.is_empty:
                print(f"[warn] 区域 {name} -> 空区域，跳过")
                continue
            area_polygons[name] = poly

        ordered_assigns = sorted(
            material_assigns,
            key=lambda item: (
                item.get("lineno") if item.get("lineno") is not None else float("inf"),
                item.get("geom_name", ""),
            ),
        )

        print("\n[info] 金属区域建模......")
        metal_geometry = None
        for material_assign in ordered_assigns:
            geom_name = material_assign.get("geom_name")
            mat_name = material_assign.get("mat_name")
            lineno = material_assign.get("lineno")
            lineno_text = f"@ Line {lineno}" if lineno is not None else "@ Line ?"
            poly = area_polygons.get(geom_name)
            if poly is None:
                print(f"[warn] {lineno_text}: {mat_name} {geom_name} -> 未找到可参与建模的 AREA")
                continue

            if mat_name == "PEC":
                metal_geometry = poly if metal_geometry is None else metal_geometry.union(poly)
                print(f"[info] {lineno_text}: {geom_name} -> {mat_name} (并入金属区域)")
            elif mat_name == "VOID":
                if metal_geometry is not None:
                    metal_geometry = metal_geometry.difference(poly)
                    print(f"[info] {lineno_text}: {geom_name} -> {mat_name} (从金属区域扣除)")
                else:
                    print(f"[info] {lineno_text}: {geom_name} -> {mat_name} (当前无金属区域，跳过扣除)")
            else:
                print(f"[warn] {lineno_text}: {geom_name} -> {mat_name} (未支持的材料类型，跳过)")

            if metal_geometry is not None:
                metal_geometry = metal_geometry.buffer(0)
                if metal_geometry.is_empty:
                    metal_geometry = None

        if metal_geometry is None:
            return {}

        polygons = [metal_geometry] if isinstance(metal_geometry, Polygon) else list(metal_geometry.geoms)
        metal_area_entities = {}
        for idx, poly in enumerate(polygons, start=1):
            if poly.is_empty:
                continue
            metal_area_entities[f"MODELED_PEC_{idx}"] = {
                "area_type": "MODELED",
                "points": [(float(x), float(y)) for x, y in poly.exterior.coords],
                "material": "PEC",
            }

        return metal_area_entities

    def build_pec_connected_components(self, metal_area_entities: dict):
        """
        将建模后的金属区域整理为前端/调试更易读的连通域点集格式：
        {
          "PEC_1": {"points": [[x, y], ...]},
          ...
        }
        """
        pec_components = {}
        for idx, entity in enumerate(metal_area_entities.values(), start=1):
            points = entity.get("points", [])
            pec_components[f"PEC_{idx}"] = {
                "points": [[float(x), float(y)] for x, y in points]
            }

        if pec_components:
            print("[info] 建模得到的 PEC 连通域:")
            print(self._format_pec_components_for_log(pec_components))
        else:
            print("[info] 建模得到的 PEC 连通域: {}")

        return pec_components

    def _format_pec_components_for_log(self, pec_components: dict) -> str:
        """仅用于终端打印：点坐标显示为 (x, y)，内部存储仍保持 JSON 友好的列表结构。"""
        lines = ["{"]
        items = list(pec_components.items())
        for idx, (name, payload) in enumerate(items):
            points = payload.get("points", [])
            point_str = ", ".join(f"({x}, {y})" for x, y in points)
            suffix = "," if idx < len(items) - 1 else ""
            lines.append(f'  "{name}": {{"points": [{point_str}]}}{suffix}')
        lines.append("}")
        return "\n".join(lines)
    

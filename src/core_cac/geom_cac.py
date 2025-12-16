################
# geom_conv.py
################
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

from shapely.geometry import Polygon, Point, LineString, MultiPolygon
from shapely.ops import unary_union
from typing import Tuple
from src.core_cac.get_geometry_results import GeomUtils

geomUtils = GeomUtils()

class GeomCac:

    @classmethod
    def conduct2void_utils(cls, area_entities, conduct2void_debug = False)->Tuple[dict, dict]:
        """
        主要逻辑：根据金属区域计算出真空区域点集
        """
        geom_utils = GeomUtils()
        void_area, geom_other_entity = geom_utils.Cond2Void(area_entities)
        if conduct2void_debug:
            print("area_entities:\n", area_entities)
            print(f"几何体结果:\n {void_area}")
            print(f"其他几何体:\n {geom_other_entity}")

        return void_area, geom_other_entity

    @classmethod
    def convert_to_xy_pairs(cls, input_str):
        num_list = list(map(float, input_str[1:-1].split()))
        return [
            (num_list[i+2], num_list[i+1]) 
            for i in range(0, len(num_list), 3)
        ]

    @classmethod
    def is_outside_with_endpoint_touch_ok(cls, line, polygon_or_multi, tol=1e-9):
        """
        判断线段是否在 polygon/MultiPolygon 外部，允许仅端点接触边界
        - 完全在外部 → True
        - 仅端点接触 → True
        - 有部分线段重合或穿入 → False
        """
        if polygon_or_multi is None or polygon_or_multi.is_empty:
            return True

        # 统一为迭代器
        if isinstance(polygon_or_multi, Polygon):
            polys = [polygon_or_multi]
        elif isinstance(polygon_or_multi, MultiPolygon):
            polys = list(polygon_or_multi.geoms)
        else:
            raise TypeError(f"Unsupported geometry type: {polygon_or_multi.geom_type}")

        for poly in polys:
            if line.disjoint(poly):
                continue  # 完全不相交，跳过这个子区域

            inter = line.intersection(poly)

            # 仅允许交集是端点
            if inter.geom_type == "Point":
                if inter.equals(Point(line.coords[0])) or inter.equals(Point(line.coords[-1])):
                    continue  # 合法，检查下一个子区域
                else:
                    return False
            else:
                # 多点、线、面交集，都算相交
                return False

        # 如果所有子区域都没触发“相交”条件
        return True
    @classmethod
    def get_emit_refPnts(cls, mobject, ex_in, geom, void_area, emit_debug = False, tol=1e-9):
        """
        现有逻辑：
        1. 根据阴极几何体名从all_cmds中获取阴极点集
        2. 读取ex_in参数找到最终排除区域
        3. 遍历mobject_pnts中的每两个点(一条边)，判断是否在排除区域外，如果存在则返回线的中点

        改为：
        1. 根据阴极几何体名从all_cmds中获取阴极点集和真空点集
        2. 读取ex_in参数EXCLUDE参数找到最终排除区域
        3. 读取ex_in参数INCLUDE参数修改真空点集，修改阴极点集
        4. 遍历阴极点集mobject_pnts中的每两个点(一条边)，判断是否在真空点集边界，且在排除区域的每个连通区域外，如果是则将线的中点字符串存入结果数组中
        """
        results = {}
        results["emit"] = {}
        results["emit_selection_refPnts"] = []
        if emit_debug:
            print(f"       原始真空点集:\n{' '*7}", void_area["pnts"])
        void_poly = Polygon([tuple(p) for p in void_area["pnts"]])
        void_boundary = void_poly.boundary
        refPnts = []
        refPnt = ""

        # 1. 分割字符串为数字列表
        #print(f"area_entities: {area_entities}")
        mobject_pnts = geom["areas"][mobject]['points']
        results["emit"]["mobject_pnts"] = mobject_pnts
        if emit_debug:
            print(f"\n       设置发射参考点: {mobject} \n{' '*7}ex_in: {ex_in}")
            print(f"       mobject:\n{' '*7}",mobject_pnts)
        p1 = ()
        p2 = ()
        # 定义最终排除区域
        final_limit_area = None
        inserted_points = set()
        if len(ex_in) >= 2:
            # 示例：['EXCLUDE', 'NO_EMISSION', 'INCLUDE', 'EMISSION']
            results["emit"]["ex_in"] = []

            for i in range(0, len(ex_in), 2):
                ex_in_kind = ex_in[i]
                ex_in_area_name = ex_in[i+1]
                if emit_debug:
                    print(f"       获取发射区域参数: {ex_in_kind} {ex_in_area_name}")

                if ex_in_kind in ("EXCLUDE", "INCLUDE"):
                    ex_in_area_pnts = geom["areas"][ex_in_area_name]['points']
                    results["emit"]["ex_in"].append({
                        "ex_in_area_name": ex_in_area_name,
                        "ex_in_kind": ex_in_kind,
                        "pnts": ex_in_area_pnts
                    })
                    
                    if emit_debug:
                        print(f"       ex_in: {ex_in_kind}\n       ", mobject_pnts)
                    ex_in_area = Polygon(ex_in_area_pnts)
                    ex_in_areas = [ex_in_area_pnts]
                    if ex_in_kind == 'EXCLUDE':
                        mobject_pnts, inserted_points1 = geomUtils.void2coord(mobject_pnts, ex_in_areas)
                        inserted_points.update(inserted_points1)
                        # 如果是排除区域，与最终排除区域合并
                        if final_limit_area is None:
                            final_limit_area = ex_in_area
                        else:
                            final_limit_area = final_limit_area.union(ex_in_area)
                    elif ex_in_kind == 'INCLUDE':
                        # 如果是包含区域，与最终排除区域取差
                        mobject_pnts, inserted_points2 = geomUtils.void2coord(mobject_pnts, ex_in_areas)
                        inserted_points.update(inserted_points2)
                        if final_limit_area is None:
                            raise ValueError("包含区域必须在排除区域之后定义")
                        else:
                            final_limit_area = final_limit_area.difference(ex_in_area)
        
        # 给真空点集添加插入点
        """
        遍历判断应该插到哪个边上
        """
        void_points = [tuple(p) for p in void_area["pnts"]]
        if emit_debug:
            print(f"       原始真空点集 有 {len(void_points)} 个点")

        edges = list(zip(void_points, void_points[1:]))

        new_void = []

        if emit_debug:
            print(f"       要插入的断点有 {inserted_points}")


        for (p1, p2) in edges:
            line = LineString([p1, p2])
            # 当前边的插入点（按投影参数排序）
            pts_on_edge = []

            for p in inserted_points:
                pt = Point(p)
                if line.distance(pt) < tol:  # 点在边上
                    t = line.project(pt)
                    pts_on_edge.append((t, p))

            # 边上的点按位置排序
            pts_on_edge.sort(key=lambda x: x[0])

            # 添加起点 + 插入点
            new_void.append(p1)
            for _, p in pts_on_edge:
                if p not in new_void:
                    new_void.append(p)
        
            # 去掉重复点
            cleaned = []
            seen = set()
            for pt in new_void:
                if cleaned and pt == cleaned[-1]:
                    continue
                if pt in seen:
                    continue
                cleaned.append(pt)
                seen.add(pt)

            # 闭合
            if cleaned and cleaned[0] != cleaned[-1]:
                cleaned.append(cleaned[0])

            void_area["pnts"] = cleaned

        # 计算一下新的真空点集有多少个点
        print(f"       新的真空点集 有 {len(cleaned)} 个点")
        if emit_debug:
            print(f"       新的真空点集:\n{' '*7}",cleaned)

        
        # 遍历mobject_pnts中的每两个点(一条边)
        for i in range(len(mobject_pnts)-1):
            p1 = mobject_pnts[i]
            p2 = mobject_pnts[i+1]
            line = LineString([p1, p2])
            
            # 判断整条线是否在区域外
            if emit_debug:
                print(f"       判断整条线是否在区域外: {line}")
                print(f"       排除区域：{final_limit_area}")

            # 条件 A：必须与真空边界重合
            on_void_boundary = void_boundary.intersection(line).length >= line.length - 1e-9
            # 条件 B：必须在排除区外（允许端点接触）
            outside_exclude = (final_limit_area is None or cls.is_outside_with_endpoint_touch_ok(line, final_limit_area))
            
            if on_void_boundary and outside_exclude:
                # 如果线完全在区域外，计算中点
                midpoint = [(a + b) / 2 for a, b in zip(p1, p2)]
                x坐标 = round(midpoint[0], 10)
                y坐标 = round(midpoint[1], 10)
                refPnt = f"[0.0 {y坐标} {x坐标}]"
                refPnts.append(refPnt)
                if emit_debug:
                    print(f"[info] 添加发射参考点: {refPnt}")
        
        print("       emit refPnts = ",refPnts)
        results["emit_selection_refPnts"] = refPnts
        return void_area, results

    @classmethod
    def get_emits_refPnts(cls, emits, geom, void_area, emit_debug = False):
        """
        主要逻辑：从emits中计算发射参考点，并给几何点集打断点
        """
        results = {}
        for emit in emits:
            #print(f"[info] 处理发射: \n{emit}")
            emit_type = emit['kind']
            if emit_type == 'emission':
                pass
            elif emit_type == 'emit':
                mobject = emit['mobject']
                if 'model' in emit:
                    emit_kind = emit['model']
                if 'ex_in' in emit:
                    ex_in = emit['ex_in']
                else:
                    ex_in = []
                void_area, results = cls.get_emit_refPnts(mobject, ex_in, geom, void_area, emit_debug)
        
        return void_area, results


import numpy as np
from sympy.printing.latex import other_symbols
from typing import Iterable, List, Tuple
import pint

ureg = pint.UnitRegistry()

#################
# 几何算法模块
#################


class GeomUtils:
    from shapely.geometry import Polygon, MultiPolygon, LineString, Point, MultiPoint, MultiLineString
    from shapely.ops import unary_union

    def __init__(self):
        self.geom_conductor_entities = []
        self.geom_void_entities = []
        self.geom_other_entities = []

    def get_entities_from_list(self, entities_list):
        for name, entity in entities_list.items():
            pnts = entity['points']
            if "material" in entity:
                material = entity["material"]
                # print("       Material:", material)
                if material == "PEC":
                    self.geom_conductor_entities.append(pnts)
                elif material == "VOID":
                    self.geom_void_entities.append(pnts)
                else:
                    raise ValueError(f"不支持的材料类型:{material}")
            else:
                self.geom_other_entities.append(pnts)
        return self.geom_conductor_entities, self.geom_void_entities

    def geom_compute_envelopes(self, contour):
        """
        计算上下包络线（包含凹部处理）
        :param contour: 输入线框列表，每个线框为[(x1,z1), (x2,z2)...]
        :return: (upper_envelope, lower_envelope)
        """
        # print("Computing envelopes...",contour)
        # 收集所有顶点
        all_points = [p for p in contour]
        # print("All points...",all_points)
        # 按X主序、Z辅序排序
        sorted_points = sorted(all_points, key=lambda p: (p[0], -p[1]))
        
        # 计算上包络线（单调链变体）
        upper_part = []
        for p in sorted_points:
            while len(upper_part) >= 2:
                # 检查是否形成凹部
                v1 = (upper_part[-1][0] - upper_part[-2][0], upper_part[-1][1] - upper_part[-2][1])
                v2 = (p[0] - upper_part[-1][0], p[1] - upper_part[-1][1])
                cross = v1[0]*v2[1] - v1[1]*v2[0]
                if cross < 0:  # 保留右转点
                    break
                upper_part.pop()
            upper_part.append(p)
        
        # 计算下包络线（单调链变体）
        lower_part = []
        for p in reversed(sorted_points):
            while len(lower_part) >= 2:
                v1 = (lower_part[-1][0] - lower_part[-2][0], lower_part[-1][1] - lower_part[-2][1])
                v2 = (p[0] - lower_part[-1][0], p[1] - lower_part[-1][1])
                cross = v1[0]*v2[1] - v1[1]*v2[0]
                if cross < 0:  # 保留左转点
                    break
                lower_part.pop()
            lower_part.append(p)
        
        return upper_part, lower_part


    def geom_polygon_subtraction(self, main_poly, other_polys):
        """
        计算主多边形减去其他多边形的差集，返回Polygon对象
        
        参数:
            main_poly: 主多边形的顶点列表 [[x1,y1], [x2,y2], ...] 或 Polygon对象
            other_polys: 其他多边形的顶点列表集合 [ [[x1,y1],...], ... ] 或 Polygon对象列表
            
        返回:
            Shapely Polygon对象（可能带孔洞）
            如果结果为空则返回None
        """
        # 转换输入为Polygon对象（如果尚未转换）
        main = main_poly if isinstance(main_poly, self.Polygon) else self.Polygon(main_poly)
        others = [p if isinstance(p, self.Polygon) else self.Polygon(p) for p in other_polys]
        
        # 合并所有待减去的多边形
        for other in others:
            main = main.difference(other)
        
        result = main.buffer(0)  # 缓冲0，去除孔洞

        # 处理返回结果
        if result.is_empty:
            return None
        elif result.geom_type == 'Polygon':
            return result
        elif result.geom_type == 'MultiPolygon':
            # 返回面积最大的子多边形            
            return max(result.geoms, key=lambda p: p.area)       # type: ignore
        else:
            return None

    def geom_vertical_split(self, polygons):
        """
        上下分割：
          - 先过滤掉完全在 X<=0 的多边形
          - 上部：仍以"更高的 max_y / 质心 y"作为核心并尽量连通（合并输出单一外边界）
          - 下部：不强制连通，保留为多个独立多边形（列表返回）
        返回:
            (upper_contour, lower_contours_list)
            upper_contour: list[(x,y)] 或 []（若无上部）
            lower_contours_list: list[list[(x,y)]]（可能为空）
        """
        # 过滤掉完全在 X<=0 的多边形
        filtered_polys = []
        for poly in polygons:
            # poly 为 [(x,y), ...]，判断该多边形是否全部 x<=0
            xs = [pt[0] for pt in poly]
            if max(xs) <= 0:
                continue
            filtered_polys.append(poly)

        if not filtered_polys:
            return [], []  # 全部在 X<=0，整体忽略

        # 计算特征
        features = []
        for poly in filtered_polys:
            p = self.Polygon(poly)
            ys = [pt[1] for pt in poly]
            features.append({
                'poly': p,
                'centroid_y': p.centroid.y,
                'max_y': max(ys),
                'min_y': min(ys)
            })

        # 选上/下候选
        upper_candidate = max(features, key=lambda x: (x['max_y'], x['centroid_y']))
        lower_candidate = min(features, key=lambda x: (x['min_y'], x['centroid_y']))

        # 动态分组：上部尽量连通；下部不要求连通（直接收集）
        upper_group = [upper_candidate['poly']]
        lower_group = [lower_candidate['poly']]
        remaining = [f for f in features if f not in [upper_candidate, lower_candidate]]

        for f in remaining:
            # 先尝试加入上部：要求 union 后仍是单一 Polygon
            test_upper = self.unary_union(upper_group + [f['poly']])
            if test_upper.geom_type == 'Polygon':
                upper_group.append(f['poly'])
            else:
                # 归入下部（不要求连通）
                lower_group.append(f['poly'])

        # 输出上部：合并为单一 Polygon 外边界；若非单一，则取联合的外边界（最大壳）
        upper_union = self.unary_union(upper_group)
        if upper_union.is_empty:
            upper_contour = []
        elif upper_union.geom_type == 'Polygon':
            upper_contour = list(upper_union.exterior.coords)    # type: ignore
        else:  # MultiPolygon：取面积最大者的外边界
            largest = max(upper_union.geoms, key=lambda p: p.area)    # type: ignore
            upper_contour = list(largest.exterior.coords)

        # 输出下部：保留每个 Polygon 的外边界（不强制合并）
        lower_contours = []
        for p in lower_group:
            if p.is_empty:
                continue
            if p.geom_type == 'Polygon':
                lower_contours.append(list(p.exterior.coords))
            elif p.geom_type == 'MultiPolygon':
                for sub in p.geoms:
                    lower_contours.append(list(sub.exterior.coords))

        return upper_contour, lower_contours

    def process_result_contour(self, result_contour):
        """
        处理结果轮廓：
        1. 找到x最大且y最小的点
        2. 找到x最小且y最小的点
        3. 将轮廓分为两部分，取y均值较小的部分
        4. 与x=xmin、x=xmax、y=0围成的区域合并
        :param result_contour: 结果轮廓点集
        :return: 处理后的新轮廓点集
        """
        # 转换为numpy数组方便处理
        points = np.array(result_contour)
        
        # 1. 找到x最大且y最小的点
        max_x = np.max(points[:, 0])
        candidates = points[points[:, 0] == max_x]
        max_x_min_y_point = candidates[np.argmin(candidates[:, 1])]
        
        # 2. 找到x最小且y最小的点
        min_x = np.min(points[:, 0])
        candidates = points[points[:, 0] == min_x]
        min_x_min_y_point = candidates[np.argmin(candidates[:, 1])]
        
        # 3. 将轮廓分为两部分（以这两个点为分割点）
        # 找到这两个点在轮廓中的索引
        idx_max = np.where((points[:, 0] == max_x_min_y_point[0]) & 
                        (points[:, 1] == max_x_min_y_point[1]))[0][0]
        idx_min = np.where((points[:, 0] == min_x_min_y_point[0]) & 
                        (points[:, 1] == min_x_min_y_point[1]))[0][0]
        
        # 确保idx_min在前
        if idx_min > idx_max:
            idx_min, idx_max = idx_max, idx_min
        
        # 分割轮廓为两部分
        part1 = points[idx_min:idx_max+1]
        part2 = np.vstack([points[idx_max:], points[:idx_min+1]])
        
        # 计算两部分的y均值，选择较小的部分
        if np.mean(part1[:, 1]) < np.mean(part2[:, 1]):
            selected_part = part1
        else:
            selected_part = part2
        
        # 4. 与x=xmin、x=xmax、y=0围成的区域合并
        new_points = [
            [min_x, 0],
            [max_x, 0]
        ]
        
        # 合并点集（注意顺序）
        new_contour = np.vstack([
            new_points,
            selected_part
        ])
        
        # 确保闭合
        if not np.array_equal(new_contour[0], new_contour[-1]):
            new_contour = np.vstack([new_contour, new_contour[0]])
        
        return new_contour

    def get_union_contour_result(self, result_contour, void_contours):
        
        if not void_contours:
            return result_contour
        
        current_union = self.Polygon(result_contour)
        for contour in void_contours:
            poly = self.Polygon(contour)
            current_union = current_union.union(poly)
        
        return list(current_union.exterior.coords)    # type: ignore

    def void2coord(self, void_points, conductor_polys, tol=1e-6):
        """
        将导体点集的边界端点/交点强制插入到真空区域的边界点集上

        参数:
            void_points: [(x,y),...] 真空区域点集（闭合）
            conductor_polys: [[(x,y),...], [(x,y),...]] 导体点集列表
            tol: 容差

        返回:
            new_void_points: 插入断点后的真空区域点集
        """
        
        #print(f"void2coord: 输入参数: \n{void_points} \nconductor_polys:\n{conductor_polys} \ntol={tol}")


        new_void_points = []
        inserted_points = set()

        # 遍历真空区域的边（两点一条边）
        edges = list(zip(void_points, void_points[1:]))
        for edge_start, edge_end in edges:
            edge_line = self.LineString([edge_start, edge_end])

            # 每条边至少保留起点、终点
            edge_points = [(0.0, edge_start), (edge_line.length, edge_end)]

            # 遍历所有导体的边
            for cond in conductor_polys:
                cond_edges = list(zip(cond, cond[1:] + [cond[0]]))
                for p1, p2 in cond_edges:
                    cond_edge = self.LineString([p1, p2])

                    # 1. 导体端点在真空边上 → 插入
                    for pt in [p1, p2]:
                        if edge_line.distance(self.Point(pt)) < tol:
                            t = edge_line.project(self.Point(pt))
                            edge_points.append((t, (pt[0], pt[1])))
                            inserted_points.add((pt[0], pt[1]))

                    # 2. 导体边和真空边有交点 → 插入
                    inter = edge_line.intersection(cond_edge)
                    if not inter.is_empty:
                        if inter.geom_type == 'Point':
                            pt = (inter.x, inter.y)        # type: ignore
                            t = edge_line.project(inter)   # type: ignore
                            edge_points.append((t, pt))
                            inserted_points.add(pt)
                        elif inter.geom_type == 'MultiPoint':
                            for p in inter:                # type: ignore
                                pt = (p.x, p.y)
                                t = edge_line.project(p)
                                edge_points.append((t, pt))
                                inserted_points.add(pt)

            # 按边方向排序，去重
            edge_points = sorted(edge_points, key=lambda x: x[0])
            seen = set()
            ordered_pts = []
            for _, pt in edge_points:
                if pt not in seen:
                    ordered_pts.append(pt)
                    seen.add(pt)

            # 拼接结果
            new_void_points.extend(ordered_pts)
        
        # print(f"new_void_points:\n {new_void_points}")

        cleaned_void_points = []
        for pt in new_void_points:
            if not cleaned_void_points or pt != cleaned_void_points[-1]:
                cleaned_void_points.append(pt)

        # 闭合
        if cleaned_void_points and cleaned_void_points[0] != cleaned_void_points[-1]:
            cleaned_void_points.append(cleaned_void_points[0])

        return cleaned_void_points, inserted_points


    def Cond2Void(self, entities_list)->Tuple[dict, dict]:
        """
        conductor_contours =[
            [(0.0, 0.0), (0.0, 11.8), (12.0, 11.8), (12.0, 0.0), (0.0, 0.0)],
            [(12.0, 11.4), (12.0, 11.8), (17.0, 11.8), (17.0, 11.4), (12.0, 11.4)],
            [(0.0, 22.0), (22.0, 22.0), (30.0, 13.0), (35.0, 13.0), (35.0, 19.0), (43.7, 19.0), (43.7, 13.0), (47.0, 13.0), (47.0, 25.0), (0.0, 25.0), (0.0, 22.0)],
            [(47.0, 14.2), (48.0, 14.2), (50.2, 13.0), (52.0, 13.0), (54.2, 14.2), (55.2, 14.2), (57.4, 13.0), (59.2, 13.0), (61.4, 14.2), (62.4, 14.2), (64.6, 13.0), (66.4, 13.0), (68.6, 14.2), (69.6, 14.2), (71.8, 13.0), (73.6, 13.0), (75.8, 14.2), (76.8, 14.2), (79.0, 13.0), (80.8, 13.0), (83.0, 14.2), (84.0, 14.2), (86.2, 13.0), (88.0, 13.0), (90.2, 14.2), (91.2, 14.2), (93.4, 13.0), (95.2, 13.0), (97.4, 14.2), (98.4, 14.2), (100.6, 13.0), (102.4, 13.0), (104.6, 14.2), (105.6, 14.2), (107.8, 13.0), (109.6, 13.0), (111.8, 14.2), (112.8, 14.2), (112.8, 13.0), (113.8, 13.0), (113.8, 16.4), (115.1, 16.4), (115.1, 18.8), (47.0, 18.8), (47.0, 14.2)],
            [(115.1, 12.8), (115.1, 18.8), (140.1, 18.8), (140.1, 12.8), (115.1, 12.8)],
            [(0.0, 0.0), (0.0, 12.3), (16.95, 12.3), (16.95, 0.0), (0.0, 0.0)]
        ]
        """
        # print(f"conduct2void start:\n{entities_list}\n")

        conductor_contours, void_contours = self.get_entities_from_list(entities_list)

        # print(f"[info] conductor_contours:\n{conductor_contours}\n")
        
        # 兜底：如果所有导体的最大 X 都 <= 0，直接忽略
        if not conductor_contours or max(max(p[0] for p in poly) for poly in conductor_contours) <= 0:
            result_entity = {"kind": "polygon", "pnts": [], "material": "VOID"}
            return result_entity, {}

        # 改：上下分割 → 上部单一外轮廓 + 下部保留所有不连通外轮廓
        upper_contour, lower_contours = self.geom_vertical_split(conductor_contours)

        # 如果没有上部，直接返回空（或根据需求返回下部合并结果）
        if not upper_contour:
            result_entity = {"kind": "polygon", "pnts": [], "material": "VOID"}
            return result_entity, {}

        # 计算"上包络"
        upper_parts, _ = self.geom_compute_envelopes(upper_contour)

        # 搭"上包络 + y=0"外壳
        x_max = max(p[0] for p in upper_parts)
        x_min = min(p[0] for p in upper_parts)
        area_contour = [(x_min, 0.0), *upper_parts, (x_max, 0.0)]
        print('[info] "上包络 + y=0"外壳:')
        print({"OUTER_SHELL": {"points": area_contour}})
        all_area = self.Polygon(area_contour)

        # 对"下半部分的所有非连通区域"和"上半部分区域"都做差集
        current = all_area
        
        # 先减去上半部分
        if upper_contour:
            current = current.difference(self.Polygon(upper_contour))
        
        # 再减去下半部分的所有非连通区域
        for low in lower_contours:
            current = current.difference(self.Polygon(low))

        # 清理并取外轮廓
        current = current.buffer(0)
        if current.is_empty:
            void_contour = []
        elif current.geom_type == 'Polygon':
            void_contour = list(current.exterior.coords)
        else:  # MultiPolygon：取面积最大者
            largest = max(current.geoms, key=lambda p: p.area)       # type: ignore
            void_contour = list(largest.exterior.coords)
        

        other_entities = {}
        # for other_entity in self.geom_other_entities:
        #    other_entities[other_entity["material"]] = [(pt[0], pt[1]) for pt in other_entity["pnts"]]


        #print(f"void_contour:\n{void_contour}\n")

        void_list, inserted_points = self.void2coord(void_contour, conductor_contours)
        

        #print(f"void_list:\n{void_list}\n")

        void_entity = {
            "kind": "polygon",
            "pnts": void_list,
            "material": "VOID"
        }


        return void_entity, other_entities
    
    def split_emit_interface(self,
                         void_points,
                         cathode_points,
                         exclude_polys,          # [[(x,y),...], ...]
                         include_polys=None,     # [[(x,y),...], ...] 或 None
                         tol=1e-9,
                         debug=False):
        """
        目的：仅在“阴极-真空公共边界”上，按（EXCLUDE 合并 - INCLUDE 合并）得到的最终排除区域的边界
            产生的断点，去打断真空与阴极的轮廓（两个边界都插入相同断点）。

        参数:
            void_points     : [(x,y),...]  真空区域闭合点集
            cathode_points  : [(x,y),...]  阴极区域闭合点集
            exclude_polys   : [poly_pts,...]  需要排除的多边形集合
            include_polys   : [poly_pts,...]  需要包含(从排除里扣除)的多边形集合
            tol             : 距离容差
            debug           : 是否打印过程日志

        返回:
            new_void_points, new_cathode_points, split_candidates
        """

        # -------- 预处理/闭合 --------
        vp = list(map(tuple, void_points))
        cp = list(map(tuple, cathode_points))
        if not vp or not cp:
            return vp, cp, []

        if vp[0] != vp[-1]:
            vp = vp + [vp[0]]
        if cp[0] != cp[-1]:
            cp = cp + [cp[0]]

        if debug:
            print(f"[INIT] mobject_pnts(len={len(cp)}): {cp[:10]} ...")
            print(f"[INIT] void_pnts   (len={len(vp)}): {vp[:10]} ...")

        void_boundary    = self.LineString(vp)
        cathode_boundary = self.LineString(cp)

        # -------- 计算最终排除区域： union(EXCLUDE) - union(INCLUDE) --------
        def _to_valid_poly(poly_pts):
            poly = self.Polygon(poly_pts if poly_pts[0] == poly_pts[-1] else poly_pts + [poly_pts[0]])
            return poly if poly.is_valid else poly.buffer(0)

        ex_geoms = [_to_valid_poly(p) for p in (exclude_polys or [])]
        in_geoms = [_to_valid_poly(p) for p in (include_polys or [])]

        final_exclude = None
        if ex_geoms:
            final_exclude = self.unary_union(ex_geoms)
        if in_geoms and final_exclude is not None:
            final_exclude = final_exclude.difference(self.unary_union(in_geoms))

        # 没有排除信息时，不需要任何打断
        if not final_exclude or final_exclude.is_empty:
            return vp, cp, []

        # -------- 只在“阴极-真空公共边界”上打断：候选点收集 + 过滤 --------
        split_candidates = []

        def _collect_endpoints_from_lines(geom):
            if geom.is_empty:
                return
            if isinstance(geom, self.LineString):
                coords = list(geom.coords)
                if coords:
                    split_candidates.extend([tuple(coords[0]), tuple(coords[-1])])
            elif isinstance(geom, self.MultiLineString):
                for g in geom.geoms:
                    coords = list(g.coords)
                    if coords:
                        split_candidates.extend([tuple(coords[0]), tuple(coords[-1])])

        # 候选点来源：
        # 1) final_exclude 的边界端点
        bnd = final_exclude.boundary
        _collect_endpoints_from_lines(bnd)

        # 2) final_exclude 边界 与 阴极/真空边界的交点
        def _collect_intersections(bnd, base):
            inter = bnd.intersection(base)
            if inter.is_empty:
                return
            if isinstance(inter, self.Point):
                split_candidates.append((inter.x, inter.y))
            elif isinstance(inter, self.MultiPoint):
                for p in inter.geoms:
                    split_candidates.append((p.x, p.y))
            elif isinstance(inter, (self.LineString, self.MultiLineString)):
                _collect_endpoints_from_lines(inter)

        _collect_intersections(bnd, cathode_boundary)
        _collect_intersections(bnd, void_boundary)

        # 3) 仅保留“位于阴极-真空公共边界附近”的点（避免打断到其它真空边）
        uniq = []
        seen = set()
        for P in split_candidates:
            key = (round(P[0], 12), round(P[1], 12))
            if key in seen:
                continue
            if void_boundary.distance(self.Point(P)) <= tol and cathode_boundary.distance(self.Point(P)) <= tol:
                uniq.append(P)
                seen.add(key)
        split_candidates = uniq

        if debug:
            print(f"[SPLIT] split_candidates_on_interface(len={len(split_candidates)}): {split_candidates[:16]} ...")
            print(f"[STEP] BEFORE INSERT  mobject_pnts(len={len(cp)}): {cp[:14]} ...")
            print(f"[STEP] BEFORE INSERT  void_pnts   (len={len(vp)}): {vp[:14]} ...")

        # -------- 仅在“接口边”上插入候选点 --------
        def _edge_on_interface(a, b):
            seg = self.LineString([a, b])
            return void_boundary.distance(seg) <= tol and cathode_boundary.distance(seg) <= tol

        def _insert_points_on_interface(base_pts):
            out = []
            for a, b in zip(base_pts, base_pts[1:]):
                seg = self.LineString([a, b])
                if _edge_on_interface(a, b):
                    locs = []
                    for P in split_candidates:
                        pnt = self.Point(P)
                        if seg.distance(pnt) <= tol:
                            s = seg.project(pnt)
                            if -tol <= s <= seg.length + tol:
                                locs.append((s, P))
                    locs.sort(key=lambda x: x[0])
                    if not out or out[-1] != a:
                        out.append(a)
                    for _, P in locs:
                        if out[-1] != P:
                            out.append(P)
                    if out[-1] != b:
                        out.append(b)
                else:
                    if not out or out[-1] != a:
                        out.append(a)
                    if out[-1] != b:
                        out.append(b)
            if out and out[0] != out[-1]:
                out.append(out[0])
            return out

        # 分别对阴极/真空轮廓执行“接口插点”
        new_cp = _insert_points_on_interface(cp)
        new_vp = _insert_points_on_interface(vp)

        if debug:
            print(f"[STEP] AFTER  INSERT  mobject_pnts(len={len(new_cp)}): {new_cp[:18]} ...")
            print(f"[STEP] AFTER  INSERT  void_pnts   (len={len(new_vp)}): {new_vp[:18]} ...")

        return new_vp, new_cp, split_candidates
    

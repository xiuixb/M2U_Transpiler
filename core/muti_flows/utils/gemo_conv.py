#################
# 几何算法模块
#################

import numpy as np
from matplotlib import path as mpath
from shapely.geometry import Polygon, MultiPolygon, LineString
from shapely.ops import unary_union
import matplotlib.pyplot as plt

def compute_envelopes(contour):
    """
    计算上下包络线（包含凹部处理）
    :param contours: 输入线框列表，每个线框为[(x1,z1), (x2,z2)...]
    :return: (upper_envelope, lower_envelope)
    """
    print("Computing envelopes...",contour)
    # 收集所有顶点
    all_points = [p for p in contour]
    print("All points...",all_points)
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

def build_closed_region(contours):
    """
    构建封闭区域（图示需求）
    :contours: 输入线框列表
    :return: 闭合顶点列表
    """
    # 获取最大X值
    x_max = max(p[0] for contour in contours for p in contour)
    
    # 计算包络线
    upper, lower = compute_envelopes(contours)
    
    # 构造闭合路径
    path = []
    
    # 上包络线（从原点开始）
    current_x = 0.0
    for p in upper:
        if p[0] >= current_x:
            path.append(p)
            current_x = p[0]
    
    # 右边界垂直线
    if path[-1][0] < x_max:
        path.append((x_max, path[-1][1]))
    
    # 下包络线（从右到左）
    lower_path = []
    current_x = x_max
    for p in reversed(lower):
        if p[0] <= current_x:
            lower_path.append(p)
            current_x = p[0]
    
    # 合并路径
    full_path = [(0.0, 0.0)] + path + [(x_max, 0.0)] + lower_path[::-1]
    
    # 闭合处理
    if full_path[-1] != (0.0, 0.0):
        full_path.append((0.0, 0.0))
    
    return full_path


def contours_union(contours):
    """
    计算多个多边形的并集顶点（假设所有多边形相互相交或相邻）
    :param contours: [ [[x1,y1],...], [[x1,y1],...], ... ] 多个有序顶点列表
    :return: 并集多边形的有序顶点列表
    """
    if not contours:
        return []
    
    current_union = Polygon(contours[0])
    for contour in contours[1:]:
        poly = Polygon(contour)
        current_union = current_union.union(poly)
    
    return list(current_union.exterior.coords)


def polygon_subtraction(main_poly, other_polys):
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
    main = main_poly if isinstance(main_poly, Polygon) else Polygon(main_poly)
    others = [p if isinstance(p, Polygon) else Polygon(p) for p in other_polys]
    
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
        return max(result.geoms, key=lambda p: p.area)
    else:
        return None

def precise_vertical_split(polygons):
    """
    基于质心和y极值的精确上下分割算法
    
    参数:
        polygons: 多边形顶点列表的列表
        
    返回:
        (upper_poly, lower_poly): 上部多边形和下部多边形的顶点列表
    """
    # 阶段1：计算几何特征
    poly_features = []
    for poly in polygons:
        p = Polygon(poly)
        ys = [pt[1] for pt in poly]
        poly_features.append({
            'poly': p,
            'centroid_y': p.centroid.y,
            'max_y': max(ys),
            'min_y': min(ys)
        })
    
    # 阶段2：确定初始上下部分
    # 上部候选：y最大值最大的多边形（若有多个选质心最高的）
    upper_candidate = max(poly_features, 
                         key=lambda x: (x['max_y'], x['centroid_y']))
    # 下部候选： 
    lower_candidate = min(poly_features,
                         key=lambda x: (x['min_y'], x['centroid_y']))
    
    # 阶段3：初始连通性验证
    initial_union = upper_candidate['poly'].union(lower_candidate['poly'])
    if initial_union.geom_type == 'Polygon':
        # 如果初始已连通，直接返回整体
        return list(initial_union.exterior.coords), []
    
    # 阶段4：动态分组
    upper_group = [upper_candidate['poly']]
    lower_group = [lower_candidate['poly']]
    remaining = [f for f in poly_features if f not in [upper_candidate, lower_candidate]]
    
    for feature in remaining:
        # 先尝试加入上部
        test_upper = unary_union(upper_group + [feature['poly']])
        if test_upper.geom_type == 'Polygon':
            upper_group.append(feature['poly'])
        else:
            # 尝试加入下部
            test_lower = unary_union(lower_group + [feature['poly']])
            if test_lower.geom_type == 'Polygon':
                lower_group.append(feature['poly'])
            else:
                # 无法分组的情况（如悬浮多边形）
                if abs(feature['centroid_y'] - upper_candidate['centroid_y']) < \
                   abs(feature['centroid_y'] - lower_candidate['centroid_y']):
                    upper_group.append(feature['poly'])
                else:
                    lower_group.append(feature['poly'])
    
    # 阶段5：合并最终结果
    def get_coords(geoms):
        union = unary_union(geoms)
        return list(union.exterior.coords) if union.geom_type == 'Polygon' else []
    
    return get_coords(upper_group), get_coords(lower_group)

def process_result_contour(result_contour):
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

def plot_contour(contour, color='blue', linestyle='--', label='Contour'):
    """可视化单个轮廓"""
    x, y = zip(*contour)
    plt.plot(x + (x[0],), y + (y[0],), color=color, linestyle=linestyle, label=label)
    plt.scatter(x, y, color=color, s=5)


if __name__ == '__main__':

    input_contours =[
        [(0.0, 0.0), (0.0, 11.8), (12.0, 11.8), (12.0, 0.0), (0.0, 0.0)],
        [(12.0, 11.4), (12.0, 11.8), (17.0, 11.8), (17.0, 11.4), (12.0, 11.4)],
        [(0.0, 22.0), (22.0, 22.0), (30.0, 13.0), (35.0, 13.0), (35.0, 19.0), (43.7, 19.0), (43.7, 13.0), (47.0, 13.0), (47.0, 25.0), (0.0, 25.0), (0.0, 22.0)],
        [(47.0, 14.2), (48.0, 14.2), (50.2, 13.0), (52.0, 13.0), (54.2, 14.2), (55.2, 14.2), (57.4, 13.0), (59.2, 13.0), (61.4, 14.2), (62.4, 14.2), (64.6, 13.0), (66.4, 13.0), (68.6, 14.2), (69.6, 14.2), (71.8, 13.0), (73.6, 13.0), (75.8, 14.2), (76.8, 14.2), (79.0, 13.0), (80.8, 13.0), (83.0, 14.2), (84.0, 14.2), (86.2, 13.0), (88.0, 13.0), (90.2, 14.2), (91.2, 14.2), (93.4, 13.0), (95.2, 13.0), (97.4, 14.2), (98.4, 14.2), (100.6, 13.0), (102.4, 13.0), (104.6, 14.2), (105.6, 14.2), (107.8, 13.0), (109.6, 13.0), (111.8, 14.2), (112.8, 14.2), (112.8, 13.0), (113.8, 13.0), (113.8, 16.4), (115.1, 16.4), (115.1, 18.8), (47.0, 18.8), (47.0, 14.2)],
        [(115.1, 12.8), (115.1, 18.8), (140.1, 18.8), (140.1, 12.8), (115.1, 12.8)],
        [(0.0, 0.0), (0.0, 12.3), (16.95, 12.3), (16.95, 0.0), (0.0, 0.0)]
    ]


    upper_contour, lower_contour = precise_vertical_split(input_contours)

    upper_parts, _ = compute_envelopes(upper_contour)
    area_contour = []
    x_max = max(p[0] for p in upper_parts)
    x_min = min(p[0] for p in upper_parts)
    area_contour.append((x_min, 0))
    for part in upper_parts:
        area_contour.append(part)
    area_contour.append((x_max, 0))
    print("area_contour ",area_contour)
    all_area = Polygon(area_contour)
    upper_area = Polygon(upper_contour)
    lower_area = Polygon(lower_contour)
    result_area = polygon_subtraction(all_area, [lower_area, upper_area])
    result_contour = list(result_area.exterior.coords)
    plt.figure(figsize=(8, 6), dpi=160)  # 12英寸宽 × 6英寸高，300dpi
    plot_contour(upper_contour, color='blue', linestyle='--', label='Contour')
    plot_contour(lower_contour, color='yellow', linestyle='--', label='Contour')
    plot_contour(result_contour, color='red', label='Result')
    plt.show()
    
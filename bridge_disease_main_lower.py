# -*- coding: utf-8 -*-
"""
桥梁病害CAD标注系统 - 下部（双柱墩12.5）处理程序
处理双柱墩的盖梁和墩柱病害标注
"""

import os
import sys
import math
import random
import ezdxf
from bridge_disease_parser import parse_excel

# 固定随机种子
random.seed(42)

# 坐标比例（双柱墩12.5模板）
# 1m 对应 X方向 14 CAD单位
# 1m 对应 Y方向 16.5 CAD单位
SCALE_X = 14    # X方向比例
SCALE_Y = 16.5  # Y方向比例

# 路径配置
BASE_DIR = r'k:\works\008.S2ReportAndLayoutPic\leftRealJobs_workbuddy'
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates', '构件')
LEGENDS_DIR = os.path.join(BASE_DIR, 'templates', '病害图例')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output_pages')
TEMPLATE_FILE = os.path.join(TEMPLATES_DIR, '双柱墩12.5.dxf')
PEEL_LEGEND_FILE = os.path.join(LEGENDS_DIR, '剥落、掉角.dxf')

# 剥落图例原始数据
PEEL_OFF_GEOMETRY = None


def load_peel_off_geometry():
    """从剥落图例模板加载原始几何数据"""
    global PEEL_OFF_GEOMETRY
    if PEEL_OFF_GEOMETRY is not None:
        return PEEL_OFF_GEOMETRY

    doc = ezdxf.readfile(PEEL_LEGEND_FILE)
    block = doc.blocks.get('adfsd')

    lines = []
    polyline = []

    for entity in block:
        if entity.dxftype() == 'LINE':
            lines.append({
                'start': (entity.dxf.start[0], entity.dxf.start[1]),
                'end': (entity.dxf.end[0], entity.dxf.end[1])
            })
        elif entity.dxftype() == 'LWPOLYLINE':
            pts = list(entity.get_points())
            polyline = [(p[0], p[1]) for p in pts]

    all_points = []
    for line in lines:
        all_points.extend([line['start'], line['end']])
    all_points.extend(polyline)

    if all_points:
        xs = [p[0] for p in all_points]
        ys = [p[1] for p in all_points]
        bbox = {
            'min_x': min(xs), 'max_x': max(xs),
            'min_y': min(ys), 'max_y': max(ys)
        }
    else:
        bbox = {'min_x': 0, 'max_x': 1, 'min_y': 0, 'max_y': 1}

    PEEL_OFF_GEOMETRY = {'lines': lines, 'polyline': polyline, 'bbox': bbox}
    return PEEL_OFF_GEOMETRY


# 双柱墩坐标系统
# 盖梁坐标系：x轴向右，y轴向下
CAP_BEAM_ORIGINS = {
    '小桩号面': (45, 251),
    '大桩号面': (305, 250),
    '左挡块': {'rect': (45, 257, 252, 53)},   # (x1, y1, y2, x2) CAD坐标
    '右挡块': {'rect': (218, 253, 250, 224)},
    '左挡块_大': {'rect': (306, 257, 252, 314)},
    '右挡块_大': {'rect': (477, 253, 250, 484)},
    '右侧面': {'rect': (177, 123, 100, 207)},  # 盖梁右侧面矩形 (x1, y1, y2, x2)
    '内侧面': {'rect': (75, 123, 100, 104)},   # 盖梁内侧面矩形
}

# 墩柱坐标系：x轴向下，y轴向右
# rect格式：(x1, y1, x2, y2) CAD坐标
PIER_ORIGINS = {
    '小桩号面': {
        'N-1': {'rect': (70, 224, 91, 190)},  # 左柱
        'N-2': {'rect': (70, 224, 91, 190)},   # 右柱（用户未提供具体值，用左柱代替）
    },
    '大桩号面': {
        'N-1': {'rect': (330, 224, 351, 190)},  # 右柱
        'N-2': {'rect': (439, 224, 460, 190)},  # 左柱
    },
    '外侧面': {'rect': (181, 100, 200, 70)},
    '内侧面': {'rect': (80, 100, 100, 70)},
}


def load_honeycomb_geometry():
    """加载蜂窝麻面图例的几何数据"""
    import ezdxf
    from ezdxf.bbox import extents

    doc = ezdxf.readfile('./templates/病害图例/蜂窝麻面.dxf')
    msp = doc.modelspace()

    entities = []
    bbox = extents(msp)

    for entity in msp:
        entities.append({
            'type': entity.dxftype(),
            'dxfattribs': {'color': 7},  # 白色
            'data': entity
        })

    return {
        'entities': entities,
        'bbox': {
            'min_x': bbox.extmin[0],
            'min_y': bbox.extmin[1],
            'max_x': bbox.extmax[0],
            'max_y': bbox.extmax[1]
        }
    }


# 钢筋锈蚀图例文件路径（全局缓存）
REBAR_LEGEND_DOC = None


def draw_rebar_corrosion(msp, x1: float, y1: float, x2: float, y2: float):
    """绘制钢筋锈蚀/露筋图例（平铺钢筋锈蚀图例填充区域）

    Args:
        msp: modelspace
        x1, y1, x2, y2: CAD坐标，矩形区域对角点

    Returns:
        实际边界框 (min_x, min_y, max_x, max_y)
    """
    from ezdxf.bbox import extents
    from ezdxf.math import Matrix44
    import math

    # 确保顺序
    min_x, max_x = min(x1, x2), max(x1, x2)
    min_y, max_y = min(y1, y2), max(y1, y2)

    dst_w = max_x - min_x
    dst_h = max_y - min_y

    print(f"    [露筋] 目标区域: ({min_x:.1f},{min_y:.1f}) ~ ({max_x:.1f},{max_y:.1f}), 尺寸: {dst_w:.1f}x{dst_h:.1f}")

    # 加载钢筋锈蚀图例文件
    legend_file = os.path.join(BASE_DIR, 'templates', '病害图例', '钢筋锈蚀或可见箍筋轮廓.dxf')
    legend_doc = ezdxf.readfile(legend_file)
    legend_msp = legend_doc.modelspace()

    # 获取图例边界框（排除文字）
    non_text_entities = [e for e in legend_msp if e.dxftype() not in ['TEXT', 'MTEXT']]
    legend_bbox = extents(non_text_entities)
    src_min_x = legend_bbox.extmin[0]
    src_min_y = legend_bbox.extmin[1]
    src_max_x = legend_bbox.extmax[0]
    src_max_y = legend_bbox.extmax[1]
    src_w = src_max_x - src_min_x
    src_h = src_max_y - src_min_y

    print(f"    [露筋] 图例尺寸: {src_w:.1f}x{src_h:.1f}")

    # 缩放：让图例适配病害区域
    scale_x = dst_w / src_w if src_w > 0 else 1
    scale_y = dst_h / src_h if src_h > 0 else 1
    scale = min(scale_x, scale_y) * 0.9  # 留一点边距

    scaled_w = src_w * scale
    scaled_h = src_h * scale

    # 计算平铺数量
    n_cols = max(1, math.floor(dst_w / scaled_w))
    n_rows = max(1, math.floor(dst_h / scaled_h))

    # 从矩形左上角开始
    start_x = min_x
    start_y = min_y

    print(f"    [露筋] 缩放{scale:.2f}, 平铺: {n_cols}x{n_rows}={n_cols*n_rows}个")

    # 平铺复制
    entity_count = 0
    for row in range(n_rows):
        for col in range(n_cols):
            tile_x = start_x + col * scaled_w
            tile_y = start_y + row * scaled_h

            # 变换：p_new = p * scale + (tile - src_min * scale)
            dx = tile_x - src_min_x * scale
            dy = tile_y - src_min_y * scale
            transform = Matrix44([scale,0,0,0, 0,scale,0,0, 0,0,1,0, dx,dy,0,1])

            for entity in legend_msp:
                dxftype = entity.dxftype()
                if dxftype == 'MTEXT':
                    continue
                try:
                    new_entity = entity.copy()
                    new_entity.transform(transform)
                    msp.add_entity(new_entity)
                    entity_count += 1
                except Exception as e:
                    print(f"    [露筋] {dxftype}复制失败: {e}")

    print(f"    [露筋] 复制了 {entity_count} 个实体")

    # 返回实际边界框
    return (start_x, start_y, start_x + n_cols * scaled_w, start_y + n_rows * scaled_h)


def update_text_in_msp(msp, old_text: str, new_text: str, height: float = None):
    """替换模型空间中的文字"""
    for entity in msp:
        if entity.dxftype() == 'TEXT':
            if old_text in entity.dxf.text:
                entity.dxf.text = entity.dxf.text.replace(old_text, new_text)
                if height is not None:
                    entity.dxf.height = height
        elif entity.dxftype() == 'MTEXT':
            content = entity.text
            if old_text in content:
                entity.text = content.replace(old_text, new_text)
                if height is not None:
                    entity.dxf.char_height = height


def convert_to_cad_coords_lower(x: float, y: float, origin: tuple) -> tuple:
    """
    双柱墩坐标转换
    origin: (origin_x, origin_y) - 左上角
    X方向: 1m = SCALE_X CAD单位，向右
    Y方向: 1m = SCALE_Y CAD单位，向下（所以要减）
    """
    return (origin[0] + x * SCALE_X, origin[1] - y * SCALE_Y)


def draw_peel_off_direct(msp, x1: float, y1: float, x2: float, y2: float):
    """直接在CAD坐标绘制剥落图形（用于挡块、侧面等）
    返回实际绘制的边界框 (min_x, min_y, max_x, max_y)
    """
    geo = load_peel_off_geometry()
    bbox = geo['bbox']

    src_w = bbox['max_x'] - bbox['min_x']
    src_h = bbox['max_y'] - bbox['min_y']
    dst_w = (x2 - x1) * 0.8
    dst_h = (y2 - y1) * 0.8

    if src_w > 0 and src_h > 0:
        scale_x = dst_w / src_w
        scale_y = dst_h / src_h
        scale = min(scale_x, scale_y)
    else:
        scale = 1

    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2

    # 计算实际边界框
    actual_min_x = center_x - dst_w / 2
    actual_max_x = center_x + dst_w / 2
    actual_min_y = center_y - dst_h / 2
    actual_max_y = center_y + dst_h / 2

    # 绘制线条
    for line in geo['lines']:
        sx, sy = line['start']
        ex, ey = line['end']
        dx = (ex - sx) * scale
        dy = (ey - sy) * scale
        new_start = (center_x - dst_w/2 + (sx - bbox['min_x']) * scale,
                     center_y - dst_h/2 + (sy - bbox['min_y']) * scale)
        new_end = (new_start[0] + dx, new_start[1] + dy)
        msp.add_line(new_start, new_end, dxfattribs={'color': 7})

    # 绘制多边形
    if geo['polyline']:
        pts = []
        for px, py in geo['polyline']:
            pts.append((
                center_x - dst_w/2 + (px - bbox['min_x']) * scale,
                center_y - dst_h/2 + (py - bbox['min_y']) * scale
            ))
        msp.add_lwpolyline(pts, dxfattribs={'color': 7})

    return (actual_min_x, actual_min_y, actual_max_x, actual_max_y)


def draw_peel_off(msp, x1: float, y1: float, x2: float, y2: float, origin: tuple, return_bbox: bool = False):
    """绘制剥落图例"""
    geo = load_peel_off_geometry()
    bbox = geo['bbox']

    # 计算缩放比例
    src_w = bbox['max_x'] - bbox['min_x']
    src_h = bbox['max_y'] - bbox['min_y']
    dst_w = (x2 - x1) * 10 * 0.8  # 目标宽度（留点边距）
    dst_h = (y2 - y1) * 10 * 0.8

    if src_w > 0 and src_h > 0:
        scale_x = dst_w / src_w
        scale_y = dst_h / src_h
        scale = min(scale_x, scale_y)
    else:
        scale = 1

    # 目标中心
    center_x = (x1 + x2) / 2 * 10 + origin[0]
    center_y = (y1 + y2) / 2 * 10 + origin[1]

    # 绘制线条
    for line in geo['lines']:
        sx, sy = line['start']
        ex, ey = line['end']
        dx = (ex - sx) * scale
        dy = (ey - sy) * scale
        new_start = (center_x - dst_w/2 + (sx - bbox['min_x']) * scale,
                     center_y - dst_h/2 + (sy - bbox['min_y']) * scale)
        new_end = (new_start[0] + dx, new_start[1] + dy)
        msp.add_line(new_start, new_end, dxfattribs={'color': 7})

    # 绘制多边形
    if geo['polyline']:
        pts = []
        for px, py in geo['polyline']:
            pts.append((
                center_x - dst_w/2 + (px - bbox['min_x']) * scale,
                center_y - dst_h/2 + (py - bbox['min_y']) * scale
            ))
        msp.add_lwpolyline(pts, dxfattribs={'color': 7})

    if return_bbox:
        return (center_x - dst_w/2, center_y - dst_h/2,
                center_x + dst_w/2, center_y + dst_h/2)
    return None


def draw_polyline_leader(msp, start_x: float, start_y: float, seg2_len: float, go_left: bool = False):
    """绘制折线引线

    Args:
        go_left: 如果为True，第二段向左画（seg2_len为负）
    """
    seg1_len = 8
    angle = math.radians(45)

    if go_left:
        # 向左画：折线第一段向左上45度，第二段向左
        bend_x = start_x - seg1_len * math.cos(angle)  # 向左
        bend_y = start_y + seg1_len * math.sin(angle)  # 向上
        end_x = bend_x - abs(seg2_len)  # 继续向左
    else:
        # 向右画（默认）：折线第一段向右下45度，第二段向右
        bend_x = start_x + seg1_len * math.cos(angle)
        bend_y = start_y + seg1_len * math.sin(angle)
        end_x = bend_x + abs(seg2_len)

    end_y = bend_y

    points = [(start_x, start_y), (bend_x, bend_y), (end_x, end_y)]
    msp.add_lwpolyline(points=points, dxfattribs={'color': 7})

    return (bend_x, bend_y, end_x, end_y)


def draw_disease_label(msp, disease_type: str, value_text: str, start_x: float, start_y: float, seg2_len: float, go_left: bool = False):
    """绘制病害标注

    Args:
        disease_type: 病害名称（如"纵向裂缝"）
        value_text: 病害数值（如"L=8.00m"）
        start_x, start_y: 病害区域右上角位置
        seg2_len: 第二段水平线长度
        go_left: 如果为True，标注向左画
    """
    text_height = 2.5

    bend_x, bend_y, end_x, end_y = draw_polyline_leader(msp, start_x, start_y, seg2_len, go_left)

    if go_left:
        # 向左画：文字在折点的左侧
        text_x = bend_x - seg2_len - 1
    else:
        # 向右画：文字在折点的右侧
        text_x = bend_x + 1

    # 上方：病害名称
    msp.add_text(
        disease_type,
        dxfattribs={
            'insert': (text_x, bend_y + text_height * 0.5),
            'height': text_height,
            'color': 7
        }
    )

    # 下方：病害数值
    if value_text:
        msp.add_text(
            value_text,
            dxfattribs={
                'insert': (text_x, bend_y - text_height * 1.5),
                'height': text_height,
                'color': 7
            }
        )


def draw_crack(msp, x_start: float, x_end: float, y: float, origin: tuple):
    """绘制裂缝（手绘风格，179度倾斜）"""
    cad_x1, cad_y1 = convert_to_cad_coords_lower(x_start, y, origin)
    cad_x2, cad_y2 = convert_to_cad_coords_lower(x_end, y, origin)

    # 179度倾斜：终点Y比起点Y稍低
    # tan(1度) ≈ 0.01745
    crack_length = (x_end - x_start) * SCALE_X  # 裂缝实际长度（CAD单位）
    tilt_offset = crack_length * math.tan(math.radians(1))  # 倾斜偏移量
    cad_y2 = cad_y2 - tilt_offset  # 终点Y稍低

    # 手绘风格裂缝
    points = []
    x = cad_x1
    step = 0.8
    while x <= cad_x2:
        # 计算当前点的倾斜偏移
        progress = (x - cad_x1) / (cad_x2 - cad_x1) if cad_x2 != cad_x1 else 0
        base_tilt = tilt_offset * progress
        # 叠加手绘随机偏移
        offset_y = math.sin((x - cad_x1) / 3) * 0.15 + random.uniform(-0.1, 0.1)
        points.append((x, cad_y1 - base_tilt + offset_y))
        x += step
    points.append((cad_x2, cad_y2))

    msp.add_lwpolyline(points=points, dxfattribs={'color': 7})



def draw_vertical_crack_group(msp, x_start: float, x_end: float, y_start: float, y_end: float, n: int, origin: tuple):
    """绘制竖向裂缝群（多条平行竖线，179度倾斜）

    Args:
        x_start, x_end: 矩形区域X范围（m）
        y_start, y_end: 矩形区域Y范围（m）
        n: 裂缝数量
        origin: CAD原点
    """
    # 计算矩形边界CAD坐标
    cad_x1, cad_y1 = convert_to_cad_coords_lower(x_start, y_start, origin)
    cad_x2, cad_y2 = convert_to_cad_coords_lower(x_end, y_end, origin)

    # 确保顺序正确（X轴向右，Y轴向下）
    if cad_x1 > cad_x2:
        cad_x1, cad_x2 = cad_x2, cad_x1
    if cad_y1 > cad_y2:
        cad_y1, cad_y2 = cad_y2, cad_y1

    # 竖线在矩形左右边界内（留一点边距）
    margin = 0.5
    left_bound = cad_x1 + margin
    right_bound = cad_x2 - margin

    # 均匀分布n条竖线
    if n > 1:
        step = (right_bound - left_bound) / (n - 1)
    else:
        step = 0
        left_bound = (cad_x1 + cad_x2) / 2
        right_bound = left_bound

    # 179度倾斜偏移量
    # 裂缝高度方向（Y方向）需要轻微向右下倾斜
    crack_height = (cad_y1 - cad_y2)  # 裂缝长度（CAD单位）
    tilt_offset = crack_height * math.tan(math.radians(1))  # 倾斜偏移量

    # 绘制n条竖线（白色）
    for i in range(n):
        line_x = left_bound + i * step
        # 竖线从矩形顶部到底部（Y方向向下，所以顶部的Y值大，底部的Y值小）
        top_y = cad_y1  # y_start对应的Y坐标（较大）
        bottom_y = cad_y2  # y_end对应的Y坐标（较小）

        # 手绘风格 + 179度倾斜
        points = []
        # 根据裂缝高度生成足够多的点
        num_points = max(10, int(top_y - bottom_y) * 2)  # 至少10个点
        for j in range(num_points):
            progress = j / (num_points - 1) if num_points > 1 else 0
            y = top_y - (top_y - bottom_y) * progress
            # 计算当前点的179度倾斜偏移
            base_tilt = tilt_offset * progress
            # 叠加手绘随机偏移（使用固定的seed保证可复现）
            random.seed(42 + i * 100 + j)
            offset = random.uniform(-0.1, 0.1)
            points.append((line_x + offset + base_tilt, y))
        points.append((line_x + random.uniform(-0.1, 0.1), bottom_y))

        msp.add_lwpolyline(points=points, dxfattribs={'color': 7})  # 7=白色


def draw_honeycomb(msp, x1: float, y1: float, x2: float, y2: float, origin: tuple = None):
    """绘制蜂窝麻面图例（平铺复制modelspace实体填满整个区域）

    病害坐标系：原点为病害区域原点
    - X方向: 1m = 14 CAD单位，向右
    - Y方向: 1m = 16.5 CAD单位，向下（CAD Y减小）

    Args:
        x1, y1: 病害区域起点（m）
        x2, y2: 病害区域终点（m）
        origin: CAD原点（病害坐标系原点）- 用户提供的原点位置

    Returns:
        实际边界框 (min_x, min_y, max_x, max_y)
    """
    from ezdxf.bbox import extents
    from ezdxf.math import Matrix44

    # 直接坐标转换（病害坐标 + 原点）
    # X方向: 1m = 14 CAD单位，向右
    # Y方向: 1m = 16.5 CAD单位，向下（CAD Y = 原点Y - y * SCALE_Y）
    if origin is None:
        origin = (0, 0)

    cad_x1 = origin[0] + x1 * SCALE_X
    cad_y1 = origin[1] - y1 * SCALE_Y
    cad_x2 = origin[0] + x2 * SCALE_X
    cad_y2 = origin[1] - y2 * SCALE_Y

    # 确保顺序
    if cad_x1 > cad_x2:
        cad_x1, cad_x2 = cad_x2, cad_x1
    if cad_y1 > cad_y2:
        cad_y1, cad_y2 = cad_y2, cad_y1

    dst_w = cad_x2 - cad_x1
    dst_h = cad_y2 - cad_y1

    print(f"    [蜂窝] 目标区域: ({cad_x1:.1f},{cad_y1:.1f}) ~ ({cad_x2:.1f},{cad_y2:.1f}), 尺寸: {dst_w:.1f}x{dst_h:.1f}")
    print(f"    [蜂窝] 原点: {origin}, 病害坐标: ({x1},{y1}) ~ ({x2},{y2})")

    # 加载蜂窝麻面图例文件
    legend_doc = ezdxf.readfile('./templates/病害图例/蜂窝麻面.dxf')
    legend_msp = legend_doc.modelspace()

    # 获取图例边界框（排除文字MTEXT）
    non_text_entities = [e for e in legend_msp if e.dxftype() not in ['TEXT', 'MTEXT']]
    legend_bbox = extents(non_text_entities)
    src_w = legend_bbox.extmax[0] - legend_bbox.extmin[0]
    src_h = legend_bbox.extmax[1] - legend_bbox.extmin[1]

    print(f"    [蜂窝] 图例实际尺寸（不含文字）: {src_w:.1f}x{src_h:.1f}")

    # 放大2倍，让蜂窝效果更明显
    scale = 2.0
    scaled_w = src_w * scale
    scaled_h = src_h * scale

    # 图例左下角（最小坐标）
    src_min_x = legend_bbox.extmin[0]
    src_min_y = legend_bbox.extmin[1]

    # 计算平铺数量：只画完整且不超出边界的格子
    import math
    n_cols = max(1, math.floor(dst_w / scaled_w))  # X方向：不超右边
    n_rows = max(1, math.floor(dst_h / scaled_h))  # Y方向：不超下边

    # 从矩形左上角开始（cad_x1 左边, cad_y1 较小Y值即上边）
    start_x = cad_x1  # 左边界
    start_y = cad_y1  # 上边界（较小的Y值）

    print(f"    [蜂窝] 图例放大2倍: {scaled_w:.1f}x{scaled_h:.1f}, 平铺: {n_cols}x{n_rows}={n_cols*n_rows}个")
    print(f"    [蜂窝] 覆盖范围: ({start_x:.1f},{start_y:.1f}) ~ ({start_x + n_cols*scaled_w:.1f},{start_y + n_rows*scaled_h:.1f})")

    # 平铺复制（左边缘对齐矩形左边，从上边界向下铺）
    entity_count = 0
    for row in range(n_rows):
        for col in range(n_cols):
            # 第(col,row)个图例的左下角目标坐标
            tile_x = start_x + col * scaled_w
            tile_y = start_y + row * scaled_h

            # 变换公式：p_new = p * scale + (tile - src_min * scale)
            # 等价于：先把图例移到原点，再缩放，再移到目标
            dx = tile_x - src_min_x * scale
            dy = tile_y - src_min_y * scale
            # Matrix44([sx,0,0,0, 0,sy,0,0, 0,0,1,0, dx,dy,0,1]) 行优先
            transform = Matrix44([scale,0,0,0, 0,scale,0,0, 0,0,1,0, dx,dy,0,1])

            # 复制每个实体
            for entity in legend_msp:
                dxftype = entity.dxftype()
                if dxftype == 'MTEXT':
                    continue
                try:
                    new_entity = entity.copy()
                    new_entity.transform(transform)
                    msp.add_entity(new_entity)
                    entity_count += 1
                except Exception as e:
                    print(f"    [蜂窝] {dxftype}复制失败: {e}")

    print(f"    [蜂窝] 复制了 {entity_count} 个实体")
    # 返回平铺后的实际边界框
    actual_min_x = start_x
    actual_max_x = start_x + n_cols * scaled_w
    actual_min_y = start_y  # 下边界（较小）
    actual_max_y = start_y + n_rows * scaled_h  # 上边界（较大）
    return (actual_min_x, actual_min_y, actual_max_x, actual_max_y)


def draw_mesh_crack(msp, x1: float, y1: float, x2: float, y2: float, origin: tuple):
    """绘制网状裂缝（波浪线填充）"""
    cad_x1, cad_y1 = convert_to_cad_coords_lower(x1, y1, origin)
    cad_x2, cad_y2 = convert_to_cad_coords_lower(x2, y2, origin)

    if cad_x1 > cad_x2:
        cad_x1, cad_x2 = cad_x2, cad_x1
    if cad_y1 > cad_y2:
        cad_y1, cad_y2 = cad_y2, cad_y1

    # 波浪线填充
    wavelength = 4
    amplitude = 0.3
    spacing = 1.5

    y = cad_y1 + spacing
    while y < cad_y2:
        points = []
        x = cad_x1
        while x <= cad_x2:
            wave = math.sin((x - cad_x1) / wavelength * 2 * math.pi) * amplitude
            points.append((x, y + wave))
            x += 0.5
        msp.add_lwpolyline(points=points, dxfattribs={'color': 7})
        y += spacing


def draw_rebar_grid(msp, ax1: float, ay1: float, ax2: float, ay2: float):
    """绘制钢筋锈蚀网格（红色虚线）"""
    # 横线
    for i in range(3):
        y = ay1 + (ay2 - ay1) * (i + 1) / 4
        msp.add_line((ax1, y), (ax2, y), dxfattribs={'color': 1, 'linetype': 'DASHED'})
    # 竖线
    for i in range(3):
        x = ax1 + (ax2 - ax1) * (i + 1) / 4
        msp.add_line((x, ay1), (x, ay2), dxfattribs={'color': 1, 'linetype': 'DASHED'})



def get_face_from_location(location: str) -> str:
    """从位置描述判断面（小桩号面/大桩号面）"""
    if '小桩号面' in location:
        return '小桩号面'
    elif '大桩号面' in location:
        return '大桩号面'
    elif '侧面' in location or '挡块' in location:
        return '小桩号面'  # 默认
    return '小桩号面'


def process_cap_beam_disease(msp, disease: dict):
    """处理盖梁病害"""
    location = disease.get('缺损位置', '')
    part = disease.get('具体部件', '')  # 从病害描述中解析出的部位
    x_start = disease.get('x_start', 0)
    x_end = disease.get('x_end', 0)
    y_start = disease.get('y_start', 0)
    y_end = disease.get('y_end', 0)
    disease_type = disease.get('病害类型', '')
    disease_raw = disease.get('病害', '')

    # 判断面：优先用具体部件判断（包含"小桩号面"/"大桩号面"/"挡块"）
    face = part if part else location
    if '小桩号面' in face:
        origin = CAP_BEAM_ORIGINS['小桩号面']
    elif '大桩号面' in face:
        origin = CAP_BEAM_ORIGINS['大桩号面']
    elif '挡块' in face:
        # 挡块：直接在挡块矩形区域内绘制
        if '左' in face:
            if '大桩号' in face:
                block_rect = CAP_BEAM_ORIGINS['左挡块_大']['rect']
            else:
                block_rect = CAP_BEAM_ORIGINS['左挡块']['rect']
        else:
            if '大桩号' in face:
                block_rect = CAP_BEAM_ORIGINS['右挡块_大']['rect']
            else:
                block_rect = CAP_BEAM_ORIGINS['右挡块']['rect']
        # 挡块内坐标：x范围(x1,x2), y范围(y1,y2)
        # 挡块较小，直接在挡块矩形内绘制合适大小的剥落
        bx1, by1, by2, bx2 = block_rect
        # 挡块内留一点边距
        margin = 0.5
        x1 = bx1 + margin
        x2 = bx2 - margin
        y2 = by2 + margin  # by2是较小的值（下方）
        y1 = by1 - margin  # by1是较大的值（上方）
        # 添加标注：从病害区域上方引出
        area = disease.get('area', 0)
        if area > 0:
            # 先绘制剥落，获取实际边界框
            bbox = draw_peel_off_direct(msp, x1, y1, x2, y2)
            actual_min_x, actual_min_y, actual_max_x, actual_max_y = bbox
            # 标注起点：剥落区域上方中间
            start_x = (actual_min_x + actual_max_x) / 2  # 水平中间
            start_y = actual_max_y  # 上边缘
            # 向上引出标注
            seg2_len = max(12, len(disease_type) * 3 + len(str(area)) * 5)
            text_height = 2.5
            # 第一段向上45度
            bend_x = start_x
            bend_y = start_y + 8
            # 第二段水平
            end_x = bend_x + seg2_len
            end_y = bend_y
            # 绘制折线
            msp.add_lwpolyline([(start_x, start_y), (bend_x, bend_y), (end_x, end_y)], dxfattribs={'color': 7})
            # 上方：病害名称
            msp.add_text(disease_type, dxfattribs={
                'insert': (bend_x + 1, bend_y + text_height * 0.5),
                'height': text_height, 'color': 7
            })
            # 下方：面积
            msp.add_text(f'S={area:.2f}m²', dxfattribs={
                'insert': (bend_x + 1, bend_y - text_height * 1.5),
                'height': text_height, 'color': 7
            })
        return
    elif '侧面' in face:
        # 盖梁的侧面（使用盖梁的侧面矩形配置）
        if '右' in face:
            block_rect = CAP_BEAM_ORIGINS['右侧面']['rect']
        else:
            block_rect = CAP_BEAM_ORIGINS['内侧面']['rect']
        # 盖梁侧面较小，直接在矩形内绘制合适大小的剥落
        bx1, by1, by2, bx2 = block_rect
        # 留较大边距（因为矩形比较小）
        margin = 3
        x1 = bx1 + margin
        x2 = bx2 - margin
        y2 = by2 + margin  # by2是较小的值（下方）
        y1 = by1 - margin  # by1是较大的值（上方）
        # 绘制剥落（使用更大的缩放因子让图形更小）
        geo = load_peel_off_geometry()
        bbox = geo['bbox']
        src_w = bbox['max_x'] - bbox['min_x']
        src_h = bbox['max_y'] - bbox['min_y']
        dst_w = x2 - x1
        dst_h = abs(y2 - y1)  # 使用绝对值
        if src_w > 0 and src_h > 0:
            scale_x = dst_w / src_w
            scale_y = dst_h / src_h
            scale = min(scale_x, scale_y) * 0.5  # 缩小50%
        else:
            scale = 0.5
        # 剥落图形中心对齐到矩形中心
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        # 调试：打印坐标信息
        print(f"    [调试] 矩形: ({x1:.1f},{y1:.1f}) ~ ({x2:.1f},{y2:.1f}), 中心: ({center_x:.1f},{center_y:.1f})")
        print(f"    [调试] 剥落源尺寸: {src_w:.1f}x{src_h:.1f}, 缩放: {scale:.3f}")
        # 剥落图形中心坐标
        peel_center_x = (bbox['min_x'] + bbox['max_x']) / 2
        peel_center_y = (bbox['min_y'] + bbox['max_y']) / 2
        # 绘制线条
        for line in geo['lines']:
            sx, sy = line['start']
            ex, ey = line['end']
            # 先归一化到原点，再缩放，最后移到目标中心
            new_start = (center_x + (sx - peel_center_x) * scale,
                         center_y + (sy - peel_center_y) * scale)
            new_end = (center_x + (ex - peel_center_x) * scale,
                       center_y + (ey - peel_center_y) * scale)
            msp.add_line(new_start, new_end, dxfattribs={'color': 7})
        # 绘制多边形
        if geo['polyline']:
            pts = []
            for px, py in geo['polyline']:
                pts.append((
                    center_x + (px - peel_center_x) * scale,
                    center_y + (py - peel_center_y) * scale
                ))
            msp.add_lwpolyline(pts, dxfattribs={'color': 7})
        # 计算实际边界框
        actual_min_x = center_x - src_w * scale / 2
        actual_max_x = center_x + src_w * scale / 2
        actual_min_y = center_y - src_h * scale / 2
        actual_max_y = center_y + src_h * scale / 2
        print(f"    [调试] 剥落边界框: ({actual_min_x:.1f},{actual_min_y:.1f}) ~ ({actual_max_x:.1f},{actual_max_y:.1f})")
        # 添加标注：从病害区域上方引出
        area = disease.get('area', 0)
        if area > 0:
            # 标注起点：剥落区域上方中间
            start_x = (actual_min_x + actual_max_x) / 2  # 水平中间
            start_y = actual_max_y  # 剥落图形上边缘
            # 向上引出标注
            seg2_len = max(12, len(disease_type) * 3 + len(str(area)) * 5)
            text_height = 2.5
            # 第一段向上45度（长度8）
            offset_45 = 8 / math.sqrt(2)  # ≈5.66
            bend_x = start_x + offset_45
            bend_y = start_y + offset_45
            # 第二段水平
            end_x = bend_x + seg2_len
            end_y = bend_y
            # 绘制折线
            msp.add_lwpolyline([(start_x, start_y), (bend_x, bend_y), (end_x, end_y)], dxfattribs={'color': 7})
            # 上方：病害名称
            msp.add_text(disease_type, dxfattribs={
                'insert': (bend_x + 1, bend_y + text_height * 0.5),
                'height': text_height, 'color': 7
            })
            # 下方：面积
            msp.add_text(f'S={area:.2f}m²', dxfattribs={
                'insert': (bend_x + 1, bend_y - text_height * 1.5),
                'height': text_height, 'color': 7
            })
        return
    else:
        origin = CAP_BEAM_ORIGINS['小桩号面']


    # 获取数值数据
    length = disease.get('length', 0)
    width = disease.get('width', 0)
    area = disease.get('area', 0)
    crack_count = disease.get('裂缝条数', disease.get('count', 0))  # N=数字

    # 计算病害区域右上角（作为标注起点）
    cad_x1, cad_y1 = convert_to_cad_coords_lower(x_start, y_start, origin)
    cad_x2, cad_y2 = convert_to_cad_coords_lower(x_end, y_end, origin)
    start_x = max(cad_x1, cad_x2)
    start_y = max(cad_y1, cad_y2)

    # 计算标注第二段长度
    seg2_len = max(12, len(disease_type) * 3 + max(len(str(length)), len(str(area))) * 5)

    # 绘制病害及标注
    if '蜂窝' in disease_type or '麻面' in disease_type:
        # 蜂窝/麻面：使用蜂窝麻面图例
        # 病害原点 = 小桩号面坐标原点 (45, 251)
        # X: 1m = 14 CAD单位，向右
        # Y: 1m = 16.5 CAD单位，向下（CAD Y = 原点Y - y * 16.5）
        honeycomb_origin = (45, 251)
        bbox = draw_honeycomb(msp, x_start, y_start, x_end, y_end, origin=honeycomb_origin)
        if area > 0 and bbox:
            actual_min_x, actual_min_y, actual_max_x, actual_max_y = bbox
            # 标注起点：蜂窝区域上方中间
            label_start_x = (actual_min_x + actual_max_x) / 2
            label_start_y = actual_max_y
            # 向上引出标注
            seg2_len = max(12, len(disease_type) * 3 + len(f'{area:.2f}') * 5)
            text_height = 2.5
            # 第一段向上45度（长度8，水平垂直偏移各约5.66）
            offset_45 = 8 / math.sqrt(2)  # ≈5.66
            bend_x = label_start_x + offset_45
            bend_y = label_start_y + offset_45
            # 第二段水平
            end_x = bend_x + seg2_len
            end_y = bend_y
            # 绘制折线
            msp.add_lwpolyline([(label_start_x, label_start_y), (bend_x, bend_y), (end_x, end_y)], dxfattribs={'color': 7})
            # 上方：病害名称
            msp.add_text(disease_type, dxfattribs={
                'insert': (bend_x + 1, bend_y + text_height * 0.5),
                'height': text_height, 'color': 7
            })
            # 下方：面积
            msp.add_text(f'S={area:.2f}m²', dxfattribs={
                'insert': (bend_x + 1, bend_y - text_height * 1.5),
                'height': text_height, 'color': 7
            })
    elif '剥落' in disease_type or '破损' in disease_type:
        # 使用return_bbox获取实际边界框
        bbox = draw_peel_off(msp, x_start, y_start, x_end, y_end, origin, return_bbox=True)
        if area > 0 and bbox:
            actual_min_x, actual_min_y, actual_max_x, actual_max_y = bbox
            # 标注起点：剥落区域上方中间
            label_start_x = (actual_min_x + actual_max_x) / 2
            label_start_y = actual_max_y
            # 向上引出标注
            seg2_len = max(12, len(disease_type) * 3 + len(f'{area:.2f}') * 5)
            text_height = 2.5
            # 第一段向上45度（长度8，水平垂直偏移各约5.66）
            offset_45 = 8 / math.sqrt(2)  # ≈5.66
            bend_x = label_start_x + offset_45
            bend_y = label_start_y + offset_45
            # 第二段水平
            end_x = bend_x + seg2_len
            end_y = bend_y
            # 绘制折线
            msp.add_lwpolyline([(label_start_x, label_start_y), (bend_x, bend_y), (end_x, end_y)], dxfattribs={'color': 7})
            # 上方：病害名称
            msp.add_text(disease_type, dxfattribs={
                'insert': (bend_x + 1, bend_y + text_height * 0.5),
                'height': text_height, 'color': 7
            })
            # 下方：面积
            msp.add_text(f'S={area:.2f}m²', dxfattribs={
                'insert': (bend_x + 1, bend_y - text_height * 1.5),
                'height': text_height, 'color': 7
            })

    elif '裂缝' in disease_type:
        if crack_count > 1:
            # 裂缝群（竖向裂缝）
            draw_vertical_crack_group(msp, x_start, x_end, y_start, y_end, crack_count, origin)
            # 标注：竖向裂缝 N=15条，上方；L总=4.50m，下方
            if length > 0:
                label = f'{disease_type} N={crack_count}条'
                value = f'L总={length:.2f}m'
            else:
                label = f'{disease_type} N={crack_count}条'
                value = ''
            draw_disease_label(msp, label, value, start_x, start_y, seg2_len)
        elif y_start == y_end:
            # 单条水平裂缝
            draw_crack(msp, x_start, x_end, y_start, origin)
            if length > 0 and width > 0:
                label = f'{disease_type} L={length:.2f}m'
                value = f'W={width:.2f}mm'
            elif length > 0:
                label = f'{disease_type} L={length:.2f}m'
                value = ''
            else:
                label = disease_type
                value = ''
            if label:
                draw_disease_label(msp, label, value, start_x, start_y, seg2_len)

    elif '网状裂缝' in disease_type:
        draw_mesh_crack(msp, x_start, y_start, x_end, y_end, origin)
        if area > 0:
            draw_disease_label(msp, '网状裂缝', f'S={area:.2f}m²', start_x, start_y, seg2_len)

    elif '孔洞空洞' in disease_type:
        # 绘制矩形空洞
        msp.add_lwpolyline([(cad_x1, cad_y1), (cad_x2, cad_y1), (cad_x2, cad_y2), (cad_x1, cad_y2)],
                           dxfattribs={'color': 7})
        if area > 0:
            draw_disease_label(msp, '孔洞空洞', f'S={area:.2f}m²', start_x, start_y, seg2_len)

    elif '露筋' in disease_type or '锈胀露筋' in disease_type:
        bbox = draw_peel_off(msp, x_start, y_start, x_end, y_end, origin, return_bbox=True)
        if bbox:
            draw_rebar_grid(msp, *bbox)
        if area > 0:
            draw_disease_label(msp, disease_type, f'S={area:.2f}m²', start_x, start_y, seg2_len)


def process_pier_disease(msp, disease: dict):
    """处理墩柱病害：根据面积计算大小，从病害边缘引出标注"""
    location = disease.get('缺损位置', '')
    disease_type = disease.get('病害类型', '')
    pier_no = disease.get('墩柱号')
    column_no = disease.get('柱内编号')
    area = disease.get('area', 0)

    # 判断墩柱位置
    if pier_no and column_no:
        key = f'N-{column_no}'
        face = '小桩号面' if ('小桩号面' in location or '墩柱' in location) else '大桩号面'

        if face in PIER_ORIGINS and key in PIER_ORIGINS[face]:
            rect = PIER_ORIGINS[face][key]['rect']
            pier_x1, pier_y1, pier_x2, pier_y2 = rect

            # 根据面积计算病害区域大小（假设方形）
            # 面积 A，边长 L = sqrt(A)
            # 1m ≈ 15 CAD单位，1m² ≈ 225 CAD单位²
            # CAD边长 = sqrt(面积 * 225)
            if area > 0:
                side_len = math.sqrt(area * 225)
                # 最小尺寸限制，避免太小看不见
                side_len = max(side_len, 5)
                # 最大尺寸限制，不能超过墩柱
                pier_w = pier_x2 - pier_x1 - 6  # 留边距
                pier_h = pier_y1 - pier_y2 - 6
                side_len = min(side_len, pier_w, pier_h)
            else:
                side_len = 8  # 默认8 CAD单位

            # 病害区域：墩柱中间偏上
            pier_center_x = (pier_x1 + pier_x2) / 2
            # 墩柱Y范围: pier_y1(224)上 到 pier_y2(190)下
            # 取上部1/3区域
            pier_top = pier_y1 - (pier_y1 - pier_y2) * 0.2  # 从顶部20%处
            pier_center_y = pier_top - side_len / 2
            x1 = pier_center_x - side_len / 2
            x2 = pier_center_x + side_len / 2
            y1 = pier_center_y + side_len  # 上边缘
            y2 = pier_center_y  # 下边缘

            print(f"    [墩柱{key}] 类型={disease_type}, 面积={area}m2, 病害尺寸={side_len:.1f}CAD单位")

            # 绘制病害
            if '剥落露筋' in disease_type or '露筋' in disease_type:
                bbox = draw_rebar_corrosion(msp, x1, y1, x2, y2)
                if area > 0:
                    # 标注从病害右上角引出
                    label_start_x = bbox[2]  # 右边缘
                    label_start_y = bbox[3]  # 上边缘
                    draw_pier_disease_label(msp, disease_type, area, label_start_x, label_start_y)
            elif '剥落' in disease_type or '破损' in disease_type:
                bbox = draw_peel_off_direct(msp, x1, y1, x2, y2)
                if area > 0:
                    label_start_x = bbox[2]
                    label_start_y = bbox[3]
                    draw_pier_disease_label(msp, disease_type, area, label_start_x, label_start_y)
            elif '蜂窝' in disease_type or '麻面' in disease_type:
                draw_pier_honeycomb(msp, x1, y1, x2, y2)
                if area > 0:
                    label_start_x = max(x2 + 2, (x1 + x2) / 2)
                    label_start_y = y2
                    draw_pier_disease_label(msp, disease_type, area, label_start_x, label_start_y)
            elif '裂缝' in disease_type:
                # 水平裂缝线
                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2
                msp.add_line((x1, mid_y), (x2, mid_y), dxfattribs={'color': 7})
                length = disease.get('length', 0)
                width = disease.get('width', 0)
                if length > 0:
                    label_start_x = x2
                    label_start_y = mid_y
                    msp.add_text(f'纵向裂缝 L={length:.2f}m', dxfattribs={'insert': (label_start_x + 2, label_start_y + 2.5), 'height': 2.5, 'color': 7})
                    if width > 0:
                        msp.add_text(f'W={width:.2f}mm', dxfattribs={'insert': (label_start_x + 2, label_start_y - 2.5), 'height': 2.5, 'color': 7})


def draw_pier_disease_label(msp, disease_type: str, area: float, label_start_x: float, label_start_y: float):
    """墩柱病害标注：折线引线 + 病害名 + 面积
    标注从病害边缘(label_start_x, label_start_y)引出
    """
    text_height = 2.5
    # 折线：第一段向上45度，第二段水平
    offset_45 = 5  # 45度线长度
    bend_x = label_start_x + offset_45  # 向右
    bend_y = label_start_y + offset_45  # 向上
    # 第二段水平线，长度根据文字长度决定
    seg2_len = max(12, len(disease_type) * 3 + len(f'{area:.2f}') * 5)
    end_x = bend_x + seg2_len
    end_y = bend_y
    # 绘制折线：从病害边缘开始
    msp.add_lwpolyline([(label_start_x, label_start_y), (bend_x, bend_y), (end_x, end_y)], dxfattribs={'color': 7})
    # 上方：病害名称
    msp.add_text(disease_type, dxfattribs={
        'insert': (bend_x + 1, bend_y + text_height * 0.3),
        'height': text_height, 'color': 7
    })
    # 下方：面积
    msp.add_text(f'S={area:.2f}m²', dxfattribs={
        'insert': (bend_x + 1, bend_y - text_height * 1.5),
        'height': text_height, 'color': 7
    })


def draw_pier_honeycomb(msp, x1: float, y1: float, x2: float, y2: float):
    """墩柱蜂窝麻面：矩形内画点阵填充"""
    dot_spacing = 2.5
    dot_r = 0.4
    min_x, max_x = min(x1, x2), max(x1, x2)
    min_y, max_y = min(y1, y2), max(y1, y2)
    x = min_x + dot_spacing / 2
    while x < max_x:
        y = min_y + dot_spacing / 2
        while y < max_y:
            msp.add_circle((x, y), dot_r, dxfattribs={'color': 5})
            y += dot_spacing
        x += dot_spacing


def copy_entity_with_offset(msp, entity, y_offset: float):
    """复制实体并应用Y偏移"""
    entity_type = entity.dxftype()
    layer = entity.dxf.layer if hasattr(entity.dxf, 'layer') else '0'
    color = entity.dxf.color if hasattr(entity.dxf, 'color') else 7

    if entity_type == 'TEXT':
        text = entity.dxf.text
        height = entity.dxf.height if hasattr(entity.dxf, 'height') else 2.5
        old_x, old_y = entity.dxf.insert[0], entity.dxf.insert[1]
        new_pos = (old_x, old_y + y_offset)
        text_obj = msp.add_text(text, dxfattribs={'layer': layer, 'color': color, 'height': height})
        text_obj.dxf.insert = new_pos
        return text_obj

    elif entity_type == 'MTEXT':
        old_x, old_y = entity.dxf.insert[0], entity.dxf.insert[1]
        new_pos = (old_x, old_y + y_offset)
        mtxt = msp.add_mtext(entity.text, dxfattribs={'layer': layer})
        mtxt.dxf.insert = new_pos
        if hasattr(entity.dxf, 'char_height'):
            mtxt.dxf.char_height = entity.dxf.char_height
        if hasattr(entity.dxf, 'rect_width'):
            mtxt.dxf.rect_width = entity.dxf.rect_width
        return mtxt

    elif entity_type == 'LINE':
        start = entity.dxf.start
        end = entity.dxf.end
        new_start = (start[0], start[1] + y_offset)
        new_end = (end[0], end[1] + y_offset)
        return msp.add_line(new_start, new_end, dxfattribs={'layer': layer, 'color': color})

    elif entity_type == 'LWPOLYLINE':
        points = []
        if hasattr(entity, 'get_points'):
            for pt in entity.get_points():
                points.append((pt[0], pt[1] + y_offset))
        if points:
            return msp.add_lwpolyline(points, dxfattribs={'layer': layer, 'color': color})
        return None

    elif entity_type == 'SPLINE':
        try:
            from ezdxf.math import BSpline
            if hasattr(entity, 'control_points') and entity.control_points:
                control_points = [(pt[0], pt[1] + y_offset, 0) for pt in entity.control_points]
                spline = BSpline(control_points)
                return msp.add_spline(spline, dxfattribs={'layer': layer, 'color': color})
        except:
            pass
        return None

    elif entity_type == 'HATCH':
        try:
            return msp.add_hatch(entity.dxf.pattern_name, dxfattribs={'layer': layer})
        except:
            return None

    elif entity_type == 'INSERT':
        block_name = entity.dxf.name
        old_x, old_y = entity.dxf.insert[0], entity.dxf.insert[1]
        new_pos = (old_x, old_y + y_offset)
        x_scale = entity.dxf.xscale if hasattr(entity.dxf, 'xscale') else 1
        y_scale = entity.dxf.yscale if hasattr(entity.dxf, 'yscale') else 1
        z_scale = entity.dxf.zscale if hasattr(entity.dxf, 'zscale') else 1
        rotation = entity.dxf.rotation if hasattr(entity.dxf, 'rotation') else 0
        return msp.add_blockref(block_name, new_pos, dxfattribs={
            'layer': layer, 'xscale': x_scale, 'yscale': y_scale, 'zscale': z_scale, 'rotation': rotation
        })

    elif entity_type == 'CIRCLE':
        center = entity.dxf.center
        radius = entity.dxf.radius
        new_center = (center[0], center[1] + y_offset)
        return msp.add_circle(new_center, radius, dxfattribs={'layer': layer, 'color': color})

    elif entity_type == 'ARC':
        center = entity.dxf.center
        radius = entity.dxf.radius
        start_angle = entity.dxf.start_angle
        end_angle = entity.dxf.end_angle
        new_center = (center[0], center[1] + y_offset)
        return msp.add_arc(new_center, radius, start_angle, end_angle, dxfattribs={'layer': layer, 'color': color})

    else:
        return None


def main():
    print('='*60)
    print('桥梁病害CAD标注系统 - 下部（双柱墩12.5）处理')
    print('='*60)

    excel_path = os.path.join(BASE_DIR, 'K572+774红石牡丹江大桥（右幅）病害.xls')
    print(f'\n读取Excel文件: {excel_path}')

    data = parse_excel(excel_path)
    route_name = data['route_name']
    bridge_name = data['bridge_name']

    print(f'路线名称: {route_name}')
    print(f'桥梁名称: {bridge_name}')

    # 筛选下部（双柱墩）数据
    lower_parts = []
    for part in data['parts']:
        if '双柱墩' in part['name']:
            lower_parts.append(part)

    if not lower_parts:
        print('未找到下部（双柱墩）数据！')
        return

    print(f'\n下部（双柱墩）构件数量: {len(lower_parts)}')

    # 收集所有盖梁和墩柱病害
    cap_beam_diseases = {}  # {盖梁号: [病害列表]}
    pier_diseases = {}  # {墩柱号: [病害列表]}

    for part in lower_parts:
        for comp_id, diseases in part['grouped_data'].items():
            for d in diseases:
                location = d.get('缺损位置', '')
                if '墩柱' in location:
                    # 墩柱号是整数(如4)，柱内编号也是整数(如1)
                    # 需要组合成完整字符串如"4-1号"
                    pier_int = d.get('墩柱号')
                    col_int = d.get('柱内编号')
                    if pier_int is not None and col_int is not None:
                        pier_no = f'{pier_int}-{col_int}号'
                    elif pier_int is not None:
                        pier_no = f'{pier_int}号'
                    else:
                        pier_no = d.get('构件编号', '')
                    if pier_no:
                        if pier_no not in pier_diseases:
                            pier_diseases[pier_no] = []
                        pier_diseases[pier_no].append(d)
                else:
                    # 盖梁
                    cap_no = d.get('盖梁号')
                    if cap_no:
                        if cap_no not in cap_beam_diseases:
                            cap_beam_diseases[cap_no] = []
                        cap_beam_diseases[cap_no].append(d)

    print(f'\n盖梁构件: {sorted(cap_beam_diseases.keys())}')
    print(f'墩柱构件: {sorted(pier_diseases.keys())}')

    # 配对：按编号排序
    # 盖梁号是整数(如4)，墩柱号是字符串(如"4-1号")
    # 配对规则：墩柱号 "n-m号" 的 n 与盖梁号 n 匹配
    def get_cap_base(no):
        """提取编号的主编号，如 '4-1号' -> '4', 4 -> '4'"""
        if no is None:
            return None
        s = str(no)
        if '-' in s:
            return s.split('-')[0].replace('号', '').strip()
        return s.replace('号', '').strip()

    all_nos = set()
    for cap_no in cap_beam_diseases.keys():
        all_nos.add(str(cap_no))  # 统一转字符串
    for pier_no in pier_diseases.keys():
        base = get_cap_base(pier_no)
        if base:
            all_nos.add(base)

    page_pairs = []
    for no in sorted(all_nos, key=lambda x: int(x) if x.isdigit() else 0):
        cap_no = no  # 盖梁号直接用no
        # 查找对应的墩柱号: pier_no 的 base == no
        pier_no = None
        for p_no in pier_diseases.keys():
            if get_cap_base(p_no) == no:
                pier_no = p_no
                break
        page_pairs.append((cap_no, pier_no))

    print(f'\n配对结果: {len(page_pairs)} 页')
    for cap, pier in page_pairs:
        print(f'  盖梁{cap} + 墩柱{pier}')

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    output_files = []

    # 处理每一页
    for idx, (cap_no, pier_no) in enumerate(page_pairs):
        print(f'\n处理第{idx+1}页: 盖梁{cap_no} + 墩柱{pier_no}')

        # 复制模板
        doc = ezdxf.readfile(TEMPLATE_FILE)
        msp = doc.modelspace()

        # 修改标题
        update_text_in_msp(msp, 'LLL', route_name, height=6)
        update_text_in_msp(msp, 'QQQ', bridge_name, height=6)
        if cap_no:
            update_text_in_msp(msp, 'GGG', f'{cap_no}号盖梁', height=6)

        # 绘制盖梁病害
        if cap_no:
            # cap_no是字符串，但cap_beam_diseases键可能是整数，尝试两种方式查找
            cap_key = int(cap_no) if cap_no.isdigit() else cap_no
            diseases = cap_beam_diseases.get(cap_key) or cap_beam_diseases.get(cap_no)
            if diseases:
                for disease in diseases:
                    print(f'  盖梁{cap_no} {disease.get("缺损位置", "")} {disease.get("病害类型", "")}')
                    process_cap_beam_disease(msp, disease)

        # 绘制墩柱病害
        if pier_no and pier_no in pier_diseases:
            for disease in pier_diseases[pier_no]:
                print(f'  墩柱{pier_no} {disease.get("缺损位置", "")} {disease.get("病害类型", "")}')
                process_pier_disease(msp, disease)

        # 保存
        output_path = os.path.join(OUTPUT_DIR, f'下部病害_第{idx+1}页_v2.dxf')
        doc.saveas(output_path)
        output_files.append(output_path)
        print(f'  已保存: {output_path}')

    # 创建合并文件
    if output_files:
        print('\n' + '='*60)
        print('创建最终合并文件...')

        final_doc = ezdxf.readfile(TEMPLATE_FILE)
        final_msp = final_doc.modelspace()

        # 清空
        for entity in list(final_msp):
            entity.destroy()

        # 添加桥梁名称标题
        final_msp.add_text(bridge_name, dxfattribs={'height': 20, 'layer': '0'})

        # 复制每页
        page_height = 253  # 图框高度
        gap = 100  # 间距
        title_gap = 100

        for i, output_file in enumerate(output_files):
            if os.path.exists(output_file):
                print(f'  复制第{i+1}页...')
                y_offset = -(title_gap + page_height + i * (page_height + gap))

                page_doc = ezdxf.readfile(output_file)
                page_msp = page_doc.modelspace()

                for entity in page_msp:
                    try:
                        copy_entity_with_offset(final_msp, entity, y_offset)
                    except Exception as e:
                        print(f'    复制实体失败: {e}')

        final_output = os.path.join(BASE_DIR, '下部病害_合并结果.dxf')
        final_doc.saveas(final_output)
        print(f'\n最终文件已保存: {final_output}')

    print('='*60)


if __name__ == '__main__':
    main()

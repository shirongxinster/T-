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
# 1m 对应 X方向 14.5 CAD单位
# 1m 对应 Y方向 16.2 CAD单位
SCALE_X = 14.5  # X方向比例
SCALE_Y = 16.2  # Y方向比例

# 路径配置
BASE_DIR = r"k:\works\008.S2ReportAndLayoutPic\leftRealJobs_workbuddy"
INPUT_DIR = os.path.join(BASE_DIR, "input")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates", "构件")
LEGENDS_DIR = os.path.join(BASE_DIR, "templates", "病害图例")
OUTPUT_DIR = os.path.join(BASE_DIR, "output_pages")
TEMPLATE_FILE = os.path.join(TEMPLATES_DIR, "双柱墩12.5.dxf")
PEEL_LEGEND_FILE = os.path.join(LEGENDS_DIR, "剥落、掉角.dxf")
PEEL_REBAR_LEGEND_FILE = os.path.join(LEGENDS_DIR, "剥落、漏筋.dxf")

# 桥台模板文件
ABUT_WITH_TAI_TEMPLATE = os.path.join(TEMPLATES_DIR, "带台身桥台.dxf")
ABUT_WITHOUT_TAI_TEMPLATE = os.path.join(TEMPLATES_DIR, "不带台身桥台.dxf")

# 桥台坐标比例（根据桥台类型和部位）
# 不带桥身的桥台
ABUT_WITHOUT_SCALE_X = 15.0
ABUT_WITHOUT_SCALE_Y = 15.6

# 带桥身桥台的比例
# 台帽
ABUT_WITH_CAP_SCALE_X = 15.4
ABUT_WITH_CAP_SCALE_Y = 55.0
# 台身
ABUT_WITH_TAI_SCALE_X = 15.4
ABUT_WITH_TAI_SCALE_Y = 16.0

# 单柱墩模板文件
SINGLE_PIER_TEMPLATE = os.path.join(TEMPLATES_DIR, "单柱墩.dxf")

# 单柱墩坐标比例（独立转换系统）
SINGLE_PIER_SCALE_X = 16.7  # X方向比例
SINGLE_PIER_SCALE_Y = 13.0  # Y方向比例

# 剥落图例原始数据
PEEL_OFF_GEOMETRY = None
PEEL_REBAR_GEOMETRY = None


def load_peel_rebar_geometry():
    """从剥落露筋图例模板加载原始几何数据"""
    global PEEL_REBAR_GEOMETRY
    if PEEL_REBAR_GEOMETRY is not None:
        return PEEL_REBAR_GEOMETRY

    doc = ezdxf.readfile(PEEL_REBAR_LEGEND_FILE)
    block = doc.blocks.get("adfsd")

    lines = []
    polyline = []

    for entity in block:
        if entity.dxftype() == "LINE":
            lines.append(
                {
                    "start": (entity.dxf.start[0], entity.dxf.start[1]),
                    "end": (entity.dxf.end[0], entity.dxf.end[1]),
                }
            )
        elif entity.dxftype() == "LWPOLYLINE":
            pts = list(entity.get_points())
            polyline = [(p[0], p[1]) for p in pts]

    all_points = []
    for line in lines:
        all_points.extend([line["start"], line["end"]])
    all_points.extend(polyline)

    if all_points:
        xs = [p[0] for p in all_points]
        ys = [p[1] for p in all_points]
        bbox = {"min_x": min(xs), "max_x": max(xs), "min_y": min(ys), "max_y": max(ys)}
    else:
        bbox = {"min_x": 0, "max_x": 1, "min_y": 0, "max_y": 1}

    PEEL_REBAR_GEOMETRY = {"lines": lines, "polyline": polyline, "bbox": bbox}
    return PEEL_REBAR_GEOMETRY


def load_peel_off_geometry():
    """从剥落图例模板加载原始几何数据"""
    global PEEL_OFF_GEOMETRY
    if PEEL_OFF_GEOMETRY is not None:
        return PEEL_OFF_GEOMETRY

    doc = ezdxf.readfile(PEEL_LEGEND_FILE)
    block = doc.blocks.get("adfsd")

    lines = []
    polyline = []

    for entity in block:
        if entity.dxftype() == "LINE":
            lines.append(
                {
                    "start": (entity.dxf.start[0], entity.dxf.start[1]),
                    "end": (entity.dxf.end[0], entity.dxf.end[1]),
                }
            )
        elif entity.dxftype() == "LWPOLYLINE":
            pts = list(entity.get_points())
            polyline = [(p[0], p[1]) for p in pts]

    all_points = []
    for line in lines:
        all_points.extend([line["start"], line["end"]])
    all_points.extend(polyline)

    if all_points:
        xs = [p[0] for p in all_points]
        ys = [p[1] for p in all_points]
        bbox = {"min_x": min(xs), "max_x": max(xs), "min_y": min(ys), "max_y": max(ys)}
    else:
        bbox = {"min_x": 0, "max_x": 1, "min_y": 0, "max_y": 1}

    PEEL_OFF_GEOMETRY = {"lines": lines, "polyline": polyline, "bbox": bbox}
    return PEEL_OFF_GEOMETRY


# 双柱墩坐标系统
# 盖梁坐标系：x轴向右，y轴向下
CAP_BEAM_ORIGINS = {
    "小桩号面": (45, 251),
    "大桩号面": (305, 250),
    "左挡块": {"rect": (45, 257, 252, 53)},  # (x1, y1, y2, x2) CAD坐标
    "右挡块": {"rect": (218, 253, 250, 224)},
    "左挡块_大": {"rect": (306, 257, 252, 314)},
    "右挡块_大": {"rect": (477, 253, 250, 484)},
    "右侧面": {"rect": (177, 123, 100, 207)},  # 盖梁右侧面矩形 (x1, y1, y2, x2)
    "内侧面": {"rect": (75, 123, 100, 104)},  # 盖梁内侧面矩形
}

# 墩柱坐标系：x轴向下，y轴向右
# rect格式：(x1, y1, x2, y2) CAD坐标
PIER_ORIGINS = {
    "小桩号面": {
        "N-1": {"rect": (70, 224, 91, 190)},  # 左柱
        "N-2": {"rect": (70, 224, 91, 190)},  # 右柱（用户未提供具体值，用左柱代替）
    },
    "大桩号面": {
        "N-1": {"rect": (330, 224, 351, 190)},  # 右柱
        "N-2": {"rect": (439, 224, 460, 190)},  # 左柱
    },
    "外侧面": {"rect": (181, 100, 200, 70)},
    "内侧面": {"rect": (80, 100, 100, 70)},
}

# 桥台坐标系统（右下倾斜1度）
# 台帽坐标原点：(66,245)
# 台身坐标原点：带台身(66,219)，不带台身(57,219)
ABUT_ORIGINS = {
    "带台身桥台": {
        "台帽": (66, 245),
        "台身": (66, 219),
    },
    "不带台身桥台": {
        "台身": (57, 219),
    }
}

# 单柱墩坐标系统（右下倾斜1度）
# 盖梁坐标系：x轴向右，y轴向下
SINGLE_PIER_ORIGINS = {
    "小桩号面": (52, 264),
    "大桩号面": (294, 264),
    "右侧面": {"rect": (178, 130, 202, 70)},  # 右侧面矩形 (x1, y1, x2, y2)
    "内侧面": {"rect": (76, 130, 100, 70)},   # 内侧面矩形 (x1, y1, x2, y2)
}

# 单柱墩柱子坐标系：x轴向下，y轴向右
# rect格式：(x1, y1, x2, y2) CAD坐标
SINGLE_PIER_COLUMNS = {
    "小桩号面": {"rect": (143, 233, 167, 194)},  # 小桩号面柱子
    "大桩号面": {"rect": (385, 233, 409, 194)},  # 大桩号面柱子
}


def load_honeycomb_geometry():
    """加载蜂窝麻面图例的几何数据"""
    import ezdxf
    from ezdxf.bbox import extents

    doc = ezdxf.readfile("./templates/病害图例/蜂窝麻面.dxf")
    msp = doc.modelspace()

    entities = []
    bbox = extents(msp)

    for entity in msp:
        entities.append(
            {
                "type": entity.dxftype(),
                "dxfattribs": {"color": 7},  # 白色
                "data": entity,
            }
        )

    return {
        "entities": entities,
        "bbox": {
            "min_x": bbox.extmin[0],
            "min_y": bbox.extmin[1],
            "max_x": bbox.extmax[0],
            "max_y": bbox.extmax[1],
        },
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

    print(
        f"    [露筋] 目标区域: ({min_x:.1f},{min_y:.1f}) ~ ({max_x:.1f},{max_y:.1f}), 尺寸: {dst_w:.1f}x{dst_h:.1f}"
    )

    # 加载钢筋锈蚀图例文件
    legend_file = os.path.join(
        BASE_DIR, "templates", "病害图例", "钢筋锈蚀或可见箍筋轮廓.dxf"
    )
    legend_doc = ezdxf.readfile(legend_file)
    legend_msp = legend_doc.modelspace()

    # 获取图例边界框（排除文字）
    non_text_entities = [e for e in legend_msp if e.dxftype() not in ["TEXT", "MTEXT"]]
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

    print(f"    [露筋] 缩放{scale:.2f}, 平铺: {n_cols}x{n_rows}={n_cols * n_rows}个")

    # 平铺复制
    entity_count = 0
    for row in range(n_rows):
        for col in range(n_cols):
            tile_x = start_x + col * scaled_w
            tile_y = start_y + row * scaled_h

            # 变换：p_new = p * scale + (tile - src_min * scale)
            dx = tile_x - src_min_x * scale
            dy = tile_y - src_min_y * scale
            transform = Matrix44(
                [scale, 0, 0, 0, 0, scale, 0, 0, 0, 0, 1, 0, dx, dy, 0, 1]
            )

            for entity in legend_msp:
                dxftype = entity.dxftype()
                if dxftype == "MTEXT":
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
        if entity.dxftype() == "TEXT":
            if old_text in entity.dxf.text:
                entity.dxf.text = entity.dxf.text.replace(old_text, new_text)
                if height is not None:
                    entity.dxf.height = height
        elif entity.dxftype() == "MTEXT":
            content = entity.text
            if old_text in content:
                entity.text = content.replace(old_text, new_text)
                if height is not None:
                    entity.dxf.char_height = height


def convert_to_cad_coords_lower(x: float, y: float, origin: tuple, scale_x: float = SCALE_X, scale_y: float = SCALE_Y) -> tuple:
    """
    双柱墩坐标转换
    origin: (origin_x, origin_y) - 左上角
    X方向: 1m = scale_x CAD单位，向右
    Y方向: 1m = scale_y CAD单位，向下（所以要减）

    桥面向右下倾斜1度，需要反向修正
    """
    # 基础CAD坐标
    cad_x = origin[0] + x * scale_x
    cad_y = origin[1] - y * scale_y

    # 桥面向右下倾斜1度，反向修正（以origin为旋转中心）
    angle_rad = math.radians(1)

    # 计算相对于原点的坐标
    dx = cad_x - origin[0]
    dy = cad_y - origin[1]

    # 顺时针旋转1度
    new_dx = dx * math.cos(angle_rad) + dy * math.sin(angle_rad)
    new_dy = -dx * math.sin(angle_rad) + dy * math.cos(angle_rad)

    return (origin[0] + new_dx, origin[1] + new_dy)


def convert_to_cad_coords_abut(x: float, y: float, origin: tuple, scale_x: float = SCALE_X, scale_y: float = SCALE_Y) -> tuple:
    """
    桥台坐标转换（右下倾斜1度）
    origin: (origin_x, origin_y) - 左上角
    X方向: 1m = scale_x CAD单位，向右
    Y方向: 1m = scale_y CAD单位，向下（所以要减）

    桥面向右下倾斜1度，需要反向修正
    """
    # 基础CAD坐标
    cad_x = origin[0] + x * scale_x
    cad_y = origin[1] - y * scale_y

    # 桥面向右下倾斜1度，反向修正（以origin为旋转中心）
    angle_rad = math.radians(1)

    # 计算相对于原点的坐标
    dx = cad_x - origin[0]
    dy = cad_y - origin[1]

    # 顺时针旋转1度
    new_dx = dx * math.cos(angle_rad) + dy * math.sin(angle_rad)
    new_dy = -dx * math.sin(angle_rad) + dy * math.cos(angle_rad)

    return (origin[0] + new_dx, origin[1] + new_dy)


def draw_peel_off_direct(msp, x1: float, y1: float, x2: float, y2: float):
    """直接在CAD坐标绘制剥落图形（用于挡块、侧面等）
    返回实际绘制的边界框 (min_x, min_y, max_x, max_y)
    """
    geo = load_peel_off_geometry()
    bbox = geo["bbox"]

    src_w = bbox["max_x"] - bbox["min_x"]
    src_h = bbox["max_y"] - bbox["min_y"]
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
    for line in geo["lines"]:
        sx, sy = line["start"]
        ex, ey = line["end"]
        dx = (ex - sx) * scale
        dy = (ey - sy) * scale
        new_start = (
            center_x - dst_w / 2 + (sx - bbox["min_x"]) * scale,
            center_y - dst_h / 2 + (sy - bbox["min_y"]) * scale,
        )
        new_end = (new_start[0] + dx, new_start[1] + dy)
        msp.add_line(new_start, new_end, dxfattribs={"color": 7})

    # 绘制多边形
    if geo["polyline"]:
        pts = []
        for px, py in geo["polyline"]:
            pts.append(
                (
                    center_x - dst_w / 2 + (px - bbox["min_x"]) * scale,
                    center_y - dst_h / 2 + (py - bbox["min_y"]) * scale,
                )
            )
        msp.add_lwpolyline(pts, dxfattribs={"color": 7})

    return (actual_min_x, actual_min_y, actual_max_x, actual_max_y)


def draw_peel_off(
    msp,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    origin: tuple,
    return_bbox: bool = False,
    scale_x: float = SCALE_X,
    scale_y: float = SCALE_Y
):
    """绘制剥落图例"""
    geo = load_peel_off_geometry()
    bbox = geo["bbox"]

    # 计算缩放比例
    src_w = bbox["max_x"] - bbox["min_x"]
    src_h = bbox["max_y"] - bbox["min_y"]
    dst_w = (x2 - x1) * scale_x * 0.8  # 目标宽度（留点边距）
    dst_h = (y2 - y1) * scale_y * 0.8

    if src_w > 0 and src_h > 0:
        scale_x_calc = dst_w / src_w
        scale_y_calc = dst_h / src_h
        scale = min(scale_x_calc, scale_y_calc)
    else:
        scale = 1

    # 目标中心（使用scale_x和scale_y进行坐标转换）
    # Y方向是向下的，所以用减号；并应用1度向右下倾斜修正
    center_x = (x1 + x2) / 2 * scale_x + origin[0]
    center_y = origin[1] - (y1 + y2) / 2 * scale_y
    
    # 应用1度向右下倾斜修正（以origin为旋转中心）
    angle_rad = math.radians(1)
    dx = center_x - origin[0]
    dy = center_y - origin[1]
    new_dx = dx * math.cos(angle_rad) + dy * math.sin(angle_rad)
    new_dy = -dx * math.sin(angle_rad) + dy * math.cos(angle_rad)
    center_x = origin[0] + new_dx
    center_y = origin[1] + new_dy

    # 绘制线条
    for line in geo["lines"]:
        sx, sy = line["start"]
        ex, ey = line["end"]
        dx = (ex - sx) * scale
        dy = (ey - sy) * scale
        new_start = (
            center_x - dst_w / 2 + (sx - bbox["min_x"]) * scale,
            center_y - dst_h / 2 + (sy - bbox["min_y"]) * scale,
        )
        new_end = (new_start[0] + dx, new_start[1] + dy)
        msp.add_line(new_start, new_end, dxfattribs={"color": 7})

    # 绘制多边形
    if geo["polyline"]:
        pts = []
        for px, py in geo["polyline"]:
            pts.append(
                (
                    center_x - dst_w / 2 + (px - bbox["min_x"]) * scale,
                    center_y - dst_h / 2 + (py - bbox["min_y"]) * scale,
                )
            )
        msp.add_lwpolyline(pts, dxfattribs={"color": 7})

    if return_bbox:
        return (
            center_x - dst_w / 2,
            center_y - dst_h / 2,
            center_x + dst_w / 2,
            center_y + dst_h / 2,
        )
    return None


def draw_peel_rebar(
    msp,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    origin: tuple,
    return_bbox: bool = False,
):
    """绘制剥落露筋图例 = 剥落不规则图形 + 叠加红色虚线交叉格栅

    与上部程序的 draw_peel_off_with_rebar 保持一致：
    1. 使用模板文件绘制剥落不规则图形
    2. 在实际边界框范围内叠加 3x3 红色虚线格栅
    """
    geo = load_peel_off_geometry()
    bbox = geo["bbox"]

    # 计算缩放比例
    src_w = bbox["max_x"] - bbox["min_x"]
    src_h = bbox["max_y"] - bbox["min_y"]
    dst_w = (x2 - x1) * SCALE_X * 0.8  # 目标宽度（留点边距）
    dst_h = (y2 - y1) * SCALE_Y * 0.8

    if src_w > 0 and src_h > 0:
        scale_x = dst_w / src_w
        scale_y = dst_h / src_h
        scale = min(scale_x, scale_y)
    else:
        scale = 1

    # 目标中心（使用SCALE_X和SCALE_Y进行坐标转换）
    center_x = (x1 + x2) / 2 * SCALE_X + origin[0]
    center_y = origin[1] - (y1 + y2) / 2 * SCALE_Y

    # 应用1度向右下倾斜修正（以origin为旋转中心）
    angle_rad = math.radians(1)
    dx = center_x - origin[0]
    dy = center_y - origin[1]
    new_dx = dx * math.cos(angle_rad) + dy * math.sin(angle_rad)
    new_dy = -dx * math.sin(angle_rad) + dy * math.cos(angle_rad)
    center_x = origin[0] + new_dx
    center_y = origin[1] + new_dy

    # 计算实际边界框
    actual_min_x = center_x - dst_w / 2
    actual_max_x = center_x + dst_w / 2
    actual_min_y = center_y - dst_h / 2
    actual_max_y = center_y + dst_h / 2

    # 绘制剥落模板图形（线条）
    for line in geo["lines"]:
        sx, sy = line["start"]
        ex, ey = line["end"]
        dx = (ex - sx) * scale
        dy = (ey - sy) * scale
        new_start = (
            actual_min_x + (sx - bbox["min_x"]) * scale,
            actual_min_y + (sy - bbox["min_y"]) * scale,
        )
        new_end = (new_start[0] + dx, new_start[1] + dy)
        msp.add_line(new_start, new_end, dxfattribs={"color": 7})

    # 绘制剥落模板图形（多边形）
    if geo["polyline"]:
        pts = []
        for px, py in geo["polyline"]:
            pts.append(
                (
                    actual_min_x + (px - bbox["min_x"]) * scale,
                    actual_min_y + (py - bbox["min_y"]) * scale,
                )
            )
        msp.add_lwpolyline(pts, dxfattribs={"color": 7})

    # 叠加 3x3 红色虚线格栅（在实际边界框范围内）
    height = actual_max_y - actual_min_y
    width = actual_max_x - actual_min_x

    grid_color = 1
    # 3条横线（分成4等份，取i=1,2,3等分点）
    for i in range(1, 4):
        y = actual_min_y + height * i / 4
        msp.add_line(
            (actual_min_x, y), (actual_max_x, y), dxfattribs={"color": grid_color, "linetype": "DASHED"}
        )
    # 3条竖线
    for i in range(1, 4):
        x = actual_min_x + width * i / 4
        msp.add_line(
            (x, actual_min_y), (x, actual_max_y), dxfattribs={"color": grid_color, "linetype": "DASHED"}
        )

    if return_bbox:
        return (actual_min_x, actual_max_y, actual_max_x, actual_min_y)
    return None


def draw_polyline_leader(
    msp, start_x: float, start_y: float, seg2_len: float, go_left: bool = False
):
    """绘制折线引线

    Args:
        go_left: 如果为True，第二段向左画（seg2_len为负）
    """
    seg1_len = 8
    # 基础角度45度 + 桥面倾斜1度 = 46度（向右下倾斜）
    angle = math.radians(45 + 1)

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
    msp.add_lwpolyline(points=points, dxfattribs={"color": 7})

    return (bend_x, bend_y, end_x, end_y)


def calculate_start_point(disease: dict, origin: tuple, other_diseases: list = None, go_left: bool = False):
    """
    计算引线起点（差异化策略）
    
    规则：
    1. 区域病害（有y_start!=y_end）：
       - 引线向右下（默认）：从右下角引出
       - 引线向左上（go_left=True）：从左上角引出
    2. 线段病害（y_start==y_end）：从端点引出
       - 如果有邻近病害在右侧，从左端点引出
       - 如果有邻近病害在左侧，从右端点引出
       - 默认从左端点引出
    """
    if other_diseases is None:
        other_diseases = []
    
    x_start = disease.get('x_start', 0)
    x_end = disease.get('x_end', 0)
    y_start = disease.get('y_start', 0)
    y_end = disease.get('y_end', 0)
    
    # 左边界保护
    min_x = origin[0] + 2
    
    if y_start != y_end:
        # 区域病害（竖向裂缝群、剥落等）
        # 根据引线方向选择引出点
        # 注意：CAD中Y值越小越靠上，所以：
        # - 左上角 = (x_start, y_start)，y值小（靠上）
        # - 右下角 = (x_end, y_end)，y值大（靠下）
        if go_left:
            # 向左上引线，从左上角引出
            start_x = x_start * SCALE_X + origin[0]
            start_y = origin[1] - y_start * SCALE_Y
        else:
            # 向右下引线（默认），从右下角引出
            start_x = x_end * SCALE_X + origin[0]
            start_y = origin[1] - y_end * SCALE_Y
        
        # 应用1度向右下倾斜修正（以origin为旋转中心）
        angle_rad = math.radians(1)
        dx = start_x - origin[0]
        dy = start_y - origin[1]
        new_dx = dx * math.cos(angle_rad) + dy * math.sin(angle_rad)
        new_dy = -dx * math.sin(angle_rad) + dy * math.cos(angle_rad)
        start_x = origin[0] + new_dx
        start_y = origin[1] + new_dy
        
        # 左边界检查
        if start_x < min_x:
            start_x = min_x
    else:
        # 线段病害（纵向裂缝）
        # 检查邻近病害位置
        nearby_right = any(d.get('x_start', 0) > x_end for d in other_diseases)
        nearby_left = any(d.get('x_end', 0) < x_start for d in other_diseases)
        
        if nearby_right and not nearby_left:
            # 右侧有邻近病害，从左端点引出（向右引线）
            start_x = x_start * SCALE_X + origin[0]
        elif nearby_left and not nearby_right:
            # 左侧有邻近病害，从右端点引出（向左引线）
            start_x = x_end * SCALE_X + origin[0]
        else:
            # 默认从左端点引出
            start_x = x_start * SCALE_X + origin[0]
        
        # 左边界检查
        if start_x < min_x:
            start_x = min_x
        
        start_y = origin[1] - y_start * SCALE_Y
        
        # 应用1度修正
        angle_rad = math.radians(1)
        dx = start_x - origin[0]
        dy = start_y - origin[1]
        new_dx = dx * math.cos(angle_rad) + dy * math.sin(angle_rad)
        new_dy = -dx * math.sin(angle_rad) + dy * math.cos(angle_rad)
        start_x = origin[0] + new_dx
        start_y = origin[1] + new_dy
    
    return start_x, start_y


def get_safe_angle(disease: dict, start_x: float, start_y: float, seg1_len: float, origin: tuple, used_angles: list):
    """
    获取安全角度（根据病害位置智能选择方向）
    
    规则：
    1. 水平方向：以构件中心线为界
       - 病害在中心线左侧 → 引线向右（角度45或315）
       - 病害在中心线右侧 → 引线向左（角度135或225）
    2. 垂直方向：以构件垂直中心为界
       - 病害在上方 → 引线向下（角度315或225）
       - 病害在下方 → 引线向上（角度45或135）
    
    Args:
        disease: 病害数据
        start_x, start_y: 引线起点（CAD坐标）
        seg1_len: 第一段长度
        origin: CAD原点
        used_angles: 已使用的角度列表
    
    Returns:
        safe_angle: 安全角度
        go_left: 是否向左标注
    """
    # 获取病害中点坐标（用于判断位置）
    x_mid = (disease.get('x_start', 0) + disease.get('x_end', 0)) / 2
    y_mid = (disease.get('y_start', 0) + disease.get('y_end', 0)) / 2
    
    # 根据构件类型确定中心线
    location = disease.get('缺损位置', '')
    component_part = disease.get('具体部件', '')
    
    # 判断构件类型和中心线
    # 双柱墩盖梁：小桩号面(45,251)和大桩号面(305,250)，X中心约175
    # 单柱墩盖梁：小桩号面(52,264)和大桩号面(294,264)，X中心约173
    # 桥台：根据类型不同，中心线约在原点X+5m处
    
    if '盖梁' in component_part or '盖梁' in location:
        # 盖梁：小桩号面和大桩号面，X范围约0-12m
        x_center_m = 6.0  # 盖梁X方向中心（米）
        y_center_m = 0.5  # 盖梁Y方向中心（米），假设总高度约1m
    elif '墩柱' in component_part or '墩柱' in location:
        # 墩柱：X范围较小，主要分左右两侧
        x_center_m = 0.5  # 墩柱X方向中心（米）
        y_center_m = 3.5  # 墩柱Y方向中心（米），假设总高度约7m
    elif '台身' in component_part or '台身' in location:
        # 台身
        x_center_m = 5.0
        y_center_m = 2.0
    elif '台帽' in component_part or '台帽' in location:
        # 台帽
        x_center_m = 5.0
        y_center_m = 0.5
    else:
        # 默认中心
        x_center_m = 6.0
        y_center_m = 1.0
    
    # 判断水平方向（左/右）
    go_right = x_mid < x_center_m  # 病害在中心线左侧 → 向右引线
    
    # 判断垂直方向（上/下）
    go_up = y_mid < y_center_m  # 病害在中心线下方（y小）→ 向上引线
    
    # 根据方向组合确定首选角度
    if go_right and go_up:
        preferred_angle = 45   # 右上
        go_left = False
    elif go_right and not go_up:
        preferred_angle = 315  # 右下
        go_left = False
    elif not go_right and go_up:
        preferred_angle = 135  # 左上
        go_left = True
    else:
        preferred_angle = 225  # 左下
        go_left = True
    
    # 检查首选角度是否安全（不超出边界）
    def is_angle_safe(angle, left):
        """检查角度是否满足边界约束"""
        end_y = start_y + seg1_len * math.sin(math.radians(angle))
        # 上边界检查：不能超出原点上方（origin[1]是上方，Y值小）
        if end_y > origin[1]:
            return False
        # 左边界检查（向左的角度）
        if left:
            end_x = start_x + seg1_len * math.cos(math.radians(angle))
            if end_x < origin[0]:
                return False
        return True
    
    # 如果首选角度安全且未被使用，直接返回
    if is_angle_safe(preferred_angle, go_left) and preferred_angle not in used_angles:
        return preferred_angle, go_left
    
    # 否则，收集所有安全角度
    candidates = []
    angles_to_check = [
        (45, False),   # 右上
        (315, False),  # 右下
        (135, True),   # 左上
        (225, True),   # 左下
    ]
    
    for angle, left in angles_to_check:
        if is_angle_safe(angle, left):
            candidates.append({'angle': angle, 'go_left': left})
    
    # 优先选择未被使用的角度
    for candidate in candidates:
        if candidate['angle'] not in used_angles:
            return candidate['angle'], candidate['go_left']
    
    # 如果没有未使用的角度，返回第一个安全角度
    if candidates:
        return candidates[0]['angle'], candidates[0]['go_left']
    
    # 默认返回首选角度（即使不安全）
    return preferred_angle, go_left


def find_nearby_diseases(current_disease: dict, all_diseases: list, threshold_m: float = 3.0):
    """
    查找邻近病害
    
    Args:
        current_disease: 当前病害
        all_diseases: 所有病害列表
        threshold_m: 距离阈值（米）
    
    Returns:
        nearby_diseases: 邻近病害列表
    """
    nearby = []
    
    # 当前病害中点
    cur_x = (current_disease.get('x_start', 0) + current_disease.get('x_end', 0)) / 2
    cur_y = (current_disease.get('y_start', 0) + current_disease.get('y_end', 0)) / 2
    
    for disease in all_diseases:
        if disease is current_disease:
            continue
        
        # 其他病害中点
        other_x = (disease.get('x_start', 0) + disease.get('x_end', 0)) / 2
        other_y = (disease.get('y_start', 0) + disease.get('y_end', 0)) / 2
        
        # 计算距离
        distance = math.sqrt((cur_x - other_x)**2 + (cur_y - other_y)**2)
        
        if distance <= threshold_m:
            nearby.append(disease)
    
    return nearby


def check_boundary_constraints(start_x, start_y, bend_x, bend_y, end_x, text_x, text_y_list, origin):
    """
    检查边界约束
    
    Returns:
        is_safe: 是否满足约束
        adjustments: 调整建议
    """
    is_safe = True
    adjustments = {}
    
    # 上边界检查（y <= origin_y）
    for text_y in text_y_list:
        if text_y > origin[1]:
            is_safe = False
            adjustments['offset_y'] = text_y - origin[1] + 2
            break
    
    # 左边界检查（x >= origin_x）
    if text_x < origin[0]:
        is_safe = False
        adjustments['offset_x'] = origin[0] - text_x + 2
    
    # 引线弯曲点检查
    if bend_x < origin[0]:
        is_safe = False
        adjustments['adjust_angle'] = True
    
    return is_safe, adjustments


def draw_disease_label_safe(
    msp,
    disease: dict,
    disease_type: str,
    value_text: str,
    start_x: float,
    start_y: float,
    seg2_len: float,
    angle: float,
    go_left: bool,
    origin: tuple,
):
    """
    绘制病害标注（带边界检查）
    
    Returns:
        bbox: 标注边界框
    """
    text_height = 2.5
    
    # 绘制引线
    bend_x, bend_y, end_x, end_y = draw_polyline_leader(
        msp, start_x, start_y, seg2_len, go_left
    )
    
    # 文字位置
    if go_left:
        text_x = bend_x - seg2_len - 1
    else:
        text_x = bend_x + 1
    
    # 上方：病害名称
    text1_y = bend_y + text_height * 0.5
    msp.add_text(
        disease_type,
        dxfattribs={
            "insert": (text_x, text1_y),
            "height": text_height,
            "color": 7,
        },
    )
    
    # 下方：病害数值
    if value_text:
        text2_y = bend_y - text_height * 1.5
        msp.add_text(
            value_text,
            dxfattribs={
                "insert": (text_x, text2_y),
                "height": text_height,
                "color": 7,
            },
        )
    else:
        text2_y = None
    
    # 计算边界框
    min_x = min(start_x, bend_x, end_x, text_x)
    max_x = max(end_x, text_x + seg2_len)  # 假设文字宽度约seg2_len
    
    if text2_y:
        min_y = min(start_y, text2_y - text_height)
        max_y = max(start_y, text1_y)
    else:
        min_y = min(start_y, bend_y - text_height * 2)
        max_y = max(start_y, text1_y)
    
    # 记录角度（用于下一个病害避让）
    disease['label_angle'] = angle
    
    return (min_x, min_y, max_x, max_y)


def draw_disease_label(
    msp,
    disease: dict,
    disease_type: str,
    value_text: str,
    start_x: float,
    start_y: float,
    seg2_len: float,
    angle: float = 315,
    go_left: bool = False,
    origin: tuple = (0, 0),
):
    """绘制病害标注（支持避让算法）

    Args:
        disease: 病害数据字典（用于记录角度）
        disease_type: 病害名称（如"纵向裂缝"）
        value_text: 病害数值（如"L=8.00m"）
        start_x, start_y: 病害区域引线起点位置
        seg2_len: 第二段水平线长度
        angle: 引线角度（度）
        go_left: 如果为True，标注向左画
        origin: CAD原点
    """
    text_height = 2.5
    
    # 使用带边界检查的标注绘制
    bbox = draw_disease_label_safe(
        msp, disease, disease_type, value_text, start_x, start_y,
        seg2_len, angle, go_left, origin
    )
    
    return bbox


def draw_crack(msp, x_start: float, x_end: float, y_start: float, y_end: float = None, origin: tuple = None):
    """绘制裂缝（手绘风格，179度倾斜）
    
    Args:
        x_start, x_end: X坐标范围
        y_start: Y起点（或Y坐标，当绘制水平裂缝时）
        y_end: Y终点（当绘制竖向裂缝时），如果为None则使用y_start（水平裂缝）
    """
    if origin is None:
        origin = (0, 0)
    
    # 如果没有传y_end，则视为水平裂缝，y_end = y_start
    if y_end is None:
        y_end = y_start
    
    # 判断是水平裂缝还是竖向裂缝
    is_vertical = (x_start == x_end)  # 竖向裂缝：x固定，y变化
    
    if is_vertical:
        # 竖向裂缝：从(x, y_start)到(x, y_end)
        cad_x1, cad_y1 = convert_to_cad_coords_lower(x_start, y_start, origin)
        cad_x2, cad_y2 = convert_to_cad_coords_lower(x_start, y_end, origin)
    else:
        # 水平裂缝：从(x_start, y)到(x_end, y)
        cad_x1, cad_y1 = convert_to_cad_coords_lower(x_start, y_start, origin)
        cad_x2, cad_y2 = convert_to_cad_coords_lower(x_end, y_start, origin)

    # 179度倾斜：终点Y比起点Y稍低（仅对水平裂缝）
    if is_vertical:
        # 竖向裂缝不需要倾斜偏移，保持垂直
        tilt_offset = 0
    else:
        crack_length = (x_end - x_start) * SCALE_X
        tilt_offset = crack_length * math.tan(math.radians(1))
        cad_y2 = cad_y2 - tilt_offset

    # 手绘风格裂缝
    points = []
    if is_vertical:
        # 竖向裂缝：沿Y方向绘制
        y = cad_y1
        step = 0.8
        while y >= cad_y2:  # CAD中Y越小越靠下
            # 叠加手绘随机偏移
            offset_x = math.sin((cad_y1 - y) / 3) * 0.15 + random.uniform(-0.1, 0.1)
            points.append((cad_x1 + offset_x, y))
            y -= step
        points.append((cad_x2, cad_y2))
    else:
        # 水平裂缝：沿X方向绘制
        x = cad_x1
        step = 0.8
        while x <= cad_x2:
            progress = (x - cad_x1) / (cad_x2 - cad_x1) if cad_x2 != cad_x1 else 0
            base_tilt = tilt_offset * progress
            offset_y = math.sin((x - cad_x1) / 3) * 0.15 + random.uniform(-0.1, 0.1)
            points.append((x, cad_y1 - base_tilt + offset_y))
            x += step
        points.append((cad_x2, cad_y2))

    msp.add_lwpolyline(points=points, dxfattribs={"color": 7})


def draw_vertical_crack_group(
    msp,
    x_start: float,
    x_end: float,
    y_start: float,
    y_end: float,
    n: int,
    origin: tuple,
):
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
    crack_height = cad_y1 - cad_y2  # 裂缝长度（CAD单位）
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

        msp.add_lwpolyline(points=points, dxfattribs={"color": 7})  # 7=白色
    
    # 返回边界框
    return (cad_x1, cad_y2, cad_x2, cad_y1)


def draw_honeycomb(
    msp, x1: float, y1: float, x2: float, y2: float, origin: tuple = None, scale_x: float = SCALE_X, scale_y: float = SCALE_Y, rotation_deg: float = 0
):
    """绘制蜂窝麻面图例（平铺复制modelspace实体填满整个区域）

    病害坐标系：原点为病害区域原点
    - X方向: 1m = scale_x CAD单位，向右
    - Y方向: 1m = scale_y CAD单位，向下（CAD Y减小）

    Args:
        x1, y1: 病害区域起点（m）
        x2, y2: 病害区域终点（m）
        origin: CAD原点（病害坐标系原点）- 用户提供的原点位置
        scale_x: X方向比例尺
        scale_y: Y方向比例尺

    Returns:
        实际边界框 (min_x, min_y, max_x, max_y)
    """
    from ezdxf.bbox import extents
    from ezdxf.math import Matrix44

    # 直接坐标转换（病害坐标 + 原点）
    # X方向: 1m = scale_x CAD单位，向右
    # Y方向: 1m = scale_y CAD单位，向下（CAD Y = 原点Y - y * scale_y）
    if origin is None:
        origin = (0, 0)

    import math as _math
    _tan_rot = _math.tan(_math.radians(rotation_deg))

    # 坐标转换（不加倾斜，倾斜只影响平铺偏移）
    cad_x1 = origin[0] + x1 * scale_x
    cad_y1 = origin[1] - y1 * scale_y  # y=0时等于origin_y（上边界）
    cad_x2 = origin[0] + x2 * scale_x
    cad_y2 = origin[1] - y2 * scale_y

    # 确保x顺序
    if cad_x1 > cad_x2:
        cad_x1, cad_x2 = cad_x2, cad_x1

    # 确保y顺序
    cad_y_max = max(cad_y1, cad_y2)  # 上边界（较大Y）
    cad_y_min = min(cad_y1, cad_y2)  # 下边界（较小Y）

    dst_w = cad_x2 - cad_x1
    dst_h = cad_y_max - cad_y_min  # 用y范围计算高度

    print(
        f"    [蜂窝] 目标区域: ({cad_x1:.1f},{cad_y_min:.1f}) ~ ({cad_x2:.1f},{cad_y_max:.1f}), 尺寸: {dst_w:.1f}x{dst_h:.1f}"
    )
    print(f"    [蜂窝] 原点: {origin}, 病害坐标: ({x1},{y1}) ~ ({x2},{y2}), 倾斜: {rotation_deg}°")

    # 加载蜂窝麻面图例文件
    legend_doc = ezdxf.readfile("./templates/病害图例/蜂窝麻面.dxf")
    legend_msp = legend_doc.modelspace()

    # 获取图例边界框（排除文字MTEXT）
    non_text_entities = [e for e in legend_msp if e.dxftype() not in ["TEXT", "MTEXT"]]
    legend_bbox = extents(non_text_entities)
    src_w = legend_bbox.extmax[0] - legend_bbox.extmin[0]
    src_h = legend_bbox.extmax[1] - legend_bbox.extmin[1]

    print(f"    [蜂窝] 图例实际尺寸（不含文字）: {src_w:.1f}x{src_h:.1f}")

    # 放大2倍，让蜂窝效果更明显
    scale = 2.0
    scaled_w = src_w * scale
    scaled_h = src_h * scale

    # 图例边界坐标
    src_min_x = legend_bbox.extmin[0]
    src_min_y = legend_bbox.extmin[1]
    src_max_y = legend_bbox.extmax[1]

    # 计算平铺数量：只画完整且不超出边界的格子
    import math

    n_cols = max(1, math.floor(dst_w / scaled_w))  # X方向：不超右边
    n_rows = max(1, math.floor(dst_h / scaled_h))  # Y方向：不超下边

    # 从矩形左上角（cad_y_max）开始，向下（Y减小）平铺
    start_x = cad_x1      # 左边界
    start_y = cad_y_max   # 上边界（图例顶部对齐到这里）

    print(
        f"    [蜂窝] 图例放大2倍: {scaled_w:.1f}x{scaled_h:.1f}, 平铺: {n_cols}x{n_rows}={n_cols * n_rows}个"
    )

    # 平铺复制（tile_y 代表该格图例的「顶部」目标Y，向下=Y减小）
    entity_count = 0
    for row in range(n_rows):
        for col in range(n_cols):
            tile_x = start_x + col * scaled_w
            # 向下平铺：row增大 → Y减小（顶部下移）
            # 倾斜：右侧列(col增大) → Y进一步减小
            col_y_offset = col * scaled_w * _tan_rot
            tile_y = start_y - row * scaled_h - col_y_offset  # 图例顶部目标Y

            # 变换公式：让图例顶部(src_max_y)对齐到 tile_y
            # p_new = p * scale + (tile_y - src_max_y * scale)
            dx = tile_x - src_min_x * scale
            dy = tile_y - src_max_y * scale
            # Matrix44([sx,0,0,0, 0,sy,0,0, 0,0,1,0, dx,dy,0,1]) 行优先
            transform = Matrix44(
                [scale, 0, 0, 0, 0, scale, 0, 0, 0, 0, 1, 0, dx, dy, 0, 1]
            )

            # 复制每个实体
            for entity in legend_msp:
                dxftype = entity.dxftype()
                if dxftype == "MTEXT":
                    continue
                try:
                    new_entity = entity.copy()
                    new_entity.transform(transform)
                    msp.add_entity(new_entity)
                    entity_count += 1
                except Exception as e:
                    print(f"    [蜂窝] {dxftype}复制失败: {e}")

    print(f"    [蜂窝] 复制了 {entity_count} 个实体")
    # 返回实际边界框
    actual_min_x = cad_x1
    actual_max_x = cad_x2
    actual_min_y = cad_y_min
    actual_max_y = cad_y_max
    return (actual_min_x, actual_min_y, actual_max_x, actual_max_y)


def draw_peel_off_tiled(
    msp, x1: float, y1: float, x2: float, y2: float, origin: tuple = None, scale_x: float = SCALE_X, scale_y: float = SCALE_Y, rotation_deg: float = 0
):
    """绘制剥落图例（平铺复制modelspace实体填满整个区域）

    病害坐标系：原点为病害区域原点
    - X方向: 1m = scale_x CAD单位，向右
    - Y方向: 1m = scale_y CAD单位，向下（CAD Y减小）

    Args:
        x1, y1: 病害区域起点（m）
        x2, y2: 病害区域终点（m）
        origin: CAD原点（病害坐标系原点）- 用户提供的原点位置
        scale_x: X方向比例尺
        scale_y: Y方向比例尺

    Returns:
        实际边界框 (min_x, min_y, max_x, max_y)
    """
    from ezdxf.bbox import extents
    from ezdxf.math import Matrix44

    if origin is None:
        origin = (0, 0)

    import math as _math
    _tan_rot = _math.tan(_math.radians(rotation_deg))

    # 坐标转换（不加倾斜，倾斜只影响平铺偏移）
    cad_x1 = origin[0] + x1 * scale_x
    cad_y1 = origin[1] - y1 * scale_y
    cad_x2 = origin[0] + x2 * scale_x
    cad_y2 = origin[1] - y2 * scale_y

    # 确保x顺序
    if cad_x1 > cad_x2:
        cad_x1, cad_x2 = cad_x2, cad_x1

    cad_y_max = max(cad_y1, cad_y2)
    cad_y_min = min(cad_y1, cad_y2)

    dst_w = cad_x2 - cad_x1
    dst_h = cad_y_max - cad_y_min

    print(
        f"    [剥落平铺] 目标区域: ({cad_x1:.1f},{cad_y_min:.1f}) ~ ({cad_x2:.1f},{cad_y_max:.1f}), 尺寸: {dst_w:.1f}x{dst_h:.1f}"
    )

    # 加载剥落图例文件
    legend_doc = ezdxf.readfile("./templates/病害图例/剥落、掉角.dxf")
    legend_msp = legend_doc.modelspace()

    # 获取图例边界框（排除文字MTEXT）
    non_text_entities = [e for e in legend_msp if e.dxftype() not in ["TEXT", "MTEXT"]]
    legend_bbox = extents(non_text_entities)
    src_w = legend_bbox.extmax[0] - legend_bbox.extmin[0]
    src_h = legend_bbox.extmax[1] - legend_bbox.extmin[1]

    print(f"    [剥落平铺] 图例实际尺寸（不含文字）: {src_w:.1f}x{src_h:.1f}")

    # 放大1.5倍
    scale = 1.5
    scaled_w = src_w * scale
    scaled_h = src_h * scale

    # 图例边界坐标
    src_min_x = legend_bbox.extmin[0]
    src_min_y = legend_bbox.extmin[1]
    src_max_y = legend_bbox.extmax[1]

    # 计算平铺数量
    import math

    n_cols = max(1, math.floor(dst_w / scaled_w))
    n_rows = max(1, math.floor(dst_h / scaled_h))

    # 从矩形上边界（cad_y_max）开始，向下（Y减小）平铺
    start_x = cad_x1
    start_y = cad_y_max  # 上边界（图例顶部对齐到这里）

    print(
        f"    [剥落平铺] 图例放大1.5倍: {scaled_w:.1f}x{scaled_h:.1f}, 平铺: {n_cols}x{n_rows}={n_cols * n_rows}个"
    )

    # 平铺复制（tile_y代表图例顶部目标Y，向下=Y减小）
    entity_count = 0
    for row in range(n_rows):
        for col in range(n_cols):
            tile_x = start_x + col * scaled_w
            col_y_offset = col * scaled_w * _tan_rot
            tile_y = start_y - row * scaled_h - col_y_offset  # 图例顶部目标Y

            # 变换公式：让图例顶部(src_max_y)对齐到 tile_y
            dx = tile_x - src_min_x * scale
            dy = tile_y - src_max_y * scale
            transform = Matrix44(
                [scale, 0, 0, 0, 0, scale, 0, 0, 0, 0, 1, 0, dx, dy, 0, 1]
            )

            for entity in legend_msp:
                dxftype = entity.dxftype()
                if dxftype == "MTEXT":
                    continue
                try:
                    new_entity = entity.copy()
                    new_entity.transform(transform)
                    msp.add_entity(new_entity)
                    entity_count += 1
                except Exception as e:
                    print(f"    [剥落平铺] {dxftype}复制失败: {e}")

    print(f"    [剥落平铺] 复制了 {entity_count} 个实体")
    # 返回实际边界框
    actual_min_x = cad_x1
    actual_max_x = cad_x2
    actual_min_y = cad_y_min
    actual_max_y = cad_y_max
    return (actual_min_x, actual_min_y, actual_max_x, actual_max_y)


def draw_peel_off_tiled_cad(msp, x1: float, y1: float, x2: float, y2: float):
    """绘制剥落图例（平铺复制modelspace实体填满整个CAD坐标区域）

    Args:
        x1, y1: CAD坐标区域左上角
        x2, y2: CAD坐标区域右下角

    Returns:
        实际边界框 (min_x, min_y, max_x, max_y)
    """
    from ezdxf.bbox import extents
    from ezdxf.math import Matrix44

    # 确保顺序
    cad_x1, cad_x2 = min(x1, x2), max(x1, x2)
    cad_y1, cad_y2 = min(y1, y2), max(y1, y2)

    dst_w = cad_x2 - cad_x1
    dst_h = cad_y2 - cad_y1

    print(
        f"    [剥落平铺CAD] 目标区域: ({cad_x1:.1f},{cad_y1:.1f}) ~ ({cad_x2:.1f},{cad_y2:.1f}), 尺寸: {dst_w:.1f}x{dst_h:.1f}"
    )

    # 加载剥落图例文件
    legend_doc = ezdxf.readfile("./templates/病害图例/剥落、掉角.dxf")
    legend_msp = legend_doc.modelspace()

    # 获取图例边界框（排除文字MTEXT）
    non_text_entities = [e for e in legend_msp if e.dxftype() not in ["TEXT", "MTEXT"]]
    legend_bbox = extents(non_text_entities)
    src_w = legend_bbox.extmax[0] - legend_bbox.extmin[0]
    src_h = legend_bbox.extmax[1] - legend_bbox.extmin[1]

    print(f"    [剥落平铺CAD] 图例实际尺寸（不含文字）: {src_w:.1f}x{src_h:.1f}")

    # 放大1.5倍
    scale = 1.5
    scaled_w = src_w * scale
    scaled_h = src_h * scale

    # 图例左下角（最小坐标）
    src_min_x = legend_bbox.extmin[0]
    src_min_y = legend_bbox.extmin[1]

    # 计算平铺数量
    import math

    n_cols = max(1, math.floor(dst_w / scaled_w))
    n_rows = max(1, math.floor(dst_h / scaled_h))

    # 从左下角开始
    start_x = cad_x1
    start_y = cad_y1

    print(
        f"    [剥落平铺CAD] 图例放大1.5倍: {scaled_w:.1f}x{scaled_h:.1f}, 平铺: {n_cols}x{n_rows}={n_cols * n_rows}个"
    )

    # 平铺复制
    entity_count = 0
    for row in range(n_rows):
        for col in range(n_cols):
            tile_x = start_x + col * scaled_w
            tile_y = start_y + row * scaled_h

            dx = tile_x - src_min_x * scale
            dy = tile_y - src_min_y * scale
            transform = Matrix44(
                [scale, 0, 0, 0, 0, scale, 0, 0, 0, 0, 1, 0, dx, dy, 0, 1]
            )

            for entity in legend_msp:
                dxftype = entity.dxftype()
                if dxftype == "MTEXT":
                    continue
                try:
                    new_entity = entity.copy()
                    new_entity.transform(transform)
                    msp.add_entity(new_entity)
                    entity_count += 1
                except Exception as e:
                    print(f"    [剥落平铺CAD] {dxftype}复制失败: {e}")

    print(f"    [剥落平铺CAD] 复制了 {entity_count} 个实体")
    # 返回平铺后的实际边界框
    actual_min_x = start_x
    actual_max_x = start_x + n_cols * scaled_w
    actual_min_y = start_y
    actual_max_y = start_y + n_rows * scaled_h
    return (actual_min_x, actual_min_y, actual_max_x, actual_max_y)


def draw_mesh_crack(msp, x1: float, y1: float, x2: float, y2: float, origin: tuple, scale_x: float = SCALE_X, scale_y: float = SCALE_Y):
    """绘制网状裂缝（波浪线填充）"""
    cad_x1, cad_y1 = convert_to_cad_coords_lower(x1, y1, origin, scale_x, scale_y)
    cad_x2, cad_y2 = convert_to_cad_coords_lower(x2, y2, origin, scale_x, scale_y)

    # 确保 cad_x1 < cad_x2
    if cad_x1 > cad_x2:
        cad_x1, cad_x2 = cad_x2, cad_x1

    wave_length = 4
    wave_amp = 0.3
    line_spacing = 1

    # 计算波浪线覆盖的高度（取绝对值）
    height = abs(cad_y2 - cad_y1)
    num_lines = max(1, int(height / line_spacing) + 1)

    # 确定Y的范围（从较大值到较小值，即从上到下）
    y_top = max(cad_y1, cad_y2)
    y_bottom = min(cad_y1, cad_y2)

    for i in range(num_lines):
        y = y_top - i * line_spacing
        points = []
        x = cad_x1
        while x <= cad_x2 + wave_length:
            phase = (x - cad_x1) / wave_length * 2 * math.pi
            wave_y = y + math.sin(phase) * wave_amp
            points.append((x, wave_y))
            x += 0.2
        msp.add_lwpolyline(points=points, dxfattribs={"color": 7})
    
    # 返回边界框
    return (cad_x1, y_bottom, cad_x2, y_top)


def draw_rebar_grid(msp, ax1: float, ay1: float, ax2: float, ay2: float, margin: float = 0.0):
    """绘制钢筋锈蚀网格（红色虚线）
    
    Args:
        ax1, ay1, ax2, ay2: 边界框
        margin: 边距（向内收缩），默认0表示使用完整边界框
    """
    # 如果有边距，向内收缩
    if margin > 0:
        ax1 = ax1 + margin
        ay1 = ay1 + margin
        ax2 = ax2 - margin
        ay2 = ay2 - margin
    
    # 横线（只画2条，分成3等份）
    for i in range(2):
        y = ay1 + (ay2 - ay1) * (i + 1) / 3
        msp.add_line((ax1, y), (ax2, y), dxfattribs={"color": 1, "linetype": "DASHED"})
    # 竖线（只画1条，分成2等份）
    for i in range(1):
        x = ax1 + (ax2 - ax1) * (i + 1) / 2
        msp.add_line((x, ay1), (x, ay2), dxfattribs={"color": 1, "linetype": "DASHED"})


def get_face_from_location(location: str) -> str:
    """从位置描述判断面（小桩号面/大桩号面）"""
    if "小桩号面" in location:
        return "小桩号面"
    elif "大桩号面" in location:
        return "大桩号面"
    elif "侧面" in location or "挡块" in location:
        return "小桩号面"  # 默认
    return "小桩号面"


def process_cap_beam_disease(msp, disease: dict, other_diseases: list = None):
    """处理盖梁病害（支持避让算法）
    
    Args:
        msp: modelspace
        disease: 病害数据
        other_diseases: 同一页的其他病害列表（用于避让）
    """
    if other_diseases is None:
        other_diseases = []
    
    location = disease.get("缺损位置", "")
    part = disease.get("具体部件", "")  # 从病害描述中解析出的部位
    x_start = disease.get("x_start", 0)
    x_end = disease.get("x_end", 0)
    y_start = disease.get("y_start", 0)
    y_end = disease.get("y_end", 0)
    disease_type = disease.get("病害类型", "")
    disease_raw = disease.get("病害", "")
    
    # 双柱墩使用默认比例尺
    scale_x = SCALE_X
    scale_y = SCALE_Y

    # 判断面：优先用具体部件判断（包含"小桩号面"/"大桩号面"/"挡块"）
    face = part if part else location

    # 根据面类型设置原点（默认使用小桩号面）
    if "大桩号面" in face:
        origin = CAP_BEAM_ORIGINS["大桩号面"]
    else:
        # 默认使用小桩号面（包括小桩号面、挡块、侧面等）
        origin = CAP_BEAM_ORIGINS["小桩号面"]
    
    # 挡块不绘制图例，也不标注，直接跳过
    if "挡块" in face:
        print(f"    跳过挡块绘制（图例+标注）")
        return
    
    elif "侧面" in face:
        # 盖梁的侧面（使用盖梁的侧面矩形配置）
        if "右" in face:
            block_rect = CAP_BEAM_ORIGINS["右侧面"]["rect"]
        else:
            block_rect = CAP_BEAM_ORIGINS["内侧面"]["rect"]
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
        bbox = geo["bbox"]
        src_w = bbox["max_x"] - bbox["min_x"]
        src_h = bbox["max_y"] - bbox["min_y"]
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
        print(
            f"    [调试] 矩形: ({x1:.1f},{y1:.1f}) ~ ({x2:.1f},{y2:.1f}), 中心: ({center_x:.1f},{center_y:.1f})"
        )
        print(f"    [调试] 剥落源尺寸: {src_w:.1f}x{src_h:.1f}, 缩放: {scale:.3f}")
        # 剥落图形中心坐标
        peel_center_x = (bbox["min_x"] + bbox["max_x"]) / 2
        peel_center_y = (bbox["min_y"] + bbox["max_y"]) / 2
        # 绘制线条
        for line in geo["lines"]:
            sx, sy = line["start"]
            ex, ey = line["end"]
            # 先归一化到原点，再缩放，最后移到目标中心
            new_start = (
                center_x + (sx - peel_center_x) * scale,
                center_y + (sy - peel_center_y) * scale,
            )
            new_end = (
                center_x + (ex - peel_center_x) * scale,
                center_y + (ey - peel_center_y) * scale,
            )
            msp.add_line(new_start, new_end, dxfattribs={"color": 7})
        # 绘制多边形
        if geo["polyline"]:
            pts = []
            for px, py in geo["polyline"]:
                pts.append(
                    (
                        center_x + (px - peel_center_x) * scale,
                        center_y + (py - peel_center_y) * scale,
                    )
                )
            msp.add_lwpolyline(pts, dxfattribs={"color": 7})
        # 计算实际边界框
        actual_min_x = center_x - src_w * scale / 2
        actual_max_x = center_x + src_w * scale / 2
        actual_min_y = center_y - src_h * scale / 2
        actual_max_y = center_y + src_h * scale / 2
        print(
            f"    [调试] 剥落边界框: ({actual_min_x:.1f},{actual_min_y:.1f}) ~ ({actual_max_x:.1f},{actual_max_y:.1f})"
        )
        # 添加标注：从病害区域上方引出（使用避让算法）
        area = disease.get("area", 0)
        if area > 0:
            # 标注起点：剥落区域上方中间
            start_x = (actual_min_x + actual_max_x) / 2  # 水平中间
            start_y = actual_max_y  # 剥落图形上边缘
            
            # 避让算法
            nearby_diseases = find_nearby_diseases(disease, other_diseases, threshold_m=3.0)
            seg1_len = 8
            if nearby_diseases:
                seg1_len = 8 * 1.5
            
            used_angles = [d.get('label_angle') for d in nearby_diseases if d.get('label_angle')]
            angle, go_left = get_safe_angle(disease, start_x, start_y, seg1_len, origin, used_angles)
            
            seg2_len_adj = max(12, len(disease_type) * 3 + len(str(area)) * 5)
            if nearby_diseases:
                seg2_len_adj = seg2_len_adj * 1.3
            
            # 计算引线点
            bend_x = start_x + seg1_len * math.cos(math.radians(angle))
            bend_y = start_y + seg1_len * math.sin(math.radians(angle))
            end_x = bend_x + (seg2_len_adj if not go_left else -seg2_len_adj)
            end_y = bend_y
            
            # 绘制折线
            msp.add_lwpolyline(
                [(start_x, start_y), (bend_x, bend_y), (end_x, end_y)],
                dxfattribs={"color": 7},
            )
            
            # 绘制文字
            text_height = 2.5
            if go_left:
                text_x = bend_x - seg2_len_adj - 1
            else:
                text_x = bend_x + 1
            
            # 上方：病害名称
            msp.add_text(
                disease_type,
                dxfattribs={
                    "insert": (text_x, bend_y + text_height * 0.5),
                    "height": text_height,
                    "color": 7,
                },
            )
            # 下方：面积
            msp.add_text(
                f"S={area:.2f}m²",
                dxfattribs={
                    "insert": (text_x, bend_y - text_height * 1.5),
                    "height": text_height,
                    "color": 7,
                },
            )
        return
    # else: 这里不需要重新设置origin，因为前面已经根据face设置好了
    
    # 获取数值数据
    length = disease.get("length", 0)
    width = disease.get("width", 0)
    area = disease.get("area", 0)
    crack_count = disease.get("裂缝条数", disease.get("count", 0))  # N=数字

    # 计算病害区域右上角（作为标注起点）
    cad_x1, cad_y1 = convert_to_cad_coords_lower(x_start, y_start, origin)
    cad_x2, cad_y2 = convert_to_cad_coords_lower(x_end, y_end, origin)
    start_x = max(cad_x1, cad_x2)
    start_y = max(cad_y1, cad_y2)

    # 计算标注第二段长度
    seg2_len = max(
        12, len(disease_type) * 3 + max(len(str(length)), len(str(area))) * 5
    )

    # 绘制病害及标注
    if "蜂窝" in disease_type or "麻面" in disease_type:
        # 蜂窝/麻面：使用蜂窝麻面图例
        # 根据面类型选择正确的原点（已在前面计算）
        bbox = draw_honeycomb(
            msp, x_start, y_start, x_end, y_end, origin=origin
        )
        if area > 0 and bbox:
            # 避让算法：计算起点、角度
            # 使用实际bbox计算引线起点，而不是原始病害坐标
            # bbox = (min_x, min_y, max_x, max_y)
            bbox_min_x, bbox_min_y, bbox_max_x, bbox_max_y = bbox
            
            # 根据引线方向选择引出点（从bbox的角点引出）
            # 注意：CAD中Y值越小越靠上
            # - 左上角 = (min_x, min_y)
            # - 右下角 = (max_x, max_y)
            start_x = bbox_max_x  # 默认从右下角引出
            start_y = bbox_max_y
            
            # 查找邻近病害
            nearby_diseases = find_nearby_diseases(disease, other_diseases, threshold_m=3.0)
            
            # 动态调整seg1_len
            seg1_len = 8  # 蜂窝麻面默认8
            if nearby_diseases:
                seg1_len = 8 * 1.5  # 邻近病害增加到12
            
            # 获取已使用的角度
            used_angles = [d.get('label_angle') for d in nearby_diseases if d.get('label_angle')]
            
            # 获取安全角度（使用向上角度：90°或135°或45°）
            # 对于蜂窝麻面，优先使用向上角度
            angle, go_left = get_safe_angle(disease, start_x, start_y, seg1_len, origin, used_angles)
            
            # 根据go_left重新计算引线起点（使用bbox而不是原始坐标）
            if go_left:
                # 向左上引线，从bbox左上角引出
                start_x = bbox_min_x
                start_y = bbox_min_y
            else:
                # 向右下引线（默认），从bbox右下角引出
                start_x = bbox_max_x
                start_y = bbox_max_y
            
            # 动态调整seg2_len
            seg2_len = max(12, len(disease_type) * 3 + len(f"{area:.2f}") * 5)
            if nearby_diseases:
                seg2_len = seg2_len * 1.3  # 增加30%
            
            # 计算引线点
            bend_x = start_x + seg1_len * math.cos(math.radians(angle))
            bend_y = start_y + seg1_len * math.sin(math.radians(angle))
            end_x = bend_x + (seg2_len if not go_left else -seg2_len)
            end_y = bend_y
            
            # 绘制折线
            msp.add_lwpolyline(
                [(start_x, start_y), (bend_x, bend_y), (end_x, end_y)],
                dxfattribs={"color": 7},
            )
            
            # 绘制文字
            text_height = 2.5
            if go_left:
                text_x = bend_x - seg2_len - 1
            else:
                text_x = bend_x + 1
            
            # 上方：病害名称
            msp.add_text(
                disease_type,
                dxfattribs={
                    "insert": (text_x, bend_y + text_height * 0.5),
                    "height": text_height,
                    "color": 7,
                },
            )
            # 下方：面积
            msp.add_text(
                f"S={area:.2f}m²",
                dxfattribs={
                    "insert": (text_x, bend_y - text_height * 1.5),
                    "height": text_height,
                    "color": 7,
                },
            )
    elif "剥落" in disease_type or "破损" in disease_type:
        # 使用return_bbox获取实际边界框
        bbox = draw_peel_off(
            msp, x_start, y_start, x_end, y_end, origin, return_bbox=True
        )
        if area > 0 and bbox:
            # 先用默认参数计算引线起点
            start_x, start_y = calculate_start_point(disease, origin, other_diseases, go_left=False)
            
            # 查找邻近病害
            nearby_diseases = find_nearby_diseases(disease, other_diseases, threshold_m=3.0)
            
            # 动态调整seg1_len
            seg1_len = 8  # 剥落默认8
            if nearby_diseases:
                seg1_len = 8 * 1.5  # 邻近病害增加到12
            
            # 获取已使用的角度
            used_angles = [d.get('label_angle') for d in nearby_diseases if d.get('label_angle')]
            
            # 获取安全角度
            angle, go_left = get_safe_angle(disease, start_x, start_y, seg1_len, origin, used_angles)
            
            # 根据go_left重新计算引线起点
            start_x, start_y = calculate_start_point(disease, origin, other_diseases, go_left)
            
            # 动态调整seg2_len
            seg2_len = max(12, len(disease_type) * 3 + len(f"{area:.2f}") * 5)
            if nearby_diseases:
                seg2_len = seg2_len * 1.3  # 增加30%
            
            # 计算引线点
            bend_x = start_x + seg1_len * math.cos(math.radians(angle))
            bend_y = start_y + seg1_len * math.sin(math.radians(angle))
            end_x = bend_x + (seg2_len if not go_left else -seg2_len)
            end_y = bend_y
            
            # 绘制折线
            msp.add_lwpolyline(
                [(start_x, start_y), (bend_x, bend_y), (end_x, end_y)],
                dxfattribs={"color": 7},
            )
            
            # 绘制文字
            text_height = 2.5
            if go_left:
                text_x = bend_x - seg2_len - 1
            else:
                text_x = bend_x + 1
            
            # 上方：病害名称
            msp.add_text(
                disease_type,
                dxfattribs={
                    "insert": (text_x, bend_y + text_height * 0.5),
                    "height": text_height,
                    "color": 7,
                },
            )
            # 下方：面积
            msp.add_text(
                f"S={area:.2f}m²",
                dxfattribs={
                    "insert": (text_x, bend_y - text_height * 1.5),
                    "height": text_height,
                    "color": 7,
                },
            )

    elif "网状裂缝" in disease_type:
        draw_mesh_crack(msp, x_start, y_start, x_end, y_end, origin, scale_x, scale_y)
        if area > 0:
            # 避让算法：先计算起点
            start_x, start_y = calculate_start_point(disease, origin, other_diseases, go_left=False)
            nearby_diseases = find_nearby_diseases(disease, other_diseases, threshold_m=3.0)
            seg1_len = 16 if nearby_diseases else 16  # 网状裂缝默认16
            used_angles = [d.get('label_angle') for d in nearby_diseases if d.get('label_angle')]
            angle, go_left = get_safe_angle(disease, start_x, start_y, seg1_len, origin, used_angles)
            
            # 根据go_left重新计算引线起点
            start_x, start_y = calculate_start_point(disease, origin, other_diseases, go_left)
            
            seg2_len_adj = seg2_len * (1.3 if nearby_diseases else 1.0)
            
            draw_disease_label(
                msp, disease, "网状裂缝", f"S={area:.2f}m²", start_x, start_y, seg2_len_adj,
                angle=angle, go_left=go_left, origin=origin
            )

    elif "裂缝" in disease_type or "开裂" in disease_type:
        # 获取同一页的其他病害（用于避让）
        other_diseases = disease.get('_page_diseases', [])
        
        if crack_count > 1:
            # 裂缝群（竖向裂缝）
            draw_vertical_crack_group(
                msp, x_start, x_end, y_start, y_end, crack_count, origin
            )
            # 标注：竖向裂缝 N=15条，上方；L总=4.50m，下方
            if length > 0:
                label = f"{disease_type} N={crack_count}条"
                value = f"L总={length:.2f}m"
            else:
                label = f"{disease_type} N={crack_count}条"
                value = ""
            
            # 避让算法：计算起点、角度
            # 先用默认参数计算起点
            start_x, start_y = calculate_start_point(disease, origin, other_diseases, go_left=False)
            
            # 查找邻近病害
            nearby_diseases = find_nearby_diseases(disease, other_diseases, threshold_m=3.0)
            
            # 动态调整seg1_len
            seg1_len = 16  # 裂缝群默认16
            if nearby_diseases:
                seg1_len = 16 * 1.5  # 邻近病害增加到24
            
            # 获取已使用的角度
            used_angles = [d.get('label_angle') for d in nearby_diseases if d.get('label_angle')]
            
            # 获取安全角度
            angle, go_left = get_safe_angle(disease, start_x, start_y, seg1_len, origin, used_angles)
            
            # 根据go_left重新计算引线起点
            start_x, start_y = calculate_start_point(disease, origin, other_diseases, go_left)
            
            # 动态调整seg2_len
            if nearby_diseases:
                seg2_len = seg2_len * 1.3  # 增加30%
            
            # 绘制标注
            draw_disease_label(
                msp, disease, label, value, start_x, start_y, seg2_len,
                angle=angle, go_left=go_left, origin=origin
            )
            
        elif y_start == y_end:
            # 单条水平裂缝
            draw_crack(msp, x_start, x_end, y_start, y_start, origin)
            if length > 0 and width > 0:
                label = f"{disease_type} L={length:.2f}m"
                value = f"W={width:.2f}mm"
            elif length > 0:
                label = f"{disease_type} L={length:.2f}m"
                value = ""
            else:
                label = disease_type
                value = ""
            
            if label:
                # 避让算法：计算起点、角度
                # 先用默认参数计算起点
                start_x, start_y = calculate_start_point(disease, origin, other_diseases, go_left=False)
                
                # 查找邻近病害
                nearby_diseases = find_nearby_diseases(disease, other_diseases, threshold_m=3.0)
                
                # 动态调整seg1_len
                seg1_len = 8
                if nearby_diseases:
                    seg1_len = 8 * 1.5  # 邻近病害增加到12
                
                # 获取已使用的角度
                used_angles = [d.get('label_angle') for d in nearby_diseases if d.get('label_angle')]
                
                # 获取安全角度
                angle, go_left = get_safe_angle(disease, start_x, start_y, seg1_len, origin, used_angles)
                
                # 根据go_left重新计算引线起点
                start_x, start_y = calculate_start_point(disease, origin, other_diseases, go_left)
                
                # 动态调整seg2_len
                if nearby_diseases:
                    seg2_len = seg2_len * 1.3  # 增加30%
                
                # 绘制标注
                draw_disease_label(
                    msp, disease, label, value, start_x, start_y, seg2_len,
                    angle=angle, go_left=go_left, origin=origin
                )
        
        else:
            # 单条竖向裂缝 (y_start != y_end 且 x_start == x_end)
            # 绘制单条竖向裂缝
            # 使用y_start和y_end作为Y坐标范围，x作为X坐标
            crack_x = x_start  # x_start == x_end 时就是单个x坐标值
            draw_crack(msp, crack_x, crack_x, y_start, y_end, origin)
            
            if length > 0 and width > 0:
                label = f"{disease_type} L={length:.2f}m"
                value = f"W={width:.2f}mm"
            elif length > 0:
                label = f"{disease_type} L={length:.2f}m"
                value = ""
            else:
                label = disease_type
                value = ""
            
            if label:
                # 避让算法：计算起点、角度
                start_x, start_y = calculate_start_point(disease, origin, other_diseases, go_left=False)
                
                # 查找邻近病害
                nearby_diseases = find_nearby_diseases(disease, other_diseases, threshold_m=3.0)
                
                # 动态调整seg1_len
                seg1_len = 8
                if nearby_diseases:
                    seg1_len = 8 * 1.5
                
                # 获取已使用的角度
                used_angles = [d.get('label_angle') for d in nearby_diseases if d.get('label_angle')]
                
                # 获取安全角度
                angle, go_left = get_safe_angle(disease, start_x, start_y, seg1_len, origin, used_angles)
                
                # 根据go_left重新计算引线起点
                start_x, start_y = calculate_start_point(disease, origin, other_diseases, go_left)
                
                # 动态调整seg2_len
                if nearby_diseases:
                    seg2_len = seg2_len * 1.3
                
                # 绘制标注
                draw_disease_label(
                    msp, disease, label, value, start_x, start_y, seg2_len,
                    angle=angle, go_left=go_left, origin=origin
                )

    elif "空洞" in disease_type or "孔洞" in disease_type:
        # 空洞/孔洞不绘制图例，也不标注
        pass

    elif "露筋" in disease_type or "锈胀露筋" in disease_type:
        # 先绘制剥落区域边界
        bbox = draw_peel_off(
            msp, x_start, y_start, x_end, y_end, origin, return_bbox=True
        )
        if bbox:
            # 在剥落区域内绘制露筋网格（向内收缩，避免超出边界）
            draw_rebar_grid(msp, *bbox, margin=1)
            # 在剥落区域内平铺露筋图例
            draw_rebar_corrosion(msp, *bbox)
        if area > 0:
            # 查找邻近病害
            nearby_diseases = find_nearby_diseases(disease, other_diseases, threshold_m=3.0)
            
            # 动态调整seg1_len
            seg1_len_adj = 8
            if nearby_diseases:
                seg1_len_adj = 8 * 1.5
            
            # 获取已使用的角度
            used_angles = [d.get('label_angle') for d in nearby_diseases if d.get('label_angle')]
            
            # 获取安全角度
            angle, go_left = get_safe_angle(disease, start_x, start_y, seg1_len_adj, origin, used_angles)
            
            # 动态调整seg2_len
            seg2_len_adj = seg2_len * (1.3 if nearby_diseases else 1.0)
            
            draw_disease_label(
                msp, disease, "剥落露筋", f"S={area:.2f}m²", start_x, start_y, seg2_len_adj,
                angle=angle, go_left=go_left, origin=origin
            )


def process_abutment_disease(msp, disease: dict, other_diseases: list = None, abut_type: str = "带台身桥台"):
    """处理桥台病害（支持避让算法）
    
    Args:
        msp: modelspace
        disease: 病害数据
        other_diseases: 同一页的其他病害列表（用于避让）
        abut_type: 桥台类型 - "带台身桥台" 或 "不带台身桥台"
    """
    if other_diseases is None:
        other_diseases = []
    
    location = disease.get("缺损位置", "")
    part = disease.get("具体部件", "")
    
    # 只处理台身和台帽，不处理前墙、护栏等其他部位
    # 检查缺损位置是否包含前墙或护栏，如果是则跳过
    if "前墙" in location or "护栏" in location:
        print(f"    跳过前墙/护栏病害：{location}")
        return
    
    # 根据具体部件判断是台帽还是台身
    component_part = part if part else location
    
    # 如果不包含台身或台帽，也跳过
    if not ("台身" in component_part or "台帽" in component_part):
        print(f"    跳过非台身/台帽病害：{component_part}")
        return
    
    x_start = disease.get('x_start', 0)
    x_end = disease.get('x_end', 0)
    y_start = disease.get('y_start', 0)
    y_end = disease.get('y_end', 0)
    disease_type = disease.get('病害类型', '')
    disease_raw = disease.get('病害', '')
    
    # 设置原点
    if abut_type == "带台身桥台":
        if "台帽" in component_part:
            origin = ABUT_ORIGINS["带台身桥台"]["台帽"]
        else:
            # 默认使用台身
            origin = ABUT_ORIGINS["带台身桥台"]["台身"]
    else:  # 不带台身桥台
        origin = ABUT_ORIGINS["不带台身桥台"]["台身"]
    
    # 获取数值数据
    length = disease.get('length', 0)
    width = disease.get('width', 0)
    area = disease.get('area', 0)
    crack_count = disease.get('裂缝条数', disease.get('count', 0))
    
    # 根据桥台类型和部位确定比例尺
    if abut_type == "带台身桥台":
        if "台帽" in component_part:
            scale_x = ABUT_WITH_CAP_SCALE_X
            scale_y = ABUT_WITH_CAP_SCALE_Y
        else:  # 台身
            scale_x = ABUT_WITH_TAI_SCALE_X
            scale_y = ABUT_WITH_TAI_SCALE_Y
    else:  # 不带台身桥台
        scale_x = ABUT_WITHOUT_SCALE_X
        scale_y = ABUT_WITHOUT_SCALE_Y
    
    # 计算病害区域右上角（作为标注起点）
    cad_x1, cad_y1 = convert_to_cad_coords_abut(x_start, y_start, origin, scale_x, scale_y)
    cad_x2, cad_y2 = convert_to_cad_coords_abut(x_end, y_end, origin, scale_x, scale_y)
    start_x = max(cad_x1, cad_x2)
    start_y = max(cad_y1, cad_y2)
    
    # 计算标注第二段长度
    seg2_len = max(12, len(disease_type) * 3 + max(len(str(length)), len(str(area))) * 5)
    
    # 绘制病害及标注（使用避让算法）
    if "蜂窝" in disease_type or "麻面" in disease_type:
        # 蜂窝/麻面
        bbox = draw_honeycomb(msp, x_start, y_start, x_end, y_end, origin=origin, scale_x=scale_x, scale_y=scale_y)
        if area > 0 and bbox:
            # 避让算法：使用实际bbox计算引线起点
            # bbox = (min_x, min_y, max_x, max_y)
            bbox_min_x, bbox_min_y, bbox_max_x, bbox_max_y = bbox
            
            # 默认从bbox右下角引出
            start_x_calc = bbox_max_x
            start_y_calc = bbox_max_y
            
            nearby_diseases = find_nearby_diseases(disease, other_diseases, threshold_m=3.0)
            seg1_len = 8
            if nearby_diseases:
                seg1_len = 8 * 1.5
            used_angles = [d.get('label_angle') for d in nearby_diseases if d.get('label_angle')]
            angle, go_left = get_safe_angle(disease, start_x_calc, start_y_calc, seg1_len, origin, used_angles)
            
            # 根据go_left重新计算引线起点（使用bbox而不是原始坐标）
            if go_left:
                # 向左上引线，从bbox左上角引出
                start_x_calc = bbox_min_x
                start_y_calc = bbox_min_y
            else:
                # 向右下引线（默认），从bbox右下角引出
                start_x_calc = bbox_max_x
                start_y_calc = bbox_max_y
            
            seg2_len_adj = seg2_len * (1.3 if nearby_diseases else 1.0)
            
            # 绘制标注
            draw_disease_label(
                msp, disease, disease_type, f"S={area:.2f}m²", 
                start_x_calc, start_y_calc, seg2_len_adj,
                angle=angle, go_left=go_left, origin=origin
            )
    
    elif "剥落" in disease_type or "破损" in disease_type:
        # 剥落 - 使用平铺方式绘制
        bbox = draw_peel_off_tiled(msp, x_start, y_start, x_end, y_end, origin, scale_x=scale_x, scale_y=scale_y)
        if area > 0 and bbox:
            # 避让算法：使用实际bbox计算引线起点
            # bbox = (min_x, min_y, max_x, max_y)
            bbox_min_x, bbox_min_y, bbox_max_x, bbox_max_y = bbox
            
            # 默认从bbox右下角引出
            start_x_calc = bbox_max_x
            start_y_calc = bbox_max_y
            
            nearby_diseases = find_nearby_diseases(disease, other_diseases, threshold_m=3.0)
            seg1_len = 8
            if nearby_diseases:
                seg1_len = 8 * 1.5
            used_angles = [d.get('label_angle') for d in nearby_diseases if d.get('label_angle')]
            angle, go_left = get_safe_angle(disease, start_x_calc, start_y_calc, seg1_len, origin, used_angles)
            
            # 根据go_left重新计算引线起点（使用bbox而不是原始坐标）
            if go_left:
                # 向左上引线，从bbox左上角引出
                start_x_calc = bbox_min_x
                start_y_calc = bbox_min_y
            else:
                # 向右下引线（默认），从bbox右下角引出
                start_x_calc = bbox_max_x
                start_y_calc = bbox_max_y
            
            seg2_len_adj = seg2_len * (1.3 if nearby_diseases else 1.0)
            
            draw_disease_label(
                msp, disease, disease_type, f"S={area:.2f}m²",
                start_x_calc, start_y_calc, seg2_len_adj,
                angle=angle, go_left=go_left, origin=origin
            )
    
    elif "裂缝" in disease_type or "开裂" in disease_type:
        other_diseases_page = disease.get('_page_diseases', [])
        
        if crack_count > 1:
            # 裂缝群
            draw_vertical_crack_group(msp, x_start, x_end, y_start, y_end, crack_count, origin)
            if length > 0:
                label = f"{disease_type} N={crack_count}条"
                value = f"L总={length:.2f}m"
                
                # 避让算法
                start_x_calc, start_y_calc = calculate_start_point(disease, origin, other_diseases_page, go_left=False)
                nearby_diseases = find_nearby_diseases(disease, other_diseases_page, threshold_m=3.0)
                seg1_len = 16
                if nearby_diseases:
                    seg1_len = 16 * 1.5
                used_angles = [d.get('label_angle') for d in nearby_diseases if d.get('label_angle')]
                angle, go_left = get_safe_angle(disease, start_x_calc, start_y_calc, seg1_len, origin, used_angles)
                start_x_calc, start_y_calc = calculate_start_point(disease, origin, other_diseases_page, go_left)
                seg2_len_adj = seg2_len * (1.3 if nearby_diseases else 1.0)
                
                draw_disease_label(
                    msp, disease, label, value, start_x_calc, start_y_calc, seg2_len_adj,
                    angle=angle, go_left=go_left, origin=origin
                )
        
        elif y_start == y_end:
            # 单条水平裂缝
            draw_crack(msp, x_start, x_end, y_start, y_start, origin)
            if length > 0 and width > 0:
                label = f"{disease_type} L={length:.2f}m"
                value = f"W={width:.2f}mm"
            elif length > 0:
                label = f"{disease_type} L={length:.2f}m"
                value = ""
            else:
                label = disease_type
                value = ""
            
            if label:
                # 避让算法
                start_x_calc, start_y_calc = calculate_start_point(disease, origin, other_diseases_page, go_left=False)
                nearby_diseases = find_nearby_diseases(disease, other_diseases_page, threshold_m=3.0)
                seg1_len = 8
                if nearby_diseases:
                    seg1_len = 8 * 1.5
                used_angles = [d.get('label_angle') for d in nearby_diseases if d.get('label_angle')]
                angle, go_left = get_safe_angle(disease, start_x_calc, start_y_calc, seg1_len, origin, used_angles)
                start_x_calc, start_y_calc = calculate_start_point(disease, origin, other_diseases_page, go_left)
                seg2_len_adj = seg2_len * (1.3 if nearby_diseases else 1.0)
                
                draw_disease_label(
                    msp, disease, label, value, start_x_calc, start_y_calc, seg2_len_adj,
                    angle=angle, go_left=go_left, origin=origin
                )
        
        else:
            # 单条竖向裂缝
            crack_x = x_start
            draw_crack(msp, crack_x, crack_x, y_start, y_end, origin)
            
            if length > 0 and width > 0:
                label = f"{disease_type} L={length:.2f}m"
                value = f"W={width:.2f}mm"
            elif length > 0:
                label = f"{disease_type} L={length:.2f}m"
                value = ""
            else:
                label = disease_type
                value = ""
            
            if label:
                # 避让算法
                start_x_calc, start_y_calc = calculate_start_point(disease, origin, other_diseases_page, go_left=False)
                nearby_diseases = find_nearby_diseases(disease, other_diseases_page, threshold_m=3.0)
                seg1_len = 8
                if nearby_diseases:
                    seg1_len = 8 * 1.5
                used_angles = [d.get('label_angle') for d in nearby_diseases if d.get('label_angle')]
                angle, go_left = get_safe_angle(disease, start_x_calc, start_y_calc, seg1_len, origin, used_angles)
                start_x_calc, start_y_calc = calculate_start_point(disease, origin, other_diseases_page, go_left)
                seg2_len_adj = seg2_len * (1.3 if nearby_diseases else 1.0)
                
                draw_disease_label(
                    msp, disease, label, value, start_x_calc, start_y_calc, seg2_len_adj,
                    angle=angle, go_left=go_left, origin=origin
                )
    
    elif "网状裂缝" in disease_type:
        draw_mesh_crack(msp, x_start, y_start, x_end, y_end, origin, scale_x, scale_y)
        if area > 0:
            # 避让算法
            start_x_calc, start_y_calc = calculate_start_point(disease, origin, other_diseases, go_left=False)
            nearby_diseases = find_nearby_diseases(disease, other_diseases, threshold_m=3.0)
            seg1_len = 16
            used_angles = [d.get('label_angle') for d in nearby_diseases if d.get('label_angle')]
            angle, go_left = get_safe_angle(disease, start_x_calc, start_y_calc, seg1_len, origin, used_angles)
            start_x_calc, start_y_calc = calculate_start_point(disease, origin, other_diseases, go_left)
            seg2_len_adj = seg2_len * (1.3 if nearby_diseases else 1.0)
            
            draw_disease_label(
                msp, disease, "网状裂缝", f"S={area:.2f}m²", start_x_calc, start_y_calc, seg2_len_adj,
                angle=angle, go_left=go_left, origin=origin
            )
    
    elif "空洞" in disease_type or "孔洞" in disease_type:
        # 空洞/孔洞不绘制图例，也不标注
        pass
    
    elif "露筋" in disease_type or "锈胀露筋" in disease_type:
        # 剥落露筋
        bbox = draw_peel_off(msp, x_start, y_start, x_end, y_end, origin, return_bbox=True)
        if bbox:
            draw_rebar_grid(msp, *bbox, margin=1)
            draw_rebar_corrosion(msp, *bbox)
        if area > 0:
            # 避让算法
            start_x_calc, start_y_calc = calculate_start_point(disease, origin, other_diseases, go_left=False)
            nearby_diseases = find_nearby_diseases(disease, other_diseases, threshold_m=3.0)
            seg1_len = 8
            if nearby_diseases:
                seg1_len = 8 * 1.5
            used_angles = [d.get('label_angle') for d in nearby_diseases if d.get('label_angle')]
            angle, go_left = get_safe_angle(disease, start_x_calc, start_y_calc, seg1_len, origin, used_angles)
            start_x_calc, start_y_calc = calculate_start_point(disease, origin, other_diseases, go_left)
            seg2_len_adj = seg2_len * (1.3 if nearby_diseases else 1.0)
            
            draw_disease_label(
                msp, disease, "剥落露筋", f"S={area:.2f}m²", start_x_calc, start_y_calc, seg2_len_adj,
                angle=angle, go_left=go_left, origin=origin
            )


def process_single_pier_cap_beam(msp, disease: dict, origin: tuple, scale_x: float, scale_y: float):
    """处理单柱墩盖梁病害（使用独立的比例尺，右下倾斜1度）"""
    location = disease.get("缺损位置", "")
    disease_type = disease.get("病害类型", "")
    x_start = disease.get('x_start', 0)
    x_end = disease.get('x_end', 0)
    y_start = disease.get('y_start', 0)
    y_end = disease.get('y_end', 0)
    area = disease.get("area", 0)
    
    # 使用单柱墩独立的比例尺进行坐标转换（带1度旋转）
    def rotate_point(x, y, origin_x, origin_y, angle_deg=1):
        """将点绕原点旋转指定角度（顺时针）"""
        import math
        angle_rad = math.radians(angle_deg)
        dx = x - origin_x
        dy = y - origin_y
        new_dx = dx * math.cos(angle_rad) + dy * math.sin(angle_rad)
        new_dy = -dx * math.sin(angle_rad) + dy * math.cos(angle_rad)
        return (origin_x + new_dx, origin_y + new_dy)
    
    # 基础CAD坐标
    base_x1 = origin[0] + x_start * scale_x
    base_x2 = origin[0] + x_end * scale_x
    base_y1 = origin[1] - y_start * scale_y  # Y轴向下，用减法
    base_y2 = origin[1] - y_end * scale_y
    
    # 应用1度向右下倾斜旋转
    cad_x1, cad_y1 = rotate_point(base_x1, base_y1, origin[0], origin[1])
    cad_x2, cad_y2 = rotate_point(base_x2, base_y2, origin[0], origin[1])
    
    # 确保坐标顺序正确
    if cad_x1 > cad_x2:
        cad_x1, cad_x2 = cad_x2, cad_x1
    
    print(f"    [单柱墩盖梁] {disease_type} 区域: ({cad_x1:.1f},{cad_y1:.1f}) ~ ({cad_x2:.1f},{cad_y2:.1f})")
    
    # 空洞/孔洞：不绘制图形，直接返回
    if "空洞" in disease_type or "孔洞" in disease_type or "孔洞空洞" in disease_type:
        print(f"    [单柱墩盖梁] 空洞/孔洞类型，跳过绘制")
        return
    
    # 绘制病害图例（蜂窝/麻面/剥落/网状裂缝仍调用原函数，保持图例样式不变）
    if "蜂窝" in disease_type or "麻面" in disease_type:
        bbox = draw_honeycomb(msp, x_start, y_start, x_end, y_end, origin, scale_x=scale_x, scale_y=scale_y, rotation_deg=1)
    elif "剥落" in disease_type or "破损" in disease_type:
        bbox = draw_peel_off_tiled(msp, x_start, y_start, x_end, y_end, origin, scale_x=scale_x, scale_y=scale_y, rotation_deg=1)
    elif "网状裂缝" in disease_type:
        bbox = draw_mesh_crack(msp, x_start, y_start, x_end, y_end, origin, scale_x=scale_x, scale_y=scale_y)
    elif "裂缝" in disease_type:
        # 判断是单条裂缝还是裂缝群
        width_m = abs(x_end - x_start)
        height_m = abs(y_end - y_start)
        
        if width_m < 0.1 and height_m > 0.1:
            # 单条竖向裂缝（x坐标相同，y有范围）
            # 在中心位置绘制一条竖向裂缝
            x_center = (cad_x1 + cad_x2) / 2
            y_top = max(cad_y1, cad_y2)
            y_bottom = min(cad_y1, cad_y2)
            # 绘制竖向裂缝线（带波浪效果）
            import math
            points = []
            wave_amp = 0.3  # 波浪幅度
            wave_freq = 0.5  # 波浪频率
            y = y_top
            while y >= y_bottom:
                phase = (y - y_top) * wave_freq
                wave_x = x_center + math.sin(phase) * wave_amp
                points.append((wave_x, y))
                y -= 0.2
            msp.add_lwpolyline(points=points, dxfattribs={"color": 7})
            bbox = (x_center - 0.5, y_bottom, x_center + 0.5, y_top)
        elif height_m < 0.1 and width_m > 0.1:
            # 单条水平/横向裂缝（y坐标相同，x有范围）
            x_left = min(cad_x1, cad_x2)
            x_right = max(cad_x1, cad_x2)
            y_center = (cad_y1 + cad_y2) / 2
            msp.add_line((x_left, y_center), (x_right, y_center), dxfattribs={"color": 7})
            bbox = (x_left, y_center - 0.5, x_right, y_center + 0.5)
        else:
            # 裂缝群（区域有宽度和高度）
            n_cracks = max(2, int(width_m * 2))  # 每米约2条裂缝
            bbox = draw_vertical_crack_group(msp, x_start, x_end, y_start, y_end, n_cracks, origin)
    elif "水蚀" in disease_type:
        bbox = draw_water_erosion(msp, x_start, y_start, x_end, y_end, origin, scale_x=scale_x, scale_y=scale_y)
    else:
        # 默认绘制矩形框
        msp.add_lwpolyline([(cad_x1, cad_y1), (cad_x2, cad_y1), (cad_x2, cad_y2), (cad_x1, cad_y2), (cad_x1, cad_y1)], close=True)
        bbox = (cad_x1, cad_y2, cad_x2, cad_y1)
    
    # 绘制标注
    if bbox:
        bbox_min_x, bbox_min_y, bbox_max_x, bbox_max_y = bbox
        # 从右下角引出标注
        label_start_x = bbox_max_x
        label_start_y = bbox_max_y
        
        # 计算引线角度（单柱墩盖梁使用与双柱墩相同的逻辑）
        x_center_m = (x_start + x_end) / 2
        angle = 45 if x_center_m < 6 else 315  # 简化的角度逻辑
        go_left = x_center_m >= 6
        
        # 根据方向调整引线起点
        if go_left:
            label_start_x = bbox_min_x
            label_start_y = bbox_min_y
        
        # 根据病害类型选择标注内容（只传数值，病害名称由draw_disease_label自动添加）
        length = disease.get("length", 0)
        width = disease.get("width", 0)
        if "裂缝" in disease_type and length > 0:
            label_text = f"L={length:.2f}m, W={width:.2f}mm"
        elif area > 0:
            label_text = f"S={area:.2f}m²"
        else:
            label_text = ""
        
        draw_disease_label(
            msp, disease, disease_type, label_text,
            label_start_x, label_start_y, 12,
            angle=angle, go_left=go_left, origin=origin
        )


def process_single_pier_disease(msp, disease: dict):
    """处理单柱墩病害：根据面积计算大小，从病害边缘引出标注"""
    location = disease.get("缺损位置", "")
    disease_type = disease.get("病害类型", "")
    cap_no = disease.get("盖梁号")
    area = disease.get("area", 0)
    
    # 从具体部件（从病害描述解析）判断面类型
    # 缺损位置列可能只有"盖梁"，具体部件才有"小桩号面/大桩号面"
    component_part = disease.get("具体部件", "")
    
    # 判断面类型
    face = (
        "小桩号面" if "小桩号面" in component_part else "大桩号面"
    )

    # 处理盖梁病害（使用单柱墩独立的比例尺）
    if "盖梁" in location:
        if face in SINGLE_PIER_ORIGINS:
            origin = SINGLE_PIER_ORIGINS[face]
            # 使用单柱墩独立的坐标转换系统
            process_single_pier_cap_beam(msp, disease, origin, SINGLE_PIER_SCALE_X, SINGLE_PIER_SCALE_Y)
    
    # 处理柱子病害
    elif "墩柱" in location or "柱" in location:
        if face in SINGLE_PIER_COLUMNS:
            rect = SINGLE_PIER_COLUMNS[face]["rect"]
            pier_x1, pier_y1, pier_x2, pier_y2 = rect

            # 根据面积计算病害区域大小（假设方形）
            # 面积 A，边长 L = sqrt(A)
            # 1m ≈ 15 CAD单位，1m² ≈ 225 CAD单位²
            # CAD边长 = sqrt(面积 * 225)
            if area > 0:
                side_len = math.sqrt(area * 225)
                # 最小尺寸限制，避免太小看不见
                side_len = max(side_len, 5)
                # 最大尺寸限制，不能超过柱子
                pier_w = pier_x2 - pier_x1 - 6  # 留边距
                pier_h = pier_y1 - pier_y2 - 6
                side_len = min(side_len, pier_w, pier_h)
            else:
                side_len = 8  # 默认8 CAD单位

            # 病害区域：柱子中间偏上
            pier_center_x = (pier_x1 + pier_x2) / 2
            # 柱子Y范围: pier_y1(233)上 到 pier_y2(194)下
            # 取上部1/3区域
            pier_top = pier_y1 - (pier_y1 - pier_y2) * 0.2  # 从顶部20%处
            pier_center_y = pier_top - side_len / 2
            x1 = pier_center_x - side_len / 2
            x2 = pier_center_x + side_len / 2
            y1 = pier_center_y + side_len  # 上边缘
            y2 = pier_center_y  # 下边缘

            print(
                f"    [单柱墩-{face}] 类型={disease_type}, 面积={area}m2, 病害尺寸={side_len:.1f}CAD单位"
            )

            # 空洞/孔洞：不绘制图形，也不标注
            if "空洞" in disease_type or "孔洞" in disease_type:
                print(f"    [单柱墩-{face}] 空洞/孔洞类型，跳过绘制")
                return

            # 绘制病害
            if "剥落露筋" in disease_type or "露筋" in disease_type:
                bbox = draw_rebar_corrosion(msp, x1, y1, x2, y2)
                if area > 0:
                    # 标注从病害右上角引出
                    label_start_x = bbox[2]  # 右边缘
                    label_start_y = bbox[3]  # 上边缘
                    draw_pier_disease_label(
                        msp, disease_type, area, label_start_x, label_start_y
                    )
            elif "剥落" in disease_type or "破损" in disease_type:
                bbox = draw_peel_off_direct(msp, x1, y1, x2, y2)
                if area > 0:
                    label_start_x = bbox[2]
                    label_start_y = bbox[3]
                    draw_pier_disease_label(
                        msp, disease_type, area, label_start_x, label_start_y
                    )
            elif "蜂窝" in disease_type or "麻面" in disease_type:
                draw_pier_honeycomb(msp, x1, y1, x2, y2)
                if area > 0:
                    label_start_x = max(x2 + 2, (x1 + x2) / 2)
                    label_start_y = y2
                    draw_pier_disease_label(
                        msp, disease_type, area, label_start_x, label_start_y
                    )
            elif "网状裂缝" in disease_type:
                # 网状裂缝：波浪线填充
                bbox = draw_pier_mesh_crack(msp, x1, y1, x2, y2)
                if area > 0:
                    label_start_x = bbox[2]  # 右边缘
                    label_start_y = bbox[3]  # 上边缘
                    draw_pier_disease_label(
                        msp, disease_type, area, label_start_x, label_start_y
                    )
            elif "裂缝" in disease_type or "开裂" in disease_type:
                # 水平裂缝线
                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2
                msp.add_line((x1, mid_y), (x2, mid_y), dxfattribs={"color": 7})
                length = disease.get("length", 0)
                width = disease.get("width", 0)
                if length > 0:
                    label_start_x = x2
                    label_start_y = mid_y
                    msp.add_text(
                        f"纵向裂缝 L={length:.2f}m",
                        dxfattribs={
                            "insert": (label_start_x + 2, label_start_y + 2.5),
                            "height": 2.5,
                            "color": 7,
                        },
                    )
                    if width > 0:
                        msp.add_text(
                            f"W={width:.2f}mm",
                            dxfattribs={
                                "insert": (label_start_x + 2, label_start_y - 2.5),
                                "height": 2.5,
                                "color": 7,
                            },
                        )



def process_pier_disease(msp, disease: dict):
    """处理墩柱病害：根据面积计算大小，从病害边缘引出标注"""
    location = disease.get("缺损位置", "")
    disease_type = disease.get("病害类型", "")
    pier_no = disease.get("墩柱号")
    column_no = disease.get("柱内编号")
    area = disease.get("area", 0)

    # 判断墩柱位置
    if pier_no and column_no:
        key = f"N-{column_no}"
        face = (
            "小桩号面" if ("小桩号面" in location or "墩柱" in location) else "大桩号面"
        )

        if face in PIER_ORIGINS and key in PIER_ORIGINS[face]:
            rect = PIER_ORIGINS[face][key]["rect"]
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

            print(
                f"    [墩柱{key}] 类型={disease_type}, 面积={area}m2, 病害尺寸={side_len:.1f}CAD单位"
            )

            # 空洞/孔洞：不绘制图形，也不标注
            if "空洞" in disease_type or "孔洞" in disease_type:
                print(f"    [墩柱{key}] 空洞/孔洞类型，跳过绘制")
                return

            # 绘制病害
            if "剥落露筋" in disease_type or "露筋" in disease_type:
                bbox = draw_rebar_corrosion(msp, x1, y1, x2, y2)
                if area > 0:
                    # 标注从病害右上角引出
                    label_start_x = bbox[2]  # 右边缘
                    label_start_y = bbox[3]  # 上边缘
                    draw_pier_disease_label(
                        msp, disease_type, area, label_start_x, label_start_y
                    )
            elif "剥落" in disease_type or "破损" in disease_type:
                # 使用平铺方式绘制剥落图例
                bbox = draw_peel_off_tiled_cad(msp, x1, y1, x2, y2)
                if area > 0:
                    label_start_x = bbox[2]
                    label_start_y = bbox[3]
                    draw_pier_disease_label(
                        msp, disease_type, area, label_start_x, label_start_y
                    )
            elif "蜂窝" in disease_type or "麻面" in disease_type:
                draw_pier_honeycomb(msp, x1, y1, x2, y2)
                if area > 0:
                    label_start_x = max(x2 + 2, (x1 + x2) / 2)
                    label_start_y = y2
                    draw_pier_disease_label(
                        msp, disease_type, area, label_start_x, label_start_y
                    )
            elif "裂缝" in disease_type or "开裂" in disease_type:
                # 水平裂缝线
                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2
                msp.add_line((x1, mid_y), (x2, mid_y), dxfattribs={"color": 7})
                length = disease.get("length", 0)
                width = disease.get("width", 0)
                if length > 0:
                    label_start_x = x2
                    label_start_y = mid_y
                    msp.add_text(
                        f"纵向裂缝 L={length:.2f}m",
                        dxfattribs={
                            "insert": (label_start_x + 2, label_start_y + 2.5),
                            "height": 2.5,
                            "color": 7,
                        },
                    )
                    if width > 0:
                        msp.add_text(
                            f"W={width:.2f}mm",
                            dxfattribs={
                                "insert": (label_start_x + 2, label_start_y - 2.5),
                                "height": 2.5,
                                "color": 7,
                            },
                        )


def draw_pier_disease_label(
    msp, disease_type: str, area: float, label_start_x: float, label_start_y: float
):
    """墩柱病害标注：折线引线 + 病害名 + 面积
    标注从病害边缘(label_start_x, label_start_y)引出
    """
    text_height = 2.5
    # 折线：第一段向上45度，第二段水平
    offset_45 = 5  # 45度线长度
    bend_x = label_start_x + offset_45  # 向右
    bend_y = label_start_y + offset_45  # 向上
    # 第二段水平线，长度根据文字长度决定
    seg2_len = max(12, len(disease_type) * 3 + len(f"{area:.2f}") * 5)
    end_x = bend_x + seg2_len
    end_y = bend_y
    # 绘制折线：从病害边缘开始
    msp.add_lwpolyline(
        [(label_start_x, label_start_y), (bend_x, bend_y), (end_x, end_y)],
        dxfattribs={"color": 7},
    )
    # 上方：病害名称
    msp.add_text(
        disease_type,
        dxfattribs={
            "insert": (bend_x + 1, bend_y + text_height * 0.3),
            "height": text_height,
            "color": 7,
        },
    )
    # 下方：面积
    msp.add_text(
        f"S={area:.2f}m²",
        dxfattribs={
            "insert": (bend_x + 1, bend_y - text_height * 1.5),
            "height": text_height,
            "color": 7,
        },
    )


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
            msp.add_circle((x, y), dot_r, dxfattribs={"color": 5})
            y += dot_spacing
        x += dot_spacing


def draw_pier_mesh_crack(msp, x1: float, y1: float, x2: float, y2: float):
    """墩柱网状裂缝：矩形内画波浪线填充（直接使用CAD坐标）"""
    import math
    
    min_x, max_x = min(x1, x2), max(x1, x2)
    min_y, max_y = min(y1, y2), max(y1, y2)
    
    wave_length = 4
    wave_amp = 0.3
    line_spacing = 1
    
    # 计算波浪线覆盖的高度
    height = max_y - min_y
    num_lines = max(1, int(height / line_spacing) + 1)
    
    # 从上到下画波浪线
    for i in range(num_lines):
        y = max_y - i * line_spacing
        if y < min_y:
            break
        points = []
        x = min_x
        while x <= max_x + wave_length:
            phase = (x - min_x) / wave_length * 2 * math.pi
            wave_y = y + math.sin(phase) * wave_amp
            points.append((x, wave_y))
            x += 0.2
        msp.add_lwpolyline(points=points, dxfattribs={"color": 7})
    
    # 返回边界框
    return (min_x, min_y, max_x, max_y)


def copy_entity_with_offset(msp, entity, y_offset: float, final_doc=None):
    """复制实体并应用Y偏移"""
    entity_type = entity.dxftype()
    layer = entity.dxf.layer if hasattr(entity.dxf, "layer") else "0"
    color = entity.dxf.color if hasattr(entity.dxf, "color") else 7

    if entity_type == "TEXT":
        text = entity.dxf.text
        height = entity.dxf.height if hasattr(entity.dxf, "height") else 2.5
        old_x, old_y = entity.dxf.insert[0], entity.dxf.insert[1]
        new_pos = (old_x, old_y + y_offset)
        text_obj = msp.add_text(
            text, dxfattribs={"layer": layer, "color": color, "height": height}
        )
        text_obj.dxf.insert = new_pos
        return text_obj

    elif entity_type == "MTEXT":
        old_x, old_y = entity.dxf.insert[0], entity.dxf.insert[1]
        new_pos = (old_x, old_y + y_offset)
        # 使用entity.text获取原始文本内容，保留换行符(\P格式)
        text_content = entity.text
        mtxt = msp.add_mtext(text_content, dxfattribs={"layer": layer})
        mtxt.dxf.insert = new_pos
        # 复制其他属性（包括控制自动换行的width）
        if hasattr(entity.dxf, "char_height"):
            mtxt.dxf.char_height = entity.dxf.char_height
        if hasattr(entity.dxf, "rect_width"):
            mtxt.dxf.rect_width = entity.dxf.rect_width
        if hasattr(entity.dxf, "attachment_point"):
            mtxt.dxf.attachment_point = entity.dxf.attachment_point
        if hasattr(entity.dxf, "line_spacing_factor"):
            mtxt.dxf.line_spacing_factor = entity.dxf.line_spacing_factor
        if hasattr(entity.dxf, "line_spacing_style"):
            mtxt.dxf.line_spacing_style = entity.dxf.line_spacing_style
        if hasattr(entity.dxf, "defined_height"):
            mtxt.dxf.defined_height = entity.dxf.defined_height
        if hasattr(entity.dxf, "width"):
            mtxt.dxf.width = entity.dxf.width
        if hasattr(entity.dxf, "flow_direction"):
            mtxt.dxf.flow_direction = entity.dxf.flow_direction
        return mtxt

    elif entity_type == "LINE":
        start = entity.dxf.start
        end = entity.dxf.end
        new_start = (start[0], start[1] + y_offset)
        new_end = (end[0], end[1] + y_offset)
        return msp.add_line(
            new_start, new_end, dxfattribs={"layer": layer, "color": color}
        )

    elif entity_type == "LWPOLYLINE":
        points = []
        if hasattr(entity, "get_points"):
            for pt in entity.get_points():
                points.append((pt[0], pt[1] + y_offset))
        if points:
            return msp.add_lwpolyline(
                points, dxfattribs={"layer": layer, "color": color}
            )
        return None

    elif entity_type == "SPLINE":
        try:
            # 使用copy()方法复制SPLINE，然后使用transform进行偏移
            from ezdxf.math import Matrix44
            new_spline = entity.copy()
            # 创建Y方向平移变换矩阵
            transform = Matrix44.translate(0, y_offset, 0)
            new_spline.transform(transform)
            msp.add_entity(new_spline)
            return new_spline
        except Exception as e:
            print(f"    [SPLINE复制失败] {e}")
            return None

    elif entity_type == "HATCH":
        try:
            # 使用copy()方法复制HATCH，然后使用transform进行偏移
            from ezdxf.math import Matrix44
            new_hatch = entity.copy()
            # 创建Y方向平移变换矩阵
            transform = Matrix44.translate(0, y_offset, 0)
            new_hatch.transform(transform)
            msp.add_entity(new_hatch)
            return new_hatch
        except Exception as e:
            print(f"    [HATCH复制失败] {e}")
            return None

    elif entity_type == "INSERT":
        block_name = entity.dxf.name
        old_x, old_y = entity.dxf.insert[0], entity.dxf.insert[1]
        new_pos = (old_x, old_y + y_offset)
        x_scale = entity.dxf.xscale if hasattr(entity.dxf, "xscale") else 1
        y_scale = entity.dxf.yscale if hasattr(entity.dxf, "yscale") else 1
        z_scale = entity.dxf.zscale if hasattr(entity.dxf, "zscale") else 1
        rotation = entity.dxf.rotation if hasattr(entity.dxf, "rotation") else 0
        return msp.add_blockref(
            block_name,
            new_pos,
            dxfattribs={
                "layer": layer,
                "xscale": x_scale,
                "yscale": y_scale,
                "zscale": z_scale,
                "rotation": rotation,
            },
        )

    elif entity_type == "CIRCLE":
        center = entity.dxf.center
        radius = entity.dxf.radius
        new_center = (center[0], center[1] + y_offset)
        return msp.add_circle(
            new_center, radius, dxfattribs={"layer": layer, "color": color}
        )

    elif entity_type == "ARC":
        center = entity.dxf.center
        radius = entity.dxf.radius
        start_angle = entity.dxf.start_angle
        end_angle = entity.dxf.end_angle
        new_center = (center[0], center[1] + y_offset)
        return msp.add_arc(
            new_center,
            radius,
            start_angle,
            end_angle,
            dxfattribs={"layer": layer, "color": color},
        )

    else:
        return None


def main():
    print("=" * 60)
    print("桥梁病害CAD标注系统 - 下部构件处理")
    print("支持：双柱墩、单柱墩、桥台（带台身/不带台身）")
    print("支持批量处理input目录中的所有Excel文件")
    print("=" * 60)

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 获取input目录中的所有Excel文件
    excel_files = []
    if os.path.exists(INPUT_DIR):
        for filename in os.listdir(INPUT_DIR):
            if filename.endswith('.xls') or filename.endswith('.xlsx'):
                excel_files.append(os.path.join(INPUT_DIR, filename))
    
    if not excel_files:
        print(f"\n错误：未在 {INPUT_DIR} 目录中找到Excel文件！")
        return
    
    print(f"\n发现 {len(excel_files)} 个Excel文件:")
    for i, f in enumerate(excel_files, 1):
        print(f"  {i}. {os.path.basename(f)}")

    # 处理每个Excel文件
    for excel_idx, excel_path in enumerate(excel_files, 1):
        print("\n" + "=" * 60)
        print(f"[{excel_idx}/{len(excel_files)}] 处理: {os.path.basename(excel_path)}")
        print("=" * 60)

        # 解析Excel数据
        print(f"\n读取Excel文件: {excel_path}")
        try:
            data = parse_excel(excel_path)
        except Exception as e:
            print(f"  解析失败: {e}")
            continue

        route_name = data["route_name"]
        bridge_name = data["bridge_name"]

        print(f"路线名称: {route_name}")
        print(f"桥梁名称: {bridge_name}")
        
        # 创建桥梁子目录，避免文件混淆
        bridge_output_dir = os.path.join(OUTPUT_DIR, bridge_name)
        os.makedirs(bridge_output_dir, exist_ok=True)
        print(f"输出目录: {bridge_output_dir}")
        
        all_output_files = []  # 所有输出文件（双柱墩 + 单柱墩 + 桥台）

        # ============= 处理双柱墩 =============
        print("\n" + "=" * 60)
        print("处理双柱墩...")
        
        # 筛选下部（双柱墩）数据
        lower_parts = []
        for part in data["parts"]:
            if "双柱墩" in part["name"]:
                lower_parts.append(part)

        if lower_parts:
            print(f"\n下部（双柱墩）构件数量: {len(lower_parts)}")

            # 收集所有盖梁和墩柱病害
            cap_beam_diseases = {}  # {盖梁号: [病害列表]}
            pier_diseases = {}  # {墩柱号: [病害列表]}

            for part in lower_parts:
                for comp_id, diseases in part["grouped_data"].items():
                    for d in diseases:
                        location = d.get("缺损位置", "")
                        if "墩柱" in location:
                            # 墩柱号是整数(如4)，柱内编号也是整数(如1)
                            # 需要组合成完整字符串如"4-1号"
                            pier_int = d.get("墩柱号")
                            col_int = d.get("柱内编号")
                            if pier_int is not None and col_int is not None:
                                pier_no = f"{pier_int}-{col_int}号"
                            elif pier_int is not None:
                                pier_no = f"{pier_int}号"
                            else:
                                pier_no = d.get("构件编号", "")
                            if pier_no:
                                if pier_no not in pier_diseases:
                                    pier_diseases[pier_no] = []
                                pier_diseases[pier_no].append(d)
                        else:
                            # 盖梁
                            cap_no = d.get("盖梁号")
                            if cap_no:
                                if cap_no not in cap_beam_diseases:
                                    cap_beam_diseases[cap_no] = []
                                cap_beam_diseases[cap_no].append(d)

            print(f"\n盖梁构件: {sorted(cap_beam_diseases.keys())}")
            print(f"墩柱构件: {sorted(pier_diseases.keys())}")

            # 配对：按编号排序
            # 盖梁号是整数(如4)，墩柱号是字符串(如"4-1号")
            # 配对规则：墩柱号 "n-m号" 的 n 与盖梁号 n 匹配
            def get_cap_base(no):
                """提取编号的主编号，如 '4-1号' -> '4', 4 -> '4'"""
                if no is None:
                    return None
                s = str(no)
                if "-" in s:
                    return s.split("-")[0].replace("号", "").strip()
                return s.replace("号", "").strip()

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

            print(f"\n配对结果: {len(page_pairs)} 页")
            for cap, pier in page_pairs:
                print(f"  盖梁{cap} + 墩柱{pier}")

            pier_output_files = []

            # 处理每一页
            for idx, (cap_no, pier_no) in enumerate(page_pairs):
                print(f"\n处理第{idx + 1}页: 盖梁{cap_no} + 墩柱{pier_no}")

                # 复制模板
                doc = ezdxf.readfile(TEMPLATE_FILE)
                msp = doc.modelspace()

                # 修改标题
                update_text_in_msp(msp, "LLL", route_name, height=6)
                update_text_in_msp(msp, "QQQ", bridge_name, height=6)
                if cap_no:
                    update_text_in_msp(msp, "GGG", f"{cap_no}号盖梁", height=6)

                # 绘制盖梁病害
                if cap_no:
                    # cap_no是字符串，但cap_beam_diseases键可能是整数，尝试两种方式查找
                    cap_key = int(cap_no) if cap_no.isdigit() else cap_no
                    diseases = cap_beam_diseases.get(cap_key) or cap_beam_diseases.get(cap_no)
                    if diseases:
                        # 为每个病害添加id，用于避让算法
                        for i, disease in enumerate(diseases):
                            disease['_id'] = f"{cap_no}_{i}"
                            disease['_page_diseases'] = diseases  # 记录同一页的所有病害
                        
                        # 处理每个病害（带避让逻辑）
                        for disease in diseases:
                            print(
                                f"  盖梁{cap_no} {disease.get('缺损位置', '')} {disease.get('病害类型', '')}"
                            )
                            process_cap_beam_disease(msp, disease, diseases)

                # 绘制墩柱病害
                if pier_no and pier_no in pier_diseases:
                    for disease in pier_diseases[pier_no]:
                        print(
                            f"  墩柱{pier_no} {disease.get('缺损位置', '')} {disease.get('病害类型', '')}"
                        )
                        process_pier_disease(msp, disease)

                # 保存 - 文件名格式：下部第N页_盖梁号-墩柱号.dxf
                if cap_no and pier_no:
                    comp_ids_str = f"盖梁{cap_no}-墩柱{pier_no}"
                elif cap_no:
                    comp_ids_str = f"盖梁{cap_no}"
                elif pier_no:
                    comp_ids_str = f"墩柱{pier_no}"
                else:
                    comp_ids_str = f"第{idx + 1}页"
                output_path = os.path.join(bridge_output_dir, f"下部第{idx + 1}页_{comp_ids_str}.dxf")
                doc.saveas(output_path)
                pier_output_files.append(output_path)
                all_output_files.append(output_path)
                print(f"  已保存: {output_path}")
        else:
            print("\n未找到双柱墩数据，跳过")
            pier_output_files = []

        # ============= 处理单柱墩 =============
        print("\n" + "=" * 60)
        print("处理单柱墩...")
        
        # 筛选单柱墩数据
        single_pier_parts = []
        for part in data["parts"]:
            if "单柱墩" in part["name"]:
                single_pier_parts.append(part)
        
        single_pier_output_files = []
        
        if single_pier_parts:
            print(f"\n单柱墩构件数量: {len(single_pier_parts)}")
            
            # 收集所有单柱墩病害（按构件编号分组）
            single_pier_diseases = {}  # {构件编号: [病害列表]}
            
            for part in single_pier_parts:
                for comp_id, diseases in part["grouped_data"].items():
                    if comp_id not in single_pier_diseases:
                        single_pier_diseases[comp_id] = []
                    single_pier_diseases[comp_id].extend(diseases)
            
            print(f"\n单柱墩构件: {sorted(single_pier_diseases.keys())}")
            
            # 分离盖梁和墩柱病害
            cap_beam_diseases = {}  # {盖梁号: [病害列表]}
            pier_diseases = {}      # {墩柱号: [病害列表]}
            
            for comp_id, diseases in single_pier_diseases.items():
                for disease in diseases:
                    location = disease.get("缺损位置", "")
                    if "盖梁" in location:
                        if comp_id not in cap_beam_diseases:
                            cap_beam_diseases[comp_id] = []
                        cap_beam_diseases[comp_id].append(disease)
                    elif "墩柱" in location or "柱" in location:
                        # 墩柱号可能是 "4-1号" 格式
                        if comp_id not in pier_diseases:
                            pier_diseases[comp_id] = []
                        pier_diseases[comp_id].append(disease)
            
            print(f"\n盖梁构件: {sorted(cap_beam_diseases.keys())}")
            print(f"墩柱构件: {sorted(pier_diseases.keys())}")
            
            # 配对：按编号排序
            # 盖梁号是字符串(如"4号")，墩柱号也是字符串(如"4-1号")
            # 配对规则：墩柱号 "n-m号" 或 "n号" 的 n 与盖梁号 n 匹配
            def get_cap_base(no):
                """提取编号的主编号，如 '4-1号' -> '4', '4号' -> '4'"""
                if no is None:
                    return None
                s = str(no)
                if "-" in s:
                    return s.split("-")[0].replace("号", "").strip()
                return s.replace("号", "").strip()
            
            all_nos = set()
            for cap_no in cap_beam_diseases.keys():
                base = get_cap_base(cap_no)
                if base:
                    all_nos.add(base)
            for pier_no in pier_diseases.keys():
                base = get_cap_base(pier_no)
                if base:
                    all_nos.add(base)
            
            page_pairs = []
            for no in sorted(all_nos, key=lambda x: int(x) if x.isdigit() else 0):
                # 查找盖梁
                cap_no = None
                for c_no in cap_beam_diseases.keys():
                    if get_cap_base(c_no) == no:
                        cap_no = c_no
                        break
                # 查找墩柱
                pier_no = None
                for p_no in pier_diseases.keys():
                    if get_cap_base(p_no) == no:
                        pier_no = p_no
                        break
                page_pairs.append((cap_no, pier_no))
            
            print(f"\n配对结果: {len(page_pairs)} 页")
            for cap, pier in page_pairs:
                print(f"  盖梁{cap} + 墩柱{pier}")
            
            # 处理每一页
            for idx, (cap_no, pier_no) in enumerate(page_pairs):
                if not cap_no and not pier_no:
                    continue
                
                comp_id = cap_no if cap_no else pier_no
                print(f"\n处理第{idx + 1}页: 盖梁{cap_no} + 墩柱{pier_no}")
                
                # 复制模板
                doc = ezdxf.readfile(SINGLE_PIER_TEMPLATE)
                msp = doc.modelspace()
                
                # 修改标题
                update_text_in_msp(msp, "LLL", route_name, height=6)
                update_text_in_msp(msp, "QQQ", bridge_name, height=6)
                update_text_in_msp(msp, "GGG", f"{comp_id}", height=6)
                
                # 处理盖梁病害
                if cap_no and cap_no in cap_beam_diseases:
                    for disease in cap_beam_diseases[cap_no]:
                        print(f"  {cap_no} 盖梁 {disease.get('病害类型', '')}")
                        process_single_pier_disease(msp, disease)
                
                # 处理墩柱病害
                if pier_no and pier_no in pier_diseases:
                    for disease in pier_diseases[pier_no]:
                        print(f"  {pier_no} 墩柱 {disease.get('病害类型', '')}")
                        process_single_pier_disease(msp, disease)
                
                # 保存
                output_path = os.path.join(bridge_output_dir, f"单柱墩_{comp_id}.dxf")
                doc.saveas(output_path)
                single_pier_output_files.append(output_path)
                all_output_files.append(output_path)
                print(f"  已保存: {output_path}")
        else:
            print("\n未找到单柱墩数据，跳过")
            single_pier_output_files = []

        # ============= 处理桥台 =============
        print("\n" + "=" * 60)
        print("处理桥台...")
        
        # 筛选桥台数据（带台身和不带台身）
        abutment_parts = []
        for part in data["parts"]:
            if "桥台" in part["name"]:
                abutment_parts.append(part)
        
        abutment_output_files = []  # 桥台输出文件
        
        if abutment_parts:
            print(f"\n桥台构件数量: {len(abutment_parts)}")
            
            for part in abutment_parts:
                part_name = part["name"]
                template_name = part["template_name"]
                
                # 确定桥台类型
                if "带台身" in part_name:
                    abut_type = "带台身桥台"
                    template_file = ABUT_WITH_TAI_TEMPLATE
                    comp_id_key = "台号"
                    title_key = "TTT"
                else:
                    abut_type = "不带台身桥台"
                    template_file = ABUT_WITHOUT_TAI_TEMPLATE
                    comp_id_key = "台号"
                    title_key = "TTT"
                
                print(f"\n处理 {part_name} (模板: {template_name})")
                
                # 收集该类型下的所有构件病害
                for comp_id, diseases in part["grouped_data"].items():
                    if not diseases:
                        continue
                    
                    # 复制模板
                    doc = ezdxf.readfile(template_file)
                    msp = doc.modelspace()
                    
                    # 修改标题 - 替换LLL, QQQ, TTT
                    update_text_in_msp(msp, "LLL", route_name, height=6)
                    update_text_in_msp(msp, "QQQ", bridge_name, height=6)
                    update_text_in_msp(msp, title_key, f"{comp_id}", height=6)
                    
                    # 为每个病害添加id和页病害列表（用于避让）
                    for i, disease in enumerate(diseases):
                        disease['_id'] = f"{comp_id}_{i}"
                        disease['_page_diseases'] = diseases
                    
                    # 处理每个病害
                    print(f"\n  构件: {comp_id} ({len(diseases)}条病害)")
                    for disease in diseases:
                        print(f"    {disease.get('缺损位置', '')} {disease.get('病害类型', '')}")
                        process_abutment_disease(msp, disease, diseases, abut_type)
                    
                    # 保存 - 文件名格式：桥台_类型_构件号.dxf
                    safe_part_name = part_name.replace("（", "_").replace("）", "").replace(" ", "")
                    output_path = os.path.join(bridge_output_dir, f"桥台_{safe_part_name}_{comp_id}.dxf")
                    doc.saveas(output_path)
                    abutment_output_files.append(output_path)
                    all_output_files.append(output_path)
                    print(f"  已保存: {output_path}")
        else:
            print("\n未找到桥台数据，跳过")
            abutment_output_files = []
        
        # ============= 创建合并文件 =============
        if all_output_files:
            print("\n" + "=" * 60)
            print("创建最终合并文件...")
            
            # 使用第一个文件作为基础模板
            first_file = all_output_files[0]
            final_doc = ezdxf.readfile(first_file)
            final_msp = final_doc.modelspace()
            
            # 清空所有实体
            for entity in list(final_msp):
                entity.destroy()
            
            # 添加桥梁名称标题（从第一个文件复制）
            title_gap = 100
            if os.path.exists(first_file):
                first_doc = ezdxf.readfile(first_file)
                first_msp = first_doc.modelspace()
                for entity in first_msp:
                    if entity.dxftype() in ("TEXT", "MTEXT"):
                        text_content = entity.text if entity.dxftype() == "MTEXT" else entity.dxf.text
                        if "QQQ" in text_content or ("K572" in text_content and len(text_content) > 20):
                            copy_entity_with_offset(final_msp, entity, title_gap, final_doc)
            
            # 复制所有页面
            page_height = 365
            gap = 100
            title_gap = 100
            
            for i, output_file in enumerate(all_output_files):
                if os.path.exists(output_file):
                    print(f"  复制第{i + 1}页 ({os.path.basename(output_file)})...")
                    y_offset = -(title_gap + page_height + i * (page_height + gap))
                    
                    page_doc = ezdxf.readfile(output_file)
                    page_msp = page_doc.modelspace()
                    
                    # 复制块定义
                    copy_blocks_to_doc(page_doc, final_doc)
                    
                    # 复制实体
                    for entity in page_msp:
                        try:
                            copy_entity_with_offset(final_msp, entity, y_offset, final_doc)
                        except Exception as e:
                            print(f"    复制实体失败: {e}")
            
            # 保存最终文件（使用Excel文件名作为前缀）
            excel_basename = os.path.splitext(os.path.basename(excel_path))[0]
            final_output = os.path.join(BASE_DIR, f"{excel_basename}-下部病害.dxf")
            final_doc.saveas(final_output)
            print(f"\n最终文件已保存: {final_output}")
        else:
            print("\n未生成任何输出文件")

    print("\n" + "=" * 60)
    print("所有Excel文件处理完成！")
    print("=" * 60)


def copy_blocks_to_doc(source_doc, target_doc):
    """将源文档中的所有块定义复制到目标文档"""
    for block in source_doc.blocks:
        block_name = block.name
        if block_name not in target_doc.blocks:
            try:
                new_block = target_doc.blocks.new(name=block_name)
                for entity in block:
                    copy_entity_to_block(new_block, entity)
            except Exception as e:
                print(f"    复制块定义 {block_name} 失败: {e}")


def copy_entity_to_block(block, entity):
    """将实体复制到块中"""
    try:
        new_entity = entity.copy()
        block.add_entity(new_entity)
    except Exception:
        entity_type = entity.dxftype()
        layer = entity.dxf.layer if hasattr(entity.dxf, "layer") else "0"
        color = entity.dxf.color if hasattr(entity.dxf, "color") else 7

        try:
            if entity_type == "TEXT":
                text = entity.dxf.text
                height = entity.dxf.height if hasattr(entity.dxf, "height") else 2.5
                insert = entity.dxf.insert
                block.add_text(
                    text, dxfattribs={"layer": layer, "color": color, "height": height}
                ).set_pos(insert)
            elif entity_type == "MTEXT":
                mtxt = block.add_mtext(
                    entity.text, dxfattribs={"layer": layer, "color": color}
                )
                mtxt.dxf.insert = entity.dxf.insert
                if hasattr(entity.dxf, "char_height"):
                    mtxt.dxf.char_height = entity.dxf.char_height
                if hasattr(entity.dxf, "rect_width"):
                    mtxt.dxf.rect_width = entity.dxf.rect_width
                if hasattr(entity.dxf, "width"):
                    mtxt.dxf.width = entity.dxf.width
            elif entity_type == "SPLINE":
                # 手动复制SPLINE的控制点和拟合点
                new_spline = block.add_spline(dxfattribs={"layer": layer, "color": color})
                # 复制控制点
                if entity.control_points:
                    for pt in entity.control_points:
                        new_spline.control_points.append(pt)
                # 复制拟合点
                if entity.fit_points:
                    for pt in entity.fit_points:
                        new_spline.fit_points.append(pt)
                # 复制其他属性
                if hasattr(entity.dxf, "degree"):
                    new_spline.dxf.degree = entity.dxf.degree
                if hasattr(entity.dxf, "closed"):
                    new_spline.dxf.closed = entity.dxf.closed
        except Exception as e:
            print(f"    复制实体类型 {entity_type} 失败: {e}")


if __name__ == "__main__":
    main()

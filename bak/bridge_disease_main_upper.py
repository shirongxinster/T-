# -*- coding: utf-8 -*-
"""
桥梁病害CAD标注系统 - 主程序
处理上部（40mT梁）的病害标注，将两个构件放到一张图中
"""

import os
import sys
import math
import random
import shutil
import ezdxf
from bridge_disease_parser import parse_excel

# 固定随机种子
random.seed(42)

# 路径配置
BASE_DIR = r'k:\works\008.S2ReportAndLayoutPic\leftRealJobs_workbuddy'
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates', '构件')
LEGENDS_DIR = os.path.join(BASE_DIR, 'templates', '病害图例')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output_pages')
TEMPLATE_FILE = os.path.join(TEMPLATES_DIR, '40mT梁.dxf')
PEEL_LEGEND_FILE = os.path.join(LEGENDS_DIR, '剥落、掉角.dxf')
REBAR_LEGEND_FILE = os.path.join(LEGENDS_DIR, '钢筋锈蚀或可见箍筋轮廓.dxf')

# 剥落图例原始数据（从模板提取）
PEEL_OFF_GEOMETRY = None
REBAR_GEOMETRY = None

def load_peel_off_geometry():
    """从剥落图例模板加载原始几何数据"""
    global PEEL_OFF_GEOMETRY
    if PEEL_OFF_GEOMETRY is not None:
        return PEEL_OFF_GEOMETRY

    doc = ezdxf.readfile(PEEL_LEGEND_FILE)
    block = doc.blocks.get('adfsd')

    # 提取所有实体数据
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

    # 计算边界框
    all_points = []
    for line in lines:
        all_points.extend([line['start'], line['end']])
    all_points.extend(polyline)

    if all_points:
        xs = [p[0] for p in all_points]
        ys = [p[1] for p in all_points]
        bbox = {
            'min_x': min(xs),
            'max_x': max(xs),
            'min_y': min(ys),
            'max_y': max(ys)
        }
    else:
        bbox = {'min_x': 0, 'max_x': 1, 'min_y': 0, 'max_y': 1}

    PEEL_OFF_GEOMETRY = {
        'lines': lines,
        'polyline': polyline,
        'bbox': bbox
    }
    return PEEL_OFF_GEOMETRY


def load_rebar_geometry():
    """从钢筋锈蚀模板加载原始几何数据"""
    global REBAR_GEOMETRY
    if REBAR_GEOMETRY is not None:
        return REBAR_GEOMETRY

    doc = ezdxf.readfile(REBAR_LEGEND_FILE)
    msp = doc.modelspace()

    # 提取所有实体数据
    lines = []
    polylines = []

    for entity in msp:
        if entity.dxftype() == 'LINE':
            lines.append({
                'start': (entity.dxf.start[0], entity.dxf.start[1]),
                'end': (entity.dxf.end[0], entity.dxf.end[1])
            })
        elif entity.dxftype() == 'LWPOLYLINE':
            pts = list(entity.get_points())
            polylines.append([(p[0], p[1]) for p in pts])

    # 计算边界框
    all_points = []
    for line in lines:
        all_points.extend([line['start'], line['end']])
    for pl in polylines:
        all_points.extend(pl)

    if all_points:
        xs = [p[0] for p in all_points]
        ys = [p[1] for p in all_points]
        bbox = {
            'min_x': min(xs),
            'max_x': max(xs),
            'min_y': min(ys),
            'max_y': max(ys)
        }
    else:
        bbox = {'min_x': 0, 'max_x': 1, 'min_y': 0, 'max_y': 1}

    REBAR_GEOMETRY = {
        'lines': lines,
        'polylines': polylines,
        'bbox': bbox
    }
    return REBAR_GEOMETRY


# 各部件原点坐标（模板坐标系）
BEAM_ORIGINS = {
    'upper': {  # 上方T梁
        '梁底': (83.8, 274),
        '左翼缘板': (83.8, 262.3),
        '右翼缘板': (83.8, 256.5),
        '左腹板': (83.8, 262.3),
        '右腹板': (83.8, 256.5),
        '马蹄左侧面': (83.8, 244),  # 估计值
    },
    'lower': {  # 下方T梁
        '梁底': (83.8, 160),
        '左翼缘板': (83.8, 150),
        '右翼缘板': (83.8, 144.2),
        '左腹板': (83.8, 150),
        '右腹板': (83.8, 144.2),
        '马蹄左侧面': (83.8, 132),  # 估计值
        '右侧齿块': (83.8, 144.2),  # 与右翼缘板共用
        '左侧齿块': (83.8, 150),  # 与左翼缘板共用
    }
}


def get_part_origin(part_type: str, specific_part: str) -> tuple:
    origins = BEAM_ORIGINS.get(part_type, BEAM_ORIGINS['upper'])
    return origins.get(specific_part, origins['梁底'])


def is_left_side_part(specific_part: str) -> bool:
    """判断是否为T梁的左面（上方）部件

    T梁坐标系：左面 = 上方部分，右面 = 下方部分
    """
    left_parts = ['左翼缘板', '左腹板', '马蹄左侧面']
    return any(part in specific_part for part in left_parts)


def convert_to_cad_coords(x: float, y: float, origin: tuple, specific_part: str = '') -> tuple:
    """将病害坐标转换为CAD坐标

    T梁坐标系：
    - 左面（左翼缘板、左腹板等）→ 上方 → y越大，CAD Y越大
    - 右面（右翼缘板、右腹板等）→ 下方 → y越大，CAD Y越小
    """
    origin_x, origin_y = origin
    cad_x = origin_x + x * 10

    # 根据部件决定Y轴方向
    if is_left_side_part(specific_part):
        # 左面部件：Y轴正向指向上方
        cad_y = origin_y + y * 10
    else:
        # 右面部件：Y轴负向指向下方（原逻辑）
        cad_y = origin_y - y * 10

    return (cad_x, cad_y)




def get_disease_draw_method(specific_part: str) -> str:
    """判断病害应该在哪个区域绘制（上半部分还是下半部分）

    注意：这个函数的返回值现在与T梁左右位置无关
    只用于决定病害在T梁内部是画在上方还是下方
    """
    # 上方区域：翼缘板、腹板、马蹄（在T梁的上方）
    upper_parts = ['左翼缘板', '右翼缘板', '左腹板', '右腹板', '马蹄左侧面', '马蹄右侧面']
    # 下方区域：梁底、齿块（在T梁的下方）
    lower_parts = ['梁底', '右侧齿块', '左侧齿块', '右侧面', '左侧面']

    if specific_part in upper_parts:
        return 'upper'
    elif specific_part in lower_parts:
        return 'lower'
    else:
        return 'lower'  # 默认下方


def get_beam_side_from_part(specific_part: str, x_start: float) -> str:
    """判断病害应该画在左侧T梁还是右侧T梁

    根据具体部件判断：
    - 左翼缘板、左腹板、马蹄左侧面 → 左侧T梁
    - 右翼缘板、右腹板、马蹄右侧面 → 右侧T梁
    - 梁底：根据x坐标判断（x < 20m → 左侧T梁，x >= 20m → 右侧T梁）
      因为40mT梁的每个T梁宽度约40m
    """
    if '左翼' in specific_part or '左腹' in specific_part or '马蹄左' in specific_part:
        return 'left'
    elif '右翼' in specific_part or '右腹' in specific_part or '马蹄右' in specific_part:
        return 'right'
    elif '梁底' in specific_part:
        # 梁底根据x坐标判断
        # 左侧T梁 x: 0-40m，右侧T梁 x: 40-80m
        # 阈值为20m
        if x_start < 20:
            return 'left'
        else:
            return 'right'
    else:
        return 'left'  # 默认左侧


def pair_components(components: list) -> list:
    pairs = []
    for i in range(0, len(components), 2):
        if i + 1 < len(components):
            pairs.append([components[i], components[i + 1]])
        else:
            pairs.append([components[i]])
    return pairs


def update_text_in_msp(msp, old_text: str, new_text: str, height: float = None, bold: bool = None):
    """替换模型空间中的文字（处理TEXT和MTEXT类型）

    Args:
        msp: 模型空间
        old_text: 要替换的旧文本
        new_text: 替换后的新文本
        height: 可选，设置文字高度（默认不改变）
        bold: 可选，设置粗体（默认不改变）
    """
    for entity in msp:
        if entity.dxftype() == 'TEXT':
            if old_text in entity.dxf.text:
                entity.dxf.text = entity.dxf.text.replace(old_text, new_text)
                if height is not None:
                    entity.dxf.height = height
                if bold is not None:
                    entity.dxf.bold = bold
        elif entity.dxftype() == 'MTEXT':
            # MTEXT内容可能带格式代码，如 {\C0;LLL}
            content = entity.text
            if old_text in content:
                # 替换整个MTEXT内容（包括格式代码）
                # 如果内容是 {\C0;LLL}，替换后变成 {\C0;实际内容}
                if content.strip().startswith('{\\') and old_text in content:
                    # 提取格式代码部分
                    import re
                    match = re.match(r'^(\{[^}]+\;)(.*)(\})$', content)
                    if match:
                        prefix = match.group(1)
                        suffix = match.group(3)
                        new_content = prefix + content.replace(old_text, new_text).replace(prefix, '').replace(suffix, '') + suffix
                        # 简化处理：直接替换
                        entity.text = content.replace(old_text, new_text)
                    else:
                        entity.text = content.replace(old_text, new_text)
                else:
                    entity.text = content.replace(old_text, new_text)
                if height is not None:
                    # MTEXT使用char_height属性
                    entity.dxf.char_height = height
                if bold is not None and bold:
                    # MTEXT粗体通过格式代码设置，添加 \B;
                    if not content.startswith('{\\B;'):
                        # 在现有格式代码前添加粗体代码
                        import re
                        match = re.match(r'^(\{[^;]+\;)(.*)', content)
                        if match:
                            entity.text = '{\\B;' + content
                        else:
                            entity.text = '{\\B;' + content + '}'


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
        go_left: 如果为True，标注向左画（文字在左侧）
    """
    text_height = 2.5

    bend_x, bend_y, end_x, end_y = draw_polyline_leader(msp, start_x, start_y, seg2_len, go_left)

    if go_left:
        # 向左画：文字在折点的左侧
        text_x = bend_x - seg2_len - 1  # 文字起始位置向左偏移
    else:
        # 向右画：文字在折点的右侧
        text_x = bend_x + 1

    msp.add_text(
        disease_type,
        dxfattribs={
            'insert': (text_x, bend_y + text_height * 0.5),
            'height': text_height,
            'color': 7
        }
    )

    if value_text:
        msp.add_text(
            value_text,
            dxfattribs={
                'insert': (text_x, bend_y - text_height * 1.5),
                'height': text_height,
                'color': 7
            }
        )


def draw_crack(msp, x_start: float, x_end: float, y: float, origin: tuple, specific_part: str = ''):
    """绘制单条裂缝（手绘风格）"""
    cad_x1, cad_y1 = convert_to_cad_coords(x_start, y, origin, specific_part)
    cad_x2, cad_y2 = convert_to_cad_coords(x_end, y, origin, specific_part)

    points = []
    x = cad_x1
    step = 0.8
    while x <= cad_x2:
        offset_y = math.sin((x - cad_x1) / 3) * 0.15 + random.uniform(-0.1, 0.1)
        points.append((x, cad_y1 + offset_y))
        x += step
    points.append((cad_x2, cad_y1))

    msp.add_lwpolyline(points=points, dxfattribs={'color': 7})


def draw_crack_group(msp, x_start: float, x_end: float, count: int, origin: tuple, specific_part: str = ''):
    """绘制裂缝群"""
    cad_x1, cad_y1 = convert_to_cad_coords(x_start, 0, origin, specific_part)
    cad_x2, cad_y2 = convert_to_cad_coords(x_end, 0, origin, specific_part)

    for i in range(count):
        y_offset = i * 1.0 + 0.5

        points = []
        x = cad_x1
        step = 0.8
        while x <= cad_x2:
            offset_y = math.sin((x - cad_x1) / 3) * 0.15 + random.uniform(-0.1, 0.1)
            points.append((x, cad_y1 - y_offset + offset_y))
            x += step
        points.append((cad_x2, cad_y1 - y_offset))

        msp.add_lwpolyline(points=points, dxfattribs={'color': 7})


def draw_mesh_crack(msp, x1: float, y1: float, x2: float, y2: float, origin: tuple, specific_part: str = ''):
    """绘制网状裂缝（波浪线填充）"""
    cad_x1, cad_y1 = convert_to_cad_coords(x1, y1, origin, specific_part)
    cad_x2, cad_y2 = convert_to_cad_coords(x2, y2, origin, specific_part)

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
        msp.add_lwpolyline(points=points, dxfattribs={'color': 7})


def draw_peel_off_with_rebar(msp, x1: float, y1: float, x2: float, y2: float, origin: tuple, specific_part: str = ''):
    """绘制剥落露筋 = 剥落不规则图形 + 叠加红色虚线交叉格栅"""
    # 第一步：先画剥落的不规则图形，同时获取实际绘制范围
    actual_bbox = draw_peel_off(msp, x1, y1, x2, y2, origin, specific_part, return_bbox=True)

    if actual_bbox is None:
        return

    # 第二步：用剥落图形的实际边界框范围叠加红色虚线格栅
    ax1, ay1, ax2, ay2 = actual_bbox  # ax1<ax2, ay2<ay1（ay1为上，ay2为下）
    height = ay1 - ay2
    width = ax2 - ax1

    grid_color = 1
    for i in range(1, 4):
        y = ay2 + height * i / 4
        msp.add_line(
            (ax1, y), (ax2, y),
            dxfattribs={'color': grid_color, 'linetype': 'DASHED'}
        )
    for i in range(1, 4):
        x = ax1 + width * i / 4
        msp.add_line(
            (x, ay2), (x, ay1),
            dxfattribs={'color': grid_color, 'linetype': 'DASHED'}
        )


def draw_peel_off(msp, x1: float, y1: float, x2: float, y2: float, origin: tuple, specific_part: str = '', return_bbox: bool = False):
    """绘制剥落图例（原封不动从模板提取）

    Args:
        return_bbox: 若为True，返回实际绘制区域的边界框 (ax1, ay1, ax2, ay2)，ay1为上，ay2为下
    """
    cad_x1, cad_y1 = convert_to_cad_coords(x1, y1, origin, specific_part)
    cad_x2, cad_y2 = convert_to_cad_coords(x2, y2, origin, specific_part)

    # 确保 cad_x1 < cad_x2, cad_y2 < cad_y1
    if cad_x1 > cad_x2:
        cad_x1, cad_x2 = cad_x2, cad_x1
    if cad_y2 > cad_y1:
        cad_y1, cad_y2 = cad_y2, cad_y1

    # 计算目标尺寸
    target_width = cad_x2 - cad_x1
    target_height = cad_y1 - cad_y2

    # 加载剥落图例原始数据
    geometry = load_peel_off_geometry()
    bbox = geometry['bbox']

    # 计算原始图形的边界框尺寸
    orig_width = bbox['max_x'] - bbox['min_x']
    orig_height = bbox['max_y'] - bbox['min_y']

    # 计算缩放比例
    scale_x = target_width / orig_width if orig_width > 0 else 1
    scale_y = target_height / orig_height if orig_height > 0 else 1

    # 使用统一的缩放比例（取较小的以保持比例）
    scale = min(scale_x, scale_y)

    # 计算偏移量，使图形居中对齐
    offset_x = cad_x1 - bbox['min_x'] * scale
    offset_y = cad_y2 - bbox['min_y'] * scale

    # 绘制线条（模拟锯齿边缘）
    for line in geometry['lines']:
        start_x = line['start'][0] * scale + offset_x
        start_y = line['start'][1] * scale + offset_y
        end_x = line['end'][0] * scale + offset_x
        end_y = line['end'][1] * scale + offset_y
        msp.add_line(
            (start_x, start_y), (end_x, end_y),
            dxfattribs={'color': 7}
        )

    # 绘制多边形（剥落主体）
    if geometry['polyline']:
        points = [(p[0] * scale + offset_x, p[1] * scale + offset_y) for p in geometry['polyline']]
        msp.add_lwpolyline(points=points, dxfattribs={'color': 7})

    if return_bbox:
        # 返回实际绘制的边界框（缩放后的bbox + offset）
        actual_x1 = bbox['min_x'] * scale + offset_x
        actual_x2 = bbox['max_x'] * scale + offset_x
        actual_y2 = bbox['min_y'] * scale + offset_y  # 下边
        actual_y1 = bbox['max_y'] * scale + offset_y  # 上边
        return (actual_x1, actual_y1, actual_x2, actual_y2)


def process_disease_record(msp, record: dict, comp_id: str, beam_level: str):
    """处理单条病害记录

    Args:
        msp: 模型空间
        record: 病害记录
        comp_id: 构件编号
        beam_level: T梁层级 ('upper' 或 'lower')，由pair中的位置决定
                    - pair[0] = 上方T梁 (b-b断面)
                    - pair[1] = 下方T梁 (a-a断面)
    """
    specific_part = record.get('具体部件', '梁底')
    disease_type = record.get('病害类型', '')

    # 泛白不绘制也不标注
    if '泛白' in disease_type:
        return
    x_start = record.get('x_start', 0)
    x_end = record.get('x_end', 0)
    y_start = record.get('y_start', 0)
    y_end = record.get('y_end', 0)
    length = record.get('length', 0)
    width = record.get('width', 0)
    area = record.get('area', 0)
    count = record.get('count', 0)
    spacing = record.get('spacing', 0)

    # 根据具体部件确定绘图区域（翼缘板/腹板在T梁上方，梁底在下方）
    part_type = get_disease_draw_method(specific_part)
    origin = get_part_origin(beam_level, specific_part)



    # 马蹄左侧面不绘制病害
    if '马蹄左' in specific_part or '马蹄右' in specific_part:
        return

    # 齿块不绘制病害
    if '齿块' in specific_part:
        return

    cad_x1, cad_y1 = convert_to_cad_coords(x_start, y_start, origin, specific_part)
    cad_x2, cad_y2 = convert_to_cad_coords(x_end, y_end, origin, specific_part)

    start_x = max(cad_x1, cad_x2)
    start_y = max(cad_y1, cad_y2)

    seg2_len = max(12, len(disease_type) * 3 + len(str(area or length)) * 5)

    # 计算如果向右画，标注的右边界x坐标
    # 折线：起点 -> 折点(45度,8单位) -> 终点(水平,seg2_len)
    # 向右画时，终点x = 起点x + 8*cos(45) + seg2_len
    right_boundary_if_go_right = start_x + 8 * math.cos(math.radians(45)) + seg2_len

    # 检查右边界是否超过483，如果超过则向左画
    # 向左画时，终点x = 起点x - 8*cos(45) - seg2_len，需要保证 >= 83
    go_left = False
    if right_boundary_if_go_right > 483:
        left_boundary = start_x - 8 * math.cos(math.radians(45)) - seg2_len
        if left_boundary >= 83:
            go_left = True
        # 否则保持向右画（即使会超出，用户可能需要调整）

    if disease_type == '网状裂缝':
        draw_mesh_crack(msp, x_start, y_start, x_end, y_end, origin, specific_part)
        draw_disease_label(msp, '网状裂缝', f'S={area:.2f}m²', start_x, start_y, seg2_len, go_left)

    elif disease_type in ['剥落', '剥落掉角', '掉角']:
        draw_peel_off(msp, x_start, y_start, x_end, y_end, origin, specific_part)
        draw_disease_label(msp, disease_type, f'S={area:.2f}m²', start_x, start_y, seg2_len, go_left)

    elif disease_type in ['剥落露筋', '漏筋', '露筋']:
        draw_peel_off_with_rebar(msp, x_start, y_start, x_end, y_end, origin, specific_part)
        draw_disease_label(msp, '剥落露筋', f'S={area:.2f}m²', start_x, start_y, seg2_len, go_left)

    elif '裂缝' in disease_type and count > 0:
        draw_crack_group(msp, x_start, x_end, count, origin, specific_part)
        label = f'{disease_type} L总={length:.2f}m N={count}条'
        value = f'间距{spacing:.2f}m' if spacing > 0 else ''
        draw_disease_label(msp, label, value, start_x, start_y, seg2_len, go_left)

    elif '裂缝' in disease_type:
        crack_y = (y_start + y_end) / 2
        draw_crack(msp, x_start, x_end, crack_y, origin, specific_part)
        if length > 0 and width > 0:
            label = f'{disease_type} L={length:.2f}m'
            value = f'W={width:.2f}mm'
        elif length > 0:
            label = f'{disease_type} L={length:.2f}m'
            value = ''
        else:
            label = disease_type
            value = ''
        draw_disease_label(msp, label, value, start_x, start_y, seg2_len, go_left)

    elif disease_type in ['蜂窝', '麻面', '水蚀']:
        draw_peel_off(msp, x_start, y_start, x_end, y_end, origin, specific_part)
        draw_disease_label(msp, disease_type, f'S={area:.2f}m²', start_x, start_y, seg2_len, go_left)

    else:
        draw_peel_off(msp, x_start, y_start, x_end, y_end, origin, specific_part)
        draw_disease_label(msp, disease_type, '', start_x, start_y, seg2_len, go_left)


def delete_text_in_rect(msp, x1: float, y1: float, x2: float, y2: float):
    """删除矩形区域内的所有实体（使用bbox精确检测）"""
    # 确保 left < right, bottom < top
    left = min(x1, x2)
    right = max(x1, x2)
    top = max(y1, y2)
    bottom = min(y1, y2)

    def rects_overlap(ax1, ay1, ax2, ay2, bx1, by1, bx2, by2):
        """判断两个矩形是否相交或重叠"""
        return not (ax2 <= bx1 or ax1 >= bx2 or ay2 <= by1 or ay1 >= by2)

    to_delete = []
    for entity in msp:
        try:
            # 使用实体的边界框检测
            bbox = entity.bbox
            if bbox is None:
                continue

            # 获取实体的边界框坐标
            e_left = bbox.dx.min
            e_right = bbox.dx.max
            e_bottom = bbox.dy.min
            e_top = bbox.dy.max

            # 检查实体的bbox是否与删除区域相交
            if rects_overlap(left, bottom, right, top, e_left, e_bottom, e_right, e_top):
                to_delete.append(entity)

        except Exception as e:
            # 如果bbox获取失败，尝试其他方法
            dxftype = entity.dxftype()
            try:
                if dxftype in ('TEXT', 'MTEXT'):
                    insert = entity.dxf.insert
                    if left <= insert[0] <= right and bottom <= insert[1] <= top:
                        to_delete.append(entity)
                elif dxftype == 'LINE':
                    start = entity.dxf.start
                    end = entity.dxf.end
                    if (left <= start[0] <= right and bottom <= start[1] <= top) or \
                       (left <= end[0] <= right and bottom <= end[1] <= top):
                        to_delete.append(entity)
            except:
                pass

    for entity in to_delete:
        msp.delete_entity(entity)


def create_page_for_pair(template_path: str, pair: list, disease_data: dict,
                         route_name: str, bridge_name: str, page_index: int) -> str:
    """为一对构件创建一页病害图"""
    import ezdxf

    # 读取模板
    doc = ezdxf.readfile(template_path)
    msp = doc.modelspace()

    # 修改标题（字号改为6）
    update_text_in_msp(msp, 'LLL', route_name, height=6)
    update_text_in_msp(msp, 'QQQ', bridge_name, height=6)

    # 确定孔次和梁号
    if len(pair) == 2:
        span1 = pair[0].split('-')[0] if '-' in pair[0] else pair[0]
        span2 = pair[1].split('-')[0] if '-' in pair[1] else pair[1]

        if span1 == span2:
            kkk = f'第{span1}孔'
            hhh = f'{pair[0].replace("号", "")}, {pair[1].replace("号", "")}'
        else:
            kkk = f'第{span1}孔、第{span2}孔'
            hhh = f'{pair[0].replace("号", "")}, {pair[1].replace("号", "")}'
    else:
        span = pair[0].split('-')[0] if '-' in pair[0] else pair[0]
        kkk = f'第{span}孔'
        hhh = pair[0].replace('号', '')

    update_text_in_msp(msp, 'KKK', kkk, height=6)
    update_text_in_msp(msp, 'HHH', hhh, height=6.5)

    # 修改横断面标注
    # Excel先出现的构件 → b-b断面上方，后出现的构件 → a-a断面下方
    if len(pair) >= 1:
        update_text_in_msp(msp, 'a-a', pair[0])  # 后出现的放下方(a-a)
    if len(pair) >= 2:
        update_text_in_msp(msp, 'b-b', pair[1])  # 先出现的放上方(b-b)

    # 单独构件时删除b-b断面及下方T梁区域
    # 删除范围: (28, 217) 到 (503, 78) 矩形区域
    if len(pair) == 1:
        delete_text_in_rect(msp, 28, 217, 503, 78)

    # 绘制病害
    # 重要：病害分配根据配对顺序决定，而非部件类型！
    # - pair[0] (先出现的构件) → 上方T梁 (upper坐标系, b-b断面)
    # - pair[1] (后出现的构件) → 下方T梁 (lower坐标系, a-a断面)
    #
    # 模板坐标系：
    # - upper坐标系 origin_y=274 → b-b断面（上方，y轴大）
    # - lower坐标系 origin_y=160 → a-a断面（下方，y轴小）
    for idx, comp_id in enumerate(pair):
        if comp_id in disease_data:
            # 根据配对顺序决定画在哪个T梁
            # idx=0: 先出现的构件 → upper（上方的b-b断面）
            # idx=1: 后出现的构件 → lower（下方的a-a断面）
            beam_level = 'upper' if idx == 0 else 'lower'

            for record in disease_data[comp_id]:
                specific_part = record.get('具体部件', '梁底')
                disease_type = record.get('病害类型', '')
                x_start = record.get('x_start', 0)

                print(f'  {comp_id} {disease_type} ({specific_part}): idx={idx} -> beam_level={beam_level}')

                process_disease_record(msp, record, comp_id, beam_level)

    # 保存
    output_path = os.path.join(OUTPUT_DIR, f'上部病害_第{page_index}页.dxf')
    doc.saveas(output_path)
    print(f'  已保存: {output_path}')

    return output_path


def main():
    """主函数"""
    print('='*60)
    print('桥梁病害CAD标注系统 - 上部（40mT梁）处理')
    print('='*60)

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 解析Excel数据
    excel_path = os.path.join(BASE_DIR, 'K572+774红石牡丹江大桥（右幅）病害.xls')
    print(f'\n读取Excel文件: {excel_path}')
    data = parse_excel(excel_path)

    route_name = data['route_name']
    bridge_name = data['bridge_name']

    print(f'路线名称: {route_name}')
    print(f'桥梁名称: {bridge_name}')

    # 获取上部（40mT梁）的病害数据
    upper_diseases = {}
    for part in data['parts']:
        if '上部' in part['name']:
            for comp_id, records in part['grouped_data'].items():
                upper_diseases[comp_id] = records

    print(f'\n上部（40mT梁）构件数量: {len(upper_diseases)}')
    print(f'构件列表: {list(upper_diseases.keys())}')

    # 配对构件
    components = list(upper_diseases.keys())
    pairs = pair_components(components)
    print(f'\n配对结果: {len(pairs)} 页')
    for i, pair in enumerate(pairs):
        print(f'  第{i+1}页: {pair}')

    # 为每对构件创建一页
    output_files = []

    for i, pair in enumerate(pairs):
        print(f'\n处理第{i+1}页: {pair}')
        output_path = create_page_for_pair(
            TEMPLATE_FILE, pair, upper_diseases,
            route_name, bridge_name, i + 1
        )
        output_files.append(output_path)

    # 创建最终合并文件
    print('\n' + '='*60)
    print('创建最终合并文件...')

    import ezdxf

    # 读取第一个模板作为基础
    final_doc = ezdxf.readfile(TEMPLATE_FILE)
    final_msp = final_doc.modelspace()

    # 清空模型空间（重新绘制）
    for entity in list(final_msp):
        entity.destroy()

    # 从每页复制内容，Y轴间隔50
    page_height = 365  # 图框高度
    gap = 50  # 图与图之间的间距
    for i, output_file in enumerate(output_files):
        if os.path.exists(output_file):
            print(f'  复制第{i+1}页...')
            y_offset = i * (page_height + gap)

            page_doc = ezdxf.readfile(output_file)
            page_msp = page_doc.modelspace()

            for entity in page_msp:
                try:
                    # 复制实体并应用Y偏移
                    new_entity = copy_entity_with_offset(final_msp, entity, y_offset)
                except Exception as e:
                    print(f'    复制实体失败: {e}')

    # 保存最终文件
    final_output = os.path.join(BASE_DIR, '上部病害_合并结果.dxf')
    final_doc.saveas(final_output)

    print(f'\n最终文件已保存: {final_output}')
    print('='*60)


def copy_entity_with_offset(msp, entity, y_offset: float):
    """复制实体并应用Y偏移"""
    entity_type = entity.dxftype()

    layer = entity.dxf.layer if hasattr(entity.dxf, 'layer') else '0'
    color = entity.dxf.color if hasattr(entity.dxf, 'color') else 7

    if entity_type == 'TEXT':
        text = entity.dxf.text
        height = entity.dxf.height if hasattr(entity.dxf, 'height') else 2.5
        bold = entity.dxf.bold if hasattr(entity.dxf, 'bold') else False
        old_x, old_y = entity.dxf.insert[0], entity.dxf.insert[1]
        new_pos = (old_x, old_y + y_offset)
        text_obj = msp.add_text(text, dxfattribs={'layer': layer, 'color': color, 'height': height})
        text_obj.dxf.insert = new_pos
        if bold:
            text_obj.dxf.bold = bold
        return text_obj

    elif entity_type == 'MTEXT':
        # MTEXT - 直接使用原生拷贝
        old_x, old_y = entity.dxf.insert[0], entity.dxf.insert[1]
        new_pos = (old_x, old_y + y_offset)
        mtxt = msp.add_mtext(entity.text, dxfattribs={'layer': layer})
        mtxt.dxf.insert = new_pos
        if hasattr(entity.dxf, 'char_height'):
            mtxt.dxf.char_height = entity.dxf.char_height
        if hasattr(entity.dxf, 'width'):
            mtxt.dxf.width = entity.dxf.width
        if hasattr(entity.dxf, 'height'):
            mtxt.dxf.height = entity.dxf.height
        if hasattr(entity.dxf, 'style'):
            mtxt.dxf.style = entity.dxf.style
        if hasattr(entity.dxf, 'color'):
            mtxt.dxf.color = entity.dxf.color
        # 设置MTEXT的段落宽度（控制换行）
        if hasattr(entity.dxf, 'rect_width'):
            mtxt.dxf.rect_width = entity.dxf.rect_width
        elif hasattr(entity, 'rect_width'):
            mtxt.dxf.rect_width = entity.rect_width
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

    elif entity_type == 'POLYLINE':
        points = []
        if hasattr(entity, 'points'):
            for pt in entity.points:
                points.append((pt[0], pt[1] + y_offset))
        if points:
            return msp.add_polyline2d(points, dxfattribs={'layer': layer, 'color': color})
        return None

    elif entity_type == 'SPLINE':
        # SPLINE - 使用正确的ezdxf API
        try:
            from ezdxf.math import BSpline
            if hasattr(entity, 'control_points') and entity.control_points:
                control_points = [(pt[0], pt[1] + y_offset, 0) for pt in entity.control_points]
                spline = BSpline(control_points)
                return msp.add_spline(spline, dxfattribs={'layer': layer, 'color': color})
        except Exception as e:
            pass
        return None

    elif entity_type == 'HATCH':
        # HATCH - 尝试复制
        try:
            hatch = msp.add_hatch(entity.dxf.pattern_name, dxfattribs={'layer': layer})
            # 复制边界路径
            for path in entity.paths:
                if path.has_outer_path:
                    # 获取边界点
                    if hasattr(path, 'get_outer_points'):
                        outer_pts = path.get_outer_points()
                        if outer_pts:
                            # 添加边界
                            pass
            return hatch
        except:
            return None

    elif entity_type == 'INSERT':
        # INSERT - 块引用
        block_name = entity.dxf.name
        old_x, old_y = entity.dxf.insert[0], entity.dxf.insert[1]
        new_pos = (old_x, old_y + y_offset)
        x_scale = entity.dxf.xscale if hasattr(entity.dxf, 'xscale') else 1
        y_scale = entity.dxf.yscale if hasattr(entity.dxf, 'yscale') else 1
        z_scale = entity.dxf.zscale if hasattr(entity.dxf, 'zscale') else 1
        rotation = entity.dxf.rotation if hasattr(entity.dxf, 'rotation') else 0
        return msp.add_blockref(block_name, new_pos, dxfattribs={'layer': layer, 'xscale': x_scale, 'yscale': y_scale, 'zscale': z_scale, 'rotation': rotation})

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

    elif entity_type == 'POINT':
        location = entity.dxf.location
        new_location = (location[0], location[1] + y_offset)
        return msp.add_point(new_location, dxfattribs={'layer': layer, 'color': color})

    else:
        # 尝试通用复制
        return None


if __name__ == '__main__':
    main()

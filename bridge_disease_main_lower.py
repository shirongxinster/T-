# -*- coding: utf-8 -*-
"""
桥梁病害CAD标注系统 - 下部病害处理程序
处理双柱墩和桥台的病害标注
"""

import os
import sys
import math
import random
import ezdxf
from bridge_disease_parser import parse_excel

# 固定随机种子
random.seed(42)

# 路径配置
BASE_DIR = r'k:\works\008.S2ReportAndLayoutPic\leftRealJobs_workbuddy'
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates', '构件')
LEGENDS_DIR = os.path.join(BASE_DIR, 'templates', '病害图例')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output_pages')
PIER_TEMPLATE = os.path.join(TEMPLATES_DIR, '双柱墩.dxf')
ABUTMENT_TEMPLATE = os.path.join(TEMPLATES_DIR, '不带台身桥台.dxf')
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


# 双柱墩病害标注区域配置
# 原点位置和病害区域的映射
PIER_DISEASE_ZONES = {
    # 小桩号面 - 左侧区域
    '小桩号面': {
        'origin': (56.4, 139.5),
        'width': 45.5,  # 到101.2
        'height': 11.2,  # 到150.7
        'direction': 'up'  # Y轴向上
    },
    # 大桩号面 - 右侧区域
    '大桩号面': {
        'origin': (159.9, 139.5),
        'width': 58.6,  # 到218.5
        'height': 11.2,
        'direction': 'up'
    },
    # 右侧面 - 中间区域
    '右侧面': {
        'origin': (121.9, 139.5),
        'width': 38.0,  # 到159.9
        'height': 11.2,
        'direction': 'up'
    },
    # 左侧齿块
    '左侧齿块': {
        'origin': (48.0, 105.3),
        'width': 14.6,  # 48->62.5
        'height': 7.5,
        'direction': 'down'
    },
    # 右侧齿块
    '右侧齿块': {
        'origin': (156.3, 93.1),
        'width': 14.5,  # 156.3->170.8
        'height': 7.2,
        'direction': 'down'
    }
}

# 桥台病害标注区域
ABUTMENT_DISEASE_ZONES = {
    '小桩号面': {'origin': (50, 130), 'width': 50, 'height': 15, 'direction': 'up'},
    '大桩号面': {'origin': (150, 130), 'width': 50, 'height': 15, 'direction': 'up'},
    '台帽': {'origin': (50, 100), 'width': 100, 'height': 20, 'direction': 'up'},
}


def update_text_in_msp(msp, old_text: str, new_text: str):
    """替换模型空间中的文字"""
    for entity in msp:
        if entity.dxftype() == 'TEXT':
            if old_text in entity.dxf.text:
                entity.dxf.text = entity.dxf.text.replace(old_text, new_text)
        elif entity.dxftype() == 'MTEXT':
            content = entity.text
            if old_text in content:
                entity.text = content.replace(old_text, new_text)


def draw_polyline_leader(msp, start_x: float, start_y: float, seg2_len: float):
    """绘制折线引线"""
    seg1_len = 8
    angle = math.radians(45)
    bend_x = start_x + seg1_len * math.cos(angle)
    bend_y = start_y + seg1_len * math.sin(angle)
    end_x = bend_x + seg2_len
    points = [(start_x, start_y), (bend_x, bend_y), (end_x, bend_y)]
    msp.add_lwpolyline(points=points, dxfattribs={'color': 7})
    return (bend_x, bend_y, end_x, bend_y)


def draw_disease_label(msp, disease_type: str, value_text: str, start_x: float, start_y: float, seg2_len: float):
    """绘制病害标注"""
    text_height = 2.5
    bend_x, bend_y, end_x, end_y = draw_polyline_leader(msp, start_x, start_y, seg2_len)

    msp.add_text(
        disease_type,
        dxfattribs={
            'insert': (bend_x + 1, bend_y + text_height * 0.5),
            'height': text_height,
            'color': 7
        }
    )

    if value_text:
        msp.add_text(
            value_text,
            dxfattribs={
                'insert': (bend_x + 1, bend_y - text_height * 1.5),
                'height': text_height,
                'color': 7
            }
        )


def convert_to_zone_coords(x: float, y: float, zone: dict) -> tuple:
    """将病害坐标转换为模板坐标"""
    origin_x, origin_y = zone['origin']
    direction = zone['direction']

    if direction == 'up':
        # Y轴向上：CAD Y = origin_y + y * 10
        cad_x = origin_x + x * 10
        cad_y = origin_y + y * 10
    else:
        # Y轴向下
        cad_x = origin_x + x * 10
        cad_y = origin_y - y * 10

    return (cad_x, cad_y)


def draw_crack(msp, x_start: float, x_end: float, y: float, zone: dict):
    """绘制裂缝（手绘风格）"""
    cad_x1, cad_y1 = convert_to_zone_coords(x_start, y, zone)
    cad_x2, cad_y2 = convert_to_zone_coords(x_end, y, zone)

    points = []
    x = cad_x1
    step = 0.8
    while x <= cad_x2:
        offset_y = math.sin((x - cad_x1) / 3) * 0.15 + random.uniform(-0.1, 0.1)
        points.append((x, cad_y1 + offset_y))
        x += step
    points.append((cad_x2, cad_y1))

    msp.add_lwpolyline(points=points, dxfattribs={'color': 7})


def draw_crack_group(msp, x_start: float, x_end: float, count: int, zone: dict):
    """绘制裂缝群"""
    cad_x1, cad_y1 = convert_to_zone_coords(x_start, 0, zone)
    cad_x2, cad_y2 = convert_to_zone_coords(x_end, 0, zone)

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


def draw_mesh_crack(msp, x1: float, y1: float, x2: float, y2: float, zone: dict):
    """绘制网状裂缝（波浪线填充）"""
    cad_x1, cad_y1 = convert_to_zone_coords(x1, y1, zone)
    cad_x2, cad_y2 = convert_to_zone_coords(x2, y2, zone)

    if cad_x1 > cad_x2:
        cad_x1, cad_x2 = cad_x2, cad_x1
    if cad_y1 < cad_y2:
        cad_y1, cad_y2 = cad_y2, cad_y1

    wave_length = 4
    wave_amp = 0.3
    line_spacing = 1
    height = abs(cad_y2 - cad_y1)
    num_lines = max(1, int(height / line_spacing) + 1)
    y_top = max(cad_y1, cad_y2)

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


def draw_peel_off_with_rebar(msp, x1: float, y1: float, x2: float, y2: float, zone: dict):
    """绘制剥落露筋"""
    cad_x1, cad_y1 = convert_to_zone_coords(x1, y1, zone)
    cad_x2, cad_y2 = convert_to_zone_coords(x2, y2, zone)

    if cad_x1 > cad_x2:
        cad_x1, cad_x2 = cad_x2, cad_x1
    if cad_y2 > cad_y1:
        cad_y1, cad_y2 = cad_y2, cad_y1

    width = cad_x2 - cad_x1
    height = cad_y1 - cad_y2

    # 白色剥落图（矩形）
    points = [(cad_x1, cad_y1), (cad_x2, cad_y1), (cad_x2, cad_y2), (cad_x1, cad_y2), (cad_x1, cad_y1)]
    msp.add_lwpolyline(points=points, dxfattribs={'color': 7})

    # 红色虚线格栅
    grid_color = 1
    for i in range(1, 4):
        y = cad_y2 + height * i / 4
        msp.add_line(
            (cad_x1, y), (cad_x2, y),
            dxfattribs={'color': grid_color, 'linetype': 'DASHED'}
        )
    for i in range(1, 4):
        x = cad_x1 + width * i / 4
        msp.add_line(
            (x, cad_y2), (x, cad_y1),
            dxfattribs={'color': grid_color, 'linetype': 'DASHED'}
        )


def draw_peel_off(msp, x1: float, y1: float, x2: float, y2: float, zone: dict):
    """绘制剥落图例"""
    cad_x1, cad_y1 = convert_to_zone_coords(x1, y1, zone)
    cad_x2, cad_y2 = convert_to_zone_coords(x2, y2, zone)

    if cad_x1 > cad_x2:
        cad_x1, cad_x2 = cad_x2, cad_x1
    if cad_y2 > cad_y1:
        cad_y1, cad_y2 = cad_y2, cad_y1

    target_width = cad_x2 - cad_x1
    target_height = cad_y1 - cad_y2

    geometry = load_peel_off_geometry()
    bbox = geometry['bbox']

    orig_width = bbox['max_x'] - bbox['min_x']
    orig_height = bbox['max_y'] - bbox['min_y']

    scale_x = target_width / orig_width if orig_width > 0 else 1
    scale_y = target_height / orig_height if orig_height > 0 else 1
    scale = min(scale_x, scale_y)

    offset_x = cad_x1 - bbox['min_x'] * scale
    offset_y = cad_y2 - bbox['min_y'] * scale

    for line in geometry['lines']:
        start_x = line['start'][0] * scale + offset_x
        start_y = line['start'][1] * scale + offset_y
        end_x = line['end'][0] * scale + offset_x
        end_y = line['end'][1] * scale + offset_y
        msp.add_line(
            (start_x, start_y), (end_x, end_y),
            dxfattribs={'color': 7}
        )

    if geometry['polyline']:
        points = [(p[0] * scale + offset_x, p[1] * scale + offset_y) for p in geometry['polyline']]
        msp.add_lwpolyline(points=points, dxfattribs={'color': 7})


def process_disease_record(msp, record: dict, disease_zones: dict):
    """处理单条病害记录"""
    specific_part = record.get('具体部件', '小桩号面')
    disease_type = record.get('病害类型', '')
    x_start = record.get('x_start', 0)
    x_end = record.get('x_end', 0)
    y_start = record.get('y_start', 0)
    y_end = record.get('y_end', 0)
    length = record.get('length', 0)
    width = record.get('width', 0)
    area = record.get('area', 0)
    count = record.get('count', 0)

    # 获取病害区域配置
    zone = disease_zones.get(specific_part, disease_zones.get('小桩号面'))

    cad_x1, cad_y1 = convert_to_zone_coords(x_start, y_start, zone)
    cad_x2, cad_y2 = convert_to_zone_coords(x_end, y_end, zone)

    start_x = max(cad_x1, cad_x2)
    start_y = max(cad_y1, cad_y2)

    seg2_len = max(12, len(disease_type) * 3 + len(str(area or length)) * 5)

    if disease_type == '网状裂缝':
        draw_mesh_crack(msp, x_start, y_start, x_end, y_end, zone)
        draw_disease_label(msp, '网状裂缝', f'S={area:.2f}m²', start_x, start_y, seg2_len)

    elif disease_type in ['剥落', '剥落掉角', '掉角', '破损']:
        draw_peel_off(msp, x_start, y_start, x_end, y_end, zone)
        draw_disease_label(msp, disease_type, f'S={area:.2f}m²', start_x, start_y, seg2_len)

    elif disease_type in ['剥落露筋', '漏筋', '露筋']:
        draw_peel_off_with_rebar(msp, x_start, y_start, x_end, y_end, zone)
        draw_disease_label(msp, '剥落露筋', f'S={area:.2f}m²', start_x, start_y, seg2_len)

    elif '裂缝' in disease_type and count > 0:
        draw_crack_group(msp, x_start, x_end, count, zone)
        draw_disease_label(msp, f'{disease_type} N={count}条', '间距1.00m', start_x, start_y, seg2_len)

    elif '裂缝' in disease_type:
        crack_y = (y_start + y_end) / 2
        draw_crack(msp, x_start, x_end, crack_y, zone)
        if length > 0 and width > 0:
            label = f'{disease_type} L={length:.2f}m'
            value = f'W={width:.2f}mm'
        elif length > 0:
            label = f'{disease_type} L={length:.2f}m'
            value = ''
        else:
            label = disease_type
            value = ''
        draw_disease_label(msp, label, value, start_x, start_y, seg2_len)

    elif disease_type in ['蜂窝', '麻面', '水蚀', '孔洞空洞']:
        draw_peel_off(msp, x_start, y_start, x_end, y_end, zone)
        draw_disease_label(msp, disease_type, f'S={area:.2f}m²', start_x, start_y, seg2_len)

    else:
        draw_peel_off(msp, x_start, y_start, x_end, y_end, zone)
        draw_disease_label(msp, disease_type, '', start_x, start_y, seg2_len)


def create_pier_page(template_path: str, comp_id: str, records: list,
                     route_name: str, bridge_name: str, page_index: int,
                     output_dir: str) -> str:
    """为单个桥墩创建一页病害图"""
    doc = ezdxf.readfile(template_path)
    msp = doc.modelspace()

    # 解析盖梁号（去掉"号"字，后面的函数会加回来）
    cap_beam_no = comp_id.replace('号', '').split('-')[0] if '-' in comp_id else comp_id.replace('号', '')

    # 修改标题
    update_text_in_msp(msp, 'LLL', route_name)
    update_text_in_msp(msp, 'QQQ', bridge_name)
    update_text_in_msp(msp, 'GGG', f'{cap_beam_no}号盖梁')

    print(f'  盖梁号: {cap_beam_no}号')

    # 绘制病害
    for record in records:
        specific_part = record.get('具体部件', '小桩号面')
        disease_type = record.get('病害类型', '')

        # 选择病害区域
        zone = PIER_DISEASE_ZONES.get(specific_part, PIER_DISEASE_ZONES['小桩号面'])

        print(f'    {specific_part}: {disease_type}')
        process_disease_record(msp, record, PIER_DISEASE_ZONES)

    # 保存
    output_path = os.path.join(output_dir, f'下部病害_{comp_id}.dxf')
    doc.saveas(output_path)
    print(f'  已保存: {output_path}')

    return output_path


def create_abutment_page(template_path: str, comp_id: str, records: list,
                         route_name: str, bridge_name: str, page_index: int,
                         output_dir: str) -> str:
    """为单个桥台创建一页病害图"""
    doc = ezdxf.readfile(template_path)
    msp = doc.modelspace()

    # 修改标题
    update_text_in_msp(msp, 'LLL', route_name)
    update_text_in_msp(msp, 'QQQ', bridge_name)

    print(f'  桥台号: {comp_id}')

    # 绘制病害
    for record in records:
        specific_part = record.get('具体部件', '小桩号面')
        disease_type = record.get('病害类型', '')

        zone = ABUTMENT_DISEASE_ZONES.get(specific_part, ABUTMENT_DISEASE_ZONES['小桩号面'])

        print(f'    {specific_part}: {disease_type}')
        process_disease_record(msp, record, ABUTMENT_DISEASE_ZONES)

    # 保存
    output_path = os.path.join(output_dir, f'桥台病害_{comp_id}.dxf')
    doc.saveas(output_path)
    print(f'  已保存: {output_path}')

    return output_path


def main():
    """主函数"""
    print('=' * 60)
    print('桥梁病害CAD标注系统 - 下部病害处理')
    print('=' * 60)

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

    # 处理双柱墩病害
    pier_records = {}
    abutment_records = {}

    for part in data['parts']:
        if '下部' in part['name']:
            for comp_id, records in part['grouped_data'].items():
                pier_records[comp_id] = records
        elif '桥台' in part['name']:
            for comp_id, records in part['grouped_data'].items():
                abutment_records[comp_id] = records

    output_files = []

    # 生成双柱墩病害图
    if pier_records:
        print(f'\n--- 处理双柱墩病害 ({len(pier_records)} 个构件) ---')
        for i, (comp_id, records) in enumerate(pier_records.items()):
            print(f'\n处理第{i+1}个桥墩: {comp_id}')
            output_path = create_pier_page(
                PIER_TEMPLATE, comp_id, records,
                route_name, bridge_name, i + 1, OUTPUT_DIR
            )
            output_files.append(output_path)

    # 生成桥台病害图
    if abutment_records:
        print(f'\n--- 处理桥台病害 ({len(abutment_records)} 个构件) ---')
        for i, (comp_id, records) in enumerate(abutment_records.items()):
            print(f'\n处理第{i+1}个桥台: {comp_id}')
            output_path = create_abutment_page(
                ABUTMENT_TEMPLATE, comp_id, records,
                route_name, bridge_name, i + 1, OUTPUT_DIR
            )
            output_files.append(output_path)

    print('\n' + '=' * 60)
    print(f'处理完成！共生成 {len(output_files)} 个文件:')
    for f in output_files:
        print(f'  - {os.path.basename(f)}')
    print('=' * 60)


if __name__ == '__main__':
    main()

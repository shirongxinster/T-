# -*- coding: utf-8 -*-
"""
read_tbeam_template.py
用于分析40mT梁模板，获取标题方框位置和T梁各部件原点坐标

坐标系说明:
- 模板坐标系: 直接从模板读取的坐标
- 实际CAD坐标系: 输出时的坐标（需要根据比例换算）
- 1m = 10 CAD单位
"""

import ezdxf


def find_title_boxes():
    """查找标题信息空白方框的位置（模板坐标系）"""
    title_boxes = {
        'route_name': (217.4, 349.5),
        'bridge_name': (331.4, 348.3),
        'span': (433.0, 355.2),
        'beam': (433.1, 341.8),
    }
    return title_boxes


def find_part_labels():
    """查找T梁各部件的标注位置（模板坐标系）"""
    part_labels = {
        'a-a': (58.2, 314.3),
        'b-b': (56.6, 213.0),
        'LLL': (178.9, 354.7),
        'QQQ': (297.1, 356.1),
        'KKK': (441.5, 360.8),
        'HHH': (440.8, 348.0),
        '左腹板_上方': (70.2, 151.3),
        '右腹板_上方': (70.2, 140.1),
        '左腹板_下方': (70.2, 263.6),
        '右腹板_下方': (70.2, 252.5),
    }
    return part_labels


def find_ruler_info():
    """查找标尺信息（模板坐标系）"""
    ruler_x = 83.8
    
    ruler_info = {
        'ruler_x': ruler_x,
        'upper': {
            'scale_1': [274, 244],
            'scale_2_25': [262.3, 256.5],
        },
        'lower': {
            'scale_1': [132, 160],
            'scale_2_25': [144.2, 150],
        }
    }
    return ruler_info


def find_tbeam_parts():
    """分析T梁各部件位置（模板坐标系）"""
    ruler_info = find_ruler_info()
    part_labels = find_part_labels()
    
    return {
        'ruler_x': ruler_info['ruler_x'],
        'upper': {
            'y_scale_1_first': ruler_info['upper']['scale_1'][0],
            'y_scale_1_second': ruler_info['upper']['scale_1'][1],
            'y_scale_2_25_first': ruler_info['upper']['scale_2_25'][0],
            'y_scale_2_25_second': ruler_info['upper']['scale_2_25'][1],
        },
        'lower': {
            'y_scale_1_first': ruler_info['lower']['scale_1'][0],
            'y_scale_1_second': ruler_info['lower']['scale_1'][1],
            'y_scale_2_25_first': ruler_info['lower']['scale_2_25'][0],
            'y_scale_2_25_second': ruler_info['lower']['scale_2_25'][1],
        },
        'labels': part_labels,
    }


def calculate_part_origin(part_name, span_no, beam_no, is_upper):
    """计算任意部件的原点

    返回:
        (x, y, x_dir, y_dir): 原点坐标和方向
        x_dir: X轴方向（1=从左到右）
        y_dir: Y轴方向（1=从上到下，-1=从下到上）
    """
    ruler_x = 83.8

    # 用户提供的固定值
    origins_upper = {
        '梁底': (ruler_x, 274),
        '左翼缘板': (ruler_x, 262.3),
        '右翼缘板': (ruler_x, 256.5),
        '左腹板': (ruler_x, 262.3),
        '右腹板': (ruler_x, 256.5),
    }

    origins_lower = {
        '梁底': (ruler_x, 160),
        '左翼缘板': (ruler_x, 150),      # 根据2.25推算
        '右翼缘板': (ruler_x, 144.2),   # 根据2.25推算
        '左腹板': (ruler_x, 150),        # 根据2.25推算
        '右腹板': (ruler_x, 144.2),      # 根据2.25推算
    }

    # Y轴方向定义
    y_directions = {
        '梁底': 1,          # 从上到下
        '左翼缘板': -1,     # 从下到上
        '右翼缘板': 1,      # 从上到下
        '左腹板': -1,       # 从下到上
        '右腹板': 1,        # 从上到下
    }

    if is_upper:
        origins = origins_upper
    else:
        origins = origins_lower

    pos = origins.get(part_name, (ruler_x, 274 if is_upper else 160))
    x_dir = 1  # X轴始终从左到右
    y_dir = y_directions.get(part_name, 1)

    return pos[0], pos[1], x_dir, y_dir


if __name__ == '__main__':
    print("=== 标题信息方框位置（模板坐标系）===")
    title_boxes = find_title_boxes()
    for name, pos in title_boxes.items():
        print(f"  {name}: ({pos[0]}, {pos[1]})")
    
    print()
    print("=== 标尺信息 ===")
    ruler_info = find_ruler_info()
    print(f"横向标尺0 X坐标: {ruler_info['ruler_x']}")
    print(f"纵向标尺1:")
    print(f"  上方T梁: Y = {ruler_info['upper']['scale_1']}")
    print(f"  下方T梁: Y = {ruler_info['lower']['scale_1']}")
    print(f"纵向标尺2.25:")
    print(f"  上方T梁: Y = {ruler_info['upper']['scale_2_25']}")
    print(f"  下方T梁: Y = {ruler_info['lower']['scale_2_25']}")
    
    print()
    print("=== 梁底原点坐标 ===")
    print("1-1号（上方T梁）:")
    x, y, x_dir, y_dir = calculate_part_origin('梁底', span_no=1, beam_no=1, is_upper=True)
    y_dir_str = "从上到下" if y_dir == 1 else "从下到上"
    print(f"  原点: ({x}, {y})")
    print(f"  X方向: 从左到右")
    print(f"  Y方向: {y_dir_str}")
    
    print()
    print("1-2号（下方T梁）:")
    x, y, x_dir, y_dir = calculate_part_origin('梁底', span_no=1, beam_no=2, is_upper=False)
    y_dir_str = "从上到下" if y_dir == 1 else "从下到上"
    print(f"  原点: ({x}, {y})")
    print(f"  X方向: 从左到右")
    print(f"  Y方向: {y_dir_str}")
    
    print()
    print("=== 各部件原点坐标 ===")
    parts = ['梁底', '左翼缘板', '右翼缘板', '左腹板', '右腹板']
    
    print("1-1号（上方T梁）:")
    for part in parts:
        x, y, x_dir, y_dir = calculate_part_origin(part, span_no=1, beam_no=1, is_upper=True)
        y_dir_str = "从上到下" if y_dir == 1 else "从下到上"
        print(f"  {part}: ({x}, {y}), Y方向: {y_dir_str}")
    
    print()
    print("1-2号（下方T梁）:")
    for part in parts:
        x, y, x_dir, y_dir = calculate_part_origin(part, span_no=1, beam_no=2, is_upper=False)
        y_dir_str = "从上到下" if y_dir == 1 else "从下到上"
        print(f"  {part}: ({x}, {y}), Y方向: {y_dir_str}")

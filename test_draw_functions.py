# -*- coding: utf-8 -*-
"""测试病害绘制函数"""
import os
import math
import random
import ezdxf

# 固定随机种子
random.seed(42)

# 部件原点
BEAM_ORIGINS = {
    'upper': {
        '梁底': (83.8, 274),
        '左翼缘板': (83.8, 262.3),
        '右翼缘板': (83.8, 256.5),
        '左腹板': (83.8, 262.3),
        '右腹板': (83.8, 256.5),
        '马蹄左侧面': (83.8, 244),
    },
    'lower': {
        '梁底': (83.8, 160),
        '左翼缘板': (83.8, 150),
        '右翼缘板': (83.8, 144.2),
        '左腹板': (83.8, 150),
        '右腹板': (83.8, 144.2),
        '马蹄左侧面': (83.8, 132),
    }
}

def get_part_origin(part_type: str, specific_part: str) -> tuple:
    origins = BEAM_ORIGINS.get(part_type, BEAM_ORIGINS['upper'])
    return origins.get(specific_part, origins['梁底'])

def get_disease_draw_method(specific_part: str) -> str:
    if specific_part in ['左翼缘板', '右翼缘板', '左腹板', '右腹板', '马蹄左侧面']:
        return 'upper'
    else:
        return 'lower'

def convert_to_cad_coords(x: float, y: float, origin: tuple) -> tuple:
    origin_x, origin_y = origin
    cad_x = origin_x + x * 10
    cad_y = origin_y - y * 10
    return (cad_x, cad_y)


def draw_crack(msp, x_start: float, x_end: float, y: float, origin: tuple):
    """绘制单条裂缝（手绘风格）"""
    cad_x1, cad_y1 = convert_to_cad_coords(x_start, y, origin)
    cad_x2, cad_y2 = convert_to_cad_coords(x_end, y, origin)

    print(f"  绘制裂缝: ({cad_x1:.1f}, {cad_y1:.1f}) -> ({cad_x2:.1f}, {cad_y2:.1f})")

    points = []
    x = cad_x1
    step = 0.8
    while x <= cad_x2:
        offset_y = math.sin((x - cad_x1) / 3) * 0.15 + random.uniform(-0.1, 0.1)
        points.append((x, cad_y1 + offset_y))
        x += step
    points.append((cad_x2, cad_y1))

    msp.add_lwpolyline(points=points, dxfattribs={'color': 7})
    print(f"    添加了 {len(points)} 个点")


def draw_peel_off(msp, x1: float, y1: float, x2: float, y2: float, origin: tuple):
    """绘制剥落矩形"""
    cad_x1, cad_y1 = convert_to_cad_coords(x1, y1, origin)
    cad_x2, cad_y2 = convert_to_cad_coords(x2, y2, origin)

    if cad_x1 > cad_x2:
        cad_x1, cad_x2 = cad_x2, cad_x1
    if cad_y1 < cad_y2:
        cad_y1, cad_y2 = cad_y2, cad_y1

    print(f"  绘制剥落矩形: ({cad_x1:.1f}, {cad_y1:.1f}) -> ({cad_x2:.1f}, {cad_y2:.1f})")

    points = [(cad_x1, cad_y1), (cad_x2, cad_y1), (cad_x2, cad_y2), (cad_x1, cad_y2), (cad_x1, cad_y1)]
    msp.add_lwpolyline(points=points, dxfattribs={'color': 7})


def draw_mesh_crack(msp, x1: float, y1: float, x2: float, y2: float, origin: tuple):
    """绘制网状裂缝（波浪线填充）"""
    cad_x1, cad_y1 = convert_to_cad_coords(x1, y1, origin)
    cad_x2, cad_y2 = convert_to_cad_coords(x2, y2, origin)

    # 确保 cad_x1 < cad_x2
    if cad_x1 > cad_x2:
        cad_x1, cad_x2 = cad_x2, cad_x1

    print(f"  绘制网状裂缝: ({cad_x1:.1f}, {cad_y1:.1f}) -> ({cad_x2:.1f}, {cad_y2:.1f})")

    wave_length = 4
    wave_amp = 0.3
    line_spacing = 1

    # 计算波浪线覆盖的高度（取绝对值）
    height = abs(cad_y2 - cad_y1)
    num_lines = max(1, int(height / line_spacing) + 1)
    print(f"    波浪线数量: {num_lines}")

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


def main():
    # 创建测试文档 - 使用与模板相同的版本
    doc = ezdxf.new(dxfversion='AC1032')
    msp = doc.modelspace()

    # 测试梁底裂缝（1-1号的纵向裂缝）
    print("=== 测试梁底裂缝 ===")
    origin = BEAM_ORIGINS['lower']['梁底']
    draw_crack(msp, 10.0, 14.0, 0.5, origin)

    # 测试网状裂缝（1-2号的网状裂缝）
    print("\n=== 测试网状裂缝 ===")
    origin = BEAM_ORIGINS['lower']['梁底']
    draw_mesh_crack(msp, 15.0, 0.0, 30.0, 0.6, origin)

    # 测试剥落（1-2号的左翼缘板剥落）
    print("\n=== 测试左翼缘板剥落 ===")
    origin = BEAM_ORIGINS['upper']['左翼缘板']
    draw_peel_off(msp, 0.4, 0.5, 0.6, 0.6, origin)

    # 保存测试文件
    test_file = os.path.join(os.getcwd(), 'test_disease_draw.dxf')
    doc.saveas(test_file)
    print(f"\n测试文件已保存: {test_file}")


if __name__ == '__main__':
    main()

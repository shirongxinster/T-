# -*- coding: utf-8 -*-
"""详细分析T梁模板"""

import ezdxf

doc = ezdxf.readfile('templates/构件/40mT梁.dxf')
ms = doc.modelspace()

# 收集所有标题框线
print('=== 标题框分析 ===')
boxes = []
for entity in ms:
    if entity.dxftype() == 'LINE':
        color = entity.dxf.color if hasattr(entity.dxf, 'color') else 0
        if color == 5:  # 标题框颜色
            start = entity.dxf.start
            end = entity.dxf.end
            boxes.append((start, end))

# 分析每个方框
print('\n找到的方框线：')
for i, (s, e) in enumerate(boxes):
    print(f'{i+1}. ({s[0]:.1f},{s[1]:.1f}) -> ({e[0]:.1f},{e[1]:.1f})')

# 分析X方向的方框（水平线）
print('\n=== 标题框位置推断 ===')
# 找水平线
horizontal_lines = []
for s, e in boxes:
    if abs(s[1] - e[1]) < 1:  # 水平线
        horizontal_lines.append((s[0], e[0], s[1]))
        
horizontal_lines.sort(key=lambda x: x[2])  # 按Y坐标排序
for x1, x2, y in horizontal_lines:
    print(f'水平线: X={x1:.1f}~{x2:.1f}, Y={y:.1f}')

# 找垂直线
vertical_lines = []
for s, e in boxes:
    if abs(s[0] - e[0]) < 1:  # 垂直线
        vertical_lines.append((s[1], e[1], s[0]))
        
vertical_lines.sort(key=lambda x: x[2])  # 按X坐标排序
for y1, y2, x in vertical_lines:
    print(f'垂直线: Y={y1:.1f}~{y2:.1f}, X={x:.1f}')

print('\n=== 梁底/梁侧标尺分析 ===')
# 找横向标尺0的位置（X坐标最小的纵向线）
ruler_x_lines = []
for entity in ms:
    if entity.dxftype() == 'LINE':
        layer = entity.dxf.layer if hasattr(entity.dxf, 'layer') else '?'
        start = entity.dxf.start
        end = entity.dxf.end
        
        # 找X坐标较小的纵向线（标尺）
        if start[0] < 31700 and end[0] < 31700:
            if abs(start[0] - end[0]) < 5 and abs(start[1] - end[1]) > 10:
                ruler_x_lines.append((start[0], start[1], end[1], layer))

ruler_x_lines.sort(key=lambda x: x[0])
print('X方向标尺位置:')
for x, y1, y2, layer in ruler_x_lines[:10]:
    print(f'  X={x:.1f}, Y={y1:.1f}~{y2:.1f}, 图层={layer}')

# 找Y方向标尺（横向刻度）
print('\nY方向刻度:')
for entity in ms:
    if entity.dxftype() == 'LINE':
        start = entity.dxf.start
        end = entity.dxf.end
        # Y方向的小短线（标尺刻度）
        if 31640 < start[0] < 31700 and 31640 < end[0] < 31700:
            if abs(start[1] - end[1]) < 10 and abs(start[0] - end[0]) > 5:
                print(f'  ({start[0]:.1f},{start[1]:.1f}) -> ({end[0]:.1f},{end[1]:.1f})')

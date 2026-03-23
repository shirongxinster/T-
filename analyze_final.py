# -*- coding: utf-8 -*-
"""更精确地分析模板"""

import ezdxf

doc = ezdxf.readfile('templates/构件/40mT梁.dxf')
ms = doc.modelspace()

print('=== 标题框精确位置 ===')
# 分析Y=-3847.5到-3867区域的方框
boxes = []
for entity in ms:
    if entity.dxftype() == 'LINE':
        color = entity.dxf.color if hasattr(entity.dxf, 'color') else 0
        start = entity.dxf.start
        end = entity.dxf.end
        
        # 只看标题区域
        if -3900 < start[1] < -3800 and -3900 < end[1] < -3800:
            boxes.append((start[0], end[0], start[1], end[1], color))

# 去重并排序
unique_boxes = {}
for x1, x2, y1, y2, c in boxes:
    key = tuple(sorted([x1, x2]))
    if key not in unique_boxes:
        unique_boxes[key] = (y1, y2, c)

print('找到的垂直线（方框边界）：')
x_positions = set()
for (x1, x2), (y1, y2, c) in sorted(unique_boxes.items()):
    x_positions.add(x1)
    x_positions.add(x2)
    
sorted_x = sorted(x_positions)
print('X坐标:', sorted_x)

print('\n=== 标题文字位置 ===')
for entity in ms:
    if entity.dxftype() == 'TEXT':
        text = entity.dxf.text
        insert = entity.dxf.insert
        if '名称' in text or '孔' in text or '梁' in text or '图' in text:
            if -4200 < insert[1] < -3800:
                print(f'TEXT: "{text}" 位置=({insert[0]:.1f}, {insert[1]:.1f})')

print('\n=== 病害标尺原点分析 ===')
# 找梁底的横向标尺0位置（X=31657.2处的纵向线）
print('梁底横向标尺0的X坐标: 31657.2')

# 找纵向标尺1
# 上方T梁的纵向标尺1: Y约-3901.3
# 下方T梁的纵向标尺1: Y约-4001.7
print('上方T梁原点: (31657.2, -3901.3)')
print('下方T梁原点: (31657.2, -4001.7)')

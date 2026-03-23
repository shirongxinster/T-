# -*- coding: utf-8 -*-
"""分析T梁模板中的标尺和标题框位置"""

import ezdxf

# 读取T梁模板
doc = ezdxf.readfile('templates/构件/40mT梁.dxf')
ms = doc.modelspace()

print('=== 查找标题框（颜色5的线）===')
for entity in ms:
    if entity.dxftype() == 'LINE':
        color = entity.dxf.color if hasattr(entity.dxf, 'color') else '?'
        if color == 5:  # 病害图层（标题框颜色）
            start = entity.dxf.start
            end = entity.dxf.end
            # 查找Y坐标在-3800附近的方框
            if -3900 < start[1] < -3800 and -3900 < end[1] < -3800:
                print(f'LINE: ({start[0]:.1f},{start[1]:.1f})->({end[0]:.1f},{end[1]:.1f}) 颜色={color}')

print('\n=== 查找纵向标尺（Y方向的刻度线）===')
for entity in ms:
    if entity.dxftype() == 'LINE':
        layer = entity.dxf.layer if hasattr(entity.dxf, 'layer') else '?'
        start = entity.dxf.start
        end = entity.dxf.end
        
        # 找X坐标较小，Y方向的小短线（标尺刻度）
        if start[0] < 31700 and end[0] < 31700:
            # 纵向标尺刻度线（Y方向的小短线）
            if abs(start[0] - end[0]) < 50 and abs(start[1] - end[1]) > 5:
                print(f'LINE: ({start[0]:.1f},{start[1]:.1f})->({end[0]:.1f},{end[1]:.1f}) 图层={layer}')

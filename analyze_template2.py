# -*- coding: utf-8 -*-
"""分析T梁模板中的标题位置"""

import ezdxf

# 读取T梁模板
doc = ezdxf.readfile('templates/构件/40mT梁.dxf')
ms = doc.modelspace()

print('=== 查找标题相关实体 ===')
for entity in ms:
    etype = entity.dxftype()
    layer = entity.dxf.layer if hasattr(entity.dxf, 'layer') else '?'
    color = entity.dxf.color if hasattr(entity.dxf, 'color') else '?'
    
    if etype == 'TEXT':
        text = entity.dxf.text
        insert = entity.dxf.insert
        # 查找包含"名称"、"孔"、"梁"、"路线"的文字
        if any(kw in text for kw in ['名称', '孔', '梁', '路线', '图名', '上部']):
            print(f'{etype}: "{text}" 位置=({insert[0]:.1f}, {insert[1]:.1f}) 图层={layer} 颜色={color}')
    
    if etype == 'MTEXT':
        text = entity.text[:100] if hasattr(entity, 'text') else ''
        insert = entity.dxf.insert if hasattr(entity.dxf, 'insert') else None
        if insert:
            if any(kw in text for kw in ['名称', '孔', '梁', '路线', '图名', '上部']):
                print(f'{etype}: "{text}" 位置=({insert[0]:.1f}, {insert[1]:.1f}) 图层={layer} 颜色={color}')
    
    if etype == 'LINE':
        start = entity.dxf.start
        end = entity.dxf.end
        # 查找标题框相关的线（颜色5或较大的坐标范围）
        if color == 5 or color == 3:  # 红色或黄色
            # 查找接近标题位置的线
            if -4000 < start[1] < -3800 and -4000 < end[1] < -3800:
                print(f'{etype}: ({start[0]:.1f},{start[1]:.1f})->({end[0]:.1f},{end[1]:.1f}) 图层={layer} 颜色={color}')

print('\n=== 查找病害标注区域 ===')
for entity in ms:
    etype = entity.dxftype()
    if etype == 'TEXT':
        text = entity.dxf.text
        insert = entity.dxf.insert
        # 查找梁底、左翼缘等位置标注
        if any(kw in text for kw in ['梁底', '翼缘', '腹板']):
            print(f'{etype}: "{text}" 位置=({insert[0]:.1f}, {insert[1]:.1f})')

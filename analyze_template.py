# -*- coding: utf-8 -*-
"""分析T梁模板中的实体"""

import ezdxf

# 读取T梁模板
doc = ezdxf.readfile('templates/构件/40mT梁.dxf')
ms = doc.modelspace()

print('=== T梁模板中的所有实体 ===')
for entity in ms:
    etype = entity.dxftype()
    layer = entity.dxf.layer if hasattr(entity.dxf, 'layer') else '?'
    color = entity.dxf.color if hasattr(entity.dxf, 'color') else '?'
    
    if etype == 'TEXT' or etype == 'MTEXT':
        text = entity.dxf.text if etype == 'TEXT' else entity.text[:50] if hasattr(entity, 'text') else '?'
        insert = entity.dxf.insert if hasattr(entity.dxf, 'insert') else '?'
        print(f'{etype}: "{text}" 位置={insert} 图层={layer} 颜色={color}')
    elif etype == 'LINE':
        start = entity.dxf.start
        end = entity.dxf.end
        print(f'{etype}: ({start[0]:.1f},{start[1]:.1f})->({end[0]:.1f},{end[1]:.1f}) 图层={layer} 颜色={color}')
    elif etype == 'LWPOLYLINE':
        print(f'{etype}: 图层={layer} 颜色={color}')
    elif etype == 'INSERT':
        name = entity.dxf.name
        insert = entity.dxf.insert
        print(f'{etype}: {name} 位置={insert} 图层={layer} 颜色={color}')
    elif etype == 'CIRCLE':
        center = entity.dxf.center
        radius = entity.dxf.radius
        print(f'{etype}: 中心=({center[0]:.1f},{center[1]:.1f}) 半径={radius:.1f} 图层={layer} 颜色={color}')

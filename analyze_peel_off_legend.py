# -*- coding: utf-8 -*-
import ezdxf
doc = ezdxf.readfile('templates/病害图例/剥落、掉角.dxf')

# 查看 adfsd 块内容
block_name = 'adfsd'
block = doc.blocks.get(block_name)
print(f'=== 块 {block_name} 内容 ===')

for entity in block:
    etype = entity.dxftype()
    if etype == 'LINE':
        print(f'LINE: ({entity.dxf.start[0]:.1f}, {entity.dxf.start[1]:.1f}) -> ({entity.dxf.end[0]:.1f}, {entity.dxf.end[1]:.1f})')
    elif etype == 'LWPOLYLINE':
        pts = list(entity.get_points())
        print(f'LWPOLYLINE ({len(pts)} 点):')
        for p in pts:
            print(f'  ({p[0]:.1f}, {p[1]:.1f})')
    elif etype == 'TEXT':
        print(f'TEXT: {entity.dxf.text} at ({entity.dxf.insert[0]:.1f}, {entity.dxf.insert[1]:.1f})')
    else:
        print(f'{etype}')

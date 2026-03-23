# -*- coding: utf-8 -*-
import ezdxf
doc = ezdxf.readfile('templates/病害图例/剥落、掉角.dxf')

# 查看 A$C04EE150E 块
block = doc.blocks.get('A$C04EE150E')
print(f'=== 块 A$C04EE150E 完整内容 ===')

for entity in block:
    etype = entity.dxftype()
    if etype == 'LINE':
        print(f'LINE: ({entity.dxf.start[0]:.2f}, {entity.dxf.start[1]:.2f}) -> ({entity.dxf.end[0]:.2f}, {entity.dxf.end[1]:.2f})')
    elif etype == 'LWPOLYLINE':
        pts = list(entity.get_points())
        print(f'LWPOLYLINE ({len(pts)} 点):')
        for p in pts:
            print(f'  ({p[0]:.2f}, {p[1]:.2f})')
    elif etype == 'TEXT':
        print(f'TEXT: {entity.dxf.text} at ({entity.dxf.insert[0]:.2f}, {entity.dxf.insert[1]:.2f})')
    else:
        print(f'{etype}')

# 检查模型空间中这个块的引用
print('\n=== 模型空间中 A$C04EE150E 的引用 ===')
msp = doc.modelspace()
for entity in msp:
    if entity.dxftype() == 'INSERT' and entity.dxf.name == 'A$C04EE150E':
        print(f'位置: ({entity.dxf.insert[0]:.2f}, {entity.dxf.insert[1]:.2f})')
        print(f'缩放: ({entity.dxf.xscale:.4f}, {entity.dxf.yscale:.4f})')

# -*- coding: utf-8 -*-
import ezdxf
doc = ezdxf.readfile('templates/病害图例/剥落、掉角.dxf')

print('=== 块列表 ===')
for block in doc.blocks:
    print(f'块: {block.name}')
    for entity in block:
        print(f'  {entity.dxftype()}')

msp = doc.modelspace()
print('\n=== 模型空间实体 ===')
for entity in msp:
    etype = entity.dxftype()
    if etype == 'INSERT':
        print(f'块引用: {entity.dxf.name}')
        print(f'  位置: ({entity.dxf.insert[0]:.1f}, {entity.dxf.insert[1]:.1f})')

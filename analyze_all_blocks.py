# -*- coding: utf-8 -*-
import ezdxf
doc = ezdxf.readfile('templates/病害图例/剥落、掉角.dxf')

# 查看所有包含 LWPOLYLINE 的块
for block in doc.blocks:
    has_polyline = False
    for entity in block:
        if entity.dxftype() == 'LWPOLYLINE':
            has_polyline = True
            break

    if has_polyline:
        print(f'\n=== 块 {block.name} (包含LWPOLYLINE) ===')
        for entity in block:
            if entity.dxftype() == 'LWPOLYLINE':
                pts = list(entity.get_points())
                print(f'LWPOLYLINE ({len(pts)} 点):')
                for p in pts[:10]:  # 只显示前10个点
                    print(f'  ({p[0]:.1f}, {p[1]:.1f})')
                if len(pts) > 10:
                    print(f'  ... (共{len(pts)}点)')

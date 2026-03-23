# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import ezdxf

doc = ezdxf.readfile('output_pages/上部病害_第1页.dxf')
msp = doc.modelspace()

# 查找病害图形的位置（LINE, LWPOLYLINE等）
print('=== 病害图形位置 ===')
for entity in msp:
    etype = entity.dxftype()
    if etype in ['LINE', 'LWPOLYLINE', 'SPLINE']:
        if etype == 'LINE':
            x1, y1 = entity.dxf.start[0], entity.dxf.start[1]
            x2, y2 = entity.dxf.end[0], entity.dxf.end[1]
            print(f'LINE: ({x1:.1f}, {y1:.1f}) -> ({x2:.1f}, {y2:.1f})')
        elif etype == 'LWPOLYLINE':
            pts = list(entity.get_points())
            if pts:
                min_x = min(p[0] for p in pts)
                max_x = max(p[0] for p in pts)
                min_y = min(p[1] for p in pts)
                max_y = max(p[1] for p in pts)
                if max_x - min_x > 10 or max_y - min_y > 10:  # 过滤小图形
                    print(f'LWPOLYLINE: 范围 X={min_x:.1f}-{max_x:.1f}, Y={min_y:.1f}-{max_y:.1f}')

# -*- coding: utf-8 -*-
import ezdxf
import sys

doc = ezdxf.readfile(r'K:/works/008.S2ReportAndLayoutPic/leftRealJobs_workbuddy/templates/构件/双柱墩12.5.dxf')
msp = doc.modelspace()

print('=== 双柱墩模板实体 ===')
for e in msp:
    if e.dxftype() in ['LINE', 'CIRCLE', 'ARC', 'TEXT', 'MTEXT', 'LWPOLYLINE']:
        if e.dxftype() == 'TEXT':
            print(f'TEXT: text="{e.dxf.text}" at ({e.dxf.insert[0]:.1f},{e.dxf.insert[1]:.1f})')
        elif e.dxftype() == 'MTEXT':
            t = e.text.replace('\n', ' ')[:60]
            print(f'MTEXT: "{t}"')
        elif e.dxftype() == 'LINE':
            s = e.dxf.start
            en = e.dxf.end
            print(f'LINE: ({s[0]:.1f},{s[1]:.1f}) -> ({en[0]:.1f},{en[1]:.1f})')
        elif e.dxftype() == 'LWPOLYLINE':
            pts = list(e.get_points())
            if pts:
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                print(f'LWPOLYLINE: {len(pts)} pts, bbox=({min(xs):.1f},{min(ys):.1f})~({max(xs):.1f},{max(ys):.1f})')

# -*- coding: utf-8 -*-
import ezdxf
import sys
sys.stdout.reconfigure(encoding='utf-8')

doc = ezdxf.readfile('output_pages/上部T梁第10页_5-3-5-4.dxf')
msp = doc.modelspace()

print('=== Page 10 TEXT entities ===')
for e in msp:
    if e.dxftype() == 'TEXT':
        txt = e.dxf.text
        pos = e.dxf.insert
        print(f'TEXT: {txt} at ({pos[0]:.1f}, {pos[1]:.1f})')
    elif e.dxftype() == 'MTEXT':
        txt = e.text[:30]
        pos = e.dxf.insert
        print(f'MTEXT: {txt} at ({pos[0]:.1f}, {pos[1]:.1f})')
    elif e.dxftype() == 'LWPOLYLINE':
        pts = list(e.vertices_in_wcs())
        if len(pts) == 3:  # leader line
            print(f'LEADER: ({pts[0][0]:.1f},{pts[0][1]:.1f}) -> ({pts[1][0]:.1f},{pts[1][1]:.1f}) -> ({pts[2][0]:.1f},{pts[2][1]:.1f})')
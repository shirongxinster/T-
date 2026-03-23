# -*- coding: utf-8 -*-
import ezdxf

# 读取第4页
doc = ezdxf.readfile(r'K:/works/008.S2ReportAndLayoutPic/leftRealJobs_workbuddy/output_pages/下部病害_第4页_v2.dxf')
msp = doc.modelspace()

print("=== 第4页中的LINE实体 ===")
for e in msp:
    if e.dxftype() == 'LINE':
        s = e.dxf.start
        en = e.dxf.end
        # 找在墩柱范围内的线
        if 68 <= s[0] <= 95 and 68 <= en[0] <= 95:
            print(f"LINE: ({s[0]:.1f},{s[1]:.1f}) -> ({en[0]:.1f},{en[1]:.1f})")
    elif e.dxftype() == 'CIRCLE':
        c = e.dxf.center
        if 68 <= c[0] <= 95 and 185 <= c[1] <= 230:
            print(f"CIRCLE: center=({c[0]:.1f},{c[1]:.1f}), r={e.dxf.radius:.1f}")
    elif e.dxftype() == 'LWPOLYLINE':
        pts = list(e.get_points())
        if pts:
            xs = [p[0] for p in pts]
            if 68 <= min(xs) <= 95:
                print(f"LWPOLYLINE: {len(pts)} pts, X range: {min(xs):.1f}~{max(xs):.1f}")

print("\n=== 找所有在x=60~100范围内的实体 ===")
for e in msp:
    if e.dxftype() == 'LINE':
        s = e.dxf.start
        en = e.dxf.end
        if (60 <= s[0] <= 100 or 60 <= en[0] <= 100):
            if e.dxf.color != 7:
                print(f"LINE(color={e.dxf.color}): ({s[0]:.1f},{s[1]:.1f}) -> ({en[0]:.1f},{en[1]:.1f})")

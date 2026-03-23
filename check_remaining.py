# 请在CAD中运行以下命令导出第6页的实体信息
# 然后把输出粘贴给我

import ezdxf

doc = ezdxf.readfile('k:/works/008.S2ReportAndLayoutPic/leftRealJobs_workbuddy/output_pages/上部病害_第6页.dxf')
msp = doc.modelspace()

# 检查矩形范围 (28, 203) 到 (503, 78) 内的所有实体
left, right, top, bottom = 28, 503, 203, 78

print("=" * 60)
print("矩形范围 (28,203) 到 (503,78) 内的所有实体:")
print("=" * 60)

for entity in msp:
    dxftype = entity.dxftype()

    # 获取实体的几何信息
    info = ""
    try:
        if dxftype == 'LINE':
            start = entity.dxf.start
            end = entity.dxf.end
            info = f"LINE: ({start[0]:.1f},{start[1]:.1f}) -> ({end[0]:.1f},{end[1]:.1f})"
        elif dxftype == 'TEXT':
            insert = entity.dxf.insert
            info = f"TEXT at ({insert[0]:.1f},{insert[1]:.1f}): '{entity.dxf.text}'"
        elif dxftype == 'MTEXT':
            insert = entity.dxf.insert
            info = f"MTEXT at ({insert[0]:.1f},{insert[1]:.1f}): '{entity.text}'"
        elif dxftype == 'LWPOLYLINE':
            pts = list(entity.get_points())
            info = f"LWPOLYLINE with {len(pts)} points"
        elif dxftype == 'CIRCLE':
            center = entity.dxf.center
            info = f"CIRCLE center=({center[0]:.1f},{center[1]:.1f})"
        elif dxftype == 'ARC':
            center = entity.dxf.center
            info = f"ARC center=({center[0]:.1f},{center[1]:.1f})"
        elif dxftype == 'POINT':
            loc = entity.dxf.location
            info = f"POINT at ({loc[0]:.1f},{loc[1]:.1f})"
        elif dxftype == 'HATCH':
            info = f"HATCH"
        elif dxftype == 'SPLINE':
            info = f"SPLINE"
        elif dxftype == 'INSERT':
            insert = entity.dxf.insert
            info = f"INSERT: name={entity.dxf.name} at ({insert[0]:.1f},{insert[1]:.1f})"
        else:
            info = f"{dxftype}"

        # 检查是否在矩形范围内（粗略检查）
        in_range = False
        if dxftype == 'LINE':
            if (min(start[0], end[0]) <= right and max(start[0], end[0]) >= left and
                min(start[1], end[1]) <= top and max(start[1], end[1]) >= bottom):
                in_range = True
        elif dxftype in ('TEXT', 'MTEXT', 'POINT', 'CIRCLE', 'ARC', 'INSERT'):
            insert = entity.dxf.insert if dxftype != 'POINT' else entity.dxf.location
            if dxftype in ('CIRCLE', 'ARC'):
                insert = entity.dxf.center
            x, y = insert[0], insert[1]
            if left <= x <= right and bottom <= y <= top:
                in_range = True

        if info:
            print(f"  {dxftype}: {info} {'<-- 在范围内' if in_range else ''}")

    except Exception as e:
        print(f"  {dxftype}: ERROR - {e}")

print("\n" + "=" * 60)
print("分析完成")

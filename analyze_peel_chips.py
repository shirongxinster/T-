"""
分析掉角和剥落的具体图形
"""
import ezdxf

doc = ezdxf.readfile('templates/病害图例/剥落、掉角.dxf')
msp = doc.modelspace()

# 找到块引用的位置
print("=== 块引用位置 ===")
for entity in msp:
    if entity.dxftype() == 'INSERT':
        print(f"块: {entity.dxf.name}, 位置: ({entity.dxf.insert[0]:.2f}, {entity.dxf.insert[1]:.2f}), 缩放: {entity.dxf.xscale}")

# 分析88888块（掉角）
print("\n=== 88888块（掉角）详细分析 ===")
block = doc.blocks.get('88888')
for entity in block:
    if entity.dxftype() == 'LINE':
        print(f"LINE: ({entity.dxf.start[0]:.2f},{entity.dxf.start[1]:.2f}) -> ({entity.dxf.end[0]:.2f},{entity.dxf.end[1]:.2f})")
    elif entity.dxftype() == 'TEXT':
        print(f"TEXT: '{entity.dxf.text}' at ({entity.dxf.insert[0]:.2f},{entity.dxf.insert[1]:.2f})")

# 分析A$C1BE858FD块（剥落边缘）
print("\n=== A$C1BE858FD块（剥落边缘）详细分析 ===")
block = doc.blocks.get('A$C1BE858FD')
lines = []
for entity in block:
    if entity.dxftype() == 'LINE':
        lines.append((entity.dxf.start, entity.dxf.end))
        print(f"LINE: ({entity.dxf.start[0]:.2f},{entity.dxf.start[1]:.2f}) -> ({entity.dxf.end[0]:.2f},{entity.dxf.end[1]:.2f})")

# 分析A$C04EE150E块（剥落多边形）
print("\n=== A$C04EE150E块（剥落多边形）详细分析 ===")
block = doc.blocks.get('A$C04EE150E')
for entity in block:
    if entity.dxftype() == 'LINE':
        print(f"LINE: ({entity.dxf.start[0]:.2f},{entity.dxf.start[1]:.2f}) -> ({entity.dxf.end[0]:.2f},{entity.dxf.end[1]:.2f})")
    elif entity.dxftype() == 'LWPOLYLINE':
        pts = list(entity.get_points())
        print(f"LWPOLYLINE: {len(pts)}点")
        for pt in pts:
            print(f"  ({pt[0]:.2f},{pt[1]:.2f})")

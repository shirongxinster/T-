"""
详细分析剥落、掉角.dxf文件的完整结构
"""
import ezdxf

doc = ezdxf.readfile('templates/病害图例/剥落、掉角.dxf')
msp = doc.modelspace()

print("=" * 60)
print("模型空间中的实体")
print("=" * 60)

for i, entity in enumerate(msp):
    etype = entity.dxftype()
    print(f"\n实体 {i+1}: {etype}")

    if etype == 'INSERT':
        print(f"  块名: {entity.dxf.name}")
        print(f"  位置: ({entity.dxf.insert[0]:.2f}, {entity.dxf.insert[1]:.2f})")
        print(f"  X缩放: {entity.dxf.xscale}")
        print(f"  Y缩放: {entity.dxf.yscale}")
        print(f"  旋转: {entity.dxf.rotation}")

    elif etype == 'LINE':
        print(f"  起点: ({entity.dxf.start[0]:.2f}, {entity.dxf.start[1]:.2f})")
        print(f"  终点: ({entity.dxf.end[0]:.2f}, {entity.dxf.end[1]:.2f})")
        print(f"  颜色: {entity.dxf.color}")

    elif etype == 'LWPOLYLINE':
        pts = list(entity.get_points())
        print(f"  点数: {len(pts)}")
        for j, pt in enumerate(pts):
            print(f"    点{j}: ({pt[0]:.2f}, {pt[1]:.2f})")
        print(f"  颜色: {entity.dxf.color}")

    elif etype == 'MTEXT':
        print(f"  内容: {entity.text}")
        print(f"  插入点: ({entity.dxf.insert[0]:.2f}, {entity.dxf.insert[1]:.2f})")

    elif etype == 'TEXT':
        print(f"  内容: {entity.dxf.text}")
        print(f"  位置: ({entity.dxf.insert[0]:.2f}, {entity.dxf.insert[1]:.2f})")

    elif etype == 'SPLINE':
        print(f"  控制点数: {len(entity.control_points)}")
        for cp in entity.control_points[:5]:
            print(f"    ({cp[0]:.2f}, {cp[1]:.2f})")

print("\n" + "=" * 60)
print("所有块定义")
print("=" * 60)

for block in doc.blocks:
    block_name = block.name
    if block_name.startswith('*') or block_name == 'MODEL_SPACE' or block_name == 'PAPER_SPACE':
        continue
    print(f"\n块: {block_name}")
    block = doc.blocks.get(block_name)
    for j, entity in enumerate(block):
        etype = entity.dxftype()
        print(f"  实体{j+1}: {etype}", end='')

        if etype == 'LINE':
            print(f"  ({entity.dxf.start[0]:.2f},{entity.dxf.start[1]:.2f}) -> ({entity.dxf.end[0]:.2f},{entity.dxf.end[1]:.2f})")
        elif etype == 'LWPOLYLINE':
            pts = list(entity.get_points())
            print(f"  {len(pts)}点")
            for pt in pts[:6]:
                print(f"    ({pt[0]:.2f},{pt[1]:.2f})")
        elif etype == 'SPLINE':
            print(f"  控制点数: {len(entity.control_points)}")
        else:
            print()

import ezdxf

doc = ezdxf.readfile('output_pages/上部T梁第6页_3-5-4-1.dxf')
msp = doc.modelspace()

# 找所有y<130的引线
print('=== 找y<130的引线 ===')
for entity in msp:
    if entity.dxftype() == 'LWPOLYLINE':
        points = list(entity.get_points())
        if len(points) >= 2:
            ys = [p[1] for p in points]
            if max(ys) < 130:
                start = points[0]
                print(f'起点: ({start[0]:.2f}, {start[1]:.2f}), 终点: ({points[-1][0]:.2f}, {points[-1][1]:.2f})')

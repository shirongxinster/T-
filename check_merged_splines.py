# -*- coding: utf-8 -*-
import ezdxf
from ezdxf.bbox import extents

# 读取合并文件
merged_doc = ezdxf.readfile('LK572+774红石牡丹江大桥（右幅）下部病害.dxf')
merged_msp = merged_doc.modelspace()

# 收集所有SPLINE
splines = []
for entity in merged_msp:
    if entity.dxftype() == 'SPLINE':
        splines.append(entity)

print(f'合并文件总SPLINE数量: {len(splines)}')

# 检查每个SPLINE的坐标范围
for i, spline in enumerate(splines[:10]):  # 只看前10个
    try:
        bbox = extents([spline])
        print(f'SPLINE {i+1}:')
        print(f'  Control points: {len(spline.control_points)}')
        print(f'  X range: {bbox.extmin[0]:.1f} to {bbox.extmax[0]:.1f}')
        print(f'  Y range: {bbox.extmin[1]:.1f} to {bbox.extmax[1]:.1f}')
        if spline.control_points:
            print(f'  First control point: {spline.control_points[0]}')
    except Exception as e:
        print(f'SPLINE {i+1}: Error getting bbox: {e}')

# 检查是否有SPLINE在合理的图例位置（X约460左右，Y在各页区域）
print('\n检查图例区域的SPLINE（X在450-480之间）:')
legend_splines = []
for spline in splines:
    try:
        bbox = extents([spline])
        if 450 <= bbox.extmin[0] <= 480 and 450 <= bbox.extmax[0] <= 500:
            legend_splines.append(spline)
    except:
        pass

print(f'在图例区域找到的SPLINE数量: {len(legend_splines)}')

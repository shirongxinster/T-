# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'K:/works/008.S2ReportAndLayoutPic/leftRealJobs_workbuddy')
from bridge_disease_parser import parse_excel

xls_file = r'K:/works/008.S2ReportAndLayoutPic/leftRealJobs_workbuddy/K572+774红石牡丹江大桥（右幅）病害.xls'
data = parse_excel(xls_file)

# 找出墩柱相关病害
print('=== 墩柱病害 ===')
for record in data:
    location = record.get('缺损位置', '')
    if '墩柱' in location:
        print(f"构件编号: {record.get('构件编号', '')}")
        print(f"  墩柱号: {record.get('墩柱号', '')}")
        print(f"  柱内编号: {record.get('柱内编号', '')}")
        print(f"  病害类型: {record.get('病害类型', '')}")
        print(f"  x: {record.get('x_start', 0)}~{record.get('x_end', 0)}m")
        print(f"  y: {record.get('y_start', 0)}~{record.get('y_end', 0)}m")
        print(f"  面积: {record.get('area', 0)}")
        print()

# 测试坐标计算
print('\n=== 墩柱坐标计算验证 ===')
for record in data:
    location = record.get('缺损位置', '')
    if '墩柱' in location:
        x_start = record.get('x_start', 0)
        x_end = record.get('x_end', 0)
        y_start = record.get('y_start', 0)
        y_end = record.get('y_end', 0)

        pier_x1, pier_y1, pier_x2, pier_y2 = 70, 224, 91, 190
        pier_height, pier_width = 2.0, 0.5

        disease_y1 = pier_y1 - (x_start / pier_height) * (pier_y1 - pier_y2)
        disease_y2 = pier_y1 - (x_end / pier_height) * (pier_y1 - pier_y2)
        disease_x1 = pier_x1 + (y_start / pier_width) * (pier_x2 - pier_x1)
        disease_x2 = pier_x1 + (y_end / pier_width) * (pier_x2 - pier_x1)

        print(f"病害坐标: x={x_start}~{x_end}m, y={y_start}~{y_end}m")
        print(f"CAD区域: ({disease_x1:.1f},{disease_y1:.1f}) ~ ({disease_x2:.1f},{disease_y2:.1f})")

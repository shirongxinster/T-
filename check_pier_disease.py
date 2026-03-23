# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'K:/works/008.S2ReportAndLayoutPic/leftRealJobs_workbuddy')
from bridge_disease_parser import parse_excel

xls_file = r'K:/works/008.S2ReportAndLayoutPic/leftRealJobs_workbuddy/K572+774桥梁定期检查（外业记录表）表格.xls'
data = parse_excel(xls_file)

# 找出墩柱相关病害
print('=== 墩柱病害 ===')
for record in data:
    location = record.get('缺损位置', '')
    if '墩柱' in location:
        print(f"构件: {record.get('构件编号', '')}")
        print(f"  位置: {location}")
        print(f"  病害: {record.get('病害', '')}")
        print(f"  病害类型: {record.get('病害类型', '')}")
        print(f"  x: {record.get('x_start', 0)}~{record.get('x_end', 0)}m")
        print(f"  y: {record.get('y_start', 0)}~{record.get('y_end', 0)}m")
        print(f"  面积: {record.get('area', 0)}")
        print(f"  墩柱号: {record.get('墩柱号', '')}")
        print(f"  柱内编号: {record.get('柱内编号', '')}")
        print()

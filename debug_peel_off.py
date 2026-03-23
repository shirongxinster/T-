# -*- coding: utf-8 -*-
"""调试剥落绘制"""
from bridge_disease_parser import parse_excel

data = parse_excel('K572+774红石牡丹江大桥（右幅）病害.xls')

# 获取所有剥落病害
print("=== 所有剥落病害 ===")
for part in data['parts']:
    if '上部' in part['name']:
        for comp_id, records in part['grouped_data'].items():
            for r in records:
                disease_type = r.get('病害类型', '')
                if '剥落' in disease_type:
                    print(f"构件: {comp_id}")
                    print(f"  类型: {disease_type}")
                    print(f"  部件: {r.get('具体部件')}")
                    print(f"  x: {r.get('x_start')} - {r.get('x_end')}")
                    print(f"  y: {r.get('y_start')} - {r.get('y_end')}")
                    print(f"  area: {r.get('area')}")
                    print()

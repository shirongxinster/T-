# -*- coding: utf-8 -*-
"""打印下部病害数据"""

import sys
sys.path.insert(0, '.')
from bridge_disease_parser import parse_excel

excel_path = 'K572+774红石牡丹江大桥（右幅）病害.xls'
data = parse_excel(excel_path)

print('='*60)
print(f'路线名称: {data["route_name"]}')
print(f'桥梁名称: {data["bridge_name"]}')
print('='*60)

# 打印各构件类型
for part in data['parts']:
    section = part['section']
    if section == '下部':
        print(f'\n【{part["name"]}】')
        print(f'  模板: {part["template_name"]}')
        
        for comp_id, diseases in part['grouped_data'].items():
            print(f'\n  构件: {comp_id}')
            for d in diseases:
                print(f'    - 位置: {d["缺损位置"]}')
                print(f'      病害: {d["病害"]}')
                print(f'      部件: {d["具体部件"]}')
                print(f'      墩柱号: {d["墩柱号"]}, 柱内编号: {d["柱内编号"]}, 盖梁号: {d["盖梁号"]}')
                if d['x_start'] != 0 or d['x_end'] != 0:
                    print(f'      X: {d["x_start"]} ~ {d["x_end"]}')
                if d['y_start'] != 0 or d['y_end'] != 0:
                    print(f'      Y: {d["y_start"]} ~ {d["y_end"]}')
                if d.get('length'):
                    print(f'      长度: {d["length"]}')
                if d.get('area'):
                    print(f'      面积: {d["area"]}')

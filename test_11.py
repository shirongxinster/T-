import os
import sys
sys.path.insert(0, '.')
from bridge_disease_main_upper import create_page_for_pair
from bridge_disease_parser import parse_excel

excel_path = 'K572+774红石牡丹江大桥（右幅）病害.xls'
data = parse_excel(excel_path)

# 筛选6-1和6-3号
upper_diseases = {}
for part in data['parts']:
    if '上部' in part['name']:
        for comp_id, records in part['grouped_data'].items():
            if comp_id in ['6-1号', '6-3号']:
                upper_diseases[comp_id] = records

print("6-1和6-3号病害数据:")
for k, v in upper_diseases.items():
    print(f"  {k}: {v}")

template_path = './templates/上部T梁第11页.dxf'
output = create_page_for_pair(template_path, ['6-1号', '6-3号'], upper_diseases, 
                               route_name=data['route_name'], bridge_name=data['bridge_name'], page_index=11)
print(f"\n输出: {output}")
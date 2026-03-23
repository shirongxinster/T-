# -*- coding: utf-8 -*-
from bridge_disease_parser import parse_excel

data = parse_excel('K572+774红石牡丹江大桥（右幅）病害.xls')

# 获取上部病害
upper_diseases = {}
for part in data['parts']:
    if '上部' in part['name']:
        for comp_id, records in part['grouped_data'].items():
            upper_diseases[comp_id] = records

# 检查第一个构件的病害数据
for comp_id, records in list(upper_diseases.items())[:2]:
    print(f'\n=== {comp_id} ===')
    for r in records[:3]:  # 只看前3条
        print(f'  病害类型: {r.get("病害类型")}')
        print(f'  具体部件: {r.get("具体部件")}')
        print(f'  x范围: {r.get("x_start")}-{r.get("x_end")}')
        print(f'  y范围: {r.get("y_start")}-{r.get("y_end")}')
        print(f'  length: {r.get("length")}, width: {r.get("width")}, area: {r.get("area")}, count: {r.get("count")}')
        print()

# -*- coding: utf-8 -*-
from bridge_disease_parser import parse_excel
import os

excel_path = 'K572+774红石牡丹江大桥（右幅）病害.xls'
if os.path.exists(excel_path):
    data = parse_excel(excel_path)

    # 遍历所有parts
    for part in data.get('parts', []):
        part_name = part.get('name', '')
        print(f"\n=== {part_name} ===")
        grouped = part.get('grouped_data', {})

        # 查找2号盖梁
        for comp_id, diseases in grouped.items():
            if '2号' in comp_id and ('盖梁' in str(diseases) or '墩' in str(diseases)):
                print(f"\n构件: {comp_id}")
                for d in diseases:
                    print(f"  缺损位置: {d.get('缺损位置', '')}")
                    print(f"  具体部件: {d.get('具体部件', '')}")
                    print(f"  病害描述: {d.get('病害', '')}")
                    print(f"  x: {d.get('x_start', 0)} ~ {d.get('x_end', 0)}")
                    print(f"  y: {d.get('y_start', 0)} ~ {d.get('y_end', 0)}")
                    print()

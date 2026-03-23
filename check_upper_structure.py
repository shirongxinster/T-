# -*- coding: utf-8 -*-
"""查看Excel数据"""

from bridge_disease_parser import parse_excel

data = parse_excel('K572+774红石牡丹江大桥（右幅）病害.xls')
print(f'路线名称: {data["route_name"]}')
print(f'桥梁名称: {data["bridge_name"]}')

print('\n=== 按模板分组 ===')
for template_name, template_data in data.get('templates', {}).items():
    print(f'\n模板文件: {template_name}')
    for td in template_data:
        print(f'  构件类型: {td["part_name"]}')
        print(f'  构件列表: {list(td["components"].keys())}')

# 专门看上部（40mT梁）
print('\n=== 上部（40mT梁）详情 ===')
for part in data['parts']:
    if '上部' in part['name']:
        print(f"\n构件类型: {part['name']}")
        for comp_id, records in part['grouped_data'].items():
            print(f"  构件 {comp_id}: {len(records)} 条病害")
            for r in records:
                print(f"    - 序号{r['序号']}: {r['病害']}")

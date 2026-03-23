# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from bridge_disease_parser import parse_excel

# 导入判断函数
import sys
sys.path.insert(0, '.')
from bridge_disease_main_upper import get_beam_side_from_part

data = parse_excel('K572+774红石牡丹江大桥（右幅）病害.xls')

# 获取1-1号和1-2号的病害
for part in data['parts']:
    if '上部' in part['name']:
        for comp_id, records in part['grouped_data'].items():
            if comp_id in ['1-1号', '1-2号']:
                print(f'=== {comp_id} ===')
                for r in records:
                    disease = r.get('病害类型', '')
                    part_name = r.get('具体部件', '')
                    x_start = r.get('x_start', 0)

                    beam_side = get_beam_side_from_part(part_name, x_start)

                    print(f'{disease} at {part_name} (x_start={x_start})')
                    print(f'  -> {beam_side}')
                    print()

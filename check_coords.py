# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from bridge_disease_parser import parse_excel

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
                    x1 = r.get('x_start', 0)
                    x2 = r.get('x_end', 0)
                    y1 = r.get('y_start', 0)
                    y2 = r.get('y_end', 0)

                    print(f'{disease} at {part_name}')
                    print(f'  x: {x1} - {x2} m')

                    # 根据具体部件判断应该在哪个T梁
                    # 左翼缘板、马蹄左侧面 -> 左侧T梁
                    # 右翼缘板、马蹄右侧面 -> 右侧T梁
                    # 梁底 -> 根据x坐标判断
                    if '左翼' in part_name or '马蹄左' in part_name:
                        expected_beam = '左侧T梁 (a-a)'
                    elif '右翼' in part_name or '马蹄右' in part_name:
                        expected_beam = '右侧T梁 (b-b)'
                    elif '梁底' in part_name:
                        # 梁底根据x坐标判断
                        mid_x = (x1 + x2) / 2
                        if mid_x < 20:
                            expected_beam = '左侧T梁 (a-a)'
                        else:
                            expected_beam = '右侧T梁 (b-b)'
                    else:
                        expected_beam = '未知'

                    print(f'  预期: {expected_beam}')
                    print()

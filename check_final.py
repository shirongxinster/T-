# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import ezdxf

doc = ezdxf.readfile('output_pages/上部病害_第1页.dxf')
msp = doc.modelspace()

# 收集所有病害和横断面信息
sections = {}  # 存储横断面标注
diseases = []  # 存储病害

for entity in msp:
    if entity.dxftype() == 'MTEXT':
        text = entity.text
        x, y = entity.dxf.insert[0], entity.dxf.insert[1]
        # 横断面标注
        if '1-1号' in text:
            sections['1-1号'] = (x, y)
        elif '1-2号' in text:
            sections['1-2号'] = (x, y)
    elif entity.dxftype() == 'TEXT':
        text = entity.dxf.text
        x, y = entity.dxf.insert[0], entity.dxf.insert[1]
        # 病害标注
        if any(k in text for k in ['裂缝', '剥落', '网状', '露筋']):
            diseases.append((text, x, y))

print('=== 横断面标注位置 ===')
for comp, (x, y) in sections.items():
    print(f'{comp}: ({x:.1f}, {y:.1f})')

print('')
print('=== 病害位置 ===')
for text, x, y in diseases:
    print(f'{text}: ({x:.1f}, {y:.1f})')

print('')
print('=== 分析 ===')
# 根据横断面x位置判断病害属于哪个T梁
# 左侧T梁（a-a）：x约58
# 右侧T梁（b-b）：x约57

for text, x, y in diseases:
    # 病害x坐标在80-150范围的属于左侧T梁区域
    # 病害x坐标在200+范围的属于右侧T梁区域
    if x < 200:
        region = '左侧T梁 (a-a)'
    else:
        region = '右侧T梁 (b-b)'
    print(f'{text}: {region}')

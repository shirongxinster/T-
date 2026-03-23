# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import ezdxf

doc = ezdxf.readfile('output_pages/上部病害_第1页.dxf')
msp = doc.modelspace()

# 查找所有文字
print('=== 所有文字 ===')
for entity in msp:
    if entity.dxftype() == 'TEXT':
        text = entity.dxf.text
        x, y = entity.dxf.insert[0], entity.dxf.insert[1]
        print(f'TEXT: "{text}" at ({x:.1f}, {y:.1f})')
    elif entity.dxftype() == 'MTEXT':
        text = entity.text
        x, y = entity.dxf.insert[0], entity.dxf.insert[1]
        print(f'MTEXT: "{text}" at ({x:.1f}, {y:.1f})')

print('')
print('=== 病害分类 ===')

# 根据模板:
# - b-b断面在下方，y约213
# - a-a断面在上方，y约314

disease_y_values = []
for entity in msp:
    if entity.dxftype() == 'TEXT':
        text = entity.dxf.text
        if any(k in text for k in ['裂缝', '剥落', '网状', '露筋', 'S=', 'L=', 'W=']):
            y = entity.dxf.insert[1]
            disease_y_values.append((text, y))

disease_y_values.sort(key=lambda x: x[1], reverse=True)

print('病害按Y坐标排序（从上到下）:')
for text, y in disease_y_values:
    region = '上方(b-b)' if y < 270 else '下方(a-a)'
    print(f'  [{region}] y={y:.1f}: {text}')

# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import ezdxf

doc = ezdxf.readfile('output_pages/上部病害_第1页.dxf')
msp = doc.modelspace()

# 查找横断面标注
print('=== 横断面标注 ===')
for entity in msp:
    if entity.dxftype() == 'TEXT':
        text = entity.dxf.text
        if 'a-a' in text or 'b-b' in text:
            print(f'{text}: y={entity.dxf.insert[1]:.1f}')

print('')
print('=== 病害位置分析 ===')

# 上方T梁区域: CAD Y > 250
# 下方T梁区域: CAD Y <= 250

upper = []
lower = []

for entity in msp:
    if entity.dxftype() == 'TEXT':
        text = entity.dxf.text
        if any(k in text for k in ['裂缝', '剥落', '网状', '露筋']):
            y = entity.dxf.insert[1]
            if y > 250:
                upper.append(text)
            else:
                lower.append(text)

print(f'上方T梁 (b-b, y>250): {len(upper)//2} 条病害')
for t in upper:
    print(f'  {t}')

print(f'下方T梁 (a-a, y<=250): {len(lower)//2} 条病害')
for t in lower:
    print(f'  {t}')

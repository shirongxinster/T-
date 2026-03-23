# -*- coding: utf-8 -*-
"""验证病害图形是否被绘制"""
import ezdxf

doc = ezdxf.readfile('output_pages/上部病害_第1页.dxf')
msp = doc.modelspace()

# 统计各类型实体
entity_counts = {}
text_entities = []
lwpolylines = []

for entity in msp:
    etype = entity.dxftype()
    entity_counts[etype] = entity_counts.get(etype, 0) + 1

    if etype == 'TEXT' or etype == 'MTEXT':
        text = entity.text if etype == 'MTEXT' else entity.dxf.text
        text_entities.append((etype, text[:50] if len(text) > 50 else text))
    elif etype == 'LWPOLYLINE':
        if hasattr(entity, 'get_points'):
            pts = list(entity.get_points())
            lwpolylines.append(len(pts))

print("=== 实体统计 ===")
for etype, count in sorted(entity_counts.items()):
    print(f"  {etype}: {count}")

print(f"\n=== 文字实体 (前10个) ===")
for etype, text in text_entities[:10]:
    print(f"  [{etype}] {text}")

print(f"\n=== LWPOLYLINE 数量统计 ===")
print(f"  总数: {len(lwpolylines)}")
if lwpolylines:
    print(f"  点数分布: min={min(lwpolylines)}, max={max(lwpolylines)}, avg={sum(lwpolylines)/len(lwpolylines):.1f}")

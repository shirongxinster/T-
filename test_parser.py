# -*- coding: utf-8 -*-
from bridge_disease_parser import parse_disease_position

tests = [
    '梁底，x=10～14m，y=0.5m，纵向裂缝 L=4.00m，W=0.10mm',
    '梁底，x=15～30m，y=0～0.6m，网状裂缝 S=9.00m2',
]

for t in tests:
    r = parse_disease_position(t)
    print(f"Input: {t}")
    print(f"  x_start={r['x_start']}  x_end={r['x_end']}")
    print(f"  y_start={r['y_start']}  y_end={r['y_end']}")
    print(f"  disease_type={r['disease_type']}")
    print()

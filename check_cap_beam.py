# -*- coding: utf-8 -*-
import ezdxf
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

output_file = 'output_pages/下部第2页_盖梁2.dxf'
if os.path.exists(output_file):
    doc = ezdxf.readfile(output_file)
    msp = doc.modelspace()

    print("检查2号盖梁文件中的实体:")
    for entity in msp:
        if entity.dxftype() in ('TEXT', 'MTEXT'):
            text = entity.text if entity.dxftype() == 'MTEXT' else entity.dxf.text
            if 'S=' in text or '0.72' in text or '0.49' in text:
                print(f"类型: {entity.dxftype()}")
                print(f"文字: {text}")
                if entity.dxftype() == 'MTEXT':
                    print(f"位置: {entity.dxf.insert}")
                else:
                    print(f"位置: {entity.dxf.insert}")
                print()

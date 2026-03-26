# -*- coding: utf-8 -*-
import ezdxf
import os

output_file = 'output_pages/下部第1页_盖梁1.dxf'
if os.path.exists(output_file):
    doc = ezdxf.readfile(output_file)
    msp = doc.modelspace()
    for entity in msp:
        if entity.dxftype() in ('TEXT', 'MTEXT'):
            text = entity.text if entity.dxftype() == 'MTEXT' else entity.dxf.text
            if 'K572' in text:
                print('类型:', entity.dxftype())
                print('文本:', repr(text))
                print('长度:', len(text))
                if entity.dxftype() == 'MTEXT':
                    print('包含换行符 (P):', '\\P' in text)
                break

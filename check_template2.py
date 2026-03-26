# -*- coding: utf-8 -*-
import ezdxf

doc = ezdxf.readfile('templates/构件/双柱墩12.5.dxf')
msp = doc.modelspace()
for entity in msp:
    if entity.dxftype() in ('TEXT', 'MTEXT'):
        text = entity.text if entity.dxftype() == 'MTEXT' else entity.dxf.text
        if 'K572' in text or 'QQQ' in text:
            print('类型:', entity.dxftype())
            print('文本:', repr(text))
            if entity.dxftype() == 'MTEXT':
                print('包含换行符 (P):', '\\P' in text)
            break

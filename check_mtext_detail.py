# -*- coding: utf-8 -*-
import ezdxf
import os

output_file = 'output_pages/下部第1页_盖梁1.dxf'
if os.path.exists(output_file):
    doc = ezdxf.readfile(output_file)
    msp = doc.modelspace()
    for entity in msp:
        if entity.dxftype() == 'MTEXT':
            text = entity.text
            if 'K572' in text:
                print('MTEXT实体属性:')
                print('  text:', repr(text))
                print('  char_height:', entity.dxf.char_height if hasattr(entity.dxf, 'char_height') else 'N/A')
                print('  attachment_point:', entity.dxf.attachment_point if hasattr(entity.dxf, 'attachment_point') else 'N/A')
                print('  line_spacing_factor:', entity.dxf.line_spacing_factor if hasattr(entity.dxf, 'line_spacing_factor') else 'N/A')

                # 检查换行符
                print('  包含 \\P:', '\\P' in text)
                print('  包含 \\p:', '\\p' in text)
                print('  包含 \\n:', '\\n' in text)
                break

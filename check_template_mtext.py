# -*- coding: utf-8 -*-
import ezdxf

# 读取模板文件
template_doc = ezdxf.readfile('templates/构件/双柱墩12.5.dxf')
template_msp = template_doc.modelspace()

print("模板文件中的桥梁名称MTEXT:")
for entity in template_msp:
    if entity.dxftype() == 'MTEXT':
        text = entity.text
        if 'QQQ' in text or 'LLL' in text:
            print(f"  Raw text: {repr(text)}")
            print(f"  Has \\P (new line): {'\\P' in text}")
            print(f"  dxf properties:")
            if hasattr(entity.dxf, 'char_height'):
                print(f"    char_height: {entity.dxf.char_height}")
            if hasattr(entity.dxf, 'rect_width'):
                print(f"    rect_width: {entity.dxf.rect_width}")
            if hasattr(entity.dxf, 'attachment_point'):
                print(f"    attachment_point: {entity.dxf.attachment_point}")

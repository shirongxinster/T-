# -*- coding: utf-8 -*-
import ezdxf

# 读取模板文件
template_doc = ezdxf.readfile('templates/构件/双柱墩12.5.dxf')
template_msp = template_doc.modelspace()

print("模板文件中的MTEXT属性:")
for entity in template_msp:
    if entity.dxftype() == 'MTEXT':
        text = entity.text
        if 'QQQ' in text or 'LLL' in text:
            print(f"  Text: {repr(text)}")
            print(f"  Insert: {entity.dxf.insert}")
            if hasattr(entity.dxf, 'char_height'):
                print(f"  char_height: {entity.dxf.char_height}")
            if hasattr(entity.dxf, 'rect_width'):
                print(f"  rect_width: {entity.dxf.rect_width}")
            else:
                print(f"  rect_width: None (attribute not present)")
            if hasattr(entity.dxf, 'attachment_point'):
                print(f"  attachment_point: {entity.dxf.attachment_point}")
            if hasattr(entity.dxf, 'line_spacing_factor'):
                print(f"  line_spacing_factor: {entity.dxf.line_spacing_factor}")
            if hasattr(entity.dxf, 'line_spacing_style'):
                print(f"  line_spacing_factor: {entity.dxf.line_spacing_style}")

# 读取单个文件
single_doc = ezdxf.readfile('output_pages/下部第1页_盖梁1.dxf')
single_msp = single_doc.modelspace()

print("\n单个文件中的MTEXT属性:")
for entity in single_msp:
    if entity.dxftype() == 'MTEXT':
        text = entity.text
        if '红石牡丹江' in text:
            print(f"  Text: {repr(text)}")
            print(f"  Insert: {entity.dxf.insert}")
            if hasattr(entity.dxf, 'char_height'):
                print(f"  char_height: {entity.dxf.char_height}")
            if hasattr(entity.dxf, 'rect_width'):
                print(f"  rect_width: {entity.dxf.rect_width}")
            else:
                print(f"  rect_width: None (attribute not present)")

# 读取合并文件
merged_doc = ezdxf.readfile('LK572+774红石牡丹江大桥（右幅）下部病害.dxf')
merged_msp = merged_doc.modelspace()

print("\n合并文件中的MTEXT属性:")
for entity in merged_msp:
    if entity.dxftype() == 'MTEXT':
        text = entity.text
        if '红石牡丹江' in text:
            print(f"  Text: {repr(text)}")
            print(f"  Insert: {entity.dxf.insert}")
            if hasattr(entity.dxf, 'char_height'):
                print(f"  char_height: {entity.dxf.char_height}")
            if hasattr(entity.dxf, 'rect_width'):
                print(f"  rect_width: {entity.dxf.rect_width}")
            else:
                print(f"  rect_width: None (attribute not present)")

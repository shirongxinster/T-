# -*- coding: utf-8 -*-
import ezdxf

# 读取下部第6页文件
single_doc = ezdxf.readfile('output_pages/下部第6页_盖梁6.dxf')
single_msp = single_doc.modelspace()

print("下部第6页_盖梁6.dxf 中的桥梁名称MTEXT:")
for entity in single_msp:
    if entity.dxftype() == 'MTEXT':
        text = entity.text
        if '红石牡丹江' in text or 'QQQ' in text or 'LLL' in text:
            print(f"\n  Text: {repr(text)}")
            print(f"  Insert: {entity.dxf.insert}")
            if hasattr(entity.dxf, 'char_height'):
                print(f"  char_height: {entity.dxf.char_height}")
            if hasattr(entity.dxf, 'rect_width'):
                print(f"  rect_width: {entity.dxf.rect_width}")
            else:
                print(f"  rect_width: None (not present)")
            if hasattr(entity.dxf, 'attachment_point'):
                print(f"  attachment_point: {entity.dxf.attachment_point}")
            if hasattr(entity.dxf, 'line_spacing_factor'):
                print(f"  line_spacing_factor: {entity.dxf.line_spacing_factor}")

# 读取合并文件
merged_doc = ezdxf.readfile('LK572+774红石牡丹江大桥（右幅）下部病害.dxf')
merged_msp = merged_doc.modelspace()

print("\n\n合并文件 LK572+774红石牡丹江大桥（右幅）下部病害.dxf 中的桥梁名称MTEXT:")
for entity in merged_msp:
    if entity.dxftype() == 'MTEXT':
        text = entity.text
        if '红石牡丹江' in text or 'QQQ' in text or 'LLL' in text:
            print(f"\n  Text: {repr(text)}")
            print(f"  Insert: {entity.dxf.insert}")
            if hasattr(entity.dxf, 'char_height'):
                print(f"  char_height: {entity.dxf.char_height}")
            if hasattr(entity.dxf, 'rect_width'):
                print(f"  rect_width: {entity.dxf.rect_width}")
            else:
                print(f"  rect_width: None (not present)")
            if hasattr(entity.dxf, 'attachment_point'):
                print(f"  attachment_point: {entity.dxf.attachment_point}")

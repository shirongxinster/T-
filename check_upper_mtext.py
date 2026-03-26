# -*- coding: utf-8 -*-
import ezdxf
import os

# 检查上部模板
upper_template = 'templates/构件/上部T梁.dxf'
if os.path.exists(upper_template):
    template_doc = ezdxf.readfile(upper_template)
    template_msp = template_doc.modelspace()

    print("上部模板文件中的桥梁名称MTEXT:")
    for entity in template_msp:
        if entity.dxftype() == 'MTEXT':
            text = entity.text
            if 'QQQ' in text or 'LLL' in text:
                print(f"  Raw text: {repr(text)}")
                print(f"  Has \\P (new line): {'\\P' in text}")

# 检查一个上部单图文件
upper_single = 'output_pages/上部T梁第1页_1-1-1-2.dxf'
if os.path.exists(upper_single):
    single_doc = ezdxf.readfile(upper_single)
    single_msp = single_doc.modelspace()

    print("\n上部单图文件中的桥梁名称MTEXT:")
    for entity in single_msp:
        if entity.dxftype() == 'MTEXT':
            text = entity.text
            if '红石牡丹江' in text:
                print(f"  Raw text: {repr(text)}")
                print(f"  Has \\P (new line): {'\\P' in text}")
                print(f"  Display text: {text}")

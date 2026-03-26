# -*- coding: utf-8 -*-
import ezdxf

# 读取单个文件
single_doc = ezdxf.readfile('output_pages/下部第1页_盖梁1.dxf')
single_msp = single_doc.modelspace()

print("单个文件中的桥梁名称MTEXT:")
for entity in single_msp:
    if entity.dxftype() == 'MTEXT':
        text = entity.text
        if 'K572' in text:
            print(f"  Raw text: {repr(text)}")
            print(f"  Has \\P (new line): {'\\P' in text}")
            print(f"  Has \\n: {'\\n' in text}")

# 读取合并文件
merged_doc = ezdxf.readfile('LK572+774红石牡丹江大桥（右幅）下部病害.dxf')
merged_msp = merged_doc.modelspace()

print("\n合并文件中的桥梁名称MTEXT:")
for entity in merged_msp:
    if entity.dxftype() == 'MTEXT':
        text = entity.text
        if 'K572' in text:
            print(f"  Raw text: {repr(text)}")
            print(f"  Has \\P (new line): {'\\P' in text}")
            print(f"  Has \\n: {'\\n' in text}")

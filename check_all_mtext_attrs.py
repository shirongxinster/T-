# -*- coding: utf-8 -*-
import ezdxf

# 读取下部第6页文件
single_doc = ezdxf.readfile('output_pages/下部第6页_盖梁6.dxf')
single_msp = single_doc.modelspace()

print("下部第6页_盖梁6.dxf 中的桥梁名称MTEXT所有属性:")
for entity in single_msp:
    if entity.dxftype() == 'MTEXT':
        text = entity.text
        if '红石牡丹江' in text:
            print(f"\n  Text: {repr(text)}")
            print(f"  Insert: {entity.dxf.insert}")
            # 打印所有dxf属性
            for attr_name in dir(entity.dxf):
                if not attr_name.startswith('_') and hasattr(entity.dxf, attr_name):
                    try:
                        attr_value = getattr(entity.dxf, attr_name)
                        if not callable(attr_value):
                            print(f"  {attr_name}: {attr_value}")
                    except:
                        pass

# 读取合并文件
merged_doc = ezdxf.readfile('LK572+774红石牡丹江大桥（右幅）下部病害.dxf')
merged_msp = merged_doc.modelspace()

print("\n\n合并文件中的桥梁名称MTEXT所有属性:")
for entity in merged_msp:
    if entity.dxftype() == 'MTEXT':
        text = entity.text
        if '红石牡丹江' in text:
            print(f"\n  Text: {repr(text)}")
            print(f"  Insert: {entity.dxf.insert}")
            # 打印所有dxf属性
            for attr_name in dir(entity.dxf):
                if not attr_name.startswith('_') and hasattr(entity.dxf, attr_name):
                    try:
                        attr_value = getattr(entity.dxf, attr_name)
                        if not callable(attr_value):
                            print(f"  {attr_name}: {attr_value}")
                    except:
                        pass
            break  # 只检查第一个

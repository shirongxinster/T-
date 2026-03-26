# -*- coding: utf-8 -*-
import ezdxf
import os

# 查找模板文件
templates_dir = 'templates'
for f in os.listdir(templates_dir):
    if '下部' in f or '盖梁' in f or f.endswith('.dxf'):
        filepath = os.path.join(templates_dir, f)
        print(f"检查: {f}")
        try:
            doc = ezdxf.readfile(filepath)
            msp = doc.modelspace()
            for entity in msp:
                if entity.dxftype() in ('TEXT', 'MTEXT'):
                    text = entity.text if entity.dxftype() == 'MTEXT' else entity.dxf.text
                    if 'K572' in text or 'QQQ' in text:
                        print(f'  类型: {entity.dxftype()}')
                        print(f'  文本: {repr(text)}')
                        break
        except Exception as e:
            print(f'  错误: {e}')

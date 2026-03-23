# -*- coding: utf-8 -*-
"""检查模板中的文字类型"""

import ezdxf

template_path = r'k:\works\008.S2ReportAndLayoutPic\leftRealJobs_workbuddy\templates\构件\40mT梁.dxf'

doc = ezdxf.readfile(template_path)
msp = doc.modelspace()

print('=== 模板中的文字 ===')
for entity in msp:
    if entity.dxftype() in ['TEXT', 'MTEXT']:
        print(f"类型: {entity.dxftype()}, 内容: {entity.dxf.text if entity.dxftype() == 'TEXT' else entity.text[:50]}")
        # 检查是否包含我们要找的关键字
        text = entity.dxf.text if entity.dxftype() == 'TEXT' else entity.text
        for keyword in ['LLL', 'QQQ', 'HHH', 'KKK', 'a-a', 'b-b']:
            if keyword in text:
                print(f"  *** 包含关键字: {keyword}")

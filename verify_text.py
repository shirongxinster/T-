# -*- coding: utf-8 -*-
"""验证文字是否被正确替换"""

import ezdxf

output_path = r'k:\works\008.S2ReportAndLayoutPic\leftRealJobs_workbuddy\output_pages\上部病害_第1页.dxf'

doc = ezdxf.readfile(output_path)
msp = doc.modelspace()

print('=== 验证文字替换 ===')
for entity in msp:
    if entity.dxftype() in ['TEXT', 'MTEXT']:
        text = entity.text if entity.dxftype() == 'MTEXT' else entity.dxf.text
        # 检查是否包含关键字
        for keyword in ['LLL', 'QQQ', 'HHH', 'KKK', 'a-a', 'b-b']:
            if keyword in text:
                print(f"*** 未替换: {keyword} 在 '{text}'")
        # 显示包含 G11 或 K572 的内容
        if 'G11' in text or 'K572' in text or '鹤大' in text:
            print(f"已替换: {text}")
        if '1-1' in text or '1-2' in text:
            print(f"梁号: {text}")

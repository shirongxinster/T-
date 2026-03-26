# -*- coding: utf-8 -*-
# 模拟process_cap_beam_disease中的逻辑

disease = {
    '具体部件': '大桩号面',
    '缺损位置': '盖梁',
    'x_start': 6.0,
    'x_end': 7.2,
    'y_start': 0.0,
    'y_end': 0.6,
}

location = disease.get('缺损位置', '')
part = disease.get('具体部件', '')

# 判断面：优先用具体部件判断（包含"小桩号面"/"大桩号面"/"挡块"）
face = part if part else location

print(f"location: {location}")
print(f"part: {part}")
print(f"face: {face}")
print(f"'大桩号面' in face: {'大桩号面' in face}")

# 根据面类型设置原点（默认使用小桩号面）
CAP_BEAM_ORIGINS = {
    "小桩号面": (45, 251),
    "大桩号面": (305, 250),
}

if "大桩号面" in face:
    origin = CAP_BEAM_ORIGINS["大桩号面"]
    print(f"使用大桩号面原点: {origin}")
else:
    origin = CAP_BEAM_ORIGINS["小桩号面"]
    print(f"使用小桩号面原点: {origin}")

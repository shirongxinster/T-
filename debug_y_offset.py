# -*- coding: utf-8 -*-
"""
调试Y偏移逻辑
"""
import math

# 模拟两个掉角的参数
# 病害1: x=0~0.3m, y=2~2.3m
# 病害2: x=1.4~1.7m, y=2~2.3m

X_SCALE = 10
Y_SCALE = 9.73
origin_x = 70
origin_y = 290

# 病害1
d1_x1 = 0
d1_x2 = 0.3
d1_y1 = 2
d1_y2 = 2.3
cad1_x1 = origin_x + d1_x1 * X_SCALE
cad1_y1 = origin_y - d1_y1 * Y_SCALE
cad1_x2 = origin_x + d1_x2 * X_SCALE
cad1_y2 = origin_y - d1_y2 * Y_SCALE

# 病害2
d2_x1 = 1.4
d2_x2 = 1.7
d2_y1 = 2
d2_y2 = 2.3
cad2_x1 = origin_x + d2_x1 * X_SCALE
cad2_y1 = origin_y - d2_y1 * Y_SCALE
cad2_x2 = origin_x + d2_x2 * X_SCALE
cad2_y2 = origin_y - d2_y2 * Y_SCALE

# 对于225°角度，引线起点是右下角
# 起点应该是cad_x2（右上角x）, cad_y1（较大值，因为从上到下）
leader1_start_x = cad1_x2  # 73.0
leader1_start_y = cad1_y1  # 270.5

leader2_start_x = cad2_x2  # 87.0
leader2_start_y = cad2_y1  # 270.5

print(f"病害1引线起点: ({leader1_start_x}, {leader1_start_y})")
print(f"病害2引线起点: ({leader2_start_x}, {leader2_start_y})")

# 计算get_label_bbox (seg1_len=8, seg2_len=20, angle=225)
def get_label_bbox(start_x, start_y, angle, seg1_len, seg2_len):
    angle_rad = math.radians(angle)
    bend_x = start_x + seg1_len * math.cos(angle_rad)
    bend_y = start_y + seg1_len * math.sin(angle_rad)

    cos_angle = math.cos(angle_rad)
    if cos_angle >= 0:
        end_x = bend_x + seg2_len
    else:
        end_x = bend_x - seg2_len
    end_y = bend_y

    text_margin = 5
    all_x = [bend_x, end_x]
    all_y = [bend_y, end_y]
    all_x.extend([end_x - seg2_len * 0.5 - text_margin, end_x + text_margin])
    all_y.extend([end_y - text_margin - 3, end_y + text_margin + 3])

    return (min(all_x), min(all_y), max(all_x), max(all_y))

# 模拟第一个病害处理后的标注位置
leader1_bbox = get_label_bbox(leader1_start_x, leader1_start_y, 225, 8, 20)
print(f"\n病害1的标注bbox: {leader1_bbox}")
print(f"  中心Y: {(leader1_bbox[1] + leader1_bbox[3]) / 2}")

# 模拟第二个病害处理时的Y偏移逻辑
# 已有标注的Y中心
existing_y_mid = (leader1_bbox[1] + leader1_bbox[3]) / 2
current_y = leader2_start_y

print(f"\n现有标注Y中心: {existing_y_mid}")
print(f"当前病害起点Y: {current_y}")

# 决定偏移方向
if current_y > existing_y_mid:
    print("当前病害在下方，需要向上偏移")
else:
    print("当前病害在上方，需要向下偏移")

# 尝试Y偏移
y_offset_options = [10, 20, 35, 50, 70]
for y_offset in y_offset_options:
    if current_y > existing_y_mid:
        offset_y = -y_offset  # 向上偏移
    else:
        offset_y = y_offset   # 向下偏移

    offset_start_y = current_y + offset_y
    offset_bbox = get_label_bbox(leader2_start_x, offset_start_y, 225, 8, 20)

    print(f"\nY偏移={offset_y}:")
    print(f"  偏移后起点Y: {offset_start_y}")
    print(f"  偏移后bbox Y范围: {offset_bbox[1]:.1f} ~ {offset_bbox[3]:.1f}")
    print(f"  偏移后中心Y: {(offset_bbox[1] + offset_bbox[3]) / 2}")

    # 检查与已有标注的距离
    new_y_mid = (offset_bbox[1] + offset_bbox[3]) / 2
    y_gap = abs(new_y_mid - existing_y_mid)
    print(f"  与已有标注的Y距离: {y_gap:.1f}")

    if y_gap > 10:  # 需要至少10单位的Y距离才能分开
        print(f"  -> 足够分开! (距离>{10})")
        break
    else:
        print(f"  -> 仍然太近 (距离<{10})")

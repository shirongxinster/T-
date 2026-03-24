# -*- coding: utf-8 -*-
"""
模拟5-3号右腹板两个掉角病害的处理流程分析
"""

print("="*60)
print("5-3号 右腹板 两个掉角病害的处理流程分析")
print("="*60)

# 病害1: x=0~0.3m, y=2~2.3m, 掉角 S=0.09m²
# 病害2: x=1.4~1.7m, y=2~2.3m, 掉角 S=0.09m²

# 右腹板的参数（从代码中获取）
# X_SCALE = 10, Y_SCALE = 9.73
X_SCALE = 10
Y_SCALE = 9.73

# 右腹板的原点坐标（对于5-3号上部T梁）
# 右腹板 origin = (70, 290) - 根据代码逻辑
origin_x = 70
origin_y = 290

print("\n【步骤1】计算病害的CAD绝对坐标")
print("-"*40)

# 病害1计算
disease1_x_start = 0
disease1_x_end = 0.3
disease1_y_start = 2
disease1_y_end = 2.3

cad1_x1 = origin_x + disease1_x_start * X_SCALE
cad1_y1 = origin_y - disease1_y_start * Y_SCALE  # 右腹板是从上到下
cad1_x2 = origin_x + disease1_x_end * X_SCALE
cad1_y2 = origin_y - disease1_y_end * Y_SCALE

print(f"病害1: x={disease1_x_start}~{disease1_x_end}m, y={disease1_y_start}~{disease1_y_end}m")
print(f"  CAD坐标: ({cad1_x1:.1f}, {cad1_y1:.1f}) ~ ({cad1_x2:.1f}, {cad1_y2:.1f})")
print(f"  中心点: ({(cad1_x1+cad1_x2)/2:.1f}, {(cad1_y1+cad1_y2)/2:.1f})")

# 病害2计算
disease2_x_start = 1.4
disease2_x_end = 1.7
disease2_y_start = 2
disease2_y_end = 2.3

cad2_x1 = origin_x + disease2_x_start * X_SCALE
cad2_y1 = origin_y - disease2_y_start * Y_SCALE
cad2_x2 = origin_x + disease2_x_end * X_SCALE
cad2_y2 = origin_y - disease2_y_end * Y_SCALE

print(f"\n病害2: x={disease2_x_start}~{disease2_x_end}m, y={disease2_y_start}~{disease2_y_end}m")
print(f"  CAD坐标: ({cad2_x1:.1f}, {cad2_y1:.1f}) ~ ({cad2_x2:.1f}, {cad2_y2:.1f})")
print(f"  中心点: ({(cad2_x1+cad2_x2)/2:.1f}, {(cad2_y1+cad2_y2)/2:.1f})")

print("\n【步骤2】计算两个病害中心点的距离")
print("-"*40)

import math
center1_x = (cad1_x1 + cad1_x2) / 2
center1_y = (cad1_y1 + cad1_y2) / 2
center2_x = (cad2_x1 + cad2_x2) / 2
center2_y = (cad2_y1 + cad2_y2) / 2

distance = math.sqrt((center2_x - center1_x)**2 + (center2_y - center1_y)**2)
print(f"病害1中心: ({center1_x:.1f}, {center1_y:.1f})")
print(f"病害2中心: ({center2_x:.1f}, {center2_y:.1f})")
print(f"距离: {distance:.1f}")

print("\n【步骤3】确定引线角度")
print("-"*40)

# 右腹板的标准角度是225°（左下方向）
# 但因为Y方向是从上到下，所以实际显示会不同
# 角度规则：135°=左上, 225°=左下, 315°=右上, 45°=右下
# 右腹板用的是225°（向左下延伸）

base_angle = 225
print(f"右腹板默认角度: {base_angle}° (向左下方向)")
print(f"  135°=左上, 225°=左下, 315°=右上, 45°=右下")

print("\n【步骤4】计算引线起点")
print("-"*40)

# 对于225°角度，引线起点应该是右下角
# 因为右腹板是从上到下方向，所以Y是减小的
# 225°意味着向左下走

# 引线起点取病害区域的右下角（对于向下走的角度）
leader1_start_x = cad1_x2  # 右下角x
leader1_start_y = cad1_y1  # 右下角y (注意：cad_y1 > cad_y2因为是从上到下)

leader2_start_x = cad2_x2
leader2_start_y = cad2_y1

print(f"病害1引线起点: ({leader1_start_x:.1f}, {leader1_start_y:.1f})")
print(f"病害2引线起点: ({leader2_start_x:.1f}, {leader2_start_y:.1f})")

print("\n【步骤5】重叠检测")
print("-"*40)

# 检查两个引线起点之间的距离
start_distance = math.sqrt((leader2_start_x - leader1_start_x)**2 + (leader2_start_y - leader1_start_y)**2)
print(f"两个引线起点距离: {start_distance:.1f}")

# 检查两个病害中心之间的距离
print(f"两个病害中心距离: {distance:.1f}")

# 阈值判断
DISTANCE_THRESHOLD = 80
if distance < DISTANCE_THRESHOLD:
    print(f"  -> 距离 {distance:.1f} < {DISTANCE_THRESHOLD}，需要防重叠处理!")
else:
    print(f"  -> 距离 {distance:.1f} >= {DISTANCE_THRESHOLD}，不需要防重叠")

print("\n【步骤6】Y方向偏移尝试")
print("-"*40)

# 尝试Y方向偏移
y_offset_options = [8, 15, 25, 40]
for y_offset in y_offset_options:
    for y_direction in [1, -1]:
        offset_y = y_offset * y_direction

        # 偏移后的引线起点
        offset1_start_y = leader1_start_y + offset_y
        offset2_start_y = leader2_start_y + offset_y

        # 检查两个偏移后的起点是否仍然很近
        new_start_distance = math.sqrt((leader2_start_x - leader1_start_x)**2 + (offset2_start_y - offset1_start_y)**2)

        if new_start_distance > 40:  # 40是起点不重叠的阈值
            print(f"  Y偏移{offset_y}: 起点距离={new_start_distance:.1f} > 40, 可以分开!")

print("\n【问题分析】")
print("-"*40)
print("两个病害的关键问题:")
print("1. 两个病害的Y坐标完全相同（y=2~2.3m），所以CAD中的Y坐标相同")
print("2. 225°角度意味着向左下走，两个引线的折点和终点都在同一水平线上")
print("3. 虽然X坐标不同（相距约13个单位），但Y坐标完全相同")
print("4. Y方向偏移可能有效，但需要足够大的偏移量（>40）")
print("5. 当前的偏移选项[8,15,25,40]可能不够大")

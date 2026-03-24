"""更详细的边界测试"""
import math

# 右翼缘板参数
RIGHT_WING_ORIGIN_X = 84
RIGHT_WING_ORIGIN_Y = 234.4
X_SCALE = 10
Y_SCALE = 9.73
BEAM_BOUNDS_UPPER = {'min_x': 84, 'max_x': 483, 'min_y': 228, 'max_y': 289}

# 病害2: x=0～0.1m, y=0～0.4m  
disease2_x = (0 + 0.1) / 2  # 0.05m
disease2_y = (0 + 0.4) / 2  # 0.2m
disease2_cad_x = RIGHT_WING_ORIGIN_X + disease2_x * X_SCALE
disease2_cad_y = RIGHT_WING_ORIGIN_Y + disease2_y * Y_SCALE

print(f"病害2 CAD坐标: x={disease2_cad_x}, y={disease2_cad_y}")

def get_label_bbox(start_x, start_y, angle, seg1_len, seg2_len=12):
    """计算标注的边界框"""
    seg1_rad = math.radians(angle)
    
    bend_x = start_x + seg1_len * math.cos(seg1_rad)
    bend_y = start_y + seg1_len * math.sin(seg1_rad)
    
    text_half_width = seg2_len / 2
    text_height = 10
    
    if angle == 45:  # 右上：文字在左侧
        x_min = bend_x - text_half_width - 5
        x_max = bend_x + 5
        y_min = bend_y
        y_max = bend_y + text_height + 5
    elif angle == 135:  # 左上：文字在右侧
        x_min = bend_x - 5
        x_max = bend_x + text_half_width + 5
        y_min = bend_y
        y_max = bend_y + text_height + 5
    elif angle == 225:  # 左下：文字在右侧
        x_min = bend_x - 5
        x_max = bend_x + text_half_width + 5
        y_min = bend_y - text_height - 5
        y_max = bend_y
    else:  # 315: 右下：文字在左侧
        x_min = bend_x - text_half_width - 5
        x_max = bend_x + 5
        y_min = bend_y - text_height - 5
        y_max = bend_y
    
    return (x_min, y_min, x_max, y_max)

def check_in_bounds(bbox, bounds):
    x_min, y_min, x_max, y_max = bbox
    return (x_min >= bounds['min_x'] and x_max <= bounds['max_x'] and
            y_min >= bounds['min_y'] and y_max <= bounds['max_y'])

# 测试不同角度和seg1值
print("\n--- 测试315度 ---")
for seg1 in [8, 10, 12]:
    bbox = get_label_bbox(disease2_cad_x, disease2_cad_y, 315, seg1, 12)
    in_bounds = check_in_bounds(bbox, BEAM_BOUNDS_UPPER)
    print(f"seg1={seg1}: bbox=({bbox[0]:.1f}, {bbox[1]:.1f}, {bbox[2]:.1f}, {bbox[3]:.1f}), in_bounds={in_bounds}")

# 看看315度在y方向上的极限
print("\n--- 测试y方向边界 ---")
# y_min >= 228
# 对于315度: y_min = bend_y - 17, bend_y = start_y + seg1 * sin(315)
# 需要: start_y + seg1 * sin(315) - 17 >= 228
# sin(315) = -0.707
# start_y = 236.346
# 236.346 - 0.707*seg1 - 17 >= 228
# 219.346 - 0.707*seg1 >= 228
# -0.707*seg1 >= 8.654
# seg1 <= -12.24 (不可能)

# 所以315度肯定超出y下边界! 让我重新计算
print(f"sin(315°) = {math.sin(math.radians(315))}")
print(f"y_min 需要 >= {BEAM_BOUNDS_UPPER['min_y']}")

# 对于315度，y_min = bend_y - 17 = start_y + seg1*sin(315) - 17
# = 236.346 + seg1*(-0.707) - 17 = 219.346 - 0.707*seg1
# 需要 219.346 - 0.707*seg1 >= 228
# -0.707*seg1 >= 8.654
# seg1 <= -12.24 (impossible)

print("\n315度无法满足y_min >= 228的要求，因为seg1越大，y_min越小")

# 尝试135度（左上方向）
print("\n--- 测试135度 ---")
for seg1 in [8, 10, 12, 16]:
    bbox = get_label_bbox(disease2_cad_x, disease2_cad_y, 135, seg1, 12)
    in_bounds = check_in_bounds(bbox, BEAM_BOUNDS_UPPER)
    print(f"seg1={seg1}: bbox=({bbox[0]:.1f}, {bbox[1]:.1f}, {bbox[2]:.1f}, {bbox[3]:.1f}), in_bounds={in_bounds}")

# 135度是左上方向，文字在右侧
# 对于右翼缘板来说，135度可能会超出右边界
print("\n--- 测试225度（左下方向）---")
for seg1 in [8, 10, 12]:
    bbox = get_label_bbox(disease2_cad_x, disease2_cad_y, 225, seg1, 12)
    in_bounds = check_in_bounds(bbox, BEAM_BOUNDS_UPPER)
    print(f"seg1={seg1}: bbox=({bbox[0]:.1f}, {bbox[1]:.1f}, {bbox[2]:.1f}, {bbox[3]:.1f}), in_bounds={in_bounds}")

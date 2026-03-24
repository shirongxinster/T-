"""找出需要的seg1值来分离两个标注"""
import math

RIGHT_WING_ORIGIN_X = 84
RIGHT_WING_ORIGIN_Y = 234.4
X_SCALE = 10
Y_SCALE = 9.73
BEAM_BOUNDS_UPPER = {'min_x': 84, 'max_x': 483, 'min_y': 228, 'max_y': 289}

# 病害1: x=1.1m, y=0.5m
disease1_cad_x = 84 + 1.1 * 10  # 95
disease1_cad_y = 234.4 + 0.5 * 9.73  # 239.265

# 病害2: x=0.05m, y=0.2m
disease2_cad_x = 84 + 0.05 * 10  # 84.5
disease2_cad_y = 234.4 + 0.2 * 9.73  # 236.346

def get_label_bbox(start_x, start_y, angle, seg1_len, seg2_len=12):
    seg1_rad = math.radians(angle)
    bend_x = start_x + seg1_len * math.cos(seg1_rad)
    bend_y = start_y + seg1_len * math.sin(seg1_rad)
    
    text_half_width = seg2_len / 2
    text_height = 10
    
    if angle == 45:
        x_min = bend_x - text_half_width - 5
        x_max = bend_x + 5
        y_min = bend_y
        y_max = bend_y + text_height + 5
    else:
        raise ValueError("Only 45 degree tested")
    
    return (x_min, y_min, x_max, y_max)

def check_in_bounds(bbox, bounds):
    x_min, y_min, x_max, y_max = bbox
    return (x_min >= bounds['min_x'] and x_max <= bounds['max_x'] and
            y_min >= bounds['min_y'] and y_max <= bounds['max_y'])

def check_overlap(b1, b2):
    return not (b1[2] <= b2[0] or b1[0] >= b2[2] or b1[3] <= b2[1] or b1[1] >= b2[3])

# 病害1用默认seg1=8
bbox1 = get_label_bbox(disease1_cad_x, disease1_cad_y, 45, 8, 12)
print(f"病害1 (seg1=8): bbox y={bbox1[1]:.1f}~{bbox1[3]:.1f}")

# 尝试不同的seg1值
print("\n尝试扩展seg1:")
for seg1 in [8, 12, 16, 20, 24, 28, 32, 36, 40, 50]:
    bbox2 = get_label_bbox(disease2_cad_x, disease2_cad_y, 45, seg1, 12)
    in_bounds = check_in_bounds(bbox2, BEAM_BOUNDS_UPPER)
    overlap = check_overlap(bbox1, bbox2)
    print(f"seg1={seg1:2d}: y={bbox2[1]:.1f}~{bbox2[3]:.1f}, in_bounds={in_bounds}, overlap={overlap}")
    if not overlap and in_bounds:
        print(f"  >>> 找到分离方案! seg1={seg1}")
        break

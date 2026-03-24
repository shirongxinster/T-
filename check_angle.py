import math

BEAM_BOUNDS = {
    'upper': {'min_x': 84, 'max_x': 483, 'min_y': 228, 'max_y': 289},
    'lower': {'min_x': 84, 'max_x': 483, 'min_y': 117, 'max_y': 177}
}

def get_label_bbox_new(start_x, start_y, angle, seg1_len, seg2_len):
    """修复后版本：315度横线向右，不含起点"""
    angle_rad = math.radians(angle)
    bend_x = start_x + seg1_len * math.cos(angle_rad)
    bend_y = start_y + seg1_len * math.sin(angle_rad)
    # 315和45向右，135和225向左
    cos_angle = math.cos(angle_rad)
    if cos_angle >= 0:
        end_x = bend_x + seg2_len
    else:
        end_x = bend_x - seg2_len
    end_y = bend_y
    # 不含起点
    all_x = [bend_x, end_x]
    all_y = [bend_y, end_y]
    text_margin = 5
    all_x.extend([end_x - seg2_len * 0.5 - text_margin, end_x + text_margin])
    all_y.extend([end_y - text_margin - 3, end_y + text_margin + 3])
    return (min(all_x), min(all_y), max(all_x), max(all_y))

def check_in_bounds(bbox, beam_level):
    bounds = BEAM_BOUNDS.get(beam_level, BEAM_BOUNDS['upper'])
    x_min, y_min, x_max, y_max = bbox
    return (x_min >= bounds['min_x'] and x_max <= bounds['max_x'] and
            y_min >= bounds['min_y'] and y_max <= bounds['max_y'])

bounds = BEAM_BOUNDS['lower']
print(f'lower边界: x={bounds["min_x"]}-{bounds["max_x"]}, y={bounds["min_y"]}-{bounds["max_y"]}')
print()

seg1_len = 8
seg2_len = 12

# 4-5号 右腹板 lower CAD: (88.80, 141.46) -> (93.80, 146.32)
# 315度起点=右下角
start_x_315 = 93.80
start_y_315 = 141.46
bbox_315 = get_label_bbox_new(start_x_315, start_y_315, 315, seg1_len, seg2_len)
in_315 = check_in_bounds(bbox_315, 'lower')
print(f'4-5号 315度 起点=({start_x_315}, {start_y_315})')
print(f'4-5号 315度 折点=({start_x_315+seg1_len*math.cos(math.radians(315)):.2f}, {start_y_315+seg1_len*math.sin(math.radians(315)):.2f})')
print(f'4-5号 315度 bbox: {bbox_315}')
print(f'4-5号 315度 in_bounds: {in_315}')
print()

# 4-4号 右腹板 lower CAD: (83.80, 141.46) -> (88.80, 144.38)
# 315度起点=右下角
start_x_44 = 88.80
start_y_44 = 141.46
bbox_44 = get_label_bbox_new(start_x_44, start_y_44, 315, seg1_len, seg2_len)
in_44 = check_in_bounds(bbox_44, 'lower')
print(f'4-4号 315度 起点=({start_x_44}, {start_y_44})')
print(f'4-4号 315度 bbox: {bbox_44}')
print(f'4-4号 315度 in_bounds: {in_44}')

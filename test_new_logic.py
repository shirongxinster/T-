"""测试新的seg1延长逻辑"""
import math

RIGHT_WING_ORIGIN_X = 84
RIGHT_WING_ORIGIN_Y = 234.4
X_SCALE = 10
Y_SCALE = 9.73

# 病害1: x=1.1m, y=0.5m (更高)
disease1_cad_x = 84 + 1.1 * 10
disease1_cad_y = 234.4 + 0.5 * 9.73

# 病害2: x=0.05m, y=0.2m (更低)
disease2_cad_x = 84 + 0.05 * 10
disease2_cad_y = 234.4 + 0.2 * 9.73

print(f"病害1 CAD: x={disease1_cad_x}, y={disease1_cad_y}")
print(f"病害2 CAD: x={disease2_cad_x}, y={disease2_cad_y}")

def get_label_bbox(start_x, start_y, angle, seg1_len, seg2_len=12):
    seg1_rad = math.radians(angle)
    bend_x = start_x + seg1_len * math.cos(seg1_rad)
    bend_y = start_y + seg1_len * math.sin(seg1_rad)
    
    text_half_width = seg2_len / 2
    text_height = 10
    
    if angle == 45:  # 右上
        x_min = bend_x - text_half_width - 5
        x_max = bend_x + 5
        y_min = bend_y
        y_max = bend_y + text_height + 5
    
    return (x_min, y_min, x_max, y_max)

def check_overlap(b1, b2):
    return not (b1[2] <= b2[0] or b1[0] >= b2[2] or b1[3] <= b2[1] or b1[1] >= b2[3])

# 模拟新逻辑：
# 斜向上(45°)时：更低的标注延长（文字更高）

# 处理病害1（更高）
bbox1 = get_label_bbox(disease1_cad_x, disease1_cad_y, 45, 8, 12)
print(f"\n病害1 (更高): seg1=8, bbox y={bbox1[1]:.1f}~{bbox1[3]:.1f}")

# 处理病害2（更低）- 应该延长
print(f"\n处理病害2 (更低):")
# 当前更低，斜向上 → 应该延长
for seg1 in [8, 12, 16, 20, 24, 30]:
    bbox2 = get_label_bbox(disease2_cad_x, disease2_cad_y, 45, seg1, 12)
    overlap = check_overlap(bbox1, bbox2)
    print(f"  seg1={seg1}: bbox y={bbox2[1]:.1f}~{bbox2[3]:.1f}, overlap={overlap}")
    if not overlap:
        print(f"  >>> 找到分离方案! seg1={seg1}")
        break

# 分析
print(f"\n分析:")
print(f"病害1 bbox顶部: {bbox1[3]}")
print(f"两者Y差: {abs(disease1_cad_y - disease2_cad_y)}")
print(f"45度文字高度: 15单位")
print(f"因为两者Y只差约3单位，seg1需要足够长让病害2的文字超过病害1")

"""测试5-2号右翼缘板两个病害的标注重叠问题"""
import math

# 模拟两个病害的位置
# 5-2号 右翼缘板, x=1～1.2m, y=0.4～0.6m, 剥落 S=0.04m2
# 5-2号 右翼缘板, x=0～0.1m, y=0～0.4m, 剥落露筋 S=0.04m2

# 右翼缘板的原点坐标 (上方T梁)
RIGHT_WING_ORIGIN_X = 84
RIGHT_WING_ORIGIN_Y = 234.4

# 坐标换算: 1m = 10 (x), 1m = 9.73 (y)
X_SCALE = 10
Y_SCALE = 9.73

# 病害1: x=1～1.2m, y=0.4～0.6m
disease1_x = (1.0 + 1.2) / 2  # 中心点 1.1m
disease1_y = (0.4 + 0.6) / 2  # 中心点 0.5m
disease1_cad_x = RIGHT_WING_ORIGIN_X + disease1_x * X_SCALE
disease1_cad_y = RIGHT_WING_ORIGIN_Y + disease1_y * Y_SCALE

# 病害2: x=0～0.1m, y=0～0.4m  
disease2_x = (0 + 0.1) / 2  # 中心点 0.05m
disease2_y = (0 + 0.4) / 2  # 中心点 0.2m
disease2_cad_x = RIGHT_WING_ORIGIN_X + disease2_x * X_SCALE
disease2_cad_y = RIGHT_WING_ORIGIN_Y + disease2_y * Y_SCALE

print(f"病害1 CAD坐标: x={disease1_cad_x}, y={disease1_cad_y}")
print(f"病害2 CAD坐标: x={disease2_cad_x}, y={disease2_cad_y}")

# 右翼缘板的Y方向是从上到下，所以y越大越靠上
# 两个病害的Y中心: disease1_y=0.5m (靠上), disease2_y=0.2m (靠下)

# 右翼缘板的标注角度: 45度(右上方)
# x > 284 (在中心线右侧), 应该向左连接
# 右翼缘板是向上方向
# 所以角度应该是 45度 (右上)

# 模拟seg1_len = 8 (默认) 和 seg1_len = 12 (扩展) 的情况
def get_label_bbox(start_x, start_y, angle, seg1_len, seg2_len=12):
    """计算标注的边界框"""
    seg1_rad = math.radians(angle)
    seg2_rad = math.radians(angle)
    
    # 折线点（拐点）
    bend_x = start_x + seg1_len * math.cos(seg1_rad)
    bend_y = start_y + seg1_len * math.sin(seg1_rad)
    
    # 文字区域（从拐点水平延伸）
    # 45度角：向右上方，文字应该在左侧（从bend点向左延伸）
    # 135度：向左上方，文字应该在右侧
    # 225度：向左下方，文字应该在右侧
    # 315度：向右下方，文字应该在左侧
    
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

# 测试两个病害的标注（都用45度）
angle = 45
seg1_len_default = 8
seg1_len_extended = 12

bbox1 = get_label_bbox(disease1_cad_x, disease1_cad_y, angle, seg1_len_default, 12)
bbox2 = get_label_bbox(disease2_cad_x, disease2_cad_y, angle, seg1_len_default, 12)
bbox2_ext = get_label_bbox(disease2_cad_x, disease2_cad_y, angle, seg1_len_extended, 12)

print(f"\n默认seg1=8:")
print(f"病害1 bbox: x={bbox1[0]:.1f}~{bbox1[2]:.1f}, y={bbox1[1]:.1f}~{bbox1[3]:.1f}")
print(f"病害2 bbox: x={bbox2[0]:.1f}~{bbox2[2]:.1f}, y={bbox2[1]:.1f}~{bbox2[3]:.1f}")

# 检查重叠
def check_overlap(b1, b2):
    return not (b1[2] <= b2[0] or b1[0] >= b2[2] or b1[3] <= b2[1] or b1[1] >= b2[3])

print(f"默认bbox重叠: {check_overlap(bbox1, bbox2)}")

print(f"\nseg1扩展到12:")
print(f"病害2 bbox: x={bbox2_ext[0]:.1f}~{bbox2_ext[2]:.1f}, y={bbox2_ext[1]:.1f}~{bbox2_ext[3]:.1f}")
print(f"扩展后bbox重叠: {check_overlap(bbox1, bbox2_ext)}")

# 尝试更大的扩展
for seg1 in [16, 20, 24]:
    bbox_test = get_label_bbox(disease2_cad_x, disease2_cad_y, angle, seg1, 12)
    overlap = check_overlap(bbox1, bbox_test)
    print(f"seg1={seg1}: bbox x={bbox_test[0]:.1f}~{bbox_test[2]:.1f}, y={bbox_test[1]:.1f}~{bbox_test[3]:.1f}, 重叠={overlap}")

# 分析：两个病害都是45度，文字都在左侧
# 病害1在更靠上的位置(y=0.5m)，病害2在更靠下的位置(y=0.2m)
# 45度角的文字区域是向上的，所以：
# - 病害1的文字在 y=126.5~141.5
# - 病害2的文字在 y=118.3~142.4（扩展后）
# 确实有重叠

# 解决方案：让靠下的病害2使用不同的角度，比如315度（右下）
print("\n--- 尝试不同角度组合 ---")
# 病害1保持45度，病害2尝试315度
bbox2_315 = get_label_bbox(disease2_cad_x, disease2_cad_y, 315, seg1_len_default, 12)
print(f"病害2用315度: x={bbox2_315[0]:.1f}~{bbox2_315[2]:.1f}, y={bbox2_315[1]:.1f}~{bbox2_315[3]:.1f}")
print(f"315度重叠: {check_overlap(bbox1, bbox2_315)}")

# 315度是否超出边界？
# 右翼缘板的边界: x=84~483, y方向: 右翼缘板的y范围是234.4往下
# 315度是向右下方，对于右翼缘板来说可能超出y的下边界
print(f"\n右翼缘板原点: x={RIGHT_WING_ORIGIN_X}, y={RIGHT_WING_ORIGIN_Y}")
print(f"315度的bend点: x={disease2_cad_x + seg1_len_default * math.cos(math.radians(315)):.1f}, y={disease2_cad_y + seg1_len_default * math.sin(math.radians(315)):.1f}")

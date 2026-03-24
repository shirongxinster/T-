import pandas as pd

# 模拟get_label_angle函数
UPPER_LEFT_THRESHOLD_Y = 273
UPPER_RIGHT_THRESHOLD_Y = 245
LOWER_LEFT_THRESHOLD_Y = 161
LOWER_RIGHT_THRESHOLD_Y = 132

def get_label_angle_debug(specific_part, beam_level, start_x, start_y):
    if specific_part == '右腹板':
        if beam_level == 'upper':
            threshold_y = UPPER_RIGHT_THRESHOLD_Y  # 245
        else:
            threshold_y = LOWER_RIGHT_THRESHOLD_Y
        
        print(f"  右腹板判断: beam_level={beam_level}, threshold_y={threshold_y}")
        print(f"  start_x={start_x}, start_y={start_y}")
        
        if start_x < 100:
            if start_y > threshold_y:
                print(f"    x < 100, y > {threshold_y} -> 返回315")
                return 315
            else:
                print(f"    x < 100, y <= {threshold_y} -> 返回45")
                return 45
        elif start_x <= 450:
            if start_y > threshold_y:
                print(f"    100<=x<={450}, y({start_y}) > {threshold_y} -> 返回315")
                return 315
            else:
                print(f"    100<=x<={450}, y({start_y}) <= {threshold_y} -> 返回45")
                return 45
        else:
            if start_y > threshold_y:
                return 225
            else:
                return 135
    return 45

# 3-5号右腹板数据
print("测试3-5号右腹板 x=1.9～4.9m，y=2.24m:")
origin_x, origin_y = 84, 234.4  # 上方T梁右腹板原点
x_start = 1.9
y_start = 2.24

cad_x1 = origin_x + x_start * 10
cad_y1 = origin_y + y_start * 9.73

print(f"CAD坐标: ({cad_x1}, {cad_y1})")
print()

angle = get_label_angle_debug('右腹板', 'upper', cad_x1, cad_y1)
print(f"最终返回角度: {angle}")

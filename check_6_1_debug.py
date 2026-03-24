from bridge_disease_main_upper import get_label_angle

# 6-1号 梁底：x=20～21m, y=0.2～0.6m
# 梁底 origin = (45, 274)
# X_SCALE = 10

origin_x, origin_y = 45, 274
x_start, x_end = 20, 21
y_start, y_end = 0.2, 0.6

cad_x_mid = origin_x + (x_start + x_end) / 2 * 10
cad_y_mid = origin_y - (y_start + y_end) / 2 * 9.73

print(f"6-1号 梁底:")
print(f"  病害坐标: x={x_start}~{x_end}m, y={y_start}~{y_end}m")
print(f"  CAD坐标: cad_x_mid={cad_x_mid}, cad_y_mid={cad_y_mid}")
print(f"  X_CENTER=284.0")
print(f"  go_right = (cad_x_mid < 284) = {cad_x_mid < 284}")
print(f"  梁底 go_up = False")
print(f"  最终角度 = 315° (右下)")
print()
print(f"实际角度应该是: 315°")
print(f"如果显示225°，说明 x坐标被错误判断 > 284")
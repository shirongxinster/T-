# -*- coding: utf-8 -*-
# 计算验证

SCALE_X = 14
SCALE_Y = 16.5

origin_xiaozhuanghao = (45, 251)
origin_dazhuanghao = (305, 250)

x_start, x_end = 6.0, 7.2
y_start, y_end = 0.0, 0.6

# 小桩号面计算
x1_xiao = origin_xiaozhuanghao[0] + x_start * SCALE_X
x2_xiao = origin_xiaozhuanghao[0] + x_end * SCALE_X
y1_xiao = origin_xiaozhuanghao[1] - y_start * SCALE_Y
y2_xiao = origin_xiaozhuanghao[1] - y_end * SCALE_Y

print(f"小桩号面计算:")
print(f"  x: {x1_xiao} ~ {x2_xiao}")
print(f"  y: {y1_xiao} ~ {y2_xiao}")

# 大桩号面计算
x1_da = origin_dazhuanghao[0] + x_start * SCALE_X
x2_da = origin_dazhuanghao[0] + x_end * SCALE_X
y1_da = origin_dazhuanghao[1] - y_start * SCALE_Y
y2_da = origin_dazhuanghao[1] - y_end * SCALE_Y

print(f"\n大桩号面计算:")
print(f"  x: {x1_da} ~ {x2_da}")
print(f"  y: {y1_da} ~ {y2_da}")

# 实际输出位置
print(f"\n实际输出位置 (S=0.72): (152.46, 241.59)")
print(f"小桩号面计算的中心: ({(x1_xiao+x2_xiao)/2}, {(y1_xiao+y2_xiao)/2})")
print(f"大桩号面计算的中心: ({(x1_da+x2_da)/2}, {(y1_da+y2_da)/2})")

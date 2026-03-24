import ezdxf
import math

# 读取第6页文件
doc = ezdxf.readfile('output_pages/上部T梁第6页_3-5-4-1.dxf')
msp = doc.modelspace()

print("分析LWPOLYLINE实体（引线）：")
print("="*50)

count = 0
for entity in msp:
    if entity.dxftype() == 'LWPOLYLINE':
        points = entity.get_points()
        if len(points) >= 3:
            # 检查是否是引线格式
            p0 = points[0]
            p1 = points[1]
            
            # 计算第一段斜线的角度
            dx = p1[0] - p0[0]
            dy = p1[1] - p0[1]
            
            if abs(dx) > 2 or abs(dy) > 2:  # 排除水平/垂直短线
                angle_rad = math.atan2(dy, dx)
                angle_deg = math.degrees(angle_rad)
                if angle_deg < 0:
                    angle_deg += 360
                
                count += 1
                print(f"[{count}] LWPOLYLINE:")
                print(f"    起点: ({p0[0]:.1f}, {p0[1]:.1f})")
                print(f"    折点: ({p1[0]:.1f}, {p1[1]:.1f})")
                print(f"    终点: ({points[2][0]:.1f}, {points[2][1]:.1f})")
                print(f"    斜线: dx={dx:.1f}, dy={dy:.1f}")
                print(f"    角度: {angle_deg:.1f}度")
                
                # 判断方向
                if 0 <= angle_deg < 45 or 315 <= angle_deg <= 360:
                    direction = "向右/右下"
                elif 45 <= angle_deg < 135:
                    direction = "向上"
                elif 135 <= angle_deg < 225:
                    direction = "向左"
                else:  # 225 <= angle_deg < 315
                    direction = "向下/左下"
                print(f"    方向: {direction}")
                print()

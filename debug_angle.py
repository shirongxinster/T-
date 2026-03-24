import pandas as pd

# 读取Excel
df = pd.read_excel('K572+774红石牡丹江大桥（右幅）病害.xls', header=None)

# 找3-5号右腹板的数据
for idx, row in df.iterrows():
    构件编号 = str(row.iloc[1]) if pd.notna(row.iloc[1]) else ''
    病害 = str(row.iloc[3]) if pd.notna(row.iloc[3]) else ''
    
    if '3-5号' in 构件编号 and '右腹板' in 病害:
        print(f'行{idx}: {构件编号}')
        print(f'  病害: {病害}')
        
        # 解析坐标
        import re
        # 提取 x=xxx～xxxm
        x_match = re.search(r'x=([\d.]+)～([\d.]+)m', 病害)
        y_match = re.search(r'y=([\d.]+)m', 病害)
        
        if x_match:
            x_start = float(x_match.group(1))
            x_end = float(x_match.group(2))
            print(f'  x: {x_start}～{x_end}m')
            
            # 用upper坐标系计算
            origin_x, origin_y = 84, 234.4  # 上方T梁右腹板原点
            X_SCALE = 10
            Y_SCALE = 9.73
            
            cad_x1 = origin_x + x_start * X_SCALE
            cad_x2 = origin_x + x_end * X_SCALE
            # 右腹板Y方向：从下到上
            cad_y1 = origin_y + float(y_match.group(1)) * Y_SCALE
            cad_y2 = cad_y1  # 纵向裂缝y相同
            
            print(f'  CAD坐标: ({cad_x1}, {cad_y1}) ~ ({cad_x2}, {cad_y2})')
            
            # 角度判断
            beam_level = 'upper'
            threshold_y = 245
            start_x = cad_x1
            start_y = cad_y1
            
            print(f'  beam_level={beam_level}')
            print(f'  start_x={start_x}, start_y={start_y}')
            print(f'  threshold_y={threshold_y}')
            
            if start_x < 100:
                print('  分支: x < 100')
            elif start_x <= 450:
                print('  分支: 100 <= x <= 450')
                if start_y > threshold_y:
                    print(f'    y({start_y}) > threshold_y({threshold_y}) -> 返回315度')
                else:
                    print(f'    y({start_y}) <= threshold_y({threshold_y}) -> 返回45度')
            else:
                print('  分支: x > 450')
        print()

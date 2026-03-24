import pandas as pd
from collections import OrderedDict

# 读取Excel
df = pd.read_excel('K572+774红石牡丹江大桥（右幅）病害.xls', header=None)

# 提取所有T梁构件
all_components = []
for idx, row in df.iterrows():
    构件编号 = str(row.iloc[1]) if pd.notna(row.iloc[1]) else ''
    if '号' in 构件编号:
        构件类型 = str(row.iloc[2]) if pd.notna(row.iloc[2]) else ''
        if 'T梁' in 构件类型:
            all_components.append(构件编号)

print('所有T梁构件（按读取顺序）：')
for i, comp in enumerate(all_components):
    print(f'{i}: {comp}')

# 找到3-5号的位置
print()
print('3-5号在构件列表中的位置：')
for i, comp in enumerate(all_components):
    if '3-5' in comp:
        print(f'  索引{i}: {comp}')
        
# 看看第6页的配对
# 假设配对是按顺序每两个配一对
print()
print('配对结果（每两个一组）：')
for i in range(0, len(all_components), 2):
    pair = all_components[i:i+2]
    if len(pair) == 2:
        print(f'  第{i//2 + 1}页: {pair}')
        if '3-5' in pair:
            print(f'    -> 3-5号在pair[{pair.index("3-5号")}]，应该是upper')

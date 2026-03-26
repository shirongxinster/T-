import pandas as pd

# 直接读取Excel
excel_path = r"k:\works\008.S2ReportAndLayoutPic\leftRealJobs_workbuddy\K572+774红石牡丹江大桥（右幅）病害.xls"

df = pd.read_excel(excel_path, header=None)

print("=== 下部（双柱墩12.5）数据 ===")
# 找到下部数据的起始行
start_row = None
for i in range(len(df)):
    cell = df.iloc[i, 0]
    if pd.notna(cell) and '下部（双柱墩12.5）' in str(cell):
        start_row = i
        break

if start_row is None:
    print("未找到下部（双柱墩12.5）数据")
    exit()

print(f"下部数据起始行: {start_row}")

# 显示下部数据的前30行（从start_row+3开始，跳过标题行）
print("\n=== 下部构件病害数据 ===")
for i in range(start_row + 3, min(start_row + 30, len(df))):
    row = df.iloc[i]
    # 检查是否是数字序号
    first_col = row[0]
    if pd.notna(first_col) and (isinstance(first_col, (int, float)) or 
                                (isinstance(first_col, str) and first_col.isdigit())):
        print(f"行 {i}: {list(row)}")
        # 检查是否是盖梁2的数据
        if pd.notna(row[1]) and '2' in str(row[1]):
            print(f"  ^-- 这是盖梁2的数据!")

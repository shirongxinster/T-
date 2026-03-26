import pandas as pd

# 直接读取Excel的前几行
excel_path = r"k:\works\008.S2ReportAndLayoutPic\leftRealJobs_workbuddy\K572+774红石牡丹江大桥（右幅）病害.xls"

df = pd.read_excel(excel_path, header=None)

print("=== Excel 前30行 ===")
for i in range(min(30, len(df))):
    row = df.iloc[i]
    print(f"行 {i}: {list(row)}")

print("\n=== 查找构件类型标题 ===")
for i in range(len(df)):
    cell = df.iloc[i, 0]
    if pd.notna(cell) and '（' in str(cell) and '）' in str(cell):
        part_name = str(cell).strip()
        if '桥梁名称' not in part_name:
            print(f"行 {i}: {part_name}")

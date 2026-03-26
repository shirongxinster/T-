import pandas as pd
import sys

# 读取Excel文件
excel_path = r"k:\works\008.S2ReportAndLayoutPic\leftRealJobs_workbuddy\K572+774红石牡丹江大桥（右幅）病害.xls"

try:
    # 尝试读取下部构件表
    df = pd.read_excel(excel_path, sheet_name="下部构件")
    
    print("=== 下部构件表数据 ===")
    print(f"总行数: {len(df)}")
    print(f"列名: {list(df.columns)}")
    print()
    
    # 筛选盖梁2的数据
    cap2_data = df[df['构件号'] == 2]
    print(f"=== 盖梁2 的数据 ({len(cap2_data)} 条) ===")
    for idx, row in cap2_data.iterrows():
        print(f"\n行号: {idx}")
        print(f"  构件号: {row['构件号']}")
        print(f"  具体部件: {row['具体部件']}")
        print(f"  病害类型: {row['病害类型']}")
        print(f"  x_start: {row.get('x_start', 'N/A')}")
        print(f"  x_end: {row.get('x_end', 'N/A')}")
        print(f"  y_start: {row.get('y_start', 'N/A')}")
        print(f"  y_end: {row.get('y_end', 'N/A')}")
        print(f"  面积: {row.get('面积', 'N/A')}")
        
    # 特别查找大桩号面的剥落
    print("\n=== 大桩号面剥落数据 ===")
    peel_large = df[(df['具体部件'].str.contains('大桩号面', na=False)) & 
                    (df['病害类型'].str.contains('剥落', na=False))]
    print(f"找到 {len(peel_large)} 条大桩号面剥落数据:")
    for idx, row in peel_large.iterrows():
        print(f"\n行号: {idx}")
        print(f"  构件号: {row['构件号']}")
        print(f"  具体部件: {row['具体部件']}")
        print(f"  病害类型: {row['病害类型']}")
        print(f"  x_start: {row.get('x_start', 'N/A')}")
        print(f"  x_end: {row.get('x_end', 'N/A')}")
        print(f"  y_start: {row.get('y_start', 'N/A')}")
        print(f"  y_end: {row.get('y_end', 'N/A')}")
        print(f"  面积: {row.get('面积', 'N/A')}")

except Exception as e:
    print(f"读取Excel失败: {e}")
    sys.exit(1)

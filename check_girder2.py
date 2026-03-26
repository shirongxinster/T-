import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bridge_disease_parser import parse_excel

# 解析Excel
excel_path = r"k:\works\008.S2ReportAndLayoutPic\leftRealJobs_workbuddy\K572+774红石牡丹江大桥（右幅）病害.xls"
data = parse_excel(excel_path)

print("=== 桥梁信息 ===")
print(f"路线: {data['route_name']}")
print(f"桥梁: {data['bridge_name']}")
print()

# 查找双柱墩数据
for part in data['parts']:
    if '双柱墩' in part['name']:
        print(f"=== {part['name']} ===")
        print(f"部位分类: {part['section']}")
        print(f"模板: {part['template_name']}")
        print()
        
        # 查找盖梁2的数据
        if '2' in part['grouped_data']:
            print("=== 盖梁2 的病害数据 ===")
            for i, disease in enumerate(part['grouped_data']['2']):
                print(f"\n病害 {i+1}:")
                print(f"  序号: {disease['序号']}")
                print(f"  构件编号: {disease['构件编号']}")
                print(f"  缺损位置: {disease['缺损位置']}")
                print(f"  具体部件: {disease['具体部件']}")
                print(f"  病害: {disease['病害']}")
                print(f"  病害类型: {disease['病害类型']}")
                print(f"  x_start: {disease['x_start']}")
                print(f"  x_end: {disease['x_end']}")
                print(f"  y_start: {disease['y_start']}")
                print(f"  y_end: {disease['y_end']}")
                print(f"  面积: {disease['area']}")
        else:
            print("没有找到盖梁2的数据")
        
        # 打印所有盖梁号
        cap_beams = [k for k in part['grouped_data'].keys() if k.isdigit()]
        print(f"\n=== 所有盖梁号: {sorted(cap_beams, key=int)} ===")
        break

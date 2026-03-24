with open(r'k:\works\008.S2ReportAndLayoutPic\leftRealJobs_workbuddy\bridge_disease_main_upper.py', encoding='utf-8') as f:
    lines = f.readlines()
    for i in range(1407, 1418):
        print(f'Line {i+1}: {repr(lines[i][:70])}')
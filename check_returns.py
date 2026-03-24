with open(r'k:\works\008.S2ReportAndLayoutPic\leftRealJobs_workbuddy\bridge_disease_main_upper.py', encoding='utf-8') as f:
    lines = f.readlines()
    in_func = False
    for i, line in enumerate(lines):
        if 'def find_non_overlapping_position' in line:
            in_func = True
        if in_func and 'return' in line and '(' in line:
            print(f'Line {i+1}: {line.strip()}')
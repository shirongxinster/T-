import sys
sys.path.insert(0, r'k:\works\008.S2ReportAndLayoutPic\leftRealJobs_workbuddy')

# 临时patch来debug
import bridge_disease_main_upper as main

original_func = main.find_non_overlapping_position

def patched_func(start_x, start_y, base_angle, flip_angle, seg1_len, seg2_len,
                beam_level, max_attempts=10, specific_part=None, disease_cad_coords=None):
    result = original_func(start_x, start_y, base_angle, flip_angle, seg1_len, seg2_len,
                          beam_level, max_attempts, specific_part, disease_cad_coords)
    if result is not None:
        print(f"DEBUG find_non_overlapping_position returned: len={len(result)}, values={result}")
    return result

main.find_non_overlapping_position = patched_func

# 运行主程序
main.main()

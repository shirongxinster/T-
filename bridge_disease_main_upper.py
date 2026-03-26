# -*- coding: utf-8 -*-
"""
桥梁病害CAD标注系统 - 主程序
处理上部（40mT梁）的病害标注，将两个构件放到一张图中
"""

import os
import sys
import math
import random
import shutil
import ezdxf
from bridge_disease_parser import parse_excel

# 固定随机种子
random.seed(42)

# 路径配置
BASE_DIR = r"k:\works\008.S2ReportAndLayoutPic\leftRealJobs_workbuddy"
INPUT_DIR = os.path.join(BASE_DIR, "input")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates", "构件")
LEGENDS_DIR = os.path.join(BASE_DIR, "templates", "病害图例")
OUTPUT_DIR = os.path.join(BASE_DIR, "output_pages")
TEMPLATE_FILE = os.path.join(TEMPLATES_DIR, "40mT梁.dxf")
PEEL_LEGEND_FILE = os.path.join(LEGENDS_DIR, "剥落、掉角.dxf")
REBAR_LEGEND_FILE = os.path.join(LEGENDS_DIR, "钢筋锈蚀或可见箍筋轮廓.dxf")

# 剥落图例原始数据（从模板提取）
PEEL_OFF_GEOMETRY = None
REBAR_GEOMETRY = None

# 标注位置缓存（每页重置）
LABEL_POSITIONS_CACHE = []  # 存储 (x1, y1, x2, y2, angle) 的标注边界框和角度

# T梁标注范围限制
BEAM_BOUNDS = {
    "upper": {"min_x": 84, "max_x": 483, "min_y": 228, "max_y": 289},
    "lower": {"min_x": 84, "max_x": 483, "min_y": 117, "max_y": 177},
}

# 各部件标注方向配置 - 2026-03-24 重写，统一逻辑
# 规则：
#   水平方向（左右）：以整体X中心线 284 为界
#       病害x中点 < 284 → 引线向右（连接病害图右侧）
#       病害x中点 >= 284 → 引线向左（连接病害图左侧）
#   垂直方向（上下，仅腹板）：以各腹板自身Y中心线为界
#       病害y中点 > Y中心线 → 病害在上方 → 引线向下（-y 方向）
#       病害y中点 <= Y中心线 → 病害在下方 → 引线向上（+y 方向）
#   翼缘板 / 梁底 / 马蹄侧面：只用X方向判断，固定向上（翼缘板朝外）或向下（马蹄）

# 各腹板 Y 轴中心线（CAD坐标），= 原点Y ± 腹板高度/2
WEB_Y_CENTER = {
    "upper": {
        "左腹板": 273.5,  # (284.4 + 262.5) / 2
        "右腹板": 245.3,  # (234.4 + 256.3) / 2
    },
    "lower": {
        "左腹板": 161.1,  # (172.0 + 150.1) / 2
        "右腹板": 132.9,  # (122.0 + 143.9) / 2
    },
}

X_CENTER = 284.0  # T梁水平中心线


def get_label_angle(
    specific_part: str, beam_level: str, start_x: float, start_y: float
) -> float:
    """根据病害区域中点坐标获取引线角度。

    角度定义：0°=向右，90°=向上，180°=向左，270°=向下
    组合角：45°=右上，135°=左上，225°=左下，315°=右下

    Args:
        start_x: 病害区域x中点（CAD坐标）
        start_y: 病害区域y中点（CAD坐标）
    """
    # ---- 第一步：确定水平方向（左/右） ----
    go_right = start_x < X_CENTER  # True=向右, False=向左

    # ---- 第二步：确定垂直方向（上/下） ----
    if specific_part in ("左腹板", "右腹板"):
        # 腹板有Y轴中心线，根据病害y中点与中心线的关系决定上下
        y_center = WEB_Y_CENTER.get(beam_level, {}).get(specific_part, 273.5)
        go_up = start_y <= y_center  # 在中心线下方（y小）→ 向上；在上方→ 向下
    elif specific_part in ("左翼缘板", "梁底"):
        # 翼缘板和梁底：向下（引线从病害向外延伸，翼缘板在上半部分朝外是向下）
        go_up = False
    elif specific_part == "右翼缘板":
        # 右翼缘板在T梁下方，向上
        go_up = True
    elif specific_part == "马蹄左侧面":
        # 马蹄左侧面：向上
        go_up = True
    elif specific_part == "马蹄右侧面":
        # 马蹄右侧面：向下
        go_up = False
    else:
        go_up = True  # 默认向上

    # ---- 第三步：组合得到角度 ----
    if go_right and go_up:
        return 45  # 右上
    elif go_right and not go_up:
        return 315  # 右下
    elif not go_right and go_up:
        return 135  # 左上
    else:
        return 225  # 左下


def reset_label_cache():
    """重置标注位置缓存（每页开始时调用）"""
    global LABEL_POSITIONS_CACHE
    LABEL_POSITIONS_CACHE = []


def get_label_bbox(start_x, start_y, angle, seg1_len, seg2_len):
    """计算标注的边界框

    引线结构：起点 -> 斜线段(8单位) -> 折点 -> 水平横线(seg2_len长度) -> 终点

    Args:
        start_x, start_y: 引线起点
        angle: 第一段角度（度）
        seg1_len: 第一段长度（斜线）
        seg2_len: 第二段长度（水平横线）

    Returns:
        (min_x, min_y, max_x, max_y)
    """
    angle_rad = math.radians(angle)

    # 折点位置（第一段斜线终点）
    bend_x = start_x + seg1_len * math.cos(angle_rad)
    bend_y = start_y + seg1_len * math.sin(angle_rad)

    # 终点位置（第二段水平横线）
    # 横线方向与斜线的x分量方向一致：
    # 45度（右上）、315度（右下）→ 横线向右（+x）
    # 135度（左上）、225度（左下）→ 横线向左（-x）
    cos_angle = math.cos(angle_rad)
    if cos_angle >= 0:
        end_x = bend_x + seg2_len
    else:
        end_x = bend_x - seg2_len
    end_y = bend_y

    # 计算边界框（只包含标注文字和水平横线区域，不含引线起点本身）
    # 引线起点在病害图上，属于病害区域，不是标注区域
    all_x = [bend_x, end_x]
    all_y = [bend_y, end_y]

    # 文字区域（在水平线终点附近）
    text_margin = 5
    # 文字在水平线上方和下方
    all_x.extend([end_x - seg2_len * 0.5 - text_margin, end_x + text_margin])
    all_y.extend([end_y - text_margin - 3, end_y + text_margin + 3])

    return (min(all_x), min(all_y), max(all_x), max(all_y))


def check_bbox_overlap(bbox1, bbox2, margin=2):
    """检查两个边界框是否重叠（带边距）"""
    x1_min, y1_min, x1_max, y1_max = bbox1
    x2_min, y2_min, x2_max, y2_max = bbox2

    # 添加边距
    x1_min -= margin
    y1_min -= margin
    x1_max += margin
    y1_max += margin

    return not (
        x1_max <= x2_min or x1_min >= x2_max or y1_max <= y2_min or y1_min >= y2_max
    )


def check_in_bounds(bbox, beam_level):
    """检查边界框是否在T梁范围内"""
    bounds = BEAM_BOUNDS.get(beam_level, BEAM_BOUNDS["upper"])
    x_min, y_min, x_max, y_max = bbox

    return (
        x_min >= bounds["min_x"]
        and x_max <= bounds["max_x"]
        and y_min >= bounds["min_y"]
        and y_max <= bounds["max_y"]
    )


def find_non_overlapping_position(
    start_x,
    start_y,
    base_angle,
    flip_angle,
    seg1_len,
    seg2_len,
    beam_level,
    max_attempts=10,
    specific_part=None,
    disease_cad_coords=None,
):
    """寻找不重叠的标注位置

    规则：
    1. 优先使用base_angle，只有当base_angle完全无法放置（超出边界）时才尝试其他角度
    2. 新标注与已有标注的角度差不能是锐角（<90度），避免文字与斜线交叉
    3. 标注必须在T梁范围内
    4. 标注之间不能重叠
    5. 如果与已有标注角度相同且病害绝对坐标距离很近，尝试翻转角度避免重叠
    6. 马蹄左侧面/右侧面不允许翻转角度（固定向上/向下）

    Returns:
        (angle, bbox) - 使用的角度和边界框，如果找不到则返回None
    """
    global LABEL_POSITIONS_CACHE

    # 马蹄部件不允许翻转角度
    is_horsehoof = specific_part in ("马蹄左侧面", "马蹄右侧面")

    # 检查是否需要翻转角度：当与已有标注角度相同且病害绝对坐标距离很近时
    START_DISTANCE_THRESHOLD = 80  # 使用绝对坐标判断真实距离
    should_flip_for_proximity = False

    # 如果提供了病害CAD坐标，使用病害坐标判断；否则使用引线起点
    if disease_cad_coords:
        current_disease_x, current_disease_y = disease_cad_coords
    else:
        current_disease_x, current_disease_y = start_x, start_y

    for existing in LABEL_POSITIONS_CACHE:
        existing_bbox = existing[:4]
        existing_angle = existing[4] if len(existing) > 4 else None
        existing_disease_coords = (
            existing[5:7] if len(existing) > 6 else None
        )  # 存储的病害坐标

        if existing_angle == base_angle and existing_disease_coords:
            # 使用病害的绝对坐标计算真实距离
            existing_disease_x, existing_disease_y = existing_disease_coords
            distance = math.sqrt(
                (current_disease_x - existing_disease_x) ** 2
                + (current_disease_y - existing_disease_y) ** 2
            )

            if distance < START_DISTANCE_THRESHOLD:
                should_flip_for_proximity = True
                break

    # 如果需要翻转角度，优先尝试flip_angle（马蹄除外）
    if should_flip_for_proximity and not is_horsehoof:
        # 尝试翻转角度，如果重叠则增加横线长度
        for length_multiplier in [1.0, 1.5, 2.0]:
            extended_seg2_len = seg2_len * length_multiplier
            flip_bbox = get_label_bbox(
                start_x, start_y, flip_angle, seg1_len, extended_seg2_len
            )
            if check_in_bounds(flip_bbox, beam_level):
                # 检查flip_angle是否与已有标注重叠
                overlap = False
                for existing in LABEL_POSITIONS_CACHE:
                    if check_bbox_overlap(flip_bbox, existing[:4]):
                        overlap = True
                        break
                if not overlap:
                    return (flip_angle, seg1_len, extended_seg2_len, flip_bbox)

        # 如果flip_angle所有长度都重叠，尝试其他角度+延长
        all_angles = [45, 135, 225, 315]
        for angle in all_angles:
            if angle == base_angle:
                continue
            for length_multiplier in [1.5, 2.0, 2.5]:
                extended_seg2_len = seg2_len * length_multiplier
                bbox = get_label_bbox(
                    start_x, start_y, angle, seg1_len, extended_seg2_len
                )
                if check_in_bounds(bbox, beam_level):
                    overlap = False
                    for existing in LABEL_POSITIONS_CACHE:
                        if check_bbox_overlap(bbox, existing[:4]):
                            overlap = True
                            break
                    if not overlap:
                        return (angle, seg1_len, extended_seg2_len, bbox)

    # 首先检查base_angle是否可以放置
    bbox = get_label_bbox(start_x, start_y, base_angle, seg1_len, seg2_len)
    in_bounds = check_in_bounds(bbox, beam_level)

    if in_bounds:
        # 检查是否与已有标注重叠（同时检查bbox重叠和起点距离）
        overlap = False
        for existing in LABEL_POSITIONS_CACHE:
            existing_bbox = existing[:4]
            # 检查bbox重叠
            is_overlap = check_bbox_overlap(bbox, existing_bbox)
            # 额外检查：如果bbox不重叠，但起点很近，也算重叠
            # 起点在引线的第一段附近（bend_x, bend_y）
            bend_x_current = start_x + seg1_len * math.cos(math.radians(base_angle))
            bend_y_current = start_y + seg1_len * math.sin(math.radians(base_angle))
            # 已有标注的起点需要从bbox反推，或者直接检查bbox的min/max
            # 使用bbox中心作为近似
            existing_start_x = (
                existing_bbox[0] + existing_bbox[2]
            ) / 2 - 10  # 减去横线长度近似
            existing_start_y = (existing_bbox[1] + existing_bbox[3]) / 2 - 5
            start_distance = math.sqrt(
                (bend_x_current - existing_start_x) ** 2
                + (bend_y_current - existing_start_y) ** 2
            )

            if is_overlap or start_distance < 40:
                overlap = True
                break

        if not overlap:
            # 不重叠，直接使用
            # 返回格式: (angle, seg1_len, seg2_len, bbox)
            return (base_angle, seg1_len, seg2_len, bbox)

        # 检查与已有标注的Y坐标关系
        # 如果Y坐标接近（垂直同层），优先延长seg1_len让引线斜线错开
        y_vertical_overlap = False
        current_disease_y = start_y  # 默认用引线起点Y
        if disease_cad_coords:
            current_disease_y = disease_cad_coords[1]  # 使用病害CAD坐标Y

        print(
            f"    DEBUG y_vertical: current_disease_y={current_disease_y:.2f}, cache_size={len(LABEL_POSITIONS_CACHE)}"
        )

        for existing in LABEL_POSITIONS_CACHE:
            existing_bbox = existing[:4]
            existing_disease_coords = existing[5:7] if len(existing) > 6 else None
            if existing_disease_coords and disease_cad_coords:
                # 使用病害的CAD坐标来判断是否垂直同层
                existing_disease_y = existing_disease_coords[1]
                y_diff = abs(current_disease_y - existing_disease_y)
                print(
                    f"    DEBUG y_vertical: existing_y={existing_disease_y:.2f}, y_diff={y_diff:.2f}"
                )
                if y_diff < 1.0:  # 病害CAD坐标差值小于1视为垂直同层
                    y_vertical_overlap = True
                    break
            else:
                # 兼容旧格式：用bbox中间Y和start_y比较
                existing_mid_y = (existing_bbox[1] + existing_bbox[3]) / 2
                y_diff = abs(start_y - existing_mid_y)
                if y_diff < 10:
                    y_vertical_overlap = True
                    break

        print(f"    DEBUG y_vertical: y_vertical_overlap={y_vertical_overlap}")

        # 如果Y坐标垂直同层，延长seg1_len和seg2_len让水平线向右下角延伸
        # 这样水平线会出现在已有标注的右下方，从而分离
        print(
            f"    DEBUG: 检查条件 y_vo={y_vertical_overlap}, ba={base_angle}, horse={is_horsehoof}"
        )
        if y_vertical_overlap and base_angle in (225, 315) and not is_horsehoof:
            print(
                f"    DEBUG: 进入垂直同层处理, base_angle={base_angle}, seg1_len={seg1_len}, seg2_len={seg2_len}"
            )
            # 同时延长 seg1_len 和 seg2_len，让水平线向右下角延伸
            # 马蹄部件 seg2_len 上限为 40
            seg2_max = 40 if is_horsehoof else float("inf")
            for seg1_mult in [1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0]:
                for seg2_mult in [1.5, 2.0, 2.5]:
                    extended_seg1 = seg1_len * seg1_mult
                    extended_seg2 = min(seg2_len * seg2_mult, seg2_max)
                    extended_bbox = get_label_bbox(
                        start_x, start_y, base_angle, extended_seg1, extended_seg2
                    )
                    if check_in_bounds(extended_bbox, beam_level):
                        overlap_ext = False
                        for existing in LABEL_POSITIONS_CACHE:
                            existing_bbox = existing[:4]
                            is_overlap = check_bbox_overlap(
                                extended_bbox, existing_bbox
                            )
                            if is_overlap:
                                print(
                                    f"    DEBUG: seg1={extended_seg1:.1f}, seg2={extended_seg2:.1f} 重叠"
                                )
                                overlap_ext = True
                                break
                        if not overlap_ext:
                            print(
                                f"    DEBUG: 延长成功 seg1={extended_seg1:.1f}, seg2={extended_seg2:.1f}"
                            )
                            return (
                                base_angle,
                                extended_seg1,
                                extended_seg2,
                                extended_bbox,
                            )
                    else:
                        print(
                            f"    DEBUG: seg1={extended_seg1:.1f}, seg2={extended_seg2:.1f} 超出边界"
                        )
            # 无法解决，记录警告并返回None
            print(f"  警告: 垂直同层病害无法分离 ({start_x:.1f}, {start_y:.1f})")
            return None

        # 非垂直同层时，先尝试增加seg2_len（水平段长度）让标注在水平方向分开
        # 马蹄部件 seg2_len 上限为 40
        seg2_max = 40 if is_horsehoof else float("inf")
        for length_multiplier in [1.5, 2.0, 2.5, 3.0]:
            extended_seg2_len = min(seg2_len * length_multiplier, seg2_max)
            extended_bbox = get_label_bbox(
                start_x, start_y, base_angle, seg1_len, extended_seg2_len
            )
            if check_in_bounds(extended_bbox, beam_level):
                # 检查是否与现有标注重叠
                overlap_extended = False
                for existing in LABEL_POSITIONS_CACHE:
                    if check_bbox_overlap(extended_bbox, existing[:4]):
                        overlap_extended = True
                        break
                if not overlap_extended:
                    # 返回实际使用的seg2_len
                    return (base_angle, seg1_len, extended_seg2_len, extended_bbox)

        # 如果增加seg2_len不够，尝试增加seg1_len（斜线长度）让引线起点更远
        for seg1_multiplier in [1.5, 2.0, 2.5, 3.0, 4.0, 5.0]:
            extended_seg1 = seg1_len * seg1_multiplier
            extended_bbox = get_label_bbox(
                start_x, start_y, base_angle, extended_seg1, seg2_len
            )
            if check_in_bounds(extended_bbox, beam_level):
                overlap_ext = False
                for existing in LABEL_POSITIONS_CACHE:
                    if check_bbox_overlap(extended_bbox, existing[:4]):
                        overlap_ext = True
                        break
                if not overlap_ext:
                    return (base_angle, extended_seg1, seg2_len, extended_bbox)

        # 如果增加seg1_len仍无法解决，尝试同时延长seg1和seg2
        # 逻辑：
        #   斜向上(45°/135°)时：延长Y值更小的标注（文字更高，给更高的标注留出空间）
        #   斜向下(225°/315°)时：延长Y值更大的标注（文字更低，给更低的标注留出空间）
        is_upward = base_angle in (45, 135)  # 斜向上还是斜向下

        # 找到与当前病害Y值最接近的已有标注
        closest_existing = None
        min_y_diff = float("inf")

        for existing in LABEL_POSITIONS_CACHE:
            existing_bbox = existing[:4]
            existing_mid_y = (existing_bbox[1] + existing_bbox[3]) / 2
            y_diff = abs(start_y - existing_mid_y)
            if y_diff < min_y_diff:
                min_y_diff = y_diff
                closest_existing = existing

        # 判断当前病害相对于最近标注的位置，决定是否延长当前标注
        if closest_existing:
            existing_bbox = closest_existing[:4]
            existing_mid_y = (existing_bbox[1] + existing_bbox[3]) / 2
            current_higher = start_y > existing_mid_y  # 当前病害是否更高（Y值更大）

            # 斜向上(文字向上延伸)：更低的标注应该延长（文字更高）
            # 斜向下(文字向下延伸)：更高的标注应该延长（文字更低）
            if is_upward:
                # 斜向上时，延长Y值更小的（更低的标注）
                should_extend_current = not current_higher  # 当前更低 → 延长
            else:
                # 斜向下时，延长Y值更大的（更高的标注）
                should_extend_current = current_higher  # 当前更高 → 延长
        else:
            should_extend_current = True

        # 无论should_extend_current是什么，先尝试延长当前标注看看能否分开
        for seg1_multiplier in [1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0]:
            extended_seg1 = seg1_len * seg1_multiplier
            extended_bbox = get_label_bbox(
                start_x, start_y, base_angle, extended_seg1, seg2_len
            )
            if check_in_bounds(extended_bbox, beam_level):
                # 检查是否与现有标注重叠
                overlap_extended = False
                for existing in LABEL_POSITIONS_CACHE:
                    existing_bbox = existing[:4]
                    if check_bbox_overlap(extended_bbox, existing_bbox):
                        overlap_extended = True
                        break
                    # 检查起点距离
                    bend_x_ext = start_x + extended_seg1 * math.cos(
                        math.radians(base_angle)
                    )
                    bend_y_ext = start_y + extended_seg1 * math.sin(
                        math.radians(base_angle)
                    )
                    existing_start_x = (existing_bbox[0] + existing_bbox[2]) / 2 - 10
                    existing_start_y = (existing_bbox[1] + existing_bbox[3]) / 2 - 5
                    start_distance = math.sqrt(
                        (bend_x_ext - existing_start_x) ** 2
                        + (bend_y_ext - existing_start_y) ** 2
                    )
                    if start_distance < 40:
                        overlap_extended = True
                        break

                if not overlap_extended:
                    return (base_angle, extended_seg1, seg2_len, extended_bbox)

        # 延长当前标注后仍重叠，尝试翻转角度
        flip_bbox = get_label_bbox(start_x, start_y, flip_angle, seg1_len, seg2_len)
        if check_in_bounds(flip_bbox, beam_level):
            overlap_flip = False
            for existing in LABEL_POSITIONS_CACHE:
                if check_bbox_overlap(flip_bbox, existing[:4]):
                    overlap_flip = True
                    break
            if not overlap_flip:
                return (flip_angle, seg1_len, seg2_len, flip_bbox)

        # 翻转角度也重叠，尝试翻转+延长seg2
        for seg2_mult in [1.5, 2.0, 2.5, 3.0]:
            flip_bbox2 = get_label_bbox(
                start_x, start_y, flip_angle, seg1_len, seg2_len * seg2_mult
            )
            if check_in_bounds(flip_bbox2, beam_level):
                overlap_flip2 = False
                for existing in LABEL_POSITIONS_CACHE:
                    if check_bbox_overlap(flip_bbox2, existing[:4]):
                        overlap_flip2 = True
                        break
                if not overlap_flip2:
                    return (flip_angle, seg1_len, seg2_len * seg2_mult, flip_bbox2)

    # base_angle无法放置，尝试其他角度
    angles_to_try = [flip_angle]

    # 添加其他三个主要方向
    all_angles = [45, 135, 225, 315]
    for angle in all_angles:
        if angle not in angles_to_try and angle != base_angle:
            angles_to_try.append(angle)

    for angle in angles_to_try[:max_attempts]:
        bbox = get_label_bbox(start_x, start_y, angle, seg1_len, seg2_len)

        # 检查是否在范围内
        if not check_in_bounds(bbox, beam_level):
            continue

        # 检查是否与已有标注重叠
        overlap = False
        for existing in LABEL_POSITIONS_CACHE:
            existing_bbox = existing[:4]
            if check_bbox_overlap(bbox, existing_bbox):
                overlap = True
                break

        if overlap:
            continue

        # 检查角度差
        angle_conflict = False
        for existing in LABEL_POSITIONS_CACHE:
            existing_bbox = existing[:4]
            existing_angle = existing[4] if len(existing) > 4 else None

            if existing_angle is None:
                continue

            existing_start_x = (existing_bbox[0] + existing_bbox[2]) / 2
            existing_start_y = (existing_bbox[1] + existing_bbox[3]) / 2
            distance = math.sqrt(
                (start_x - existing_start_x) ** 2 + (start_y - existing_start_y) ** 2
            )

            if distance < 50:
                angle_diff = abs(angle - existing_angle)
                if angle_diff > 180:
                    angle_diff = 360 - angle_diff

                if angle_diff < 90:
                    angle_conflict = True
                    break

        if angle_conflict:
            continue

        return (angle, seg1_len, seg2_len, bbox)

    return None


def load_peel_off_geometry():
    """从剥落图例模板加载原始几何数据"""
    global PEEL_OFF_GEOMETRY
    if PEEL_OFF_GEOMETRY is not None:
        return PEEL_OFF_GEOMETRY

    doc = ezdxf.readfile(PEEL_LEGEND_FILE)
    block = doc.blocks.get("adfsd")

    # 提取所有实体数据
    lines = []
    polyline = []

    for entity in block:
        if entity.dxftype() == "LINE":
            lines.append(
                {
                    "start": (entity.dxf.start[0], entity.dxf.start[1]),
                    "end": (entity.dxf.end[0], entity.dxf.end[1]),
                }
            )
        elif entity.dxftype() == "LWPOLYLINE":
            pts = list(entity.get_points())
            polyline = [(p[0], p[1]) for p in pts]

    # 计算边界框
    all_points = []
    for line in lines:
        all_points.extend([line["start"], line["end"]])
    all_points.extend(polyline)

    if all_points:
        xs = [p[0] for p in all_points]
        ys = [p[1] for p in all_points]
        bbox = {"min_x": min(xs), "max_x": max(xs), "min_y": min(ys), "max_y": max(ys)}
    else:
        bbox = {"min_x": 0, "max_x": 1, "min_y": 0, "max_y": 1}

    PEEL_OFF_GEOMETRY = {"lines": lines, "polyline": polyline, "bbox": bbox}
    return PEEL_OFF_GEOMETRY


def load_rebar_geometry():
    """从钢筋锈蚀模板加载原始几何数据"""
    global REBAR_GEOMETRY
    if REBAR_GEOMETRY is not None:
        return REBAR_GEOMETRY

    doc = ezdxf.readfile(REBAR_LEGEND_FILE)
    msp = doc.modelspace()

    # 提取所有实体数据
    lines = []
    polylines = []

    for entity in msp:
        if entity.dxftype() == "LINE":
            lines.append(
                {
                    "start": (entity.dxf.start[0], entity.dxf.start[1]),
                    "end": (entity.dxf.end[0], entity.dxf.end[1]),
                }
            )
        elif entity.dxftype() == "LWPOLYLINE":
            pts = list(entity.get_points())
            polylines.append([(p[0], p[1]) for p in pts])

    # 计算边界框
    all_points = []
    for line in lines:
        all_points.extend([line["start"], line["end"]])
    for pl in polylines:
        all_points.extend(pl)

    if all_points:
        xs = [p[0] for p in all_points]
        ys = [p[1] for p in all_points]
        bbox = {"min_x": min(xs), "max_x": max(xs), "min_y": min(ys), "max_y": max(ys)}
    else:
        bbox = {"min_x": 0, "max_x": 1, "min_y": 0, "max_y": 1}

    REBAR_GEOMETRY = {"lines": lines, "polylines": polylines, "bbox": bbox}
    return REBAR_GEOMETRY


# 各部件原点坐标（模板坐标系）- 2026-03-23 更新
BEAM_ORIGINS = {
    "upper": {  # 上方T梁（1-1号，奇数梁）
        "梁底": (84, 262),  # Y方向: 从上到下
        "左翼缘板": (84, 284.4),  # Y方向: 从下到上
        "右翼缘板": (84, 234.4),  # Y方向: 从上到下
        "左腹板": (84, 284.4),  # Y方向: 从上到下
        "右腹板": (84, 234.4),  # Y方向: 从下到上
        "马蹄左侧面": (84, 266),  # 只有X坐标，从左到右
        "马蹄右侧面": (84, 253),  # 只有X坐标，从左到右
    },
    "lower": {  # 下方T梁（1-2号，偶数梁）
        "梁底": (83.8, 150),  # Y方向: 从上到下
        "左翼缘板": (83.8, 172),  # Y方向: 从下到上
        "右翼缘板": (83.8, 122),  # Y方向: 从上到下
        "左腹板": (83.8, 172),  # Y方向: 从上到下
        "右腹板": (83.8, 122),  # Y方向: 从下到上
        "马蹄左侧面": (84, 153),  # 只有X坐标，从左到右
        "马蹄右侧面": (84, 141),  # 只有X坐标，从左到右
    },
}


def get_part_origin(part_type: str, specific_part: str) -> tuple:
    origins = BEAM_ORIGINS.get(part_type, BEAM_ORIGINS["upper"])
    return origins.get(specific_part, origins["梁底"])


# 各部件Y方向定义（从上到下 = Y值减小，从下到上 = Y值增大）
PART_Y_DIRECTION = {
    # 上方T梁（1-1号）
    "upper": {
        "梁底": "从上到下",  # Y值减小（相对坐标从上到下，原点在梁顶上方）
        "左翼缘板": "从下到上",  # Y值增大
        "右翼缘板": "从上到下",  # Y值减小（靠近T梁中心）
        "左腹板": "从下到上",  # Y值增大
        "右腹板": "从下到上",  # Y值增大
        "马蹄左侧面": "从左到右",  # 只有X方向
        "马蹄右侧面": "从左到右",  # 只有X方向
    },
    # 下方T梁（1-2号）
    "lower": {
        "梁底": "从上到下",  # Y值减小（相对坐标从上到下，原点在梁顶上方）
        "左翼缘板": "从下到上",  # Y值增大
        "右翼缘板": "从上到下",  # Y值减小（靠近T梁中心）
        "左腹板": "从下到上",  # Y值增大
        "右腹板": "从下到上",  # Y值增大
        "马蹄左侧面": "从左到右",  # 只有X方向
        "马蹄右侧面": "从左到右",  # 只有X方向
    },
}


def convert_to_cad_coords(
    x: float,
    y: float,
    origin: tuple,
    specific_part: str = "",
    beam_level: str = "upper",
) -> tuple:
    """将病害坐标转换为CAD坐标（T梁专用）

    T梁坐标换算：
    - X方向：1m = 10坐标
    - Y方向：1m = 9.73坐标（2.25m = 21.9坐标）

    Args:
        x: 病害x坐标（米）
        y: 病害y坐标（米）
        origin: 部件原点CAD坐标
        specific_part: 具体部件名称
        beam_level: 'upper'（上方T梁/奇数梁）或 'lower'（下方T梁/偶数梁）

    Returns:
        (cad_x, cad_y)
    """
    # T梁坐标换算系数
    X_SCALE = 10  # X方向：1m = 10坐标
    Y_SCALE = 9.73  # Y方向：1m = 9.73坐标（2.25m = 21.9坐标）

    origin_x, origin_y = origin
    # X方向：统一从左到右
    cad_x = origin_x + x * X_SCALE

    # Y方向：根据部件和T梁位置决定
    direction = PART_Y_DIRECTION.get(beam_level, {}).get(specific_part, "从上到下")
    if direction == "从左到右":
        # 马蹄左侧面/右侧面：虽然主要是X方向，但也需要支持y参数（用于设置高度）
        # y_start=0, y_end=0.2 表示从原点向上0.2m范围
        if y > 0:
            # 有y坐标，用作高度范围
            cad_y = origin_y + y * Y_SCALE
        else:
            # 无y坐标，默认原点
            cad_y = origin_y
    elif direction == "从下到上":
        # 从下到上：y越大，CAD Y越大（原点是最下方）
        cad_y = origin_y + y * Y_SCALE
    else:
        # 从上到下：y越大，CAD Y越小（原点是最上方）
        cad_y = origin_y - y * Y_SCALE

    return (cad_x, cad_y)


def get_disease_draw_method(specific_part: str) -> str:
    """判断病害应该在哪个区域绘制（上半部分还是下半部分）

    注意：这个函数的返回值现在与T梁左右位置无关
    只用于决定病害在T梁内部是画在上方还是下方
    """
    # 上方区域：翼缘板、腹板、马蹄（在T梁的上方）
    upper_parts = [
        "左翼缘板",
        "右翼缘板",
        "左腹板",
        "右腹板",
        "马蹄左侧面",
        "马蹄右侧面",
    ]
    # 下方区域：梁底、齿块（在T梁的下方）
    lower_parts = ["梁底", "右侧齿块", "左侧齿块", "右侧面", "左侧面"]

    if specific_part in upper_parts:
        return "upper"
    elif specific_part in lower_parts:
        return "lower"
    else:
        return "lower"  # 默认下方


def get_beam_side_from_part(specific_part: str, x_start: float) -> str:
    """判断病害应该画在左侧T梁还是右侧T梁

    根据具体部件判断：
    - 左翼缘板、左腹板、马蹄左侧面 → 左侧T梁
    - 右翼缘板、右腹板、马蹄右侧面 → 右侧T梁
    - 梁底：根据x坐标判断（x < 20m → 左侧T梁，x >= 20m → 右侧T梁）
      因为40mT梁的每个T梁宽度约40m
    """
    if "左翼" in specific_part or "左腹" in specific_part or "马蹄左" in specific_part:
        return "left"
    elif (
        "右翼" in specific_part or "右腹" in specific_part or "马蹄右" in specific_part
    ):
        return "right"
    elif "梁底" in specific_part:
        # 梁底根据x坐标判断
        # 左侧T梁 x: 0-40m，右侧T梁 x: 40-80m
        # 阈值为20m
        if x_start < 20:
            return "left"
        else:
            return "right"
    else:
        return "left"  # 默认左侧


def pair_components(components: list) -> list:
    pairs = []
    for i in range(0, len(components), 2):
        if i + 1 < len(components):
            pairs.append([components[i], components[i + 1]])
        else:
            pairs.append([components[i]])
    return pairs


def update_text_in_msp(
    msp, old_text: str, new_text: str, height: float = None, bold: bool = None
):
    """替换模型空间中的文字（处理TEXT和MTEXT类型）

    Args:
        msp: 模型空间
        old_text: 要替换的旧文本
        new_text: 替换后的新文本
        height: 可选，设置文字高度（默认不改变）
        bold: 可选，设置粗体（默认不改变）
    """
    for entity in msp:
        if entity.dxftype() == "TEXT":
            if old_text in entity.dxf.text:
                entity.dxf.text = entity.dxf.text.replace(old_text, new_text)
                if height is not None:
                    entity.dxf.height = height
                if bold is not None:
                    entity.dxf.bold = bold
        elif entity.dxftype() == "MTEXT":
            # MTEXT内容可能带格式代码，如 {\C0;LLL}
            content = entity.text
            if old_text in content:
                # 替换整个MTEXT内容（包括格式代码）
                # 如果内容是 {\C0;LLL}，替换后变成 {\C0;实际内容}
                if content.strip().startswith("{\\") and old_text in content:
                    # 提取格式代码部分
                    import re

                    match = re.match(r"^(\{[^}]+\;)(.*)(\})$", content)
                    if match:
                        prefix = match.group(1)
                        suffix = match.group(3)
                        new_content = (
                            prefix
                            + content.replace(old_text, new_text)
                            .replace(prefix, "")
                            .replace(suffix, "")
                            + suffix
                        )
                        # 简化处理：直接替换
                        entity.text = content.replace(old_text, new_text)
                    else:
                        entity.text = content.replace(old_text, new_text)
                else:
                    entity.text = content.replace(old_text, new_text)
                if height is not None:
                    # MTEXT使用char_height属性
                    entity.dxf.char_height = height
                if bold is not None and bold:
                    # MTEXT粗体通过格式代码设置，添加 \B;
                    if not content.startswith("{\\B;"):
                        # 在现有格式代码前添加粗体代码
                        import re

                        match = re.match(r"^(\{[^;]+\;)(.*)", content)
                        if match:
                            entity.text = "{\\B;" + content
                        else:
                            entity.text = "{\\B;" + content + "}"


def draw_polyline_leader(
    msp,
    start_x: float,
    start_y: float,
    seg2_len: float,
    angle: float = 45,
    seg1_len: float = 8,
):
    """绘制折线引线

    结构：起点(紧贴图例角点) -> 斜线段(seg1_len单位) -> 折点 -> 水平横线(seg2_len长度) -> 终点

    规则：向哪里倾斜，水平横线就向哪里（同向延伸）
    - 45°（右上）：斜线向右上 → 水平线向右
    - 135°（左上）：斜线向左上 → 水平线向左
    - 225°（左下）：斜线向左下 → 水平线向左
    - 315°（右下）：斜线向右下 → 水平线向右

    Args:
        seg2_len: 第二段水平长度
        angle: 第一段角度（度），0=右，90=上，180=左，270=下
               45=右上，135=左上，225=左下，315=右下
        seg1_len: 第一段斜线长度，默认8，网状裂缝/裂缝群使用16

    Returns:
        (bend_x, bend_y, end_x, end_y)
    """
    angle_rad = math.radians(angle)

    # 计算折点位置（第一段斜线终点）
    bend_x = start_x + seg1_len * math.cos(angle_rad)
    bend_y = start_y + seg1_len * math.sin(angle_rad)

    # 第二段水平横线方向：向哪里倾斜，水平线就向哪里
    # 45°和315°（向右倾斜）：水平线向右
    # 135°和225°（向左倾斜）：水平线向左
    if angle == 45 or angle == 315:
        # 向右倾斜，水平线向右延伸
        end_x = bend_x + seg2_len
    else:
        # 向左倾斜（135°、225°），水平线向左延伸
        end_x = bend_x - seg2_len
    end_y = bend_y

    points = [(start_x, start_y), (bend_x, bend_y), (end_x, end_y)]
    msp.add_lwpolyline(points=points, dxfattribs={"color": 7})

    return (bend_x, bend_y, end_x, end_y)


def get_leader_start_point(cad_x1, cad_y1, cad_x2, cad_y2, angle):
    """根据角度获取引线起点（紧贴图例的对应角点）

    Args:
        cad_x1, cad_y1: 病害区域左上角
        cad_x2, cad_y2: 病害区域右下角
        angle: 引线角度

    Returns:
        (start_x, start_y)
    """
    # 确保坐标顺序
    left = min(cad_x1, cad_x2)
    right = max(cad_x1, cad_x2)
    top = max(cad_y1, cad_y2)
    bottom = min(cad_y1, cad_y2)

    # 根据角度选择角点
    if angle == 45:  # 右上
        return (right, top)
    elif angle == 135:  # 左上
        return (left, top)
    elif angle == 225:  # 左下
        return (left, bottom)
    elif angle == 315:  # 右下
        return (right, bottom)
    else:
        # 默认使用右上角
        return (right, top)


def draw_disease_label_with_angle(
    msp,
    disease_type: str,
    value_text: str,
    start_x: float,
    start_y: float,
    seg2_len: float = None,
    angle: float = 45,
    seg1_len: float = 8,
):
    """绘制病害标注（支持指定角度）

    引线结构：起点(紧贴图例角点) -> 斜线段(seg1_len单位) -> 折点 -> 水平横线 -> 终点
    文字位置：在水平横线上方和下方，水平线长度根据文字长度自动调整

    Args:
        seg2_len: 第二段水平线长度，若为None则自动计算
        angle: 第一段斜线角度（度）
        seg1_len: 第一段斜线长度，默认8，网状裂缝/裂缝群使用16
    """
    text_height = 2.5

    # 计算文字所需的最小宽度
    # 假设每个汉字/字符宽度约为 text_height * 0.8
    char_width = text_height * 0.8
    disease_text_width = len(disease_type) * char_width
    value_text_width = len(value_text) * char_width if value_text else 0
    # 取两个文字中最长的那个
    max_text_width = max(disease_text_width, value_text_width)

    # 如果未提供seg2_len，则根据文字长度自动计算
    if seg2_len is None:
        # 横线长度 = 文字最大宽度 + 四个文字的宽度（作为边距）
        # 这样横线会比文字长一些，看起来更加美观
        extra_width = 4 * char_width  # 四个文字的宽度作为边距
        seg2_len = max_text_width + extra_width
        # 最小长度保证
        seg2_len = max(seg2_len, 10)

    bend_x, bend_y, end_x, end_y = draw_polyline_leader(
        msp, start_x, start_y, seg2_len, angle, seg1_len
    )

    mid_y = bend_y  # 水平线y坐标相同

    # 计算文字在横线上的居中位置
    # 文字起始位置 = 横线起始位置 + (横线长度 - 文字宽度) / 2
    if angle == 45 or angle == 315:  # x轴中心线左方，向右倾斜
        # 横线从bend_x开始，向右延伸
        text_start_x = bend_x + (seg2_len - disease_text_width) / 2

        # 病害名称位置（在水平线上方）
        text_y = mid_y + text_height * 0.5
        msp.add_text(
            disease_type,
            dxfattribs={
                "insert": (text_start_x, text_y),
                "height": text_height,
                "color": 7,
            },
        )

        if value_text:
            # 数值位置（在水平线下方）
            value_x = bend_x + (seg2_len - value_text_width) / 2
            value_y = mid_y - text_height * 1.5
            msp.add_text(
                value_text,
                dxfattribs={
                    "insert": (value_x, value_y),
                    "height": text_height,
                    "color": 7,
                },
            )
    else:  # angle == 135 or angle == 225，x轴中心线右方，向左倾斜
        # 文字从横线终点开始，从左向右写
        # 文字开始位置与横线终点对齐（x值小的那个点）
        text_start_x = end_x  # 直接使用横线终点作为文字开始位置

        # 病害名称位置（在水平线上方）
        text_y = mid_y + text_height * 0.5
        msp.add_text(
            disease_type,
            dxfattribs={
                "insert": (text_start_x, text_y),
                "height": text_height,
                "color": 7,
            },
        )

        if value_text:
            # 数值位置（在水平线下方）
            value_x = end_x  # 直接使用横线终点作为文字开始位置
            value_y = mid_y - text_height * 1.5
            msp.add_text(
                value_text,
                dxfattribs={
                    "insert": (value_x, value_y),
                    "height": text_height,
                    "color": 7,
                },
            )

    return (bend_x, bend_y, end_x, end_y)


def draw_crack(
    msp,
    x_start: float,
    x_end: float,
    y: float,
    origin: tuple,
    specific_part: str = "",
    beam_level: str = "upper",
):
    """绘制单条裂缝（手绘风格）"""
    cad_x1, cad_y1 = convert_to_cad_coords(
        x_start, y, origin, specific_part, beam_level
    )
    cad_x2, cad_y2 = convert_to_cad_coords(x_end, y, origin, specific_part, beam_level)

    points = []
    x = cad_x1
    step = 0.8
    while x <= cad_x2:
        offset_y = math.sin((x - cad_x1) / 3) * 0.15 + random.uniform(-0.1, 0.1)
        points.append((x, cad_y1 + offset_y))
        x += step
    points.append((cad_x2, cad_y1))

    msp.add_lwpolyline(points=points, dxfattribs={"color": 7})


def draw_crack_group(
    msp,
    x_start: float,
    x_end: float,
    count: int,
    origin: tuple,
    specific_part: str = "",
    beam_level: str = "upper",
):
    """绘制裂缝群"""
    cad_x1, cad_y1 = convert_to_cad_coords(
        x_start, 0, origin, specific_part, beam_level
    )
    cad_x2, cad_y2 = convert_to_cad_coords(x_end, 0, origin, specific_part, beam_level)

    for i in range(count):
        y_offset = i * 1.0 + 0.5

        points = []
        x = cad_x1
        step = 0.8
        while x <= cad_x2:
            offset_y = math.sin((x - cad_x1) / 3) * 0.15 + random.uniform(-0.1, 0.1)
            points.append((x, cad_y1 - y_offset + offset_y))
            x += step
        points.append((cad_x2, cad_y1 - y_offset))

        msp.add_lwpolyline(points=points, dxfattribs={"color": 7})


def draw_mesh_crack(
    msp,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    origin: tuple,
    specific_part: str = "",
    beam_level: str = "upper",
):
    """绘制网状裂缝（波浪线填充）"""
    cad_x1, cad_y1 = convert_to_cad_coords(x1, y1, origin, specific_part, beam_level)
    cad_x2, cad_y2 = convert_to_cad_coords(x2, y2, origin, specific_part, beam_level)

    # 确保 cad_x1 < cad_x2
    if cad_x1 > cad_x2:
        cad_x1, cad_x2 = cad_x2, cad_x1

    wave_length = 4
    wave_amp = 0.3
    line_spacing = 1

    # 计算波浪线覆盖的高度（取绝对值）
    height = abs(cad_y2 - cad_y1)
    num_lines = max(1, int(height / line_spacing) + 1)

    # 确定Y的范围（从较大值到较小值，即从上到下）
    y_top = max(cad_y1, cad_y2)
    y_bottom = min(cad_y1, cad_y2)

    for i in range(num_lines):
        y = y_top - i * line_spacing
        points = []
        x = cad_x1
        while x <= cad_x2 + wave_length:
            phase = (x - cad_x1) / wave_length * 2 * math.pi
            wave_y = y + math.sin(phase) * wave_amp
            points.append((x, wave_y))
            x += 0.2
        msp.add_lwpolyline(points=points, dxfattribs={"color": 7})


def draw_honeycomb(
    msp,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    origin: tuple,
    specific_part: str = "",
    beam_level: str = "upper",
    return_bbox: bool = False,
    area: float = None,
):
    """绘制蜂窝麻面图例（平铺复制modelspace实体填满整个区域）

    T梁坐标换算：
    - X方向：1m = 10坐标
    - Y方向：1m = 9.73坐标

    Args:
        x1, y1: 病害区域起点（m）
        x2, y2: 病害区域终点（m）
        origin: CAD原点（病害坐标系原点）
        specific_part: 具体部件名称
        beam_level: 'upper' 或 'lower'
        return_bbox: 若为True，返回实际绘制区域的边界框
        area: 病害实际面积（m²），用于计算合适的缩放比例

    Returns:
        实际边界框 (min_x, min_y, max_x, max_y) 或 None
    """
    from ezdxf.bbox import extents
    from ezdxf.math import Matrix44
    import math

    # 坐标转换
    X_SCALE = 10
    Y_SCALE = 9.73

    origin_x, origin_y = origin

    # 确定Y方向
    direction = PART_Y_DIRECTION.get(beam_level, {}).get(specific_part, "从上到下")
    if direction == "从下到上":
        cad_x1 = origin_x + x1 * X_SCALE
        cad_y1 = origin_y + y1 * Y_SCALE
        cad_x2 = origin_x + x2 * X_SCALE
        cad_y2 = origin_y + y2 * Y_SCALE
    elif direction == "从上到下":
        cad_x1 = origin_x + x1 * X_SCALE
        cad_y1 = origin_y - y1 * Y_SCALE
        cad_x2 = origin_x + x2 * X_SCALE
        cad_y2 = origin_y - y2 * Y_SCALE
    elif direction == "从左到右":
        # 马蹄等情况
        cad_x1 = origin_x + x1 * X_SCALE
        cad_y1 = origin_y + y1 * Y_SCALE
        cad_x2 = origin_x + x2 * X_SCALE
        cad_y2 = origin_y + y2 * Y_SCALE
    else:
        cad_x1 = origin_x + x1 * X_SCALE
        cad_y1 = origin_y + y1 * Y_SCALE
        cad_x2 = origin_x + x2 * X_SCALE
        cad_y2 = origin_y + y2 * Y_SCALE

    # 确保顺序
    if cad_x1 > cad_x2:
        cad_x1, cad_x2 = cad_x2, cad_x1
    if cad_y1 > cad_y2:
        cad_y1, cad_y2 = cad_y2, cad_y1

    dst_w = cad_x2 - cad_x1
    dst_h = cad_y2 - cad_y1

    # 加载蜂窝麻面图例文件
    legend_doc = ezdxf.readfile("./templates/病害图例/蜂窝麻面.dxf")
    legend_msp = legend_doc.modelspace()

    # 获取图例边界框（排除文字MTEXT）
    non_text_entities = [e for e in legend_msp if e.dxftype() not in ["TEXT", "MTEXT"]]
    legend_bbox = extents(non_text_entities)
    src_w = legend_bbox.extmax[0] - legend_bbox.extmin[0]
    src_h = legend_bbox.extmax[1] - legend_bbox.extmin[1]

    # 根据面积计算缩放比例，使图标大小反映病害实际大小
    # 病害区域物理尺寸（m）
    physical_width = abs(x2 - x1)
    physical_height = abs(y2 - y1)
    physical_area = physical_width * physical_height

    if area and area > 0:
        # 根据面积比例计算缩放：面积越大，图标越大
        # 基准：0.4m²对应scale=1.0（比较合理的大小）
        # 面积与缩放比例成正比
        base_area = 0.4  # 基准面积
        scale = (area / base_area) * 0.8
        # 限制缩放范围：最小0.3，最大3.0
        scale = max(0.3, min(3.0, scale))
    else:
        # 无面积信息时使用默认缩放
        scale = 1.5

    scaled_w = src_w * scale
    scaled_h = src_h * scale

    # 图例左下角（最小坐标）
    src_min_x = legend_bbox.extmin[0]
    src_min_y = legend_bbox.extmin[1]

    # 计算平铺数量
    n_cols = max(1, math.floor(dst_w / scaled_w))
    n_rows = max(1, math.floor(dst_h / scaled_h))

    start_x = cad_x1
    start_y = cad_y1

    # 平铺复制
    entity_count = 0
    for row in range(n_rows):
        for col in range(n_cols):
            tile_x = start_x + col * scaled_w
            tile_y = start_y + row * scaled_h

            dx = tile_x - src_min_x * scale
            dy = tile_y - src_min_y * scale
            transform = Matrix44(
                [scale, 0, 0, 0, 0, scale, 0, 0, 0, 0, 1, 0, dx, dy, 0, 1]
            )

            for entity in legend_msp:
                dxftype = entity.dxftype()
                if dxftype == "MTEXT":
                    continue
                try:
                    new_entity = entity.copy()
                    new_entity.transform(transform)
                    msp.add_entity(new_entity)
                    entity_count += 1
                except Exception as e:
                    pass

    # 返回平铺后的实际边界框
    actual_min_x = start_x
    actual_max_x = start_x + n_cols * scaled_w
    actual_min_y = start_y
    actual_max_y = start_y + n_rows * scaled_h

    if return_bbox:
        return (actual_min_x, actual_min_y, actual_max_x, actual_max_y)
    return None


def draw_peel_off_with_rebar(
    msp,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    origin: tuple,
    specific_part: str = "",
    beam_level: str = "upper",
    return_bbox: bool = False,
):
    """绘制剥落露筋 = 剥落不规则图形 + 叠加红色虚线交叉格栅

    Args:
        return_bbox: 若为True，返回实际绘制区域的边界框 (ax1, ay1, ax2, ay2)
    """
    # 第一步：先画剥落的不规则图形，同时获取实际绘制范围
    actual_bbox = draw_peel_off(
        msp, x1, y1, x2, y2, origin, specific_part, beam_level, return_bbox=True
    )

    if actual_bbox is None:
        return None

    # 第二步：用剥落图形的实际边界框范围叠加红色虚线格栅
    ax1, ay1, ax2, ay2 = actual_bbox  # ax1<ax2, ay2<ay1（ay1为上，ay2为下）
    height = ay1 - ay2
    width = ax2 - ax1

    grid_color = 1
    for i in range(1, 4):
        y = ay2 + height * i / 4
        msp.add_line(
            (ax1, y), (ax2, y), dxfattribs={"color": grid_color, "linetype": "DASHED"}
        )
    for i in range(1, 4):
        x = ax1 + width * i / 4
        msp.add_line(
            (x, ay2), (x, ay1), dxfattribs={"color": grid_color, "linetype": "DASHED"}
        )

    if return_bbox:
        return actual_bbox
    return None


def draw_peel_off(
    msp,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    origin: tuple,
    specific_part: str = "",
    beam_level: str = "upper",
    return_bbox: bool = False,
):
    """绘制剥落图例（原封不动从模板提取）

    Args:
        return_bbox: 若为True，返回实际绘制区域的边界框 (ax1, ay1, ax2, ay2)，ay1为上，ay2为下
    """
    cad_x1, cad_y1 = convert_to_cad_coords(x1, y1, origin, specific_part, beam_level)
    cad_x2, cad_y2 = convert_to_cad_coords(x2, y2, origin, specific_part, beam_level)

    # 确保 cad_x1 < cad_x2, cad_y2 < cad_y1
    if cad_x1 > cad_x2:
        cad_x1, cad_x2 = cad_x2, cad_x1
    if cad_y2 > cad_y1:
        cad_y1, cad_y2 = cad_y2, cad_y1

    # 计算目标尺寸
    target_width = cad_x2 - cad_x1
    target_height = cad_y1 - cad_y2

    # 加载剥落图例原始数据
    geometry = load_peel_off_geometry()
    bbox = geometry["bbox"]

    # 计算原始图形的边界框尺寸
    orig_width = bbox["max_x"] - bbox["min_x"]
    orig_height = bbox["max_y"] - bbox["min_y"]

    # 计算缩放比例
    scale_x = target_width / orig_width if orig_width > 0 else 1
    scale_y = target_height / orig_height if orig_height > 0 else 1

    # 使用统一的缩放比例（取较小的以保持比例）
    scale = min(scale_x, scale_y)

    # 计算偏移量，使图形居中对齐
    offset_x = cad_x1 - bbox["min_x"] * scale
    offset_y = cad_y2 - bbox["min_y"] * scale

    # 绘制线条（模拟锯齿边缘）
    for line in geometry["lines"]:
        start_x = line["start"][0] * scale + offset_x
        start_y = line["start"][1] * scale + offset_y
        end_x = line["end"][0] * scale + offset_x
        end_y = line["end"][1] * scale + offset_y
        msp.add_line((start_x, start_y), (end_x, end_y), dxfattribs={"color": 7})

    # 绘制多边形（剥落主体）
    if geometry["polyline"]:
        points = [
            (p[0] * scale + offset_x, p[1] * scale + offset_y)
            for p in geometry["polyline"]
        ]
        msp.add_lwpolyline(points=points, dxfattribs={"color": 7})

    if return_bbox:
        # 返回实际绘制的边界框（缩放后的bbox + offset）
        actual_x1 = bbox["min_x"] * scale + offset_x
        actual_x2 = bbox["max_x"] * scale + offset_x
        actual_y2 = bbox["min_y"] * scale + offset_y  # 下边
        actual_y1 = bbox["max_y"] * scale + offset_y  # 上边
        return (actual_x1, actual_y1, actual_x2, actual_y2)


def process_disease_record(msp, record: dict, comp_id: str, beam_level: str):
    """处理单条病害记录（带防重叠标注）

    Args:
        msp: 模型空间
        record: 病害记录
        comp_id: 构件编号
        beam_level: T梁层级 ('upper' 或 'lower')，由pair中的位置决定
                    - pair[0] = 上方T梁 (b-b断面)
                    - pair[1] = 下方T梁 (a-a断面)
    """
    global LABEL_POSITIONS_CACHE

    specific_part = record.get("具体部件", "梁底")
    disease_type = record.get("病害类型", "")

    # 马蹄部件的标注前面加"马蹄"两个字
    is_horse_hoof = "马蹄" in specific_part
    disease_type_display = f"马蹄{disease_type}" if is_horse_hoof else disease_type

    # 泛白不绘制也不标注
    if "泛白" in disease_type:
        return
    x_start = record.get("x_start", 0)
    x_end = record.get("x_end", 0)
    y_start = record.get("y_start", 0)
    y_end = record.get("y_end", 0)
    length = record.get("length", 0)
    width = record.get("width", 0)
    area = record.get("area", 0)
    count = record.get("count", 0)
    spacing = record.get("spacing", 0)

    # 根据具体部件确定绘图区域（翼缘板/腹板在T梁上方，梁底在下方）
    part_type = get_disease_draw_method(specific_part)
    origin = get_part_origin(beam_level, specific_part)

    # 齿块不绘制病害
    if "齿块" in specific_part:
        return

    # 马蹄左侧面/右侧面：只有X坐标，Y坐标固定
    is_horse_hoof = "马蹄左" in specific_part or "马蹄右" in specific_part

    # 马蹄侧面：如果y坐标为0（Excel中没有y坐标），给一个默认高度
    if is_horse_hoof and y_start == 0 and y_end == 0:
        y_start = 0.0  # 0.0-0.2m范围 = 0.2m总高度
        y_end = 0.2

    cad_x1, cad_y1 = convert_to_cad_coords(
        x_start, y_start, origin, specific_part, beam_level
    )
    cad_x2, cad_y2 = convert_to_cad_coords(
        x_end, y_end, origin, specific_part, beam_level
    )

    # 马蹄部件：只有X坐标，Y坐标固定，病害区域用固定高度表示
    if is_horse_hoof:
        cad_y1 = cad_y1 - 2.5  # 向上扩展2.5
        cad_y2 = cad_y2 + 2.5  # 向下扩展2.5

    # 获取部件标注基础角度（根据位置动态计算）
    # 使用病害区域x中点坐标计算角度，避免x区间跨越分界线时判断错误
    cad_x_mid = (cad_x1 + cad_x2) / 2
    cad_y_mid = (cad_y1 + cad_y2) / 2
    print(
        f"    DEBUG: {specific_part}, beam={beam_level}, cad_x_mid={cad_x_mid:.1f}, cad_y_mid={cad_y_mid:.1f}"
    )
    base_angle = get_label_angle(specific_part, beam_level, cad_x_mid, cad_y_mid)
    print(f"    DEBUG: angle={base_angle}")

    # 定义翻转角度（用于防重叠时尝试）
    # 翻转规则：水平线延伸方向取反
    # 45度（右上，水平向右）-> 225度（左下，水平向左）
    # 135度（左上，水平向左）-> 315度（右下，水平向右）
    # 225度（左下，水平向左）-> 45度（右上，水平向右）
    # 315度（右下，水平向右）-> 135度（左上，水平向左）
    if base_angle == 45:
        flip_angle = 225  # 右上 -> 左下
    elif base_angle == 135:
        flip_angle = 315  # 左上 -> 右下
    elif base_angle == 225:
        flip_angle = 45  # 左下 -> 右上
    elif base_angle == 315:
        flip_angle = 135  # 右下 -> 左上（水平延伸方向取反：右->左）
    else:
        flip_angle = (base_angle + 180) % 360

    # 根据角度获取引线起点（紧贴图例的对应角点）
    leader_start = get_leader_start_point(cad_x1, cad_y1, cad_x2, cad_y2, base_angle)

    # 估算水平线长度用于防重叠检测
    char_width = 2.5 * 0.8
    # 基于最终显示的文字长度计算
    display_text = f"{disease_type_display} S={area:.2f}m²"
    value_text = (
        f"W={width:.2f}mm"
        if width > 0
        else f"间距{spacing:.2f}m"
        if spacing > 0
        else ""
    )
    max_text_length = max(len(display_text), len(value_text))
    text_width = max_text_length * char_width
    seg2_len_estimate = max(text_width + 10, 15)
    # 马蹄部件横线长度限制在30以内
    if is_horse_hoof:
        seg2_len_estimate = min(seg2_len_estimate, 30)
    seg1_len_estimate = 8  # 初始斜线长度

    # 检查是否与之前的标注重叠，如果很近，则增加x坐标较大的病害的引线长度
    current_x = (cad_x1 + cad_x2) / 2  # 当前病害的x中心
    current_y = (cad_y1 + cad_y2) / 2  # 当前病害的y中心

    # 遍历之前的标注，检查是否有近距离的病害
    for i, existing in enumerate(LABEL_POSITIONS_CACHE):
        if len(existing) >= 4:
            # 计算现有标注的边界框
            existing_bbox = existing[:4]
            existing_min_x = existing_bbox[0]
            existing_max_x = existing_bbox[2]
            existing_min_y = existing_bbox[1]
            existing_max_y = existing_bbox[3]

            # 计算现有标注的中心位置
            existing_center_x = (existing_min_x + existing_max_x) / 2

            # 检查当前病害是否与现有标注的边界框重叠或距离很近
            # 计算病害中心与现有标注边界框的最小距离
            closest_x = max(existing_min_x, min(current_x, existing_max_x))
            closest_y = max(existing_min_y, min(current_y, existing_max_y))
            distance = math.sqrt(
                (current_x - closest_x) ** 2 + (current_y - closest_y) ** 2
            )

            # 如果距离很近（小于20单位）
            if distance < 20:
                # 如果当前病害的x坐标较大（更靠右），则增加其引线长度
                # 用户要求延长seg1_len（斜线），所以同时增加seg1_len和seg2_len
                if current_x > existing_center_x:
                    # 增加seg1_len（斜线）为原来的3倍，让引线起点更远
                    seg1_len_estimate = 8 * 3
                    # 同时也增加seg2_len
                    seg2_len_estimate *= 3
                    # 马蹄部件横线长度限制在40以内
                    if is_horse_hoof:
                        seg2_len_estimate = min(seg2_len_estimate, 40)
                    print(
                        f"  检测到近距离病害，增加seg1_len至: {seg1_len_estimate}, seg2_len至: {seg2_len_estimate}"
                    )
                    break

    # 检查是否垂直同层，并找到第一个病害（x坐标最小的）
    y_vertical_overlap_check = False
    first_disease_idx = None
    first_disease_x = float("inf")

    for idx, existing in enumerate(LABEL_POSITIONS_CACHE):
        existing_disease_coords = existing[5:7] if len(existing) > 6 else None
        if existing_disease_coords:
            y_diff = abs(existing_disease_coords[1] - cad_y_mid)
            if y_diff < 1.0:
                y_vertical_overlap_check = True
                if existing_disease_coords[0] < first_disease_x:
                    first_disease_x = existing_disease_coords[0]
                    first_disease_idx = idx

    # 如果是垂直同层且当前病害x坐标更大，则先修改第一个病害的seg1_len
    if (
        y_vertical_overlap_check
        and first_disease_idx is not None
        and cad_x_mid > first_disease_x
    ):
        first_existing = LABEL_POSITIONS_CACHE[first_disease_idx]
        first_angle = first_existing[4]
        first_disease_coords = first_existing[5:7]
        # 延长第一个病害的seg1_len到18
        new_seg1 = 18
        # 重新计算bbox（使用第一个病害的leader_start，但需要估算）
        # 由于没有存储原始leader_start，使用当前计算的值作为近似
        first_bbox = first_existing[:4]
        first_start_x = first_bbox[0] - 10  # 近似还原
        first_start_y = first_bbox[1] - 10
        new_bbox = get_label_bbox(
            first_start_x, first_start_y, first_angle, new_seg1, seg2_len_estimate
        )
        LABEL_POSITIONS_CACHE[first_disease_idx] = new_bbox + (
            first_angle,
            first_disease_coords[0],
            first_disease_coords[1],
        )
        print(f"  垂直同层，延长第一个病害seg1_len至: {new_seg1}")
        # 重置标记，因为已经处理过了
        y_vertical_overlap_check = False

    # 寻找不重叠的标注位置（优先使用base_angle）
    # 使用病害的绝对CAD坐标判断真实距离
    result = find_non_overlapping_position(
        leader_start[0],
        leader_start[1],
        base_angle,
        flip_angle,
        seg1_len_estimate,
        seg2_len_estimate,
        beam_level,
        specific_part=specific_part,
        disease_cad_coords=(cad_x_mid, cad_y_mid),
    )

    if result is None:
        # 仍然找不到，使用默认角度
        angle = base_angle
        start_x, start_y = leader_start
        seg2_len = seg2_len_estimate
        # 马蹄部件横线长度限制
        if is_horse_hoof:
            seg2_len = min(seg2_len, 40)
        seg1_len_used = 8
        bbox = get_label_bbox(start_x, start_y, angle, seg1_len_used, seg2_len)
        LABEL_POSITIONS_CACHE.append(bbox + (angle, cad_x_mid, cad_y_mid))
    else:
        # 新格式: (angle, seg1_len, seg2_len, bbox)
        if len(result) == 4:
            angle, seg1_len_used, seg2_len, bbox = result
            # 根据最终角度重新计算起点
            start_x, start_y = get_leader_start_point(
                cad_x1, cad_y1, cad_x2, cad_y2, angle
            )
        else:
            # 兼容旧格式
            print(
                f"  警告: find_non_overlapping_position返回了未知格式 len={len(result)}, result={result}"
            )
            angle = base_angle
            seg1_len_used = 8
            seg2_len = seg2_len_estimate
            start_x, start_y = leader_start
            bbox = get_label_bbox(start_x, start_y, angle, seg1_len_used, seg2_len)
        # 记录标注位置到缓存
        LABEL_POSITIONS_CACHE.append(bbox + (angle, cad_x_mid, cad_y_mid))

    # 绘制病害图形
    if disease_type == "网状裂缝":
        draw_mesh_crack(
            msp, x_start, y_start, x_end, y_end, origin, specific_part, beam_level
        )
        draw_disease_label_with_angle(
            msp,
            disease_type_display,
            f"S={area:.2f}m²",
            start_x,
            start_y,
            angle=angle,
            seg1_len=16,
        )

    elif disease_type in ["剥落", "剥落掉角", "掉角"]:
        # 获取实际边界框，用于计算引线起点
        actual_bbox = draw_peel_off(
            msp,
            x_start,
            y_start,
            x_end,
            y_end,
            origin,
            specific_part,
            beam_level,
            return_bbox=True,
        )
        if actual_bbox:
            leader_start = get_leader_start_point(
                actual_bbox[0], actual_bbox[1], actual_bbox[2], actual_bbox[3], angle
            )
            draw_disease_label_with_angle(
                msp,
                disease_type_display,
                f"S={area:.2f}m²",
                leader_start[0],
                leader_start[1],
                angle=angle,
                seg1_len=seg1_len_used,
                seg2_len=seg2_len,
            )
        else:
            draw_disease_label_with_angle(
                msp,
                disease_type_display,
                f"S={area:.2f}m²",
                start_x,
                start_y,
                angle=angle,
                seg1_len=seg1_len_used,
                seg2_len=seg2_len,
            )

    elif disease_type in ["剥落露筋", "漏筋", "露筋", "锈胀露筋"]:
        # 获取实际边界框，用于计算引线起点
        actual_bbox = draw_peel_off_with_rebar(
            msp,
            x_start,
            y_start,
            x_end,
            y_end,
            origin,
            specific_part,
            beam_level,
            return_bbox=True,
        )
        if actual_bbox:
            # 使用实际边界框的右上角作为引线起点
            leader_start_x, leader_start_y = actual_bbox[0], actual_bbox[1]  # ax1, ay1
            leader_start = get_leader_start_point(
                actual_bbox[0], actual_bbox[1], actual_bbox[2], actual_bbox[3], angle
            )
            draw_disease_label_with_angle(
                msp,
                disease_type_display,
                f"S={area:.2f}m²",
                leader_start[0],
                leader_start[1],
                angle=angle,
                seg1_len=seg1_len_used,
                seg2_len=seg2_len,
            )
        else:
            draw_disease_label_with_angle(
                msp,
                disease_type_display,
                f"S={area:.2f}m²",
                start_x,
                start_y,
                angle=angle,
                seg1_len=seg1_len_used,
                seg2_len=seg2_len,
            )

    elif "裂缝" in disease_type and count > 0:
        # 裂缝群（N条裂缝），第一段引线长度增加到16
        draw_crack_group(msp, x_start, x_end, count, origin, specific_part, beam_level)
        label = f"{disease_type_display} L总={length:.2f}m N={count}条"
        value = f"间距{spacing:.2f}m" if spacing > 0 else ""
        draw_disease_label_with_angle(
            msp, label, value, start_x, start_y, angle=angle, seg1_len=16
        )

    elif "裂缝" in disease_type:
        crack_y = (y_start + y_end) / 2
        draw_crack(msp, x_start, x_end, crack_y, origin, specific_part, beam_level)
        if length > 0 and width > 0:
            label = f"{disease_type_display} L={length:.2f}m"
            value = f"W={width:.2f}mm"
        elif length > 0:
            label = f"{disease_type_display} L={length:.2f}m"
            value = ""
        else:
            label = disease_type_display
            value = ""
        draw_disease_label_with_angle(
            msp,
            label,
            value,
            start_x,
            start_y,
            angle=angle,
            seg1_len=seg1_len_used,
            seg2_len=seg2_len,
        )

    elif "蜂窝" in disease_type or "麻面" in disease_type or "水蚀" in disease_type:
        # 蜂窝、麻面、水蚀使用蜂窝麻面图例（平铺复制）
        actual_bbox = draw_honeycomb(
            msp,
            x_start,
            y_start,
            x_end,
            y_end,
            origin,
            specific_part,
            beam_level,
            return_bbox=True,
            area=area,
        )
        if actual_bbox:
            leader_start = get_leader_start_point(
                actual_bbox[0], actual_bbox[1], actual_bbox[2], actual_bbox[3], angle
            )
            draw_disease_label_with_angle(
                msp,
                disease_type_display,
                f"S={area:.2f}m²",
                leader_start[0],
                leader_start[1],
                angle=angle,
                seg1_len=seg1_len_used,
                seg2_len=seg2_len,
            )
        else:
            draw_disease_label_with_angle(
                msp,
                disease_type_display,
                f"S={area:.2f}m²",
                start_x,
                start_y,
                angle=angle,
                seg1_len=seg1_len_used,
                seg2_len=seg2_len,
            )

    else:
        # 获取实际边界框，用于计算引线起点
        actual_bbox = draw_peel_off(
            msp,
            x_start,
            y_start,
            x_end,
            y_end,
            origin,
            specific_part,
            beam_level,
            return_bbox=True,
        )
        if actual_bbox:
            leader_start = get_leader_start_point(
                actual_bbox[0], actual_bbox[1], actual_bbox[2], actual_bbox[3], angle
            )
            draw_disease_label_with_angle(
                msp,
                disease_type_display,
                "",
                leader_start[0],
                leader_start[1],
                angle=angle,
                seg1_len=seg1_len_used,
                seg2_len=seg2_len,
            )
        else:
            draw_disease_label_with_angle(
                msp,
                disease_type_display,
                "",
                start_x,
                start_y,
                angle=angle,
                seg1_len=seg1_len_used,
                seg2_len=seg2_len,
            )


def delete_text_in_rect(msp, x1: float, y1: float, x2: float, y2: float):
    """删除矩形区域内的所有实体（使用bbox精确检测）"""
    # 确保 left < right, bottom < top
    left = min(x1, x2)
    right = max(x1, x2)
    top = max(y1, y2)
    bottom = min(y1, y2)

    def rects_overlap(ax1, ay1, ax2, ay2, bx1, by1, bx2, by2):
        """判断两个矩形是否相交或重叠"""
        return not (ax2 <= bx1 or ax1 >= bx2 or ay2 <= by1 or ay1 >= by2)

    to_delete = []
    for entity in msp:
        try:
            # 使用实体的边界框检测
            bbox = entity.bbox
            if bbox is None:
                continue

            # 获取实体的边界框坐标
            e_left = bbox.dx.min
            e_right = bbox.dx.max
            e_bottom = bbox.dy.min
            e_top = bbox.dy.max

            # 检查实体的bbox是否与删除区域相交
            if rects_overlap(
                left, bottom, right, top, e_left, e_bottom, e_right, e_top
            ):
                to_delete.append(entity)

        except Exception as e:
            # 如果bbox获取失败，尝试其他方法
            dxftype = entity.dxftype()
            try:
                if dxftype in ("TEXT", "MTEXT"):
                    insert = entity.dxf.insert
                    if left <= insert[0] <= right and bottom <= insert[1] <= top:
                        to_delete.append(entity)
                elif dxftype == "LINE":
                    start = entity.dxf.start
                    end = entity.dxf.end
                    if (left <= start[0] <= right and bottom <= start[1] <= top) or (
                        left <= end[0] <= right and bottom <= end[1] <= top
                    ):
                        to_delete.append(entity)
            except:
                pass

    for entity in to_delete:
        msp.delete_entity(entity)


def create_page_for_pair(
    template_path: str,
    pair: list,
    disease_data: dict,
    route_name: str,
    bridge_name: str,
    bridge_output_dir: str,
    page_index: int,
) -> str:
    """为一对构件创建一页病害图"""
    import ezdxf

    # 读取模板
    doc = ezdxf.readfile(template_path)
    msp = doc.modelspace()

    # 修改标题（字号改为6）
    update_text_in_msp(msp, "LLL", route_name, height=6)
    update_text_in_msp(msp, "QQQ", bridge_name, height=6)

    # 确定孔次和梁号
    if len(pair) == 2:
        span1 = pair[0].split("-")[0] if "-" in pair[0] else pair[0]
        span2 = pair[1].split("-")[0] if "-" in pair[1] else pair[1]

        if span1 == span2:
            kkk = f"第{span1}孔"
            hhh = f"{pair[0].replace('号', '')}, {pair[1].replace('号', '')}"
        else:
            kkk = f"第{span1}孔、第{span2}孔"
            hhh = f"{pair[0].replace('号', '')}, {pair[1].replace('号', '')}"
    else:
        span = pair[0].split("-")[0] if "-" in pair[0] else pair[0]
        kkk = f"第{span}孔"
        hhh = pair[0].replace("号", "")

    update_text_in_msp(msp, "KKK", kkk, height=6)
    update_text_in_msp(msp, "HHH", hhh, height=6.5)

    # 修改横断面标注
    # Excel先出现的构件 → b-b断面上方，后出现的构件 → a-a断面下方
    if len(pair) >= 1:
        update_text_in_msp(msp, "a-a", pair[0])  # 后出现的放下方(a-a)
    if len(pair) >= 2:
        update_text_in_msp(msp, "b-b", pair[1])  # 先出现的放上方(b-b)

    # 单独构件时删除b-b断面及下方T梁区域
    # 删除范围: (28, 217) 到 (503, 78) 矩形区域
    if len(pair) == 1:
        delete_text_in_rect(msp, 28, 217, 503, 78)

    # 绘制病害
    # 重要：病害分配根据配对顺序决定，而非部件类型！
    # - pair[0] (先出现的构件) → 上方T梁 (upper坐标系, b-b断面)
    # - pair[1] (后出现的构件) → 下方T梁 (lower坐标系, a-a断面)
    #
    # 模板坐标系：
    # - upper坐标系 origin_y=274 → b-b断面（上方，y轴大）
    # - lower坐标系 origin_y=160 → a-a断面（下方，y轴小）
    for idx, comp_id in enumerate(pair):
        if comp_id in disease_data:
            # 根据配对顺序决定画在哪个T梁
            # idx=0: 先出现的构件 → upper（上方的b-b断面）
            # idx=1: 后出现的构件 → lower（下方的a-a断面）
            beam_level = "upper" if idx == 0 else "lower"

            for record in disease_data[comp_id]:
                specific_part = record.get("具体部件", "梁底")
                disease_type = record.get("病害类型", "")
                x_start = record.get("x_start", 0)

                print(
                    f"  {comp_id} {disease_type} ({specific_part}): idx={idx} -> beam_level={beam_level}"
                )

                process_disease_record(msp, record, comp_id, beam_level)

    # 保存 - 文件名格式：上部T梁第N页_构件号.dxf
    comp_ids_str = "-".join([c.replace("号", "") for c in pair])  # 如 "1-1-1-2"
    output_path = os.path.join(
        bridge_output_dir, f"上部T梁第{page_index}页_{comp_ids_str}.dxf"
    )
    doc.saveas(output_path)
    print(f"  已保存: {output_path}")

    return output_path


def main():
    """主函数：处理input目录中的所有Excel文件"""
    print("=" * 60)
    print("桥梁病害CAD标注系统 - 上部（40mT梁）处理")
    print("支持批量处理input目录中的所有Excel文件")
    print("=" * 60)

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 获取input目录中的所有Excel文件
    excel_files = []
    if os.path.exists(INPUT_DIR):
        for filename in os.listdir(INPUT_DIR):
            if filename.endswith('.xls') or filename.endswith('.xlsx'):
                excel_files.append(os.path.join(INPUT_DIR, filename))
    
    if not excel_files:
        print(f"\n错误：未在 {INPUT_DIR} 目录中找到Excel文件！")
        return
    
    print(f"\n发现 {len(excel_files)} 个Excel文件:")
    for i, f in enumerate(excel_files, 1):
        print(f"  {i}. {os.path.basename(f)}")

    # 处理每个Excel文件
    for excel_idx, excel_path in enumerate(excel_files, 1):
        print("\n" + "=" * 60)
        print(f"[{excel_idx}/{len(excel_files)}] 处理: {os.path.basename(excel_path)}")
        print("=" * 60)

        # 解析Excel数据
        print(f"\n读取Excel文件: {excel_path}")
        try:
            data = parse_excel(excel_path)
        except Exception as e:
            print(f"  解析失败: {e}")
            continue

        route_name = data["route_name"]
        bridge_name = data["bridge_name"]

        print(f"路线名称: {route_name}")
        print(f"桥梁名称: {bridge_name}")
        
        # 创建桥梁子目录，避免文件混淆
        bridge_output_dir = os.path.join(OUTPUT_DIR, bridge_name)
        os.makedirs(bridge_output_dir, exist_ok=True)
        print(f"输出目录: {bridge_output_dir}")

        # 获取上部（40mT梁）的病害数据
        upper_diseases = {}
        for part in data["parts"]:
            if "上部" in part["name"]:
                for comp_id, records in part["grouped_data"].items():
                    upper_diseases[comp_id] = records

        if not upper_diseases:
            print("  未找到上部病害数据，跳过")
            continue

        print(f"\n上部（40mT梁）构件数量: {len(upper_diseases)}")
        print(f"构件列表: {list(upper_diseases.keys())}")

        # 配对构件
        components = list(upper_diseases.keys())
        pairs = pair_components(components)
        print(f"\n配对结果: {len(pairs)} 页")
        for i, pair in enumerate(pairs):
            print(f"  第{i + 1}页: {pair}")

        # 为每对构件创建一页
        output_files = []

        for i, pair in enumerate(pairs):
            print(f"\n处理第{i + 1}页: {pair}")
            # 每页开始时重置标注位置缓存
            reset_label_cache()
            output_path = create_page_for_pair(
                TEMPLATE_FILE, pair, upper_diseases, route_name, bridge_name, bridge_output_dir, i + 1
            )
            output_files.append(output_path)

        # 创建最终合并文件
        print("\n" + "=" * 60)
        print("创建最终合并文件...")

        import ezdxf

        # 读取第一个模板作为基础
        final_doc = ezdxf.readfile(TEMPLATE_FILE)
        final_msp = final_doc.modelspace()

        # 清空模型空间（重新绘制）
        for entity in list(final_msp):
            entity.destroy()

        # 添加桥梁名称标题（字号20，宋体），放在最上方
        # 标题在最上方，间距100后放置第一张图
        title_gap = 100  # 标题与第一张图的间距
        final_msp.add_text(bridge_name, dxfattribs={"height": 20, "layer": "0"})

        # 从每页复制内容，Y轴向下排列（负Y方向）
        # 最先处理的放在最上方，依次向下
        page_height = 365  # 图框高度
        gap = 50  # 图与图之间的间距
        num_pages = len(output_files)
        for i, output_file in enumerate(output_files):
            if os.path.exists(output_file):
                print(f"  复制第{i + 1}页...")
                # 第i页的偏移：最先处理的(i=0)放在最上方，偏移量最小
                y_offset = -(title_gap + page_height + i * (page_height + gap))

                page_doc = ezdxf.readfile(output_file)
                page_msp = page_doc.modelspace()

                # 首先复制所有块定义到最终文档
                copy_blocks_to_doc(page_doc, final_doc)

                for entity in page_msp:
                    try:
                        # 复制实体并应用Y偏移
                        new_entity = copy_entity_with_offset(
                            final_msp, entity, y_offset, final_doc
                        )
                    except Exception as e:
                        print(f"    复制实体失败: {e}")

        # 保存最终文件
        # 获取Excel文件名（不含扩展名）
        excel_basename = os.path.splitext(os.path.basename(excel_path))[0]
        final_output = os.path.join(BASE_DIR, f"{excel_basename}-上部病害.dxf")
        final_doc.saveas(final_output)
        print(f"\n最终文件已保存: {final_output}")

    print("\n" + "=" * 60)
    print("所有Excel文件处理完成！")
    print("=" * 60)

    print(f"\n最终文件已保存: {final_output}")
    print("=" * 60)


def copy_blocks_to_doc(source_doc, target_doc):
    """将源文档中的所有块定义复制到目标文档"""
    for block in source_doc.blocks:
        block_name = block.name
        # 检查目标文档是否已存在该块定义
        if block_name not in target_doc.blocks:
            try:
                # 创建新块
                new_block = target_doc.blocks.new(name=block_name)
                # 复制块中的所有实体
                for entity in block:
                    copy_entity_to_block(new_block, entity)
            except Exception as e:
                print(f"    复制块定义 {block_name} 失败: {e}")


def copy_entity_to_block(block, entity):
    """将实体复制到块中 - 使用原生copy方法"""
    try:
        # 使用原生copy方法复制实体
        new_entity = entity.copy()
        block.add_entity(new_entity)
    except Exception as e:
        # 如果原生复制失败，使用手动复制
        entity_type = entity.dxftype()
        layer = entity.dxf.layer if hasattr(entity.dxf, "layer") else "0"
        color = entity.dxf.color if hasattr(entity.dxf, "color") else 7

        try:
            if entity_type == "TEXT":
                text = entity.dxf.text
                height = entity.dxf.height if hasattr(entity.dxf, "height") else 2.5
                insert = entity.dxf.insert
                block.add_text(
                    text, dxfattribs={"layer": layer, "color": color, "height": height}
                ).set_pos(insert)
            elif entity_type == "MTEXT":
                mtxt = block.add_mtext(
                    entity.text, dxfattribs={"layer": layer, "color": color}
                )
                mtxt.dxf.insert = entity.dxf.insert
                if hasattr(entity.dxf, "char_height"):
                    mtxt.dxf.char_height = entity.dxf.char_height
            elif entity_type == "LINE":
                block.add_line(
                    entity.dxf.start,
                    entity.dxf.end,
                    dxfattribs={"layer": layer, "color": color},
                )
            elif entity_type == "LWPOLYLINE":
                if hasattr(entity, "get_points"):
                    points = [(p[0], p[1]) for p in entity.get_points()]
                    block.add_lwpolyline(
                        points, dxfattribs={"layer": layer, "color": color}
                    )
            elif entity_type == "CIRCLE":
                block.add_circle(
                    entity.dxf.center,
                    entity.dxf.radius,
                    dxfattribs={"layer": layer, "color": color},
                )
            elif entity_type == "ARC":
                block.add_arc(
                    entity.dxf.center,
                    entity.dxf.radius,
                    entity.dxf.start_angle,
                    entity.dxf.end_angle,
                    dxfattribs={"layer": layer, "color": color},
                )
            elif entity_type == "SPLINE":
                from ezdxf.math import BSpline

                if hasattr(entity, "control_points") and entity.control_points:
                    control_points = [(pt[0], pt[1], 0) for pt in entity.control_points]
                    spline = BSpline(control_points)
                    block.add_spline(
                        spline, dxfattribs={"layer": layer, "color": color}
                    )
            elif entity_type == "HATCH":
                hatch = block.add_hatch(color=color, dxfattribs={"layer": layer})
                for path in entity.paths:
                    if hasattr(path, "vertices"):
                        hatch.paths.add_polyline_path(
                            [(v[0], v[1]) for v in path.vertices]
                        )
                if hasattr(entity.dxf, "pattern_name"):
                    try:
                        hatch.set_pattern_fill(entity.dxf.pattern_name)
                    except:
                        pass
            elif entity_type == "POINT":
                block.add_point(
                    entity.dxf.location, dxfattribs={"layer": layer, "color": color}
                )
        except:
            pass


def copy_entity_with_offset(msp, entity, y_offset: float, target_doc=None):
    """复制实体并应用Y偏移 - 使用ezdxf原生copy方法"""
    entity_type = entity.dxftype()

    try:
        # 对于大多数实体类型，使用原生copy和translate
        if entity_type in (
            "TEXT",
            "MTEXT",
            "LINE",
            "LWPOLYLINE",
            "POLYLINE",
            "SPLINE",
            "CIRCLE",
            "ARC",
            "POINT",
            "HATCH",
            "ELLIPSE",
        ):
            new_entity = entity.copy()
            new_entity.translate(0, y_offset, 0)
            msp.add_entity(new_entity)
            return new_entity

        elif entity_type == "INSERT":
            # INSERT - 块引用需要特殊处理
            block_name = entity.dxf.name
            old_x, old_y = entity.dxf.insert[0], entity.dxf.insert[1]
            new_pos = (old_x, old_y + y_offset)
            x_scale = entity.dxf.xscale if hasattr(entity.dxf, "xscale") else 1
            y_scale = entity.dxf.yscale if hasattr(entity.dxf, "yscale") else 1
            z_scale = entity.dxf.zscale if hasattr(entity.dxf, "zscale") else 1
            rotation = entity.dxf.rotation if hasattr(entity.dxf, "rotation") else 0
            layer = entity.dxf.layer if hasattr(entity.dxf, "layer") else "0"

            # 检查块定义是否存在
            if target_doc and block_name not in target_doc.blocks:
                print(f"    警告: 块定义 {block_name} 不存在，跳过此块引用")
                return None

            return msp.add_blockref(
                block_name,
                new_pos,
                dxfattribs={
                    "layer": layer,
                    "xscale": x_scale,
                    "yscale": y_scale,
                    "zscale": z_scale,
                    "rotation": rotation,
                },
            )
        else:
            # 其他类型尝试原生复制
            new_entity = entity.copy()
            new_entity.translate(0, y_offset, 0)
            msp.add_entity(new_entity)
            return new_entity

    except Exception as e:
        # 如果原生复制失败，使用手动复制
        return copy_entity_manual(msp, entity, y_offset, target_doc)


def copy_entity_manual(msp, entity, y_offset: float, target_doc=None):
    """手动复制实体（备用方法）"""
    entity_type = entity.dxftype()
    layer = entity.dxf.layer if hasattr(entity.dxf, "layer") else "0"
    color = entity.dxf.color if hasattr(entity.dxf, "color") else 7

    try:
        if entity_type == "TEXT":
            text = entity.dxf.text
            height = entity.dxf.height if hasattr(entity.dxf, "height") else 2.5
            old_x, old_y = entity.dxf.insert[0], entity.dxf.insert[1]
            new_pos = (old_x, old_y + y_offset)
            text_obj = msp.add_text(
                text, dxfattribs={"layer": layer, "color": color, "height": height}
            )
            text_obj.dxf.insert = new_pos
            return text_obj

        elif entity_type == "MTEXT":
            old_x, old_y = entity.dxf.insert[0], entity.dxf.insert[1]
            new_pos = (old_x, old_y + y_offset)
            mtxt = msp.add_mtext(entity.text, dxfattribs={"layer": layer})
            mtxt.dxf.insert = new_pos
            if hasattr(entity.dxf, "char_height"):
                mtxt.dxf.char_height = entity.dxf.char_height
            return mtxt

        elif entity_type == "LINE":
            start = entity.dxf.start
            end = entity.dxf.end
            new_start = (start[0], start[1] + y_offset)
            new_end = (end[0], end[1] + y_offset)
            return msp.add_line(
                new_start, new_end, dxfattribs={"layer": layer, "color": color}
            )

        elif entity_type == "LWPOLYLINE":
            points = []
            if hasattr(entity, "get_points"):
                for pt in entity.get_points():
                    points.append((pt[0], pt[1] + y_offset))
            if points:
                return msp.add_lwpolyline(
                    points, dxfattribs={"layer": layer, "color": color}
                )
            return None

        elif entity_type == "SPLINE":
            from ezdxf.math import BSpline

            if hasattr(entity, "control_points") and entity.control_points:
                control_points = [
                    (pt[0], pt[1] + y_offset, 0) for pt in entity.control_points
                ]
                spline = BSpline(control_points)
                return msp.add_spline(
                    spline, dxfattribs={"layer": layer, "color": color}
                )
            return None

        elif entity_type == "HATCH":
            # HATCH使用原生复制
            new_hatch = entity.copy()
            new_hatch.translate(0, y_offset, 0)
            msp.add_entity(new_hatch)
            return new_hatch

        elif entity_type == "INSERT":
            block_name = entity.dxf.name
            old_x, old_y = entity.dxf.insert[0], entity.dxf.insert[1]
            new_pos = (old_x, old_y + y_offset)
            x_scale = entity.dxf.xscale if hasattr(entity.dxf, "xscale") else 1
            y_scale = entity.dxf.yscale if hasattr(entity.dxf, "yscale") else 1
            rotation = entity.dxf.rotation if hasattr(entity.dxf, "rotation") else 0

            if target_doc and block_name not in target_doc.blocks:
                return None

            return msp.add_blockref(
                block_name,
                new_pos,
                dxfattribs={
                    "layer": layer,
                    "xscale": x_scale,
                    "yscale": y_scale,
                    "rotation": rotation,
                },
            )

        elif entity_type == "CIRCLE":
            center = entity.dxf.center
            radius = entity.dxf.radius
            new_center = (center[0], center[1] + y_offset)
            return msp.add_circle(
                new_center, radius, dxfattribs={"layer": layer, "color": color}
            )

        elif entity_type == "ARC":
            center = entity.dxf.center
            radius = entity.dxf.radius
            start_angle = entity.dxf.start_angle
            end_angle = entity.dxf.end_angle
            new_center = (center[0], center[1] + y_offset)
            return msp.add_arc(
                new_center,
                radius,
                start_angle,
                end_angle,
                dxfattribs={"layer": layer, "color": color},
            )

        else:
            return None
    except Exception as e:
        return None


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
桥梁病害CAD标注系统 - 数据解析模块
用于解析Excel中的病害数据
"""

import pandas as pd
import re
from collections import defaultdict
from typing import Dict, List, Any


def parse_excel(excel_path: str) -> Dict[str, Any]:
    """
    解析Excel文件，提取桥梁信息和病害数据
    
    Args:
        excel_path: Excel文件路径
        
    Returns:
        包含桥梁信息和病害数据的字典
    """
    df = pd.read_excel(excel_path, header=None)
    
    # 提取桥梁基本信息
    # 处理可能的空值（NaN）情况
    route_name_raw = df.iloc[0, 0]
    bridge_name_raw = df.iloc[1, 0]
    
    # 确保转换为字符串，处理NaN
    route_name = str(route_name_raw).replace('路线名称:', '').strip() if pd.notna(route_name_raw) else ''
    
    # 第二行可能是桥梁名称（新格式）或带前缀的桥梁名称（旧格式）
    if pd.notna(bridge_name_raw):
        bridge_name_str = str(bridge_name_raw)
        if '桥梁名称' in bridge_name_str:
            # 旧格式："桥梁名称：K575+266黄泥河大桥（右幅）"
            bridge_name = bridge_name_str.replace('桥梁名称：', '').strip()
        else:
            # 新格式：直接是桥梁名称"K575+266黄泥河大桥（右幅）"
            bridge_name = bridge_name_str.strip()
    else:
        bridge_name = ''
    
    # 如果没有提取到桥梁名称，尝试从第一行提取
    if not bridge_name and pd.notna(route_name_raw):
        first_line = str(route_name_raw)
        # 格式如："一、K575+266黄泥河大桥（右幅）"
        if '、' in first_line:
            bridge_name = first_line.split('、', 1)[1].strip()
        else:
            bridge_name = first_line.strip()
    
    # 找到所有构件类型的起止位置
    # 方法：先找到所有构件类型标题行，然后计算每个构件的数据范围
    part_titles = []  # [(行号, 构件名称), ...]
    for i in range(len(df)):
        cell = df.iloc[i, 0]
        cell_str = str(cell)
        # 支持全角括号（）和半角括号()
        if pd.notna(cell) and (('（' in cell_str and '）' in cell_str) or ('(' in cell_str and ')' in cell_str)):
            part_name = cell_str.strip()
            # 跳过桥梁基本信息行（包含"桥梁名称"）
            if '桥梁名称' in part_name:
                continue
            # 跳过看起来像标题序号的行（如"一、..."、"二、..."等）
            if re.match(r'^[一二三四五六七八九十]+、', part_name):
                continue
            part_titles.append((i, part_name))
    
    # 计算每个构件的数据起止行
    parts = []
    for idx, (title_row, part_name) in enumerate(part_titles):
        # 下一个构件标题行作为当前构件的结束边界
        if idx + 1 < len(part_titles):
            next_title_row = part_titles[idx + 1][0]
        else:
            next_title_row = len(df)
        
        # 在 title_row+1 到 next_title_row-1 之间找第一个数字序号行
        start_row = None
        for j in range(title_row + 1, next_title_row):
            first_col = df.iloc[j, 0]
            if pd.notna(first_col):
                if isinstance(first_col, (int, float)):
                    start_row = j
                    break
                first_str = str(first_col).strip()
                if first_str.isdigit() or (first_str.endswith('号') and first_str[:-1].isdigit()):
                    start_row = j
                    break
        
        if start_row is None:
            continue
        
        # 数据结束行：下一个构件标题的前一行，或到 next_title_row-1
        end_row = next_title_row
        
        parts.append({
            'name': part_name,
            'start_row': start_row,
            'end_row': end_row
        })
    
    # 解析每个构件类型的病害数据
    result = {
        'route_name': route_name,
        'bridge_name': bridge_name,
        'parts': []
    }
    
    for part in parts:
        part_data = []
        section = get_section(part['name'])  # 获取部位分类
        
        for i in range(part['start_row'], part['end_row']):
            row = df.iloc[i]
            if pd.notna(row[0]) and isinstance(row[0], (int, float)):
                comp_id_raw = str(row[1]).strip() if pd.notna(row[1]) else ''
                defect_loc = str(row[2]).strip() if pd.notna(row[2]) else ''  # 缺损位置
                disease_raw = str(row[3]).strip() if pd.notna(row[3]) else ''
                disease_parsed = parse_disease_position(disease_raw)  # 解析病害位置
                comp_parsed = parse_component_id(comp_id_raw, part['name'], defect_loc)
                # 获取病害图例
                disease_legend = get_legend_name(disease_raw)
                
                part_data.append({
                    '序号': int(row[0]),
                    '构件编号': comp_id_raw,
                    '部位分类': section,
                    '缺损位置': defect_loc,
                    '具体部件': disease_parsed['part'],  # 病害具体部件：梁底、左翼缘板等
                    '孔号': comp_parsed['span_no'],
                    '梁号': comp_parsed['beam_no'],
                    '墩柱号': comp_parsed['pier_no'],
                    '柱内编号': comp_parsed['column_no'],
                    '盖梁号': comp_parsed['cap_beam_no'],
                    '台号': comp_parsed['abut_no'],
                    '位置': defect_loc,
                    '病害': disease_raw,
                    '病害类型': disease_parsed['disease_type'],
                    '病害图例': disease_legend if disease_legend else '无',
                    'x_start': disease_parsed['x_start'],
                    'x_end': disease_parsed['x_end'],
                    'y_start': disease_parsed['y_start'],
                    'y_end': disease_parsed['y_end'],
                    'length': disease_parsed['length'],  # 裂缝长度
                    'width': disease_parsed['width'],    # 裂缝宽度
                    'area': disease_parsed['area'],      # 剥落面积
                    'count': disease_parsed['count'],    # 裂缝数量
                    'spacing': disease_parsed['spacing'], # 裂缝间距
                })
        
        # 按构件编号分组
        grouped = defaultdict(list)
        for item in part_data:
            if item['构件编号']:
                grouped[item['构件编号']].append(item)
        
        # 确定模板文件
        template_name = get_template_name(part['name'])
        
        result['parts'].append({
            'name': part['name'],
            'section': section,
            'template_name': template_name,
            'grouped_data': dict(grouped)
        })
    
    # 按模板分组整理数据（方便后续CAD绘制）
    templates = defaultdict(list)
    for part in result['parts']:
        template_name = part['template_name']
        if template_name:
            templates[template_name].append({
                'part_name': part['name'],
                'section': part['section'],
                'components': part['grouped_data']
            })
    
    result['templates'] = dict(templates)
    
    return result


def parse_component_id(comp_id: str, part_name: str = '', defect_location: str = '') -> Dict[str, Any]:
    """
    解析构件编号，根据构件大类和缺损位置返回不同字段。

    T梁（上部）格式：
        '1-1号' → span_no=1, beam_no=1
        '2-3号' → span_no=2, beam_no=3

    双柱墩：
        - 缺损位置='墩柱'时：'n-m号' → pier_no=n (墩柱号), column_no=m (从内向外第几根)
        - 缺损位置='盖梁'时：'n号'   → cap_beam_no=n
    单柱墩：
        - 缺损位置='墩柱'时：'n号'   → pier_no=n
        - 缺损位置='盖梁'时：'n号'   → cap_beam_no=n
    桥台：
        - 'n号' → abut_no=n (台号)

    Args:
        comp_id        : 构件编号字符串，如 '1-1号' / '1号'
        part_name      : 构件大类名称，如 '下部（双柱墩）' / '桥台（不带台身桥台）'
        defect_location: 缺损位置，如 '墩柱' / '盖梁' / '桥台'

    Returns:
        T梁:           {'span_no': int, 'beam_no': int, 'pier_no': None, 'column_no': None, 'cap_beam_no': None, 'abut_no': None, 'raw': str}
        双柱墩-墩柱:   {'span_no': None, 'beam_no': None, 'pier_no': int, 'column_no': int, 'cap_beam_no': None, 'abut_no': None, 'raw': str}
        双柱墩-盖梁:   {'span_no': None, 'beam_no': None, 'pier_no': None, 'column_no': None, 'cap_beam_no': int, 'abut_no': None, 'raw': str}
        单柱墩:        {'span_no': None, 'beam_no': None, 'pier_no': None, 'column_no': None, 'cap_beam_no': int, 'abut_no': None, 'raw': str}
        桥台:          {'span_no': None, 'beam_no': None, 'pier_no': None, 'column_no': None, 'cap_beam_no': None, 'abut_no': int, 'raw': str}
    """
    import re
    result = {
        'span_no': None, 'beam_no': None,
        'pier_no': None, 'column_no': None,
        'cap_beam_no': None, 'abut_no': None,
        'raw': comp_id
    }

    # 判断是否为双柱墩
    is_double_column_pier = '双柱墩' in part_name
    is_bridge_abut = '桥台' in part_name

    if is_bridge_abut:
        # 桥台：n号 → 台号
        m = re.match(r'^(\d+)号?$', comp_id.strip())
        if m:
            result['abut_no'] = int(m.group(1))
        return result

    if is_double_column_pier:
        # 双柱墩：根据缺损位置区分
        if '墩柱' in defect_location:
            # 墩柱：n-m号，n=墩柱号，m=从内向外第几根
            m = re.match(r'^(\d+)-(\d+)号?$', comp_id.strip())
            if m:
                result['pier_no'] = int(m.group(1))
                result['column_no'] = int(m.group(2))
            return result
        else:
            # 盖梁：n号
            m = re.match(r'^(\d+)号?$', comp_id.strip())
            if m:
                result['cap_beam_no'] = int(m.group(1))
            return result

    # 单柱墩或普通下部结构：统一按盖梁号处理
    if '柱墩' in part_name or '下部' in part_name:
        m = re.match(r'^(\d+)号?$', comp_id.strip())
        if m:
            result['cap_beam_no'] = int(m.group(1))
        return result

    # T梁或其他：解析孔号 + 梁号
    # 格式：数字-数字[号]，如 '1-1号'
    m = re.match(r'^(\d+)-(\d+)号?$', comp_id.strip())
    if m:
        result['span_no'] = int(m.group(1))
        result['beam_no'] = int(m.group(2))
        return result

    # 格式：纯数字（单号），如 '3号'
    m2 = re.match(r'^(\d+)号?$', comp_id.strip())
    if m2:
        result['span_no'] = int(m2.group(1))
        return result

    return result


def get_section(part_name: str) -> str:
    """
    根据构件大类名称判断属于上部还是下部。
    
    上部：T梁、箱梁、空心板等
    下部：桥台、桥墩、柱墩等
    
    Args:
        part_name: 构件大类名称，如 '上部（40mT梁）' / '下部（双柱墩）'
        
    Returns:
        '上部' 或 '下部'
    """
    if '上部' in part_name:
        return '上部'
    elif '下部' in part_name:
        return '下部'
    # 兜底：根据关键词判断
    upper_keywords = ['T梁', '箱梁', '空心板', '板梁', '梁']
    lower_keywords = ['桥台', '桥墩', '柱墩', '墩']
    for kw in upper_keywords:
        if kw in part_name:
            return '上部'
    for kw in lower_keywords:
        if kw in part_name:
            return '下部'
    return ''


def get_template_name(part_name: str) -> str:
    """
    根据构件名称获取对应的模板文件名
    
    Args:
        part_name: 构件名称
        
    Returns:
        模板文件名
    """
    mapping = {
        '上部（40mT梁）': '40mT梁.dxf',
        '上部(40mT梁)': '40mT梁.dxf',
        '下部（双柱墩）': '双柱墩12.5.dxf',
        '下部（双柱墩12.5m）': '双柱墩12.5.dxf',
        '下部（单柱墩）': '单柱墩.dxf',
        '桥台（不带台身桥台）': '不带台身桥台.dxf',
        '桥台（带台身桥台）': '带台身桥台.dxf'
    }
    return mapping.get(part_name, '')


def get_legend_name(disease_desc: str) -> str:
    """
    根据病害描述获取对应的图例文件名
    
    Args:
        disease_desc: 病害描述
        
    Returns:
        图例文件名
    """
    # 纯泛白不需要处理，但泛白+裂缝需要处理裂缝
    if disease_desc.strip() == '泛白' or disease_desc.endswith('泛白'):
        return None  # 纯泛白不需要处理
    
    if '马蹄' in disease_desc:
        return None  # 马蹄的病害不处理
    
    mapping = {
        '纵向裂缝': '裂缝及其长宽.dxf',
        '竖向裂缝': '裂缝及其长宽.dxf',
        '横向裂缝': '裂缝及其长宽.dxf',
        '水平裂缝': '裂缝及其长宽.dxf',
        '斜向裂缝': '裂缝及其长宽.dxf',
        '网状裂缝': '网状裂缝.dxf',
        '开裂': '裂缝及其长宽.dxf',
        '剥落掉角': '剥落、掉角.dxf',
        '掉角': '剥落、掉角.dxf',
        '剥落': '剥落、掉角.dxf',
        '水蚀': '水蚀.dxf',
        '剥落露筋': '剥落、漏筋.dxf',
        '漏筋': '剥落、漏筋.dxf',
        '露筋': '剥落、漏筋.dxf',
        '锈胀露筋': '钢筋锈蚀或可见箍筋轮廓.dxf',
        '蜂窝': '蜂窝麻面.dxf',
        '麻面': '蜂窝麻面.dxf',
        '破损': '剥落、掉角.dxf',
        '孔洞空洞': '孔洞空洞.dxf',
    }
    
    for key, value in mapping.items():
        if key in disease_desc:
            return value
    
    return None


def parse_disease_position(disease_desc: str) -> Dict[str, Any]:
    """
    解析病害描述中的位置信息
    
    Args:
        disease_desc: 病害描述，如 "梁底，x=10～14m，y=0.5m，纵向裂缝 L=4.00m，W=0.10mm"
        
    Returns:
        包含位置信息的字典
    """
    result = {
        'part': '',  # 部位：梁底、左翼缘板、右翼缘板等
        'x_start': 0,
        'x_end': 0,
        'y_start': 0,
        'y_end': 0,
        'disease_type': '',  # 病害类型
        'length': 0,  # 长度（裂缝）
        'width': 0,  # 宽度（裂缝）
        'area': 0,  # 面积（剥落等）
        'count': 0,  # 数量（多条裂缝）
        'spacing': 0,  # 间距
    }
    
    # 解析部位
    parts = disease_desc.split('，')
    if parts:
        result['part'] = parts[0].strip()
    
    # 解析坐标
    import re
    for part in parts:
        # x坐标范围
        x_range_match = re.search(r'x=([\d.]+)～([\d.]+)m', part)
        if x_range_match:
            result['x_start'] = float(x_range_match.group(1))
            result['x_end'] = float(x_range_match.group(2))
        
        # 只有x坐标（无范围）— 前面必须是边界（行首、逗号、空格、y等）
        x_single_match = re.search(r'(?:^|[,，\s])x=([\d.]+)m(?:[,，]|$|\s)', part)
        if x_single_match and not x_range_match:
            result['x_start'] = float(x_single_match.group(1))
            result['x_end'] = float(x_single_match.group(1))
        
        # 只有y坐标（无范围）— 末尾逗号可选
        y_match = re.search(r'y=([\d.]+)m(?:[,，]|$|\s)', part)
        if y_match and not re.search(r'y=([\d.]+)～([\d.]+)m', part):
            result['y_start'] = float(y_match.group(1))
            result['y_end'] = float(y_match.group(1))
        
        # y坐标范围
        y_range_match = re.search(r'y=([\d.]+)～([\d.]+)m', part)
        if y_range_match:
            result['y_start'] = float(y_range_match.group(1))
            result['y_end'] = float(y_range_match.group(2))
        
        # 长度 L
        l_match = re.search(r'L=([\d.]+)m', part)
        if l_match:
            result['length'] = float(l_match.group(1))
        
        # 最大长度 Lmax
        lmax_match = re.search(r'Lmax=([\d.]+)m', part)
        if lmax_match:
            result['length'] = float(lmax_match.group(1))
        
        # 总长度 L总
        ltotal_match = re.search(r'L总=([\d.]+)m', part)
        if ltotal_match:
            result['length'] = float(ltotal_match.group(1))
        
        # 宽度 W
        w_match = re.search(r'W=([\d.]+)mm', part)
        if w_match:
            result['width'] = float(w_match.group(1))
        
        # 最大宽度 Wmax
        wmax_match = re.search(r'Wmax=([\d.]+)mm', part)
        if wmax_match:
            result['width'] = float(wmax_match.group(1))
        
        # 面积 S
        s_match = re.search(r'S=([\d.]+)m2', part)
        if s_match:
            result['area'] = float(s_match.group(1))
        
        # 总面积 S总
        stotal_match = re.search(r'S总=([\d.]+)m2', part)
        if stotal_match:
            result['area'] = float(stotal_match.group(1))
        
        # 数量 N
        n_match = re.search(r'N=(\d+)条', part)
        if n_match:
            result['count'] = int(n_match.group(1))
        
        # 间距
        spacing_match = re.search(r'间距([\d.]+)m', part)
        if spacing_match:
            result['spacing'] = float(spacing_match.group(1))
        
        # 病害类型（注意：更长/更具体的关键词必须排在前面，避免被短词提前匹配）
        disease_types = ['纵向裂缝', '竖向裂缝', '横向裂缝', '水平裂缝', '斜向裂缝', '网状裂缝',
                        '剥落露筋', '漏筋', '锈胀露筋', '露筋',
                        '剥落掉角', '剥落', '掉角', '水蚀',
                        '蜂窝、麻面', '麻面、蜂窝', '蜂窝', '麻面', '泛白吸附', '泛白', '破损', 
                        '空洞、孔洞', '孔洞空洞', '空洞', '孔洞',
                        '开裂']
        for dt in disease_types:
            if dt in part:
                result['disease_type'] = dt
                break
    
    return result


if __name__ == '__main__':
    # 测试解析
    data = parse_excel('K572+774红石牡丹江大桥（右幅）病害.xls')
    print(f"路线名称: {data['route_name']}")
    print(f"桥梁名称: {data['bridge_name']}")
    print(f"构件类型数量: {len(data['parts'])}")
    
    for part in data['parts']:
        section = part.get('section', '')
        print(f"\n构件类型: {part['name']}")
        print(f"部位分类: {section}")
        print(f"模板: {part['template_name']}")
        print(f"构件数量: {len(part['grouped_data'])}")
        for comp_id, records in part['grouped_data'].items():
            r0 = records[0]
            defect_loc = r0.get('缺损位置', '')
            is_double_pier = '双柱墩' in part['name']
            
            if is_double_pier:
                if '墩柱' in defect_loc:
                    # 墩柱：显示墩柱号和柱内编号
                    pier = r0.get('墩柱号')
                    col = r0.get('柱内编号')
                    print(f"  构件编号={comp_id}  缺损位置={defect_loc}  墩柱号={pier}  柱内编号={col}  ({len(records)}条病害)")
                else:
                    # 盖梁：显示盖梁号
                    cap = r0.get('盖梁号')
                    print(f"  构件编号={comp_id}  缺损位置={defect_loc}  盖梁号={cap}  ({len(records)}条病害)")
            elif '柱墩' in part['name'] or '下部' in part['name']:
                cap = r0.get('盖梁号')
                print(f"  构件编号={comp_id}  缺损位置={defect_loc}  盖梁号={cap}  ({len(records)}条病害)")
            elif '桥台' in part['name']:
                abut = r0.get('台号')
                print(f"  构件编号={comp_id}  缺损位置={defect_loc}  台号={abut}  ({len(records)}条病害)")
            else:
                span = r0.get('孔号')
                beam = r0.get('梁号')
                print(f"  构件编号={comp_id}  孔号={span}  梁号={beam}  ({len(records)}条病害)")
            
            for r in records:
                # 直接使用已解析的数据
                specific_part = r.get('具体部件', '')
                disease_type = r.get('病害类型', '')
                disease_legend = r.get('病害图例', '无')
                x_s, x_e = r.get('x_start', 0), r.get('x_end', 0)
                y_s, y_e = r.get('y_start', 0), r.get('y_end', 0)
                print(f"    序号={r['序号']}  具体部件={specific_part}  病害类型={disease_type}  "
                      f"病害图例={disease_legend}  x=[{x_s},{x_e}]m  y=[{y_s},{y_e}]m")
    
    # 按模板分组输出（方便后续CAD绘制）
    print("\n" + "="*60)
    print("按模板分组（准备画到同一张图的数据）:")
    print("="*60)
    
    for template_name, template_data in data.get('templates', {}).items():
        print(f"\n模板文件: {template_name}")
        print(f"包含构件类型数: {len(template_data)}")
        
        total_components = 0
        total_diseases = 0
        for td in template_data:
            comp_count = len(td['components'])
            disease_count = sum(len(v) for v in td['components'].values())
            total_components += comp_count
            total_diseases += disease_count
            print(f"  - {td['part_name']}: {comp_count}个构件, {disease_count}条病害")
        
        print(f"  合计: {total_components}个构件, {total_diseases}条病害")
        
        # 列出所有构件编号
        all_comp_ids = []
        for td in template_data:
            all_comp_ids.extend(td['components'].keys())
        print(f"  构件编号列表: {all_comp_ids}")
    
    # 测试病害位置解析
    test_desc = "梁底，x=10～14m，y=0.5m，纵向裂缝 L=4.00m，W=0.10mm"
    pos = parse_disease_position(test_desc)
    print(f"\n测试解析: {test_desc}")
    print(f"结果: {pos}")
    
    # 测试 parse_component_id
    print("\n=== 构件编号解析测试 ===")
    cases = [
        ('1-1号',   '上部（40mT梁）', ''),
        ('2-5号',   '上部（40mT梁）', ''),
        ('1-2号',   '下部（双柱墩）', '墩柱'),  # 双柱墩-墩柱
        ('3-1号',   '下部（双柱墩）', '墩柱'),
        ('1号',     '下部（双柱墩）', '盖梁'),  # 双柱墩-盖梁
        ('5号',     '下部（双柱墩）', '盖梁'),
        ('3号',     '下部（单柱墩）', '墩柱'),  # 单柱墩
        ('3号',     '下部（单柱墩）', '盖梁'),  # 单柱墩
        ('桥台',    '桥台（不带台身桥台）', ''),
    ]
    for cid, pname, defect_loc in cases:
        r = parse_component_id(cid, pname, defect_loc)
        if r['pier_no'] is not None:
            print(f"  {cid!r:8s} [{pname}] 缺损位置={defect_loc!r:6s}  -> 墩柱号={r['pier_no']}  柱内编号={r['column_no']}")
        elif r['cap_beam_no'] is not None:
            print(f"  {cid!r:8s} [{pname}] 缺损位置={defect_loc!r:6s}  -> 盖梁号={r['cap_beam_no']}")
        else:
            print(f"  {cid!r:8s} [{pname}] 缺损位置={defect_loc!r:6s}  -> 孔号={r['span_no']}  梁号={r['beam_no']}")

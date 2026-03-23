# -*- coding: utf-8 -*-
"""
直接读取Excel并打印结构化数据
"""

import pandas as pd
import re
from collections import defaultdict

EXCEL_PATH = 'K572+774红石牡丹江大桥（右幅）病害.xls'

# ──────────────────────────────────────────────
# 1. 原始数据浏览
# ──────────────────────────────────────────────
def show_raw(df):
    print('=' * 80)
    print('【原始表格（前60行，前6列）】')
    print('=' * 80)
    for i in range(min(60, len(df))):
        row_cells = []
        for j in range(min(6, df.shape[1])):
            v = df.iloc[i, j]
            row_cells.append(f'[{j}]{v!r}')
        print(f'  行{i:>3}: ' + '  '.join(row_cells))


# ──────────────────────────────────────────────
# 2. 解析基本信息
# ──────────────────────────────────────────────
def parse_header(df):
    route_name = ''
    bridge_name = ''
    for i in range(min(10, len(df))):
        cell = str(df.iloc[i, 0]) if pd.notna(df.iloc[i, 0]) else ''
        if '路线名称' in cell:
            route_name = cell.replace('路线名称:', '').replace('路线名称：', '').strip()
        if '桥梁名称' in cell and '上部' not in cell and '下部' not in cell:
            bridge_name = cell.replace('桥梁名称:', '').replace('桥梁名称：', '').strip()
    return route_name, bridge_name


# ──────────────────────────────────────────────
# 3. 找构件分区
# ──────────────────────────────────────────────
def find_parts(df):
    """找出每个构件大类的行范围"""
    parts = []
    for i in range(len(df)):
        cell = df.iloc[i, 0]
        if pd.isna(cell):
            continue
        s = str(cell).strip()
        # 构件大类行：含有（）括号，且第一列有值
        if '（' in s and '）' in s and '桥梁名称' not in s and '路线' not in s:
            parts.append({'name': s, 'header_row': i})

    # 计算每个部分的结束行
    for idx, p in enumerate(parts):
        if idx + 1 < len(parts):
            p['end_row'] = parts[idx + 1]['header_row']
        else:
            p['end_row'] = len(df)
        # 数据从 header_row+2 开始（跳过表头行）
        p['data_start'] = p['header_row'] + 2

    return parts


# ──────────────────────────────────────────────
# 4. 解析一个构件区的所有行
# ──────────────────────────────────────────────
def parse_part_rows(df, part):
    rows = []
    for i in range(part['data_start'], part['end_row']):
        r = df.iloc[i]
        # 序号列必须是数字
        seq = r.iloc[0]
        if pd.isna(seq):
            continue
        try:
            seq_int = int(seq)
        except (ValueError, TypeError):
            continue

        comp_id = str(r.iloc[1]).strip() if pd.notna(r.iloc[1]) else ''
        location = str(r.iloc[2]).strip() if pd.notna(r.iloc[2]) else ''
        disease = str(r.iloc[3]).strip() if pd.notna(r.iloc[3]) else ''

        rows.append({
            '序号': seq_int,
            '构件编号': comp_id,
            '位置': location,
            '病害': disease,
        })
    return rows


# ──────────────────────────────────────────────
# 5. 解析病害描述中的结构化位置信息
# ──────────────────────────────────────────────
def parse_disease(desc: str) -> dict:
    result = {
        'raw': desc,
        'part': '',          # 部位
        'x_start': None,
        'x_end': None,
        'y_start': None,
        'y_end': None,
        'disease_type': '',
        'L': None,           # 长度 m
        'W': None,           # 宽度 mm
        'S': None,           # 面积 m2
        'N': None,           # 条数
        'spacing': None,     # 间距 m
    }

    segments = re.split('[，,]', desc)
    if segments:
        result['part'] = segments[0].strip()

    for seg in segments:
        seg = seg.strip()

        # x 范围
        m = re.search(r'x\s*=\s*([\d.]+)\s*[～~]\s*([\d.]+)\s*m', seg)
        if m:
            result['x_start'] = float(m.group(1))
            result['x_end']   = float(m.group(2))

        # y 单值
        m = re.search(r'y\s*=\s*([\d.]+)\s*m(?:[，,]|$|\s)', seg)
        if m and result['y_start'] is None:
            result['y_start'] = float(m.group(1))
            result['y_end']   = float(m.group(1))

        # y 范围
        m = re.search(r'y\s*=\s*([\d.]+)\s*[～~]\s*([\d.]+)\s*m', seg)
        if m:
            result['y_start'] = float(m.group(1))
            result['y_end']   = float(m.group(2))

        # L（长度）
        for pat in [r'L总\s*=\s*([\d.]+)\s*m', r'Lmax\s*=\s*([\d.]+)\s*m', r'L\s*=\s*([\d.]+)\s*m']:
            m = re.search(pat, seg)
            if m:
                result['L'] = float(m.group(1))
                break

        # W（宽度 mm）
        for pat in [r'Wmax\s*=\s*([\d.]+)\s*mm', r'W\s*=\s*([\d.]+)\s*mm']:
            m = re.search(pat, seg)
            if m:
                result['W'] = float(m.group(1))
                break

        # S（面积）
        for pat in [r'S总\s*=\s*([\d.]+)\s*m2', r'S\s*=\s*([\d.]+)\s*m2']:
            m = re.search(pat, seg)
            if m:
                result['S'] = float(m.group(1))
                break

        # N（条数）
        m = re.search(r'N\s*=\s*(\d+)\s*条', seg)
        if m:
            result['N'] = int(m.group(1))

        # 间距
        m = re.search(r'间距([\d.]+)\s*m', seg)
        if m:
            result['spacing'] = float(m.group(1))

        # 病害类型
        for dtype in ['纵向裂缝', '竖向裂缝', '横向裂缝', '网状裂缝',
                      '剥落露筋', '锈胀露筋', '剥落掉角', '剥落', '掉角',
                      '水蚀', '漏筋', '蜂窝', '麻面', '泛白']:
            if dtype in seg:
                result['disease_type'] = dtype
                break

    return result


# ──────────────────────────────────────────────
# 6. 打印
# ──────────────────────────────────────────────
def print_structured(route, bridge, parts_data):
    print()
    print('=' * 80)
    print('【结构化数据】')
    print('=' * 80)
    print(f'  路线名称: {route}')
    print(f'  桥梁名称: {bridge}')
    print()

    for pd_item in parts_data:
        part_name = pd_item['name']
        rows      = pd_item['rows']

        print(f'  +- 构件大类: {part_name}')
        print(f'  |  共 {len(rows)} 条记录')

        # 按构件编号分组
        grouped = defaultdict(list)
        for r in rows:
            grouped[r['构件编号']].append(r)

        for comp_id, comp_rows in grouped.items():
            print(f'  |')
            print(f'  +-- 构件编号: {comp_id}  ({len(comp_rows)} 条病害)')
            for r in comp_rows:
                parsed = parse_disease(r['病害'])
                print(f'  |    序号={r["序号"]}  位置={r["位置"]!r}')
                print(f'  |    病害原文: {r["病害"]}')
                print(f'  |    解析结果:')
                print(f'  |      部位={parsed["part"]!r}')
                print(f'  |      病害类型={parsed["disease_type"]!r}')
                print(f'  |      x=[{parsed["x_start"]}, {parsed["x_end"]}] m')
                print(f'  |      y=[{parsed["y_start"]}, {parsed["y_end"]}] m')
                if parsed['L'] is not None:
                    print(f'  |      L={parsed["L"]} m  ->  CAD单位={parsed["L"]*10:.1f}')
                if parsed['W'] is not None:
                    print(f'  |      W={parsed["W"]} mm')
                if parsed['S'] is not None:
                    print(f'  |      S={parsed["S"]} m2')
                if parsed['N'] is not None:
                    print(f'  |      N={parsed["N"]} 条')
                if parsed['spacing'] is not None:
                    print(f'  |      间距={parsed["spacing"]} m')
                print(f'  |      - - -')
        print()


# ──────────────────────────────────────────────
# 主程序
# ──────────────────────────────────────────────
if __name__ == '__main__':
    df = pd.read_excel(EXCEL_PATH, header=None)

    # 原始预览
    show_raw(df)

    # 解析
    route, bridge = parse_header(df)
    parts_meta    = find_parts(df)

    parts_data = []
    for p in parts_meta:
        rows = parse_part_rows(df, p)
        parts_data.append({'name': p['name'], 'rows': rows})

    # 打印结构化
    print_structured(route, bridge, parts_data)

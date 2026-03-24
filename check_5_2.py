import ezdxf

doc = ezdxf.readfile('output_pages/上部T梁第9页_5-1-5-2.dxf')
msp = doc.modelspace()

# 查找5-2号右翼缘板的剥落标注
print('=== 5-2号 右翼缘板 剥落标注 ===')
for entity in msp:
    if entity.dxftype() == 'TEXT':
        text = entity.dxf.text
        if '剥落' in text and '露筋' not in text:
            print(f'TEXT: "{text}" at ({entity.dxf.insert[0]:.1f}, {entity.dxf.insert[1]:.1f})')
    elif entity.dxftype() == 'MTEXT':
        text = entity.text
        if '剥落' in text and '露筋' not in text:
            print(f'MTEXT: "{text}" at ({entity.dxf.insert[0]:.1f}, {entity.dxf.insert[1]:.1f})')

# 找LINE（引线）
print('\n=== 所有LINE（可能包含引线）===')
for entity in msp:
    if entity.dxftype() == 'LINE':
        start = entity.dxf.start
        end = entity.dxf.end
        # 找靠近(94.8, 126.9)的线
        if 85 < start[0] < 105 and 115 < start[1] < 140:
            print(f'LINE: ({start[0]:.1f}, {start[1]:.1f}) -> ({end[0]:.1f}, {end[1]:.1f})')

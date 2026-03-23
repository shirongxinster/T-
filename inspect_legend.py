# -*- coding: utf-8 -*-
"""查看网状裂缝图例的结构和边界尺寸"""
import ezdxf

def inspect_dxf(path):
    doc = ezdxf.readfile(path)
    ms = doc.modelspace()

    print(f'=== {path} ===')
    xs = []
    ys = []

    for e in ms:
        t = e.dxftype()
        layer = e.dxf.layer if hasattr(e.dxf, 'layer') else '?'

        if t == 'LINE':
            s = e.dxf.start
            end = e.dxf.end
            print(f'  LINE ({s[0]:.3f},{s[1]:.3f}) -> ({end[0]:.3f},{end[1]:.3f})  layer={layer}')
            xs += [s[0], end[0]]
            ys += [s[1], end[1]]
        elif t == 'LWPOLYLINE':
            pts = list(e.get_points())
            closed = e.closed
            print(f'  LWPOLYLINE {len(pts)}pts closed={closed}  layer={layer}')
            for p in pts:
                print(f'    ({p[0]:.3f},{p[1]:.3f})')
                xs.append(p[0])
                ys.append(p[1])
        elif t == 'HATCH':
            print(f'  HATCH pattern={e.dxf.pattern_name}  layer={layer}')
        elif t == 'INSERT':
            ins = e.dxf.insert
            print(f'  INSERT block={e.dxf.name}  pos=({ins[0]:.3f},{ins[1]:.3f})')
        elif t in ('TEXT', 'MTEXT'):
            try:
                txt = e.dxf.text if t == 'TEXT' else e.plain_mtext()[:60]
            except Exception:
                txt = '?'
            ins = e.dxf.insert
            print(f'  {t} "{txt}"  pos=({ins[0]:.3f},{ins[1]:.3f})')
        else:
            print(f'  {t}  layer={layer}')

    if xs:
        print(f'\n  边界: X=[{min(xs):.3f}, {max(xs):.3f}]  Y=[{min(ys):.3f}, {max(ys):.3f}]')
        print(f'  宽度={max(xs)-min(xs):.3f}  高度={max(ys)-min(ys):.3f}')
    print()

if __name__ == '__main__':
    import os
    legend_dir = r'templates\病害图例'
    for fname in os.listdir(legend_dir):
        if fname.endswith('.dxf'):
            inspect_dxf(os.path.join(legend_dir, fname))

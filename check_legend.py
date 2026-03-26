# -*- coding: utf-8 -*-
import ezdxf

# 读取裂缝图例模板
legend_doc = ezdxf.readfile('templates/病害图例/裂缝及其长宽.dxf')
legend_msp = legend_doc.modelspace()

print('裂缝及其长宽图例中的实体:')
for entity in legend_msp:
    entity_type = entity.dxftype()
    if entity_type == 'SPLINE':
        print(f'  SPLINE: control_points={len(entity.control_points)}, fit_points={len(entity.fit_points)}')
        if entity.control_points:
            print(f'    First point: {entity.control_points[0]}')
            print(f'    Last point: {entity.control_points[-1]}')
    elif entity_type == 'LINE':
        print(f'  LINE: ({entity.dxf.start[0]:.1f},{entity.dxf.start[1]:.1f}) -> ({entity.dxf.end[0]:.1f},{entity.dxf.end[1]:.1f})')
    elif entity_type == 'LWPOLYLINE':
        print(f'  LWPOLYLINE')
    elif entity_type in ('TEXT', 'MTEXT'):
        text = entity.dxf.text if entity_type == 'TEXT' else entity.text
        print(f'  {entity_type}: "{text[:30]}..." at ({entity.dxf.insert[0]:.1f},{entity.dxf.insert[1]:.1f})')
    else:
        print(f'  {entity_type}')

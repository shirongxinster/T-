# -*- coding: utf-8 -*-
"""将DWG模板导出为DXF格式"""
import os
import win32com.client

def export_dwg_to_dxf(dwg_path):
    """将DWG文件导出为DXF"""
    if not os.path.exists(dwg_path):
        print(f"文件不存在: {dwg_path}")
        return False
    
    dxf_path = dwg_path.replace('.dwg', '.dxf', 1)
    
    try:
        # 连接浩辰CAD
        cad_app = win32com.client.Dispatch('GstarCAD.Application')
        cad_app.Visible = False
        
        # 打开DWG文件
        doc = cad_app.Documents.Open(os.path.abspath(dwg_path))
        
        # 导出为DXF
        doc.SendCommand(f'-export dxf "{os.path.abspath(dxf_path)}" \n')
        
        # 关闭文档
        doc.Close(False)
        
        # 退出CAD
        cad_app.Quit()
        
        print(f"已导出: {dxf_path}")
        return True
    except Exception as e:
        print(f"导出失败 {dwg_path}: {e}")
        return False

if __name__ == '__main__':
    base_dir = r"k:\works\008.S2ReportAndLayoutPic\leftRealJobs_workbuddy"
    
    # 导出构件模板
    components = [
        os.path.join(base_dir, 'templates', '构件', '40mT梁.dwg'),
        os.path.join(base_dir, 'templates', '构件', '双柱墩.dwg'),
        os.path.join(base_dir, 'templates', '构件', '单柱墩.dwg'),
        os.path.join(base_dir, 'templates', '构件', '不带台身桥台.dwg'),
        os.path.join(base_dir, 'templates', '构件', '带台身桥台.dwg'),
    ]
    
    for dwg_path in components:
        export_dwg_to_dxf(dwg_path)

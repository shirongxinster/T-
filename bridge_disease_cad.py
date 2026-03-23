# -*- coding: utf-8 -*-
"""
桥梁病害CAD标注系统 - CAD处理模块
使用浩辰CAD COM接口操作CAD文件
"""

import os
import win32com.client
import pythoncom
import time
from typing import Dict, Any, Optional, Tuple, List


class CADOperator:
    """浩辰CAD操作类"""
    
    def __init__(self):
        self.cad_app = None
        self.doc = None
        self.modelspace = None
        self.script_commands: List[str] = []  # 存储脚本命令
    
    def start(self, visible: bool = True) -> bool:
        """
        启动浩辰CAD
        
        Args:
            visible: 是否显示CAD窗口
            
        Returns:
            是否启动成功
        """
        try:
            # 尝试连接已运行的浩辰CAD
            self.cad_app = win32com.client.GetActiveObject("GstarCAD.Application")
            print("已连接到运行的浩辰CAD")
        except:
            try:
                # 尝试启动浩辰CAD
                self.cad_app = win32com.client.Dispatch("GstarCAD.Application")
                self.cad_app.Visible = visible
                print("已启动浩辰CAD")
            except Exception as e:
                print(f"启动浩辰CAD失败: {e}")
                return False
        
        return True
    
    def add_script_command(self, command: str):
        """
        添加脚本命令
        
        Args:
            command: CAD命令
        """
        self.script_commands.append(command)
    
    def execute_script(self, dxf_path: str = None) -> bool:
        """
        执行脚本命令并保存到文件
        
        Args:
            dxf_path: 可选的dxf文件路径
            
        Returns:
            是否成功
        """
        if not self.script_commands:
            return True
        
        # 生成脚本文件
        if dxf_path:
            script_path = dxf_path.replace('.dxf', '.scr')
        else:
            script_path = 'temp_script.scr'
        
        try:
            with open(script_path, 'w', encoding='utf-8') as f:
                for cmd in self.script_commands:
                    f.write(cmd + '\n')
            
            print(f"已生成脚本文件: {script_path}")
            
            # 如果CAD已打开，执行脚本
            if self.cad_app and self.doc:
                # 使用脚本文件
                self.doc.SendCommand(f'(load "{script_path}")\n')
                time.sleep(0.5)
            
            return True
        except Exception as e:
            print(f"生成脚本文件失败: {e}")
            return False
    
    def clear_script(self):
        """清空脚本命令"""
        self.script_commands = []
    
    def open_drawing(self, dxf_path: str) -> bool:
        """
        打开CAD图纸
        
        Args:
            dxf_path: CAD文件路径
            
        Returns:
            是否打开成功
        """
        if not self.cad_app:
            print("浩辰CAD未启动")
            return False
        
        try:
            # 如果文件已打开，关闭它
            for doc in self.cad_app.Documents:
                if doc.FullName.lower() == dxf_path.lower():
                    doc.Close(False)
                    break
            
            # 打开文件
            self.doc = self.cad_app.Documents.Open(dxf_path)
            self.modelspace = self.doc.ModelSpace
            return True
        except Exception as e:
            print(f"打开CAD文件失败: {e}")
            return False
    
    def create_new_drawing(self, dxf_path: str, template_path: str = None) -> bool:
        """
        创建新的CAD图纸
        
        Args:
            dxf_path: CAD文件保存路径
            template_path: 可选的模板文件路径
            
        Returns:
            是否创建成功
        """
        if not self.cad_app:
            print("浩辰CAD未启动")
            return False
        
        # 方法1: 使用模板或空白文件
        try:
            if template_path and os.path.exists(template_path):
                print(f"  使用模板创建: {template_path}")
                self.doc = self.cad_app.Documents.Add(template_path)
            else:
                print("  创建空白文档")
                self.doc = self.cad_app.Documents.Add()
            
            self.modelspace = self.doc.ModelSpace
            
            # 保存文件
            self.doc.SaveAs(dxf_path)
            print(f"  文件已保存: {dxf_path}")
            return True
        except Exception as e:
            print(f"  方法1失败: {e}")
        
        # 方法2: 打开现有模板文件然后另存
        try:
            if template_path and os.path.exists(template_path):
                print(f"  方法2: 打开模板文件")
                self.doc = self.cad_app.Documents.Open(template_path)
                self.modelspace = self.doc.ModelSpace
                self.doc.SaveAs(dxf_path)
                print(f"  文件已保存: {dxf_path}")
                return True
        except Exception as e2:
            print(f"  方法2失败: {e2}")
        
        # 方法3: 使用Wblock导出
        try:
            print("  方法3: 尝试创建新文件")
            # 直接创建新文件
            self.doc = self.cad_app.ActiveDocument
            # 另存为
            self.doc.SaveAs(dxf_path)
            return True
        except Exception as e3:
            print(f"  方法3失败: {e3}")
        
            return False
    
    def create_from_template(self, dxf_path: str, template_path: str = None) -> bool:
        """
        从模板创建新的CAD图纸
        
        Args:
            dxf_path: CAD文件保存路径
            template_path: 模板文件路径
            
        Returns:
            是否创建成功
        """
        import shutil
        import time
        
        if not self.cad_app:
            print("浩辰CAD未启动")
            return False
        
        if not template_path or not os.path.exists(template_path):
            print(f"模板文件不存在: {template_path}")
            return False
        
        try:
            # 先关闭任何已打开的同名文件
            self._close_document(dxf_path)
            time.sleep(0.5)  # 等待文件释放
            
            # 方法1: 直接复制文件
            print(f"  复制模板文件到: {dxf_path}")
            shutil.copy2(template_path, dxf_path)
            print(f"  文件已复制")
            time.sleep(0.5)  # 等待文件复制完成
            
            # 打开复制后的文件
            print(f"  打开文件: {dxf_path}")
            self.doc = self.cad_app.Documents.Open(dxf_path)
            self.modelspace = self.doc.ModelSpace
            
            # 统计模板中的实体数量
            entity_count = self.modelspace.Count
            print(f"  文件中有 {entity_count} 个实体")
            
            return True
            
        except Exception as e:
            print(f"从模板创建失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _close_document(self, dxf_path: str):
        """关闭已打开的CAD文档"""
        if not self.cad_app:
            return
        
        try:
            # 遍历所有打开的文档
            for doc in self.cad_app.Documents:
                try:
                    if os.path.abspath(doc.FullName).lower() == os.path.abspath(dxf_path).lower():
                        doc.Close(False)
                        print(f"  已关闭文档: {dxf_path}")
                except:
                    continue
        except:
            pass
    
    def copy_layout_from_template(self, template_path: str, y_offset: float = 0) -> list:
        """
        从模板复制图纸布局到当前文档
        
        Args:
            template_path: 模板文件路径
            y_offset: Y轴偏移量
            
        Returns:
            复制的实体列表（用于后续修改）
        """
        if not self.cad_app:
            print("浩辰CAD未启动")
            return []
        
        copied_entities = []
        
        try:
            # 打开模板文件（以只读方式）
            template_doc = self.cad_app.Documents.Open(template_path)
            template_ms = template_doc.ModelSpace
            
            # 遍历模板中的所有实体并复制到当前文档
            entity_count = template_ms.Count
            print(f"    模板中有 {entity_count} 个实体")
            
            for i in range(entity_count):
                entity = template_ms.Item(i)
                entity_type = entity.EntityName
                
                # 记录实体信息用于后续处理
                copied_entities.append({
                    'type': entity_type,
                    'entity': entity,
                    'original': True
                })
            
            template_doc.Close(False)
            return copied_entities
            
        except Exception as e:
            print(f"从模板复制失败: {e}")
            return []

    def add_entity_from_template(self, template_path: str, y_offset: float = 0) -> bool:
        """
        从模板添加内容到当前文档（带Y偏移）
        
        Args:
            template_path: 模板文件路径
            y_offset: Y轴偏移量
            
        Returns:
            是否成功
        """
        if not self.cad_app or not self.modelspace:
            print("浩辰CAD未初始化")
            return False
        
        try:
            # 打开模板文件
            template_doc = self.cad_app.Documents.Open(template_path)
            template_ms = template_doc.ModelSpace
            
            # 遍历并复制实体
            count = template_ms.Count
            for i in range(count):
                entity = template_ms.Item(i)
                entity_name = entity.EntityName
                
                try:
                    if entity_name == "AcDbText":
                        # 复制单行文字
                        text = entity.TextString
                        pt = entity.InsertionPoint
                        height = entity.Height
                        if pt and len(pt) >= 2:
                            new_pt = (pt[0], pt[1] + y_offset, pt[2] if len(pt) > 2 else 0)
                            new_text = self.modelspace.AddText(text, new_pt, height)
                            if entity.Layer:
                                new_text.Layer = entity.Layer
                                
                    elif entity_name == "AcDbMText":
                        # 复制多行文字
                        text = entity.TextString
                        pt = entity.InsertionPoint
                        if pt and len(pt) >= 2:
                            new_pt = (pt[0], pt[1] + y_offset, pt[2] if len(pt) > 2 else 0)
                            new_mtext = self.modelspace.AddMText(new_pt, 100, text)
                            if entity.Layer:
                                new_mtext.Layer = entity.Layer
                                
                    elif entity_name == "AcDbLine":
                        # 复制直线
                        start = entity.StartPoint
                        end = entity.EndPoint
                        if start and end:
                            new_start = (start[0], start[1] + y_offset)
                            new_end = (end[0], end[1] + y_offset)
                            new_line = self.modelspace.AddLine(new_start, new_end)
                            if entity.Layer:
                                new_line.Layer = entity.Layer
                                
                    elif entity_name == "AcDbPolyline":
                        # 复制多段线
                        points = []
                        if hasattr(entity, 'Coordinates'):
                            coords = entity.Coordinates
                            for j in range(0, len(coords), 2):
                                if j + 1 < len(coords):
                                    points.append((coords[j], coords[j+1] + y_offset))
                        if points:
                            from win32com.client import constants
                            pline = self.modelspace.AddPolyline(points)
                            if entity.Layer:
                                pline.Layer = entity.Layer
                                
                    elif entity_name == "AcDbBlockReference":
                        # 复制图块引用
                        if hasattr(entity, 'InsertionPoint'):
                            pt = entity.InsertionPoint
                            if pt:
                                new_pt = (pt[0], pt[1] + y_offset, pt[2] if len(pt) > 2 else 0)
                                # 检查是否是属性图块
                                if hasattr(entity, 'GetAttributes'):
                                    # 复制图块
                                    block_name = entity.Name
                                    try:
                                        new_block = self.modelspace.InsertBlock(new_pt, block_name, 1, 1, 1, 0)
                                        if entity.Layer:
                                            new_block.Layer = entity.Layer
                                    except:
                                        pass
                                        
                    elif entity_name == "AcDbCircle":
                        # 复制圆
                        center = entity.Center
                        radius = entity.Radius
                        if center and radius:
                            new_center = (center[0], center[1] + y_offset)
                            new_circle = self.modelspace.AddCircle(new_center, radius)
                            if entity.Layer:
                                new_circle.Layer = entity.Layer
                                
                    elif entity_name == "AcDbArc":
                        # 复制圆弧
                        center = entity.Center
                        radius = entity.Radius
                        start_angle = entity.StartAngle
                        end_angle = entity.EndAngle
                        if center:
                            new_center = (center[0], center[1] + y_offset)
                            new_arc = self.modelspace.AddArc(new_center, radius, start_angle, end_angle)
                            if entity.Layer:
                                new_arc.Layer = entity.Layer
                                
                    # 可以继续添加其他实体类型的处理
                    
                except Exception as e2:
                    print(f"    复制实体 {i} 失败: {e2}")
                    continue
            
            template_doc.Close(False)
            print(f"    已从模板复制 {count} 个实体")
            return True
            
        except Exception as e:
            print(f"从模板添加内容失败: {e}")
            return False
    
    def add_text(self, text: str, insertion_point: Tuple[float, float], 
                 height: float = 4.25, layer: str = "0") -> bool:
        """
        添加单行文字
        
        Args:
            text: 文字内容
            insertion_point: 插入点 (x, y)
            height: 文字高度
            layer: 图层
            
        Returns:
            是否添加成功
        """
        if not self.modelspace:
            print("模型空间未初始化")
            return False
        
        try:
            # 创建文字对象
            text_obj = self.modelspace.AddText(text, insertion_point, height)
            text_obj.Layer = layer
            text_obj.style = "宋体"  # 设置字体样式
            return True
        except Exception as e:
            print(f"添加文字失败: {e}")
            return False
    
    def add_mtext(self, text: str, insertion_point: Tuple[float, float],
                  width: float = 100, height: float = 4.25, layer: str = "0") -> bool:
        """
        添加多行文字
        
        Args:
            text: 文字内容
            insertion_point: 插入点 (x, y)
            width: 文字宽度
            height: 文字高度
            layer: 图层
            
        Returns:
            是否添加成功
        """
        if not self.modelspace:
            print("模型空间未初始化")
            return False
        
        try:
            # 创建多行文字对象
            mtext_obj = self.modelspace.AddMText(insertion_point, width, text)
            mtext_obj.Layer = layer
            mtext_obj.style = "宋体"
            mtext_obj.TextHeight = height
            return True
        except Exception as e:
            print(f"添加多行文字失败: {e}")
            return False
    
    def insert_block(self, block_path: str, insertion_point: Tuple[float, float],
                     scale: float = 1.0, rotation: float = 0) -> bool:
        """
        插入图块（病害图例）
        
        Args:
            block_path: 图块文件路径
            insertion_point: 插入点 (x, y)
            scale: 缩放比例
            rotation: 旋转角度（度）
            
        Returns:
            是否插入成功
        """
        if not self.modelspace:
            print("模型空间未初始化")
            return False
        
        try:
            # 插入图块
            block_ref = self.modelspace.InsertBlock(insertion_point, block_path, 
                                                    scale, scale, scale, rotation)
            return True
        except Exception as e:
            print(f"插入图块失败: {e}")
            return False
    
    def draw_line(self, start_point: Tuple[float, float], 
                  end_point: Tuple[float, float], 
                  layer: str = "0") -> bool:
        """
        绘制直线
        
        Args:
            start_point: 起点 (x, y)
            end_point: 终点 (x, y)
            layer: 图层
            
        Returns:
            是否绘制成功
        """
        if not self.modelspace:
            print("模型空间未初始化")
            return False
        
        try:
            line = self.modelspace.AddLine(start_point, end_point)
            line.Layer = layer
            return True
        except Exception as e:
            print(f"绘制直线失败: {e}")
            return False
    
    def draw_rectangle(self, corner: Tuple[float, float], 
                      width: float, height: float, layer: str = "0") -> bool:
        """
        绘制矩形
        
        Args:
            corner: 角点 (x, y)
            width: 宽度
            height: 高度
            layer: 图层
            
        Returns:
            是否绘制成功
        """
        if not self.modelspace:
            print("模型空间未初始化")
            return False
        
        try:
            points = [
                (corner[0], corner[1]),
                (corner[0] + width, corner[1]),
                (corner[0] + width, corner[1] + height),
                (corner[0], corner[1] + height),
                (corner[0], corner[1])
            ]
            
            for i in range(4):
                self.draw_line(points[i], points[i + 1], layer)
            return True
        except Exception as e:
            print(f"绘制矩形失败: {e}")
            return False
    
    def find_text_position(self, search_text: str) -> Optional[Tuple[float, float]]:
        """
        查找文字的位置（用于找到模板中的标注框）
        
        Args:
            search_text: 要搜索的文字
            
        Returns:
            文字的位置 (x, y)，如果未找到则返回 None
        """
        if not self.modelspace:
            return None
        
        try:
            # 遍历模型空间中的文字
            for entity in self.modelspace:
                if entity.EntityName == "AcDbText":
                    if search_text in entity.TextString:
                        return (entity.InsertionPoint[0], entity.InsertionPoint[1])
            return None
        except Exception as e:
            print(f"查找文字失败: {e}")
            return None
    
    def find_all_text_with_prefix(self, prefix: str) -> list:
        """
        查找所有以指定前缀开头的文字
        
        Args:
            prefix: 文字前缀
            
        Returns:
            文字对象列表
        """
        if not self.modelspace:
            return []
        
        results = []
        try:
            for entity in self.modelspace:
                if entity.EntityName == "AcDbText":
                    if entity.TextString and prefix in entity.TextString:
                        results.append({
                            'text': entity.TextString,
                            'position': entity.InsertionPoint,
                            'entity': entity
                        })
        except Exception as e:
            print(f"查找文字失败: {e}")
        
        return results
    
    def get_entity_count(self) -> int:
        """
        获取模型空间中的实体数量
        
        Returns:
            实体数量
        """
        if not self.modelspace:
            return 0
        return self.modelspace.Count
    
    def save(self) -> bool:
        """
        保存当前图纸
        
        Returns:
            是否保存成功
        """
        if not self.doc:
            print("没有打开的文档")
            return False
        
        try:
            self.doc.Save()
            return True
        except Exception as e:
            print(f"保存失败: {e}")
            return False
    
    def save_as(self, dxf_path: str) -> bool:
        """
        另存为
        
        Args:
            dxf_path: 保存路径
            
        Returns:
            是否保存成功
        """
        if not self.doc:
            print("没有打开的文档")
            return False
        
        try:
            self.doc.SaveAs(dxf_path)
            return True
        except Exception as e:
            print(f"另存为失败: {e}")
            return False
    
    def close(self):
        """关闭当前文档"""
        if self.doc:
            try:
                self.doc.Close(False)
            except:
                pass
            self.doc = None
            self.modelspace = None
    
    def quit(self):
        """退出浩辰CAD"""
        if self.cad_app:
            try:
                self.cad_app.Quit()
            except:
                pass
            self.cad_app = None


def convert_dxf_to_internal_units(value: float, unit_type: str = 'length') -> float:
    """
    将实际单位转换为CAD内部单位
    
    根据Prompt.md，标尺的刻度1m = 真实的坐标增加10
    
    Args:
        value: 实际值
        unit_type: 单位类型 ('length' 或 'width')
        
    Returns:
        CAD内部单位
    """
    # 1m = 10 个CAD单位
    return value * 10


def calculate_beam_position(beam_id: str) -> Tuple[str, str, int]:
    """
    从构件编号计算孔次和梁号
    
    Args:
        beam_id: 构件编号，如 "1-1号"
        
    Returns:
        (孔次, 梁号类型, 梁号列表)
    """
    import re
    
    # 解析构件编号
    match = re.match(r'(\d+)-(\d+)号', beam_id)
    if match:
        hole = match.group(1)
        num = int(match.group(2))
        return (hole, 'single', [num])
    
    return ('', '', [])


def group_tbeams_by_hole(beam_ids: list) -> Dict[str, list]:
    """
    将T梁构件按孔次分组
    
    Args:
        beam_ids: 构件编号列表
        
    Returns:
        按孔次分组的字典
    """
    import re
    from collections import defaultdict
    
    grouped = defaultdict(list)
    
    for beam_id in beam_ids:
        match = re.match(r'(\d+)-(\d+)号', beam_id)
        if match:
            hole = match.group(1)
            num = int(match.group(2))
            grouped[hole].append((beam_id, num))
    
    # 对每个孔次的梁进行排序
    for hole in grouped:
        grouped[hole].sort(key=lambda x: x[1])
    
    return dict(grouped)


def pair_tbeams(beam_ids_with_nums: list) -> list:
    """
    将T梁配对（每两个梁一对，但按顺序分配到不同图纸）
    
    例如：梁号 [1,2,3,4,5] -> [[1,2], [3,4], [5]]
    不是 [1,2], [3,4], [5] 的简单连续配对，而是:
    第1张图: 梁1,2
    第2张图: 梁3,4  
    第3张图: 梁5
    
    Args:
        beam_ids_with_nums: [(构件编号, 梁号数字), ...]
        
    Returns:
        对列表 [[(id1, num1), (id2, num2)], ...]
    """
    # 按梁号排序
    sorted_beams = sorted(beam_ids_with_nums, key=lambda x: x[1])
    
    pairs = []
    for i in range(0, len(sorted_beams), 2):
        if i + 1 < len(sorted_beams):
            # 每两个梁配一对
            pairs.append([sorted_beams[i], sorted_beams[i + 1]])
        else:
            # 奇数个梁，最后一个单独一组
            pairs.append([sorted_beams[i]])
    
    return pairs


class EZDXFOperator:
    """使用ezdxf库操作dxf/DXF文件"""
    
    def __init__(self):
        try:
            import ezdxf
            self.ezdxf = ezdxf
        except ImportError:
            print("错误: ezdxf库未安装")
            print("请运行: pip install ezdxf")
            self.ezdxf = None
        self.doc = None
        self.modelspace = None
        self.output_path = ""
        self.output_dxf_path = ""  # DXF输出路径
    
    def start(self, visible: bool = True) -> bool:
        """启动（ezdxf不需要启动CAD）"""
        return True
    
    def _find_dxf_file(self, dxf_path: str) -> str:
        """
        查找对应的DXF文件
        
        Args:
            dxf_path: dxf文件路径
            
        Returns:
            DXF文件路径，如果不存在则返回原路径
        """
        # 替换后缀为dxf
        dxf_path = dxf_path.replace('.dxf', '.dxf', 1)
        if os.path.exists(dxf_path):
            return dxf_path
        return dxf_path
    
    def create_from_template(self, dxf_path: str, template_path: str = None) -> bool:
        """
        从模板创建新文件（支持dxf和DXF模板）
        优先使用DXF文件，如果不存在则尝试dxf文件
        
        Args:
            dxf_path: 输出文件路径
            template_path: 模板文件路径（dxf或DXF）
            
        Returns:
            是否成功
        """
        if not self.ezdxf:
            return False
        
        # 优先查找DXF文件
        actual_template_path = template_path
        if template_path and os.path.exists(template_path):
            # 尝试找对应的DXF文件
            dxf_version = template_path.replace('.dxf', '.dxf', 1)
            if os.path.exists(dxf_version):
                actual_template_path = dxf_version
                print(f"  找到DXF模板: {actual_template_path}")
            else:
                print(f"  使用dxf模板: {template_path}")
                print(f"  警告: 建议将dxf模板导出为DXF格式以获得更好的兼容性")
        
        try:
            if actual_template_path and os.path.exists(actual_template_path):
                # 读取模板文件
                print(f"  读取模板: {actual_template_path}")
                self.doc = self.ezdxf.readfile(actual_template_path)
            else:
                # 创建新文档
                print("  创建空白文档")
                self.doc = self.ezdxf.new('R2010')
            
            self.modelspace = self.doc.modelspace()
            
            # 设置输出路径（改为dxf后缀）
            base_name = os.path.splitext(dxf_path)[0]
            self.output_dxf_path = base_name + '.dxf'
            self.output_path = dxf_path
            
            print(f"  已加载模板")
            return True
        except Exception as e:
            print(f"从模板创建失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def copy_entities_from_template(self, template_path: str, y_offset: float = 0) -> bool:
        """
        从DXF/dxf模板复制实体到当前文档（带Y偏移）
        
        Args:
            template_path: 模板文件路径
            y_offset: Y轴偏移量
            
        Returns:
            是否成功
        """
        if not self.ezdxf or not self.doc:
            print("ezdxf未初始化")
            return False
        
        # 优先查找DXF文件
        actual_template_path = template_path
        dxf_version = template_path.replace('.dxf', '.dxf', 1)
        if os.path.exists(dxf_version):
            actual_template_path = dxf_version
        
        try:
            # 读取模板文件
            print(f"    读取模板: {actual_template_path}")
            template_doc = self.ezdxf.readfile(actual_template_path)
            template_ms = template_doc.modelspace()
            
            # 遍历模板中的所有实体并复制
            entity_count = 0
            for entity in template_ms:
                try:
                    # 复制实体并应用Y偏移
                    new_entity = self._copy_entity_with_offset(entity, y_offset)
                    if new_entity:
                        entity_count += 1
                except Exception as e:
                    print(f"    复制实体失败: {e}")
                    continue
            
            print(f"    已复制 {entity_count} 个实体")
            return True
            
        except Exception as e:
            print(f"从模板复制失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _copy_entity_with_offset(self, entity, y_offset: float):
        """
        复制实体并应用Y偏移
        
        Args:
            entity: 源实体
            y_offset: Y轴偏移量
            
        Returns:
            复制的新实体
        """
        try:
            entity_type = entity.dxftype()
            
            # 获取原始图层和颜色
            layer = entity.dxf.layer if hasattr(entity.dxf, 'layer') else '0'
            color = entity.dxf.color if hasattr(entity.dxf, 'color') else 7
            
            if entity_type == 'TEXT':
                # 单行文字
                text = entity.dxf.text
                height = entity.dxf.height if hasattr(entity.dxf, 'height') else 2.5
                
                # 获取位置
                if hasattr(entity.dxf, 'insert'):
                    old_x, old_y = entity.dxf.insert[0], entity.dxf.insert[1]
                    new_pos = (old_x, old_y + y_offset)
                elif hasattr(entity.dxf, 'p1'):
                    old_x, old_y = entity.dxf.p1[0], entity.dxf.p1[1]
                    new_pos = (old_x, old_y + y_offset)
                else:
                    new_pos = (0, 0)
                
                text_obj = self.modelspace.add_text(
                    text,
                    dxfattribs={'layer': layer, 'color': color, 'height': height}
                )
                text_obj.dxf.insert = new_pos
                return text_obj
                
            elif entity_type == 'MTEXT':
                # 多行文字
                text = entity.text
                char_height = entity.dxf.char_height if hasattr(entity.dxf, 'char_height') else 2.5
                width = entity.dxf.width if hasattr(entity.dxf, 'width') else 100
                
                # 获取位置
                if hasattr(entity.dxf, 'insert'):
                    old_x, old_y = entity.dxf.insert[0], entity.dxf.insert[1]
                    new_pos = (old_x, old_y + y_offset)
                else:
                    new_pos = (0, 0)
                
                mtext_obj = self.modelspace.add_mtext(
                    text,
                    dxfattribs={'layer': layer, 'color': color, 'char_height': char_height, 'width': width}
                )
                mtext_obj.dxf.insert = new_pos
                return mtext_obj
                
            elif entity_type == 'LINE':
                # 直线
                start = entity.dxf.start
                end = entity.dxf.end
                new_start = (start[0], start[1] + y_offset)
                new_end = (end[0], end[1] + y_offset)
                return self.modelspace.add_line(new_start, new_end, dxfattribs={'layer': layer, 'color': color})
                
            elif entity_type == 'POLYLINE':
                # 多段线
                points = []
                if hasattr(entity, 'points'):
                    for pt in entity.points:
                        points.append((pt[0], pt[1] + y_offset))
                if points:
                    return self.modelspace.add_polyline2d(points, dxfattribs={'layer': layer, 'color': color})
                return None
                
            elif entity_type == 'CIRCLE':
                # 圆
                center = entity.dxf.center
                radius = entity.dxf.radius
                new_center = (center[0], center[1] + y_offset)
                return self.modelspace.add_circle(new_center, radius, dxfattribs={'layer': layer, 'color': color})
                
            elif entity_type == 'ARC':
                # 圆弧
                center = entity.dxf.center
                radius = entity.dxf.radius
                start_angle = entity.dxf.start_angle
                end_angle = entity.dxf.end_angle
                new_center = (center[0], center[1] + y_offset)
                return self.modelspace.add_arc(new_center, radius, start_angle, end_angle, dxfattribs={'layer': layer, 'color': color})
                
            elif entity_type == 'LWPOLYLINE':
                # 轻量多段线
                points = []
                if hasattr(entity, 'get_points'):
                    for pt in entity.get_points():
                        points.append((pt[0], pt[1] + y_offset))
                if points:
                    return self.modelspace.add_lwpolyline(points, dxfattribs={'layer': layer, 'color': color})
                return None
                
            elif entity_type == 'INSERT':
                # 图块引用
                name = entity.dxf.name
                insert = entity.dxf.insert
                xscale = entity.dxf.xscale if hasattr(entity.dxf, 'xscale') else 1
                yscale = entity.dxf.yscale if hasattr(entity.dxf, 'yscale') else 1
                rotation = entity.dxf.rotation if hasattr(entity.dxf, 'rotation') else 0
                new_insert = (insert[0], insert[1] + y_offset)
                return self.modelspace.add_blockref(name, new_insert, dxfattribs={
                    'layer': layer, 'color': color, 'xscale': xscale, 'yscale': yscale, 'zscale': 1, 'rotation': rotation
                })
            
            # 其他类型暂时跳过
            return None
            
        except Exception as e:
            print(f"    复制实体类型{entity.dxftype()}失败: {e}")
            return None
    
    def add_text(self, text: str, insertion_point: Tuple[float, float],
                 height: float = 4.25, layer: str = "0") -> bool:
        """添加单行文字"""
        if not self.doc or not self.modelspace:
            return False
        
        try:
            text_obj = self.modelspace.add_text(
                text,
                dxfattribs={'layer': layer, 'height': height, 'color': 7}
            )
            # 设置位置
            text_obj.dxf.insert = insertion_point
            return True
        except Exception as e:
            print(f"添加文字失败: {e}")
            return False
    
    def add_mtext(self, text: str, insertion_point: Tuple[float, float],
                  width: float = 100, height: float = 4.25, layer: str = "0") -> bool:
        """添加多行文字"""
        if not self.doc or not self.modelspace:
            return False
        
        try:
            mtext_obj = self.modelspace.add_mtext(
                text,
                dxfattribs={'layer': layer, 'char_height': height, 'width': width, 'color': 7}
            )
            # 设置位置
            mtext_obj.dxf.insert = insertion_point
            return True
        except Exception as e:
            print(f"添加多行文字失败: {e}")
            return False
    
    def add_line(self, start: Tuple[float, float], end: Tuple[float, float],
                 layer: str = "0") -> bool:
        """添加直线"""
        if not self.doc or not self.modelspace:
            return False
        
        try:
            self.modelspace.add_line(start, end, dxfattribs={'layer': layer})
            return True
        except Exception as e:
            print(f"添加直线失败: {e}")
            return False

    def add_mesh_crack(self, x1: float, y_top: float, x2: float, y_bottom: float,
                       legends_dir: str, layer: str = "病害") -> bool:
        """
        在指定矩形范围内平铺网状裂缝纹理。
        
        策略：
        1. 读取 网状裂缝.dxf，提取其中所有 SPLINE/LINE 的边界框。
        2. 计算目标矩形大小，算出 x/y 缩放比例，将图例平铺满整个区域。
        3. 每个 tile 都复制一份缩放后的实体到 modelspace。
        
        Args:
            x1, y_top  : 矩形左上角 CAD 坐标
            x2, y_bottom: 矩形右下角 CAD 坐标
            legends_dir : 病害图例目录
            layer       : 目标图层
        """
        if not self.doc or not self.modelspace:
            return False

        legend_path = os.path.join(legends_dir, '网状裂缝.dxf')
        if not os.path.exists(legend_path):
            print(f"  网状裂缝图例不存在: {legend_path}")
            return False

        try:
            legend_doc = self.ezdxf.readfile(legend_path)
            legend_ms  = legend_doc.modelspace()

            # ── 收集图例中所有 SPLINE 的控制点（或近似点）以及 LINE ──
            entities_data = []
            all_xs, all_ys = [], []

            for ent in legend_ms:
                t = ent.dxftype()
                if t == 'SPLINE':
                    try:
                        pts = list(ent.control_points)
                    except Exception:
                        try:
                            pts = list(ent.fit_points)
                        except Exception:
                            pts = []
                    if pts:
                        entities_data.append(('SPLINE_CTRL', pts))
                        for p in pts:
                            all_xs.append(p[0]); all_ys.append(p[1])
                elif t == 'LINE':
                    s = ent.dxf.start
                    e = ent.dxf.end
                    entities_data.append(('LINE', (s, e)))
                    all_xs += [s[0], e[0]]; all_ys += [s[1], e[1]]
                elif t == 'LWPOLYLINE':
                    pts = [(p[0], p[1]) for p in ent.get_points()]
                    if pts:
                        entities_data.append(('LWPOLY', pts))
                        for p in pts:
                            all_xs.append(p[0]); all_ys.append(p[1])

            if not all_xs:
                print("  网状裂缝图例中没有可用的几何数据")
                return False

            # 图例原始边界
            leg_x_min, leg_x_max = min(all_xs), max(all_xs)
            leg_y_min, leg_y_max = min(all_ys), max(all_ys)
            leg_w = leg_x_max - leg_x_min
            leg_h = leg_y_max - leg_y_min

            if leg_w < 1e-6 or leg_h < 1e-6:
                print(f"  图例边界过小: w={leg_w}, h={leg_h}")
                return False

            print(f"  图例边界: x=[{leg_x_min:.2f},{leg_x_max:.2f}] y=[{leg_y_min:.2f},{leg_y_max:.2f}]")
            print(f"  图例尺寸: {leg_w:.2f} x {leg_h:.2f}")

            # 目标矩形
            rect_w = abs(x2 - x1)
            rect_h = abs(y_bottom - y_top)  # y_top < y_bottom in CAD (向上为正), 这里 y_top 更小
            # 修正: y_top 是 CAD 中的 min Y（上方）, y_bottom 是 max Y
            cad_y_min = min(y_top, y_bottom)
            cad_y_max = max(y_top, y_bottom)
            rect_h = cad_y_max - cad_y_min

            print(f"  目标矩形: x=[{x1:.1f},{x2:.1f}] y=[{cad_y_min:.1f},{cad_y_max:.1f}]")
            print(f"  目标尺寸: {rect_w:.1f} x {rect_h:.1f}")

            # ── 平铺策略：先确定单块 tile 的缩放比例 ──
            # 让图例宽高缩放到约 rect_w/3 × rect_h/2 的 tile 尺寸（保持比例）
            # 即在 x 方向约铺 3 块，y 方向约铺 2 块
            TILES_X = max(1, int(round(rect_w / leg_w)))  # 实际按 1:1 铺满
            TILES_Y = max(1, int(round(rect_h / leg_h)))

            tile_w = rect_w / TILES_X
            tile_h = rect_h / TILES_Y
            sx = tile_w / leg_w  # x 缩放
            sy = tile_h / leg_h  # y 缩放

            print(f"  平铺: {TILES_X} x {TILES_Y} 块，单块缩放 sx={sx:.3f} sy={sy:.3f}")

            def transform_point(px, py, tile_col, tile_row):
                """将图例坐标变换到对应 tile 位置"""
                # 归一化到 [0,1]
                nx = (px - leg_x_min) / leg_w
                ny = (py - leg_y_min) / leg_h
                # 映射到 tile 区域
                new_x = x1 + (tile_col + nx) * tile_w
                new_y = cad_y_min + (tile_row + ny) * tile_h
                return new_x, new_y

            # ── 绘制 ──
            count = 0
            for row in range(TILES_Y):
                for col in range(TILES_X):
                    for ent_type, ent_data in entities_data:
                        try:
                            if ent_type == 'LINE':
                                s, e = ent_data
                                ns = transform_point(s[0], s[1], col, row)
                                ne = transform_point(e[0], e[1], col, row)
                                self.modelspace.add_line(ns, ne, dxfattribs={'layer': layer})
                                count += 1
                            elif ent_type in ('SPLINE_CTRL', 'LWPOLY'):
                                pts = ent_data
                                new_pts = [transform_point(p[0], p[1], col, row) for p in pts]
                                # 用折线近似代替 SPLINE
                                if len(new_pts) >= 2:
                                    self.modelspace.add_lwpolyline(new_pts, dxfattribs={'layer': layer})
                                    count += 1
                        except Exception as draw_err:
                            print(f"    tile({col},{row}) 绘制失败: {draw_err}")

            print(f"  网状裂缝共绘制 {count} 个实体")
            return True

        except Exception as e:
            print(f"add_mesh_crack 失败: {e}")
            import traceback; traceback.print_exc()
            return False
    
    def insert_block(self, block_path: str, insertion_point: Tuple[float, float],
                     scale: float = 1.0, rotation: float = 0) -> bool:
        """插入图块"""
        if not self.doc or not self.modelspace:
            return False
        
        # 优先查找DXF文件
        actual_block_path = block_path
        dxf_version = block_path.replace('.dxf', '.dxf', 1)
        if os.path.exists(dxf_version):
            actual_block_path = dxf_version
        
        try:
            # 读取图块文件
            block_doc = self.ezdxf.readfile(actual_block_path)
            block_name = os.path.splitext(os.path.basename(actual_block_path))[0]
            
            # 检查图块是否已存在
            if block_name not in self.doc.blocks:
                # 定义图块 - 使用正确的API
                block = self.doc.blocks.new(block_name)
                # 复制图块内容 - 使用add_entity而不是add
                for entity in block_doc.modelspace():
                    block.add_entity(entity)
            
            # 插入图块引用
            self.modelspace.add_blockref(
                block_name,
                insertion_point,
                dxfattribs={'xscale': scale, 'yscale': scale, 'zscale': scale, 'rotation': rotation}
            )
            return True
        except Exception as e:
            print(f"插入图块失败: {e}")
            return False
    
    def save(self) -> bool:
        """保存文件为DXF格式"""
        if not self.doc:
            return False
        
        try:
            # 保存为DXF格式
            save_path = self.output_dxf_path if self.output_dxf_path else self.output_path
            # 确保后缀是dxf
            if not save_path.lower().endswith('.dxf'):
                save_path = save_path.rsplit('.', 1)[0] + '.dxf'
            
            self.doc.saveas(save_path)
            print(f"文件已保存: {save_path}")
            return True
        except Exception as e:
            print(f"保存失败: {e}")
            return False
    
    def close(self):
        """关闭文档"""
        if self.doc:
            self.doc = None
            self.modelspace = None


if __name__ == '__main__':
    # 测试
    cad = CADOperator()
    print("CAD操作类已创建")

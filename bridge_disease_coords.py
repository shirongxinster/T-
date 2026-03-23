# -*- coding: utf-8 -*-
"""
桥梁病害CAD标注系统 - 坐标转换模块
根据模板中的标尺体系计算病害的实际坐标
"""

from typing import Dict, Tuple, Any, Optional


# T梁模板坐标系配置
# 每个部件的原点位置和坐标轴方向需要根据实际模板确定
# 这里的配置是基于Prompt.md中的描述

# 标尺刻度与实际坐标的换算比例
SCALE_RATIO = 10  # 1m = 10 个CAD单位


class TBeamCoordinateSystem:
    """T梁坐标系"""
    
    def __init__(self, upper_beam: bool = True):
        """
        初始化T梁坐标系
        
        Args:
            upper_beam: 是否是上方的T梁（影响原点的Y坐标）
        """
        self.upper_beam = upper_beam
        
        # 这些坐标需要从模板中实际测量得到
        # 这里先定义默认的参考点，实际使用时需要从模板读取
        self.reference_x = 0  # 横向标尺0的X坐标
        # 纵向标尺位置（Y坐标）
        self.scale_1_y = 0      # 梁底的纵向标尺
        self.scale_225_y = 0     # 翼缘板/腹板的纵向标尺
    
    def set_reference_points(self, scale_0_x: float, scale_1_y: float, 
                            scale_225_y: float):
        """
        设置参考点坐标
        
        Args:
            scale_0_x: 横向标尺0的X坐标
            scale_1_y: 纵向标尺1的Y坐标（梁底）
            scale_225_y: 纵向标尺2.25的Y坐标（翼缘板/腹板）
        """
        self.reference_x = scale_0_x
        self.scale_1_y = scale_1_y
        self.scale_225_y = scale_225_y
    
    def convert_to_global(self, part: str, x: float, y: float) -> Tuple[float, float]:
        """
        将部件的相对坐标转换为全局坐标
        
        Args:
            part: 部件名称（梁底、左翼缘板、右翼缘板、左腹板、右腹板）
            x: 相对X坐标（米）
            y: 相对Y坐标（米）
            
        Returns:
            全局坐标 (x, y)
        """
        # 转换为CAD单位
        dx = x * SCALE_RATIO
        dy = y * SCALE_RATIO
        
        # 根据部件确定原点
        if part == '梁底':
            origin_x = self.reference_x
            origin_y = self.scale_1_y if self.upper_beam else self.scale_1_y + 100  # 下方梁的Y坐标不同
            # 梁底的坐标系统：x从左到右，y从上到下
            return (origin_x + dx, origin_y + dy)
        
        elif part == '左翼缘板':
            origin_x = self.reference_x
            origin_y = self.scale_225_y if self.upper_beam else self.scale_225_y + 100
            # 左翼缘板：x从左到右，y从下到上
            return (origin_x + dx, origin_y - dy)
        
        elif part == '右翼缘板':
            origin_x = self.reference_x
            # 右翼缘板的Y坐标需要根据模板确定
            origin_y = self.scale_225_y + 50 if self.upper_beam else self.scale_225_y + 150
            # 右翼缘板：x从左到右，y从上到下
            return (origin_x + dx, origin_y + dy)
        
        elif part == '左腹板':
            origin_x = self.reference_x
            origin_y = self.scale_225_y + 100 if self.upper_beam else self.scale_225_y + 200
            # 左腹板：x从左到右，y从下到上
            return (origin_x + dx, origin_y - dy)
        
        elif part == '右腹板':
            origin_x = self.reference_x
            origin_y = self.scale_225_y + 150 if self.upper_beam else self.scale_225_y + 250
            # 右腹板：x从左到右，y从下到上
            return (origin_x + dx, origin_y - dy)
        
        else:
            # 默认返回原点
            return (self.reference_x + dx, self.scale_1_y + dy)


class PierCoordinateSystem:
    """墩柱坐标系"""
    
    def __init__(self):
        self.girder_origin = (0, 0)  # 盖梁原点
        self.pier_origin = (0, 0)     # 墩柱原点
    
    def set_reference_points(self, girder_origin: Tuple[float, float],
                            pier_origin: Tuple[float, float]):
        """
        设置参考点坐标
        
        Args:
            girder_origin: 盖梁原点
            pier_origin: 墩柱原点
        """
        self.girder_origin = girder_origin
        self.pier_origin = pier_origin
    
    def convert_to_global(self, part: str, x: float, y: float) -> Tuple[float, float]:
        """
        将相对坐标转换为全局坐标
        
        Args:
            part: 部件名称（盖梁、墩柱）
            x: 相对X坐标
            y: 相对Y坐标
            
        Returns:
            全局坐标
        """
        dx = x * SCALE_RATIO
        dy = y * SCALE_RATIO
        
        if part == '盖梁':
            return (self.girder_origin[0] + dx, self.girder_origin[1] + dy)
        elif part == '墩柱':
            return (self.pier_origin[0] + dx, self.pier_origin[1] + dy)
        else:
            return (self.girder_origin[0] + dx, self.girder_origin[1] + dy)


class AbutmentCoordinateSystem:
    """桥台坐标系"""
    
    def __init__(self):
        self.abutment_origin = (0, 0)  # 桥台原点
    
    def set_reference_points(self, abutment_origin: Tuple[float, float]):
        """
        设置参考点坐标
        
        Args:
            abutment_origin: 桥台原点
        """
        self.abutment_origin = abutment_origin
    
    def convert_to_global(self, x: float, y: float) -> Tuple[float, float]:
        """
        将相对坐标转换为全局坐标
        
        Args:
            x: 相对X坐标
            y: 相对Y坐标
            
        Returns:
            全局坐标
        """
        dx = x * SCALE_RATIO
        dy = y * SCALE_RATIO
        return (self.abutment_origin[0] + dx, self.abutment_origin[1] + dy)


def calculate_legend_size(disease_info: Dict[str, Any]) -> Tuple[float, float]:
    """
    根据病害信息计算图例的大小
    
    Args:
        disease_info: 病害信息字典
        
    Returns:
        (宽度, 高度)
    """
    # 裂缝：使用长度和宽度
    if disease_info.get('length', 0) > 0:
        length = disease_info['length'] * SCALE_RATIO
        width = disease_info.get('width', 0.1) * SCALE_RATIO
        return (length, max(width, 1))  # 最小宽度为1
    
    # 剥落、网状裂缝等：使用面积
    if disease_info.get('area', 0) > 0:
        import math
        area = disease_info['area']
        # 假设是正方形区域
        size = math.sqrt(area) * SCALE_RATIO
        return (size, size)
    
    return (10, 10)  # 默认大小


def calculate_crack_positions(start_x: float, end_x: float, start_y: float, 
                             end_y: float, count: int, spacing: float) -> list:
    """
    计算多条裂缝的位置
    
    Args:
        start_x: 起始X坐标
        end_x: 结束X坐标
        start_y: 起始Y坐标
        end_y: 结束Y坐标
        count: 裂缝数量
        spacing: 间距（米）
        
    Returns:
        裂缝位置列表 [(x1, y1), (x2, y2), ...]
    """
    positions = []
    
    if count <= 1:
        positions.append(((start_x + end_x) / 2 * SCALE_RATIO, 
                        (start_y + end_y) / 2 * SCALE_RATIO))
        return positions
    
    # 计算间距
    dx = end_x - start_x
    dy = end_y - start_y
    
    # 间距转换为CAD单位
    spacing_cad = spacing * SCALE_RATIO
    
    for i in range(count):
        t = i / (count - 1) if count > 1 else 0
        x = start_x + dx * t
        y = start_y + dy * t
        positions.append((x * SCALE_RATIO, y * SCALE_RATIO))
    
    return positions


# 模板标尺参考点（需要从模板文件中测量）
# 这些值是示例值，实际使用时需要根据模板文件确定

# T梁模板参考坐标
TBEAM_TEMPLATE_REFERENCE = {
    'upper': {
        'scale_0_x': 180,    # 横向标尺0的X坐标
        'scale_1_y': 130,    # 梁底的纵向标尺1的Y坐标
        'scale_225_y': 180,  # 翼缘板的纵向标尺2.25的Y坐标
    },
    'lower': {
        'scale_0_x': 180,
        'scale_1_y': 380,    # 下方梁的梁底Y坐标
        'scale_225_y': 430,
    }
}


def create_coordinate_system(part_type: str, beam_position: str = 'upper'):
    """
    创建坐标系统
    
    Args:
        part_type: 构件类型
        beam_position: 梁位置 ('upper' 或 'lower')
        
    Returns:
        坐标系统对象
    """
    if 'T梁' in part_type:
        cs = TBeamCoordinateSystem(upper_beam=(beam_position == 'upper'))
        ref = TBEAM_TEMPLATE_REFERENCE[beam_position]
        cs.set_reference_points(ref['scale_0_x'], ref['scale_1_y'], ref['scale_225_y'])
        return cs
    elif '双柱墩' in part_type or '单柱墩' in part_type:
        return PierCoordinateSystem()
    elif '桥台' in part_type:
        return AbutmentCoordinateSystem()
    else:
        return None


if __name__ == '__main__':
    # 测试坐标系
    cs = TBeamCoordinateSystem(upper_beam=True)
    cs.set_reference_points(180, 130, 180)
    
    # 测试坐标转换
    result = cs.convert_to_global('梁底', 12, 0.5)
    print(f"梁底坐标 (x=12m, y=0.5m) -> 全局坐标: {result}")
    
    result = cs.convert_to_global('左翼缘板', 0.4, 0.5)
    print(f"左翼缘板坐标 (x=0.4m, y=0.5m) -> 全局坐标: {result}")

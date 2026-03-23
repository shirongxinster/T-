# -*- coding: utf-8 -*-
"""
桥梁病害CAD标注系统 - 主程序
整合所有模块，生成最终的CAD文件
"""

import os
import sys
import re
from collections import defaultdict

# 导入模块
from bridge_disease_parser import parse_excel, get_template_name, get_legend_name, parse_disease_position
from bridge_disease_cad import CADOperator, EZDXFOperator, convert_dxf_to_internal_units, group_tbeams_by_hole, pair_tbeams
from bridge_disease_coords import create_coordinate_system, calculate_legend_size, calculate_crack_positions


# 配置路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
COMPONENTS_DIR = os.path.join(TEMPLATES_DIR, '构件')
LEGENDS_DIR = os.path.join(TEMPLATES_DIR, '病害图例')


# CAD操作模式
USE_EZDXF = True  # 设为True使用ezdxf（DXF格式），False使用GstarCAD COM
USE_MULTI_FILE = False  # 设为True使用多文件模式，False使用单文件模式（合并所有图到一个DXF文件）


class BridgeDiseaseCADGenerator:
    """桥梁病害CAD标注生成器"""
    
    def __init__(self, excel_path: str):
        """
        初始化生成器
        
        Args:
            excel_path: Excel文件路径
        """
        self.excel_path = excel_path
        self.data = None
        
        # 根据设置选择CAD操作类
        if USE_EZDXF:
            self.cad = EZDXFOperator()
            print("使用ezdxf模式")
        else:
            self.cad = CADOperator()
            print("使用GstarCAD COM模式")
        
        self.output_path = ''
        self.page_files = []  # 存储每页的文件路径
        
    def load_data(self):
        """加载Excel数据"""
        self.data = parse_excel(self.excel_path)
        print(f"已加载数据：{self.data['bridge_name']}")
        print(f"路线名称：{self.data['route_name']}")
        
        # 设置输出文件路径（DXF格式）
        base_name = os.path.basename(self.excel_path)
        output_name = base_name.replace('.xls', '_output.dxf').replace('.xlsx', '_output.dxf')
        self.output_path = os.path.join(BASE_DIR, output_name)
        
    def start_cad(self, visible: bool = True):
        """启动CAD（仅GstarCAD模式需要）"""
        if USE_EZDXF:
            return True  # ezdxf不需要启动CAD
        return self.cad.start(visible)
    
    def process(self):
        """处理所有构件并生成CAD文件"""
        if not self.data:
            print("请先加载数据")
            return False
        
        if USE_MULTI_FILE:
            # 多文件模式：为每对梁创建独立的dxf文件
            return self._process_multi_file()
        else:
            # 单文件模式：将所有内容放在一个文件中
            return self._process_single_file()
    
    def _process_multi_file(self):
        """多文件处理模式：为每对梁创建独立的dxf文件"""
        import shutil
        
        # 创建输出文件夹
        output_dir = os.path.join(BASE_DIR, 'output_pages')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        page_count = 0
        
        # 处理每个构件类型
        for part in self.data['parts']:
            part_name = part['name']
            template_name = part['template_name']
            grouped_data = part['grouped_data']
            
            if not grouped_data:
                continue
            
            template_path = os.path.join(COMPONENTS_DIR, template_name)
            if not os.path.exists(template_path):
                print(f"警告: 模板文件不存在 - {template_path}")
                continue
            
            print(f"\n处理构件类型: {part_name}")
            
            # 根据构件类型处理
            if 'T梁' in part_name:
                # 按孔次分组
                hole_groups = group_tbeams_by_hole(list(grouped_data.keys()))
                
                for hole, beams in hole_groups.items():
                    # 将该孔的梁配对
                    beam_pairs = pair_tbeams(beams)
                    
                    for idx, pair in enumerate(beam_pairs):
                        page_count += 1
                        # 创建文件名：桥梁名_孔次_第几张.dxf
                        beam_nums = '_'.join([str(b[1]) for b in pair])
                        filename = f"{self.data['bridge_name']}_孔{hole}_{beam_nums}号.dxf"
                        output_path = os.path.join(output_dir, filename)
                        
                        # 复制模板文件
                        shutil.copy2(template_path, output_path)
                        self.page_files.append(output_path)
                        print(f"  已创建: 孔{hole}, 梁 {beam_nums}号 -> {filename}")
        
        print(f"\n共创建 {page_count} 个文件")
        print(f"输出目录: {output_dir}")
        
        # 显示结果
        print("\n创建的文件列表:")
        for i, f in enumerate(self.page_files, 1):
            print(f"  {i}. {os.path.basename(f)}")
        
        return True
    
    def _process_single_file(self):
        """单文件处理模式：将所有内容放在一个文件中"""
        # 尝试使用模板文件创建
        template_path = None
        if self.data['parts'] and self.data['parts'][0]['template_name']:
            template_path = os.path.join(COMPONENTS_DIR, self.data['parts'][0]['template_name'])
        
        # 第一次创建文件
        if not self.cad.create_from_template(self.output_path, template_path):
            print("创建CAD文件失败")
            return False
        
        print(f"已创建CAD文件: {self.output_path}")
        
        # 当前Y偏移量
        current_y_offset = 0
        first_page = True
        
        # 处理每个构件类型
        for part in self.data['parts']:
            part_name = part['name']
            template_name = part['template_name']
            grouped_data = part['grouped_data']
            
            print(f"\n处理构件类型: {part_name}")
            print(f"模板: {template_name}")
            print(f"构件数量: {len(grouped_data)}")
            
            if not grouped_data:
                print("无病害数据，跳过")
                continue
            
            # 根据构件类型处理
            if 'T梁' in part_name:
                current_y_offset, first_page = self._process_tbeams(part, current_y_offset, first_page)
            elif '双柱墩' in part_name or '单柱墩' in part_name:
                current_y_offset = self._process_piers(part, current_y_offset)
            elif '桥台' in part_name:
                current_y_offset = self._process_abutments(part, current_y_offset)
        
        # 保存文件
        self.cad.save()
        print(f"\n文件已保存到: {self.output_path}")
        
        return True
    
    def _process_tbeams(self, part: dict, start_y_offset: float, first_page: bool = True) -> tuple:
        """
        处理T梁构件
        
        Args:
            part: 构件数据
            start_y_offset: 起始Y偏移量
            first_page: 是否是第一次创建页面
            
        Returns:
            (新的Y偏移量, 是否需要复制模板)
        """
        part_name = part['name']
        template_name = part['template_name']
        grouped_data = part['grouped_data']
        
        # 按孔次分组
        hole_groups = group_tbeams_by_hole(list(grouped_data.keys()))
        
        y_offset = start_y_offset
        
        for hole, beams in hole_groups.items():
            # 将该孔的梁配对
            beam_pairs = pair_tbeams(beams)
            
            for idx, pair in enumerate(beam_pairs):
                # 为每对梁创建一个图
                # 第一页已经在create_from_template中复制过模板，后续需要额外复制
                is_first = first_page and (idx == 0)
                y_offset, _ = self._create_tbeam_page(
                    part_name, template_name, hole, pair, grouped_data, y_offset, is_first
                )
                first_page = False  # 之后每次都需要复制模板
        
        return y_offset, first_page
    
    def _create_tbeam_page(self, part_name: str, template_name: str, hole: str,
                          beam_pair: list, grouped_data: dict, y_offset: float, 
                          copy_template: bool = True) -> tuple:
        """
        创建一页T梁图纸（包含1-2根梁）
        
        Args:
            part_name: 构件类型名称
            template_name: 模板文件名
            hole: 孔次
            beam_pair: 梁对 [(构件编号, 梁号), ...]
            grouped_data: 所有分组数据
            y_offset: Y偏移量
            copy_template: 是否需要从模板复制内容
            
        Returns:
            (新的Y偏移量, 是否需要复制模板)
        """
        beam_nums = [b[0] for b in beam_pair]
        print(f"  创建图: 孔{hole}, 梁 {beam_nums}")
        
        # 获取模板文件路径
        template_path = os.path.join(COMPONENTS_DIR, template_name)
        if not os.path.exists(template_path):
            print(f"警告: 模板文件不存在 - {template_path}")
            return y_offset, False
        
        # 从模板复制内容（带Y偏移）
        if copy_template:
            self.cad.copy_entities_from_template(template_path, y_offset)
        
        # 填写标题信息
        self._fill_tbeam_title_info(part_name, hole, beam_pair, y_offset)
        
        # 添加病害标注
        for beam_id, beam_num in beam_pair:
            if beam_id in grouped_data:
                self._add_tbeam_diseases(beam_id, beam_num, y_offset, grouped_data[beam_id])
        
        # 计算新y偏移量（图的高度 + 间隔）
        # 假设每页图的高度约为250单位
        new_y_offset = y_offset + 280
        
        # 后续页面仍需要复制模板
        return new_y_offset, True
    
    def _fill_tbeam_title_info(self, part_name: str, hole: str, beam_pair: list, y_offset: float = 0):
        """
        填写T梁标题信息
        
        根据用户说明：
        - 路线名称：在后面的方框（第2个）
        - 桥梁名称：第四个方框
        - 孔次：第六个框的上方
        - 梁号：第六个框的下方
        """
        # 打印Excel数据
        route_text = self.data['route_name']
        bridge_text = self.data['bridge_name']
        beam_nums = [str(b[1]) for b in beam_pair]
        beam_text = '、'.join(beam_nums) + '号'
        
        print(f"\n=== 标题信息 ===")
        print(f"路线名称: {route_text}")
        print(f"桥梁名称: {bridge_text}")
        print(f"孔次: {hole}")
        print(f"梁号: {beam_text}")
        
        # 填写路线名称 - 第2个方框 (X=31773~31874)
        # 模板中位置: (31773.0, -3858.5)
        route_pos = (31773.0, -3858.5 - y_offset)
        print(f"路线名称坐标: {route_pos}")
        self.cad.add_mtext(route_text, route_pos, width=80, height=4.25)
        
        # 填写桥梁名称 - 第4个方框 (X=31875~31977)
        # 模板中位置: (31875.0, -3858.5)
        bridge_pos = (31875.0, -3858.5 - y_offset)
        print(f"桥梁名称坐标: {bridge_pos}")
        self.cad.add_mtext(bridge_text, bridge_pos, width=150, height=4.25)
        
        # 填写孔次 - 第六个框的上方 (右下角图例区域上方)
        # 位置: (31920.0, -3855.0)
        hole_pos = (31920.0, -3855.0 - y_offset)
        print(f"孔次坐标: {hole_pos}")
        self.cad.add_text(hole, hole_pos, height=4.25)
        
        # 填写梁号 - 第六个框的下方 (右下角图例区域下方)
        # 位置: (31920.0, -3865.0)
        beam_pos = (31920.0, -3865.0 - y_offset)
        print(f"梁号坐标: {beam_pos}")
        self.cad.add_text(beam_text, beam_pos, height=4.25)
        
        # 填写图名 - 模板中图名位置: (31908.1, -4102.6)
        figure_name = "上部病害展示图"
        figure_pos = (31908.1, -4102.6 - y_offset)
        print(f"图名坐标: {figure_pos}")
        self.cad.add_text(figure_name, figure_pos, height=4.25)
    
    def _add_tbeam_diseases(self, beam_id: str, beam_num: int, y_offset: float, diseases: list):
        """
        添加T梁病害标注
        
        根据用户说明的坐标系：
        - 原点X: 横向标尺0的X坐标 = 31657.2
        - 上方T梁原点Y: 纵向标尺1第一个出现的点 = -3901.3
        - 下方T梁原点Y: 纵向标尺1第3个出现的点 = -4001.7
        - X轴方向: 从左到右
        - Y轴方向: 从上到下
        - 1m = 10 CAD单位
        """
        print(f"    添加病害到 {beam_id}: {len(diseases)}条")
        
        # 梁底坐标系原点
        RULER_X = 31657.2  # 横向标尺0的X坐标
        TOP_BEAM_Y = -3901.3  # 上方T梁原点Y (1-1号梁)
        BOTTOM_BEAM_Y = -4001.7  # 下方T梁原点Y (1-2号梁)
        
        # 确定是上方梁还是下方梁
        # beam_num是梁号数字，1-1是1号，1-2是2号
        # 奇数梁在上方，偶数梁在下方
        is_top_beam = (beam_num % 2 == 1)
        
        if is_top_beam:
            origin_y = TOP_BEAM_Y
        else:
            origin_y = BOTTOM_BEAM_Y
        
        print(f"      梁号={beam_num}, {'上方梁' if is_top_beam else '下方梁'}, 原点=({RULER_X}, {origin_y})")
        
        for disease in diseases:
            disease_desc = disease.get('病害', '')
            if not disease_desc:
                continue
            
            # 检查是否需要处理
            if '泛白' in disease_desc:
                print(f"      跳过泛白病害")
                continue
            
            if '马蹄' in disease_desc:
                print(f"      跳过马蹄病害")
                continue
            
            # 解析病害位置
            pos_info = parse_disease_position(disease_desc)
            
            # 打印病害信息
            print(f"\n      === 病害信息 ===")
            print(f"      病害描述: {disease_desc}")
            print(f"      解析位置: {pos_info}")
            
            # 判断病害类型
            disease_type = pos_info.get('disease_type', '')
            
            # 获取坐标信息
            part = pos_info.get('part', '')
            x_start = pos_info.get('x_start', 0)  # 起始位置(m)
            x_end = pos_info.get('x_end', 0)  # 结束位置(m)
            y_pos_data = pos_info.get('y_start', 0)  # Y位置(m)
            length = pos_info.get('length', 0)  # 长度(m)
            width = pos_info.get('width', 0)  # 宽度(mm)
            
            # 计算病害在模板中的坐标
            # x=10~14m 表示X从10m到14m
            # y=0.5m 表示Y在0.5m位置
            # 原点在左下角，X向右增加，Y向上增加（但CAD中Y向上是正向）
            
            # 转换到CAD单位 (1m = 10单位)
            x_start_cad = x_start * 10  # 起点X
            x_end_cad = x_end * 10  # 终点X
            y_cad = y_pos_data * 10  # Y位置
            
            # 根据部位确定基础Y坐标
            # 梁底: 原点Y + y位置
            if '梁底' in part:
                base_y = origin_y
            elif '左翼缘板' in part:
                # 翼缘板在梁上方
                base_y = origin_y - 30  # 约往上是负方向
            elif '右翼缘板' in part:
                base_y = origin_y - 30
            elif '左腹板' in part:
                base_y = origin_y - 20
            elif '右腹板' in part:
                base_y = origin_y - 20
            else:
                # 默认梁底
                base_y = origin_y
            
            # 计算实际CAD坐标
            # X: 原点X + x位置 * 10 (X轴从左到右)
            # Y: 原点Y - y位置 * 10 (Y轴从上到下，所以减)
            x1 = RULER_X + x_start_cad
            x2 = RULER_X + x_end_cad
            y = base_y - y_cad
            
            # 应用y_offset（多页图纸的偏移）
            y = y - y_offset
            
            # 计算线宽（用户说W=0.10mm，0.1*10=1）
            line_width = width * 10 if width > 0 else 1
            
            print(f"      裂缝坐标计算:")
            print(f"        x_start={x_start}m, x_end={x_end}m, y={y_pos_data}m")
            print(f"        CAD: x1={x1:.1f}, x2={x2:.1f}, y={y:.1f}")
            print(f"        长度={length}m -> {length*10:.1f}单位, 宽度={width}mm -> {line_width:.1f}单位")
            
            # ── 按病害类型绘制 ──────────────────────────────────────
            if disease_type in ('纵向裂缝', '横向裂缝', '竖向裂缝') or (disease_type == '' and '裂缝' in disease_desc):
                # 所有普通裂缝：从 (x_start, y) 到 (x_end, y) 的水平线
                # 用户确认：纵向裂缝在这里也是水平线，位置就是起止点
                y_end_data = pos_info.get('y_end', y_pos_data)
                y_end_cad  = y_end_data * 10
                
                start_point = (x1, y)
                end_point   = (x2, y)
                
                print(f"      裂缝线: ({start_point[0]:.1f},{start_point[1]:.1f}) -> ({end_point[0]:.1f},{end_point[1]:.1f})")
                try:
                    self.cad.add_line(start_point, end_point, layer='病害')
                    print(f"      已绘制裂缝线")
                except Exception as e:
                    print(f"      绘制裂缝线失败: {e}")

            elif disease_type == '网状裂缝':
                # 网状裂缝：用图例 SPLINE 纹理平铺填充到目标矩形
                y_end_data = pos_info.get('y_end', y_pos_data)
                
                # 矩形两个对角坐标（CAD）
                rect_x1 = x1
                rect_x2 = x2
                rect_y1 = base_y - y_pos_data * 10   # 上边（y_start 对应更小的 CAD Y 值）
                rect_y2 = base_y - y_end_data  * 10  # 下边
                # 保证 rect_y1 < rect_y2 (CAD Y 轴向上为正，从上到下 Y 减小)
                cad_y_top    = min(rect_y1, rect_y2)
                cad_y_bottom = max(rect_y1, rect_y2)
                
                # 应用 y_offset
                cad_y_top    -= y_offset
                cad_y_bottom -= y_offset
                rect_x1 -= 0  # x 无需额外调整，已含 y_offset 无关
                rect_x2 -= 0
                
                w_cad = rect_x2 - rect_x1
                h_cad = abs(cad_y_bottom - cad_y_top)
                
                print(f"      网状裂缝矩形: ({rect_x1:.1f},{cad_y_top:.1f}) -> ({rect_x2:.1f},{cad_y_bottom:.1f})")
                print(f"      矩形宽={w_cad:.1f} 高={h_cad:.1f} CAD单位")
                
                try:
                    self.cad.add_mesh_crack(
                        rect_x1, cad_y_top, rect_x2, cad_y_bottom,
                        LEGENDS_DIR
                    )
                    print(f"      已绘制网状裂缝")
                except Exception as e:
                    print(f"      网状裂缝绘制失败: {e}")
                    import traceback; traceback.print_exc()

            else:
                # 其他病害类型使用图例
                legend_name = get_legend_name(disease_desc)
                if not legend_name:
                    print(f"      警告: 未知病害类型 - {disease_desc}")
                    continue
                
                legend_path = os.path.join(LEGENDS_DIR, legend_name)
                if not os.path.exists(legend_path):
                    print(f"      警告: 图例文件不存在 - {legend_path}")
                    continue
                
                insert_point = ((x1 + x2) / 2, y)
                print(f"      图例插入坐标: {insert_point}")
                try:
                    self.cad.insert_block(legend_path, insert_point, scale=1.0)
                    print(f"      已添加图例: {disease_desc[:30]}...")
                except Exception as e:
                    print(f"      添加图例失败: {e}")
    
    def _process_piers(self, part: dict, start_y_offset: float) -> float:
        """
        处理墩柱构件
        
        Args:
            part: 构件数据
            start_y_offset: 起始Y偏移量
            
        Returns:
            新的Y偏移量
        """
        part_name = part['name']
        template_name = part['template_name']
        grouped_data = part['grouped_data']
        
        y_offset = start_y_offset
        
        # 每个墩柱单独一页
        for pier_id, diseases in grouped_data.items():
            print(f"  创建图: 墩柱 {pier_id}")
            
            # TODO: 创建墩柱图
            
            y_offset += 250
        
        return y_offset
    
    def _process_abutments(self, part: dict, start_y_offset: float) -> float:
        """
        处理桥台构件
        
        Args:
            part: 构件数据
            start_y_offset: 起始Y偏移量
            
        Returns:
            新的Y偏移量
        """
        part_name = part['name']
        template_name = part['template_name']
        grouped_data = part['grouped_data']
        
        y_offset = start_y_offset
        
        # 每个桥台单独一页
        for abutment_id, diseases in grouped_data.items():
            print(f"  创建图: 桥台 {abutment_id}")
            
            # TODO: 创建桥台图
            
            y_offset += 250
        
        return y_offset
    
    def add_disease_to_cad(self, disease_desc: str, part: str, position: dict):
        """
        添加病害标注到CAD
        
        Args:
            disease_desc: 病害描述
            part: 部位
            position: 位置信息
        """
        # 检查是否需要处理
        if '泛白' in disease_desc:
            return  # 泛白不需要处理
        
        if '马蹄' in disease_desc:
            return  # 马蹄病害不需要处理
        
        # 获取图例
        legend_name = get_legend_name(disease_desc)
        if not legend_name:
            print(f"警告: 未知病害类型 - {disease_desc}")
            return
        
        legend_path = os.path.join(LEGENDS_DIR, legend_name)
        if not os.path.exists(legend_path):
            print(f"警告: 图例文件不存在 - {legend_path}")
            return
        
        # 解析位置信息
        pos_info = parse_disease_position(disease_desc)
        
        # 计算全局坐标
        # TODO: 需要根据模板确定坐标系
        
        # 插入图例
        # TODO: 实际插入图例
        
    def close(self):
        """关闭CAD"""
        self.cad.close()


def main():
    """主函数"""
    # 检查命令行参数
    if len(sys.argv) < 2:
        # 使用默认的Excel文件
        excel_path = 'K572+774红石牡丹江大桥（右幅）病害.xls'
    else:
        excel_path = sys.argv[1]
    
    # 检查文件是否存在
    if not os.path.exists(excel_path):
        print(f"错误: 文件不存在 - {excel_path}")
        return
    
    # 创建生成器
    generator = BridgeDiseaseCADGenerator(excel_path)
    
    # 加载数据
    generator.load_data()
    
    # 启动CAD
    print("\n启动浩辰CAD...")
    if not generator.start_cad(visible=True):
        print("启动CAD失败，程序退出")
        return
    
    # 处理数据
    print("\n开始处理...")
    generator.process()
    
    print("\n处理完成!")
    print(f"输出文件: {generator.output_path}")


if __name__ == '__main__':
    main()

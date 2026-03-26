# 病害图例绘制逻辑

## 概述
本文档记录桥梁病害可视化系统中各种病害图例的绘制逻辑。

---

## 剥落露筋图例（上部病害）

### 函数位置
`bridge_disease_main_upper.py`

### 核心函数
`draw_peel_off_with_rebar(msp, x1, y1, x2, y2, origin, specific_part, beam_level, return_bbox)`

### 绘制逻辑

#### 第一步：绘制剥落图形（draw_peel_off）

1. **加载模板**
   - 从模板文件 `剥落、掉角.dxf` 加载原始几何数据
   - 提取所有线条(line)和多段线(polyline)实体
   - 计算原始图形的边界框(bbox)

2. **坐标转换**
   - 将病害区域坐标(x1,y1)-(x2,y2)转换为CAD坐标
   - 确保 cad_x1 < cad_x2, cad_y2 < cad_y1

3. **缩放计算**
   ```
   target_width = cad_x2 - cad_x1
   target_height = cad_y1 - cad_y2
   scale_x = target_width / orig_width
   scale_y = target_height / orig_height
   scale = min(scale_x, scale_y)  # 使用统一缩放保持比例
   ```

4. **偏移计算（居中对齐）**
   ```
   offset_x = cad_x1 - bbox["min_x"] * scale
   offset_y = cad_y2 - bbox["min_y"] * scale
   ```

5. **绘制**
   - 绘制所有线条（颜色7=白色）
   - 绘制多段线多边形（颜色7=白色）
   - 返回实际绘制区域的边界框(ax1, ay1, ax2, ay2)

#### 第二步：叠加钢筋网格

在剥落图形实际边界框内绘制红色虚线格栅：
- **水平线**：3条（i=1,2,3，位置在高度4等分的1/4、2/4、3/4处）
- **垂直线**：3条（i=1,2,3，位置在宽度4等分的1/4、2/4、3/4处）
- **样式**：颜色1（红色），线型DASHED（虚线）

```
grid_color = 1
for i in range(1, 4):  # 水平线
    y = ay2 + height * i / 4
    msp.add_line((ax1, y), (ax2, y), dxfattribs={"color": grid_color, "linetype": "DASHED"})
for i in range(1, 4):  # 垂直线
    x = ax1 + width * i / 4
    msp.add_line((x, ay2), (x, ay1), dxfattribs={"color": grid_color, "linetype": "DASHED"})
```

### 调用场景
- 病害类型包含"剥落露筋"、"锈胀露筋"、"露筋"时调用
- 模板文件路径：`templates/剥落、掉角.dxf`

---

## 下部病害程序差异

### 下部病害程序
`bridge_disease_main_lower.py`

### 主要差异
1. **函数名称**：`draw_peel_rebar`（无模板，纯代码绘制）
2. **网格数量**：2条水平线 + 1条垂直线（更简洁）
3. **颜色**：颜色1（红色）
4. **线型**：DASHED（虚线）

### 下部代码示例
```python
# 2 horizontal lines
for i in range(2):
    y = min_y + dst_h * (i + 1) / 3
    msp.add_line((min_x, y), (max_x, y), dxfattribs={"color": 1, "linetype": "DASHED"})
# 1 vertical line
msp.add_line((min_x + dst_w / 2, min_y), (min_x + dst_w / 2, max_y), dxfattribs={"color": 1, "linetype": "DASHED"})
```

---

## 其他病害图例类型

---

## 网状裂缝图例

### 函数位置
- 上部：`bridge_disease_main_upper.py` - `draw_mesh_crack()`
- 下部：`bridge_disease_main_lower.py` - `draw_mesh_crack()`

### 绘制效果
在矩形病害区域内填充多条**水平波浪线**，形成网状裂缝效果。

### 核心算法

```python
def draw_mesh_crack(msp, x1, y1, x2, y2, origin, scale_x, scale_y):
    """绘制网状裂缝（波浪线填充）"""
    # 1. 坐标转换：将病害坐标(m)转换为CAD坐标
    cad_x1 = origin[0] + x1 * scale_x
    cad_y1 = origin[1] - y1 * scale_y  # Y轴向下，所以用减法
    cad_x2 = origin[0] + x2 * scale_x
    cad_y2 = origin[1] - y2 * scale_y
    
    # 确保 cad_x1 < cad_x2
    if cad_x1 > cad_x2:
        cad_x1, cad_x2 = cad_x2, cad_x1
    
    # 2. 波浪线参数
    wave_length = 4      # 波长（一个完整波浪的X跨度）
    wave_amp = 0.3       # 波幅（波浪的Y方向高度）
    line_spacing = 1     # 波浪线之间的垂直间距
    
    # 3. 计算需要绘制的线条数量
    height = abs(cad_y2 - cad_y1)  # 病害区域的垂直高度
    num_lines = max(1, int(height / line_spacing) + 1)
    
    # 4. 确定Y范围（从顶部向下绘制）
    y_top = max(cad_y1, cad_y2)
    y_bottom = min(cad_y1, cad_y2)
    
    # 5. 绘制每条波浪线
    for i in range(num_lines):
        y = y_top - i * line_spacing  # 当前波浪线的基准Y坐标
        points = []
        x = cad_x1
        
        # 生成波浪线上的点（步长0.2保证平滑）
        while x <= cad_x2 + wave_length:  # +wave_length确保末端覆盖完整
            phase = (x - cad_x1) / wave_length * 2 * math.pi  # 相位角
            wave_y = y + math.sin(phase) * wave_amp  # 正弦波计算Y偏移
            points.append((x, wave_y))
            x += 0.2  # 小步长使波浪线更平滑
        
        # 绘制波浪线（颜色7=白色）
        msp.add_lwpolyline(points=points, dxfattribs={"color": 7})
```

### 关键要点

1. **波浪线方向**：水平方向（X轴延伸），不是竖直方向
2. **Y轴处理**：CAD坐标系Y轴向下为正，所以用 `origin[1] - y * scale_y`
3. **线条数量**：根据病害区域高度自动计算 `num_lines = height / line_spacing + 1`
4. **绘制顺序**：从顶部向下绘制（`y_top - i * line_spacing`）
5. **末端覆盖**：`x <= cad_x2 + wave_length` 确保波浪线末端完整
6. **平滑度**：步长0.2，每个波浪约20个点

### 条件判断注意事项

**重要**：在病害处理函数中，`elif "网状裂缝" in disease_type:` 必须放在 `elif "裂缝" in disease_type:` **之前**！

因为"网状裂缝"包含"裂缝"这个词，如果顺序错误，网状裂缝会被当作普通裂缝处理，导致只画一条竖线。

```python
# ✅ 正确顺序
elif "网状裂缝" in disease_type:
    draw_mesh_crack(...)
elif "裂缝" in disease_type:
    # 处理其他裂缝类型

# ❌ 错误顺序（会导致网状裂缝变成竖线）
elif "裂缝" in disease_type:
    # 网状裂缝也会进入这里！
elif "网状裂缝" in disease_type:
    # 永远不会执行到这里
```

### 调用场景
- 病害类型包含"网状裂缝"时调用
- 病害描述示例：`大桩号面，x=10～12m，y=0～0.4m，网状裂缝 S=0.80m2`

### 裂缝图例
- **竖向裂缝**：使用 `draw_vertical_crack_group` 绘制多条平行竖线
- **横向裂缝**：使用 `draw_crack` 绘制单条水平线
- **网状裂缝**：使用 `draw_mesh_crack` 绘制水平波浪线填充（见上文）

### 蜂窝麻面图例
- 使用模板文件 `蜂窝、麻面.dxf`
- 通过平铺复制填充整个区域

### 剥落/破损图例（下部桥台）

#### 问题背景
桥台（带台身/不带台身）的"剥落"和"破损"病害最初使用 `draw_peel_off()` 函数，该函数只是将单个剥落图例缩放到适应病害区域大小，**没有平铺填满整个区域**。

#### 修复方案（2026-03-25）
将桥台处理中的剥落/破损病害改为使用 **平铺方式** 绘制，与蜂窝麻面保持一致。

**修改位置**：`bridge_disease_main_lower.py` - `process_abutment_disease()` 函数

**修改内容**：
```python
# 修改前（只绘制一个缩放图例）
bbox = draw_peel_off(msp, x_start, y_start, x_end, y_end, origin, return_bbox=True, scale_x=scale_x, scale_y=scale_y)

# 修改后（平铺填满整个区域）
bbox = draw_peel_off_tiled(msp, x_start, y_start, x_end, y_end, origin, scale_x=scale_x, scale_y=scale_y)
```

#### 平铺函数 `draw_peel_off_tiled`

**功能**：将剥落图例平铺复制，填满整个病害矩形区域。

**核心逻辑**：
1. **图例放大**：先将单个图例放大1.5倍（使细节更清晰）
2. **计算平铺数量**：
   ```
   cols = max(1, int(target_width / (legend_width * 1.5)))
   rows = max(1, int(target_height / (legend_height * 1.5)))
   ```
3. **计算实际缩放比例**：根据行列数重新计算，确保图例恰好填满区域
4. **平铺复制**：按行列循环复制图例实体

**参数**：
- `x1, y1, x2, y2`：病害区域坐标（米）
- `origin`：CAD原点坐标
- `scale_x, scale_y`：坐标转换比例

**返回值**：实际绘制区域的边界框 `(min_x, min_y, max_x, max_y)`

#### 使用场景
- 桥台台帽的剥落/破损病害
- 桥台台身的剥落/破损病害
- 需要平铺填满矩形区域的病害类型

### 水蚀图例
- 使用模板文件 `水蚀.dxf`

---

## 坐标系统

### 转换函数
- 上部：`convert_to_cad_coords(x, y, origin, specific_part, beam_level)`
- 下部：`convert_to_cad_coords_lower(x, y, origin)`

### 比例
- X方向：1m = 14 CAD单位 (SCALE_X)
- Y方向：1m = 16.5 CAD单位 (SCALE_Y)

### 特殊处理
- 1度倾斜修正（桥面朝右下倾斜）
- CAD坐标系：Y轴向下（与常规数学坐标系相反）
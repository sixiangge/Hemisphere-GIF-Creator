# 半球面 GIF 生成器

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**将平面图片映射到旋转的 3D 半球面上，生成动画 GIF。**

基于球面纹理映射 + power warp 变形算法，将 JPG/PNG 图片贴在半球穹顶上，渲染 360° 旋转动画，同时展示正面和背面（内侧面），呈现逼真的立体旋转效果。

## 特性

- **球面纹理映射** — 图片中心对准半球极点，边缘均匀压缩形成球面透视
- **Power warp 变形** — 可调节中心与边缘占比，实现鱼眼膨胀效果
- **360° 旋转** — 绕 Y 轴（竖直）或 X 轴（水平）平滑旋转
- **GUI + CLI** — 图形界面和命令行两种方式，自由选择
- **独立 EXE** — 支持 PyInstaller 打包，无需安装 Python 即可运行

## 快速开始

### 环境要求

- Python 3.8+
- NumPy
- Pillow（PIL）

```bash
pip install -r requirements.txt
```

### 命令行使用

```bash
# 基本用法
python hemisphere_gif.py 图片.jpg

# 指定输出文件
python hemisphere_gif.py 照片.jpg 输出.gif

# 完整参数
python hemisphere_gif.py 照片.jpg 输出.gif \
    --radius 250 \
    --frames 90 \
    --duration 40 \
    --axis y \
    --bg 255 255 255
```

### 图形界面使用

```bash
python hemisphere_gui.py
```

窗口布局：

- **左侧** — 点击"+"上传图片
- **中间** — 箭头 +「生成 GIF」按钮
- **右侧** — 预览成品，点击可保存
- **底部** — 参数设置（半径、帧数、时长、旋转轴、背景色）

### 打包为独立 EXE（Windows）

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "HemisphereGIF" hemisphere_gui.py
```

生成的 EXE 位于 `dist/HemisphereGIF.exe`，约 30 MB，无需 Python 环境即可运行。

也可以直接双击 `build_exe.bat` 一键打包。

## 命令行参数

| 参数           | 默认值     | 说明                                        |
|:------------ |:------- |:----------------------------------------- |
| `--radius`   | `200`   | 半球半径（像素）                                  |
| `--frames`   | `60`    | 动画帧数                                      |
| `--duration` | `50`    | 每帧持续时间（毫秒）                                |
| `--size`     | 自动      | 输出画面尺寸（默认：半径 ×2.5）                        |
| `--axis`     | `y`     | 旋转轴：`y`=竖直轴（左右旋转），`x`=水平轴（上下翻转）           |
| `--bg`       | `0 0 0` | 背景色 R G B（0–255），如 `--bg 255 255 255` 为白色 |

## 可调参数

以下参数在 `hemisphere_gif.py` 中直接修改：

| 参数                 | 默认值    | 说明                   |
|:------------------ |:------ |:-------------------- |
| `power`            | `1.25` | 球面变形强度，> 1 中心膨胀、边缘压缩 |
| `front_brightness` | `1.0`  | 正面亮度系数               |
| `back_brightness`  | `0.65` | 背面亮度系数（相对正面）         |

### Power warp 说明

```
u = arcsin(|x/R|^power) / (π/2) × 0.5 + 0.5
```

| `power` | 效果             |
|:------- |:-------------- |
| `1.0`   | 标准 arcsin 球面映射 |
| `> 1.0` | 中心膨胀、边缘压缩      |
| `< 1.0` | 中心压缩（不推荐）      |

默认 `1.25`，轻微中心膨胀，观感自然。

## 技术原理

### 反向映射

对输出画面的每个像素，反向投影到 3D 半球面以确定纹理坐标：

1. **屏幕 → 世界**：像素坐标 `(px, py)` 正交投影到半球面上的点 `(dx, dy, z)`，其中 `z = √(R² − dx² − dy²)`

2. **世界 → 原始**：应用逆旋转矩阵 `R_y(−θ)` 抵消当前帧的旋转，得到未旋转半球空间中的对应点

3. **原始 → 纹理**：使用 power warp 变形函数 `|t|^power` 计算球面纹理坐标，压缩边缘、膨胀中心

4. **背面处理**：正面转出视野时，同一半球面的内侧面暴露出来，使用相同的纹理映射但以较低亮度渲染

## 📁 项目结构

```
hemisphere-gif/
├── hemisphere_gif.py    # 核心模块（命令行 + 可供 GUI 导入）
├── hemisphere_gui.py    # 图形界面（tkinter）
├── build_exe.bat        # PyInstaller 打包脚本
├── requirements.txt     # Python 依赖
├── README.md            # 项目说明
├── LICENSE              # 开源许可
└── .gitignore
```

## 📄 许可

[MIT](LICENSE)

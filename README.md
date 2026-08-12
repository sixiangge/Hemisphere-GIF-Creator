# 半球面 GIF 生成器

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**将平面图片映射到旋转的 3D 半球面上，生成透明背景的动画 GIF。**

基于球面纹理映射 + power warp 变形算法，将 JPG/PNG 图片贴在半球穹顶上，渲染 360° 旋转动画，同时展示正面和背面（内侧面），呈现逼真的立体旋转效果。

## 特性

- **球面纹理映射** — 图片中心对准半球极点，边缘均匀压缩形成球面透视
- **Power warp 变形可调** — 界面内直接调节中心与边缘占比
- **360° 旋转** — 绕 Y 轴（竖直）或 X 轴（水平）平滑旋转
- **旋转速度可调** — 可根据需求自由调节旋转速度
- **透明背景** — GIF 输出背景透明，方便叠加到其他画面上
- **GUI + CLI** — 图形界面和命令行两种方式
- **粘贴与复制** — 右键粘贴剪贴板图片，右键复制生成结果
- **独立 EXE** — 支持 PyInstaller 打包，无需安装 Python 即可运行

## 快速开始

### 环境要求

- Python 3.8+
- Windows 64 位（剪贴板功能依赖 pywin32）

```bash
pip install -r requirements.txt
```

### 图形界面使用（推荐）

```bash
python hemisphere_gui.py
```

| 操作     | 方式                    |
|:------ |:--------------------- |
| 上传图片   | 左键点击上传框，或截图后右键 → 粘贴图片 |
| 调节参数   | 修改底部的半径、帧数、变形强度等参数    |
| 生成 GIF | 点击"生成 GIF"按钮          |
| 保存 GIF | 左键点击预览框               |
| 复制 GIF | 右键预览框 → 复制图片          |

### 命令行使用

```bash
# 基本用法
python hemisphere_gif.py 图片.jpg

# 完整参数
python hemisphere_gif.py 照片.jpg 输出.gif \
    --radius 250 \
    --frames 90 \
    --duration 40 \
    --axis y
```

### 打包为独立 EXE（Windows）

```bash
双击 build_exe.bat
```

生成的 EXE 位于 `dist/`，约 30 MB，无需任何环境。

## 命令行参数

| 参数           | 默认值   | 说明                  |
|:------------ |:----- |:------------------- |
| `--radius`   | `200` | 半球半径（像素）            |
| `--frames`   | `60`  | 动画帧数                |
| `--duration` | `50`  | 每帧持续时间（毫秒）          |
| `--size`     | 自动    | 输出画面尺寸（默认：半径 ×2.5）  |
| `--axis`     | `y`   | 旋转轴：`y`=竖直轴，`x`=水平轴 |

## 技术原理

### 反向映射

对输出画面的每个像素，反向投影到 3D 半球面以确定纹理坐标：

1. **屏幕 → 世界**：像素坐标 `(px, py)` 正交投影到半球面上的点 `(dx, dy, z)`，其中 `z = √(R² − dx² − dy²)`
2. **世界 → 原始**：应用逆旋转矩阵 `R_y(−θ)` 抵消当前帧的旋转
3. **原始 → 纹理**：使用 power warp 变形函数 `|t|^power` 计算球面纹理坐标
4. **背面处理**：正面转出视野时，同一半球面的内侧面暴露出来

### Power warp

```
u = arcsin(|x/R|^power) / (π/2) × 0.5 + 0.5
```

| `power` | 效果             |
|:------- |:-------------- |
| `1.0`   | 标准 arcsin 球面映射 |
| `> 1.0` | 中心膨胀、边缘压缩      |
| `< 1.0` | 中心压缩（不推荐）      |

默认 `1.25`，可在 GUI 中实时调节。

## 项目结构

```
hemisphere-gif/
├── hemisphere_gif.py    # 核心模块（命令行 + 可供 GUI 导入）
├── hemisphere_gui.py    # 图形界面（tkinter）
├── build_exe.bat        # PyInstaller 打包脚本
├── requirements.txt     # Python 依赖
├── README.md            # 项目说明
├── LICENSE              # MIT 许可
└── .gitignore
```

## 许可

[MIT](LICENSE)

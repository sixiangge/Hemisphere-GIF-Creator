#!/usr/bin/env python3
"""
将平面 JPG 图片映射到旋转的半球面上，生成动画 GIF。
Transform a flat JPG image onto a rotating hemisphere and output an animated GIF.

用法 / Usage:
    python hemisphere_gif.py <input.jpg> [output.gif] [options]

选项 / Options:
    --radius N      半球半径（像素），默认 200
    --frames N      动画帧数，默认 60
    --duration N    每帧持续时间（毫秒），默认 50
    --size N        输出画面尺寸（像素），默认自动（半径的 2.5 倍）
    --axis y        旋转轴 (y=竖直轴, x=水平轴)，默认 y
    --bg R G B      背景色 RGB (0-255)，默认 0 0 0（黑色）
"""

import numpy as np
from PIL import Image
import sys
import argparse
import math


def _spherical_uv(x_orig, y_orig, radius, power):
    """球面纹理映射（含 power warp 提高中心占比）

    反向映射: u = arcsin(|x/R|^power) / (π/2) * 0.5 + 0.5
    效果: power = 1 → 标准 arcsin 球面映射
          power > 1 → 中心区域膨胀、边缘压缩（power 越大中心占比越大）
          power < 1 → 中心压缩（不推荐）
    """
    t_x = np.clip(x_orig / radius, -1.0, 1.0)
    t_y = np.clip(y_orig / radius, -1.0, 1.0)

    # Power warp: |t|^power 压缩边缘，使中心占比更大
    t_x_warped = np.sign(t_x) * (np.abs(t_x) ** power)
    t_y_warped = np.sign(t_y) * (np.abs(t_y) ** power)

    u = (np.arcsin(np.clip(t_x_warped, -1.0, 1.0)) / (math.pi / 2.0) + 1.0) / 2.0
    v = (np.arcsin(np.clip(t_y_warped, -1.0, 1.0)) / (math.pi / 2.0) + 1.0) / 2.0

    return np.clip(u, 0.0, 1.0), np.clip(v, 0.0, 1.0)


def _sample_texture(img_array, u, v):
    """从纹理数组采样（最近邻）"""
    h, w = img_array.shape[:2]
    tex_x = (u * (w - 1)).astype(np.int32)
    tex_y = (v * (h - 1)).astype(np.int32)
    tex_x = np.clip(tex_x, 0, w - 1)
    tex_y = np.clip(tex_y, 0, h - 1)
    return img_array[tex_y, tex_x].astype(np.float32)


def create_hemisphere_gif(
    input_path: str,
    output_path: str = "output.gif",
    radius: int = 200,
    num_frames: int = 60,
    duration: int = 50,
    output_size: int = None,
    axis: str = "y",
    bg_color: tuple = (0, 0, 0),
):
    """
    核心函数：将输入图片映射到半球面并旋转生成 GIF。

    原理（反向映射 + 正交投影）：
    1. 对输出画面的每个像素 (px, py)，计算它"看向"的场景 3D 点
    2. 该 3D 点在旋转后的半球面上对应的纹理坐标
    3. 从原图采样 → 得到该像素的颜色
    4. 施加光照增强立体感
    """

    # ── 1. 加载并预处理输入图片 ──────────────────────────────
    print(f"[1/4] Loading: {input_path}")
    img = Image.open(input_path).convert("RGB")

    # 裁剪为正方形（取中心区域）
    size = min(img.size)
    left = (img.width - size) // 2
    top = (img.height - size) // 2
    img = img.crop((left, top, left + size, top + size))

    # 缩放纹理（分辨率越高纹理越清晰）
    tex_res = radius * 2
    img = img.resize((tex_res, tex_res), Image.LANCZOS)
    img_array = np.array(img, dtype=np.float32)  # shape: (H, W, 3), range 0-255

    # ── 2. 建立输出画面坐标网格 ──────────────────────────────
    if output_size is None:
        output_size = int(radius * 2.5)
    center = output_size / 2.0

    # 像素坐标网格
    y, x = np.ogrid[:output_size, :output_size]
    dx = x - center  # 水平偏移，shape: (1, W)
    dy = y - center  # 垂直偏移，shape: (H, 1)

    dist_sq = dx * dx + dy * dy  # 到中心的距离平方
    inside = dist_sq < radius * radius  # 在半球投影圆内的像素

    # 半球面上的 z 坐标（正交投影，摄像机沿 -z 方向）
    z_sq = radius * radius - dist_sq
    z = np.sqrt(np.maximum(z_sq, 0))  # shape: (H, W)

    # ── 3. 逐帧渲染 ──────────────────────────────────────────
    print(f"[2/4] Rendering {num_frames} frames...")
    frames = []

    # 球面变形强度：> 1.0 则中心占比更大（越大中心占比越高）
    power = 1.25

    # 正面亮度（直接使用原图颜色）
    front_brightness = 1.0

    # 背面亮度（比正面稍暗）
    back_brightness = 0.65

    for frame_idx in range(num_frames):
        # 正角度绕 Y 轴：半球正面从左向右移动（逆时针从上方看）
        angle = 2.0 * math.pi * frame_idx / num_frames
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        if axis == "y":
            # ── 绕 Y 轴旋转（竖直轴，从左向右转） ──

            # ◆ 正面：世界点 (dx, dy, +z) 对应的未旋转点 P_f
            # P_f = R_y(-angle) · (dx, dy, +z)
            x_orig_f = dx * cos_a - z * sin_a
            y_orig_f = dy
            z_orig_f = dx * sin_a + z * cos_a

            # ◆ 背面：世界点 (dx, dy, -z) 对应的未旋转点 P_b
            # 当正面不可见时（P_f_z < 0），背面（半球内侧面）暴露出来
            # P_b = R_y(-angle) · (dx, dy, -z)
            x_orig_b = dx * cos_a + z * sin_a
            y_orig_b = dy
            z_orig_b = dx * sin_a - z * cos_a
        else:
            # ── 绕 X 轴旋转（水平轴） ──
            x_orig_f = dx
            y_orig_f = dy * cos_a + z * sin_a
            z_orig_f = -dy * sin_a + z * cos_a

            x_orig_b = dx
            y_orig_b = dy * cos_a - z * sin_a
            z_orig_b = -dy * sin_a - z * cos_a

        # 可见性判断
        front_vis = inside & (z_orig_f > 1e-6)               # 正面可见
        back_vis  = inside & (z_orig_b > 1e-6) & (~front_vis) # 仅正面不可见时背面可见

        any_front = np.any(front_vis)
        any_back  = np.any(back_vis)

        if not any_front and not any_back:
            frame = np.full((output_size, output_size, 3), bg_color, dtype=np.uint8)
            frames.append(Image.fromarray(frame))
            continue

        # ── 创建输出帧 ──
        frame = np.full((output_size, output_size, 3), bg_color, dtype=np.float32)

        # ═══════════════════════════════════════════════════════
        # ◆ 渲染正面 ◆
        # ═══════════════════════════════════════════════════════
        if any_front:
            # 球面纹理映射 + power warp（提高中心占比）
            u_f, v_f = _spherical_uv(x_orig_f, y_orig_f, radius, power)
            colors_f = _sample_texture(img_array, u_f, v_f)

            # 正面保持固定亮度
            colors_f = colors_f * front_brightness

            frame[front_vis] = colors_f[front_vis]

        # ═══════════════════════════════════════════════════════
        # ◆ 渲染背面 ◆ （亮度比正面暗，呈现立体纵深感）
        # ═══════════════════════════════════════════════════════
        if any_back:
            # 背面使用相同的纹理映射（纹理"附着"在半球面上，内侧面也能看到）
            u_b, v_b = _spherical_uv(x_orig_b, y_orig_b, radius, power)
            colors_b = _sample_texture(img_array, u_b, v_b)

            # 背面亮度（比正面稍暗）
            colors_b = colors_b * back_brightness

            frame[back_vis] = colors_b[back_vis]

        # 裁剪并转换
        frame = np.clip(frame, 0, 255).astype(np.uint8)
        frames.append(Image.fromarray(frame))

        # 进度提示
        if (frame_idx + 1) % 15 == 0 or frame_idx == 0:
            pct = (frame_idx + 1) / num_frames * 100
            print(f"   Progress: {frame_idx + 1}/{num_frames} ({pct:.0f}%)")

    # ── 4. 保存 GIF ──────────────────────────────────────────
    print(f"[3/4] Saving GIF: {output_path}")
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=0,          # 无限循环
        optimize=False,  # 关闭优化以保持画质
        disposal=2,      # 每帧恢复背景
    )

    # 文件大小
    import os
    file_size = os.path.getsize(output_path)
    print(f"[4/4] Done!")
    print(f"    Output: {output_path}")
    print(f"    Size: {file_size / 1024:.1f} KB")
    print(f"    Frames: {num_frames} | Resolution: {output_size}x{output_size} | Radius: {radius}px")


def main():
    parser = argparse.ArgumentParser(
        description="将平面图片映射到旋转的半球面上，生成动画 GIF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python hemisphere_gif.py photo.jpg
    python hemisphere_gif.py photo.jpg output.gif --radius 300 --frames 90
    python hemisphere_gif.py photo.jpg --axis x --bg 30 30 50
        """,
    )
    parser.add_argument("input", help="输入 JPG/PNG 图片路径")
    parser.add_argument("output", nargs="?", default="hemisphere_output.gif",
                        help="输出 GIF 路径 (默认: hemisphere_output.gif)")
    parser.add_argument("--radius", type=int, default=200,
                        help="半球半径，像素 (默认: 200)")
    parser.add_argument("--frames", type=int, default=60,
                        help="动画帧数 (默认: 60)")
    parser.add_argument("--duration", type=int, default=50,
                        help="每帧持续时间，毫秒 (默认: 50)")
    parser.add_argument("--size", type=int, default=None,
                        help="输出画面尺寸，像素 (默认: 半径×2.5)")
    parser.add_argument("--axis", choices=["x", "y"], default="y",
                        help="旋转轴: y=竖直轴(像旋转的地球), x=水平轴(像翻书) (默认: y)")
    parser.add_argument("--bg", type=int, nargs=3, default=[0, 0, 0],
                        metavar=("R", "G", "B"),
                        help="背景色 RGB 0-255 (默认: 0 0 0)")

    args = parser.parse_args()

    create_hemisphere_gif(
        input_path=args.input,
        output_path=args.output,
        radius=args.radius,
        num_frames=args.frames,
        duration=args.duration,
        output_size=args.size,
        axis=args.axis,
        bg_color=tuple(args.bg),
    )


if __name__ == "__main__":
    main()

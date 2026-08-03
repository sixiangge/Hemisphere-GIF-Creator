#!/usr/bin/env python3
"""
半球面 GIF — GUI 前端
左侧上传图片，右侧预览成品，点击生成按钮运行程序。
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import threading
import os
import tempfile
import win32clipboard
from io import BytesIO

from hemisphere_gif import create_hemisphere_gif


class UploadBox(tk.Frame):
    """左侧上传框：点击可选择图片，显示缩略图。"""

    def __init__(self, parent, size=300, **kwargs):
        super().__init__(parent, **kwargs)
        self.size = size
        self.image_path = None
        self.thumbnail = None

        self.canvas = tk.Canvas(self, width=size, height=size,
                                bg="#f0f0f0", highlightthickness=2,
                                highlightbackground="#cccccc", cursor="hand2")
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._on_click)

        # 右键菜单
        self.canvas.bind("<Button-3>", self._on_right_click)
        self._context_menu = tk.Menu(self, tearoff=0)
        self._context_menu.add_command(label="粘贴图片", command=self._on_paste)

        self._draw_placeholder()

    def _draw_placeholder(self):
        self.canvas.delete("all")
        cx, cy = self.size // 2, self.size // 2
        self.canvas.create_rectangle(10, 10, self.size - 10, self.size - 10,
                                     outline="#aaaaaa", width=2, dash=(6, 4))
        plus_size = 40
        self.canvas.create_line(cx - plus_size, cy, cx + plus_size, cy,
                                fill="#999999", width=4)
        self.canvas.create_line(cx, cy - plus_size, cx, cy + plus_size,
                                fill="#999999", width=4)
        self.canvas.create_text(cx, cy + plus_size + 30,
                                text="点击上传\n右键可粘贴图片",
                                fill="#999999", font=("Microsoft YaHei", 11),
                                justify="center")

    def _on_click(self, event=None):
        path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png"), ("所有文件", "*.*")],
        )
        if path:
            self.load_image(path)

    def _on_right_click(self, event):
        """右键弹出菜单。"""
        self._context_menu.tk_popup(event.x_root, event.y_root)

    def _on_paste(self, event=None):
        """从剪贴板粘贴图片（win32clipboard，快速可靠）。"""
        try:
            win32clipboard.OpenClipboard()
            try:
                if not win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
                    messagebox.showinfo("粘贴失败", "剪贴板中没有图片，请先截图或复制一张图片。")
                    return
                data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
            finally:
                win32clipboard.CloseClipboard()

            # CF_DIB 转 PIL Image
            img = Image.open(BytesIO(data))
            fd, tmp_path = tempfile.mkstemp(suffix=".png")
            os.close(fd)
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            img.save(tmp_path, 'PNG')
            self.load_image(tmp_path)
        except Exception as e:
            messagebox.showinfo("粘贴失败", f"无法读取剪贴板：{e}")

    def load_image(self, path):
        self.image_path = path
        img = Image.open(path)
        img.thumbnail((self.size - 20, self.size - 20), Image.LANCZOS)
        self.thumbnail = ImageTk.PhotoImage(img)

        self.canvas.delete("all")
        cx, cy = self.size // 2, self.size // 2
        self.canvas.create_image(cx, cy, image=self.thumbnail)
        fname = os.path.basename(path)
        if len(fname) > 25:
            fname = fname[:22] + "..."
        self.canvas.create_text(cx, self.size - 15,
                                text=fname, fill="#555555",
                                font=("Microsoft YaHei", 9))


class PreviewBox(tk.Frame):
    """右侧预览框：显示生成的 GIF 第一帧，点击可保存。"""

    def __init__(self, parent, size=300, **kwargs):
        super().__init__(parent, **kwargs)
        self.size = size
        self.output_path = None
        self.preview_img = None

        self.canvas = tk.Canvas(self, width=size, height=size,
                                bg="#f0f0f0", highlightthickness=2,
                                highlightbackground="#cccccc")
        self.canvas.pack()

        # 右键菜单
        self.canvas.bind("<Button-3>", self._on_right_click)
        self._context_menu = tk.Menu(self, tearoff=0)
        self._context_menu.add_command(label="复制图片", command=self._copy_to_clipboard)

        self._draw_placeholder()

    def _draw_placeholder(self):
        self.canvas.delete("all")
        cx, cy = self.size // 2, self.size // 2
        self.canvas.create_rectangle(10, 10, self.size - 10, self.size - 10,
                                     outline="#aaaaaa", width=2, dash=(6, 4))
        self.canvas.create_text(cx, cy,
                                text="生成后显示\n预览图",
                                fill="#999999", font=("Microsoft YaHei", 11),
                                justify="center")

    def show_preview(self, gif_path):
        self.output_path = gif_path
        try:
            img = Image.open(gif_path)
            img.thumbnail((self.size - 20, self.size - 20), Image.LANCZOS)
            self.preview_img = ImageTk.PhotoImage(img)

            self.canvas.delete("all")
            cx, cy = self.size // 2, self.size // 2
            self.canvas.create_image(cx, cy, image=self.preview_img)
            self.canvas.create_text(cx, self.size - 12,
                                    text="点击保存",
                                    fill="#4a90d9",
                                    font=("Microsoft YaHei", 9, "underline"),
                                    tags="save_hint")
            self.canvas.tag_bind("save_hint", "<Button-1>", self._on_save)
            self.canvas.bind("<Button-1>", self._on_save)
        except Exception as e:
            messagebox.showerror("错误", f"加载预览失败：{e}")

    def _on_save(self, event=None):
        if not self.output_path:
            return
        dest = filedialog.asksaveasfilename(
            title="保存 GIF",
            defaultextension=".gif",
            filetypes=[("GIF 文件", "*.gif"), ("所有文件", "*.*")],
            initialfile="hemisphere_output.gif",
        )
        if dest:
            try:
                import shutil
                shutil.copy2(self.output_path, dest)
                messagebox.showinfo("完成", f"已保存到：\n{dest}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败：{e}")

    def _on_right_click(self, event):
        """右键弹出菜单。"""
        if self.output_path:
            self._context_menu.tk_popup(event.x_root, event.y_root)

    def _copy_to_clipboard(self):
        """将生成的 GIF 复制到剪贴板。"""
        if not self.output_path:
            return
        try:
            from PIL import Image
            img = Image.open(self.output_path)
            # 转为位图放入剪贴板
            output = BytesIO()
            img.convert('RGB').save(output, 'BMP')
            data = output.getvalue()[14:]  # 去掉 BMP 文件头，保留 DIB 数据
            output.close()
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
        except Exception as e:
            messagebox.showerror("复制失败", f"无法复制到剪贴板：{e}")

    def reset(self):
        self.output_path = None
        self.preview_img = None
        self._draw_placeholder()


class HemisphereApp:
    """主应用窗口。"""

    def __init__(self, root):
        self.root = root
        root.title("半球面 GIF — 3D 旋转穹顶生成器")
        root.resizable(False, False)

        BG = "#fafafa"
        ACCENT = "#4a90d9"
        root.configure(bg=BG)

        # ── 顶部标题 ──
        title_frame = tk.Frame(root, bg=BG)
        title_frame.pack(pady=(15, 5))
        tk.Label(title_frame, text="🔄 半球面 GIF",
                 font=("Microsoft YaHei", 18, "bold"), bg=BG, fg="#333333").pack()
        tk.Label(title_frame, text="将图片映射到旋转的 3D 半球面上",
                 font=("Microsoft YaHei", 10), bg=BG, fg="#888888").pack()

        # ── 主体三栏 ──
        main = tk.Frame(root, bg=BG)
        main.pack(pady=(10, 5), padx=20)

        # 左栏：上传框
        self.upload_box = UploadBox(main, size=280)
        self.upload_box.grid(row=0, column=0, padx=(0, 10))

        # 中间：箭头 + 按钮
        center_col = tk.Frame(main, bg=BG)
        center_col.grid(row=0, column=1, padx=10)

        tk.Label(center_col, text="→", font=("Segoe UI", 48, "bold"),
                 bg=BG, fg=ACCENT).pack(pady=(40, 5))

        self.generate_btn = tk.Button(
            center_col, text="生成 GIF", command=self._start_generate,
            bg=ACCENT, fg="white", font=("Microsoft YaHei", 12, "bold"),
            relief="flat", padx=20, pady=8, cursor="hand2",
            activebackground="#3a7bc8", activeforeground="white",
        )
        self.generate_btn.pack(pady=(5, 10))

        self.progress = ttk.Progressbar(center_col, mode="indeterminate", length=120)
        self.progress.pack(pady=5)
        self.status_label = tk.Label(center_col, text="",
                                     font=("Microsoft YaHei", 9), bg=BG, fg="#888888")
        self.status_label.pack()

        # 右栏：预览框
        self.preview_box = PreviewBox(main, size=280)
        self.preview_box.grid(row=0, column=2, padx=(10, 0))

        # ── 参数设置栏 ──
        param_frame = tk.LabelFrame(root, text=" 参数设置 ",
                                    font=("Microsoft YaHei", 10, "bold"),
                                    bg=BG, fg="#555555", padx=10, pady=8)
        param_frame.pack(pady=(10, 10), padx=20, fill="x")

        row1 = tk.Frame(param_frame, bg=BG)
        row1.pack(pady=3)

        self._make_param(row1, "半径：", "radius", "200", 0, "px")
        self._make_param(row1, "帧数：", "frames", "60", 1, "")
        self._make_param(row1, "时长：", "duration", "50", 2, "ms")
        self._make_param(row1, "尺寸：", "size", "", 3, "auto")

        row2 = tk.Frame(param_frame, bg=BG)
        row2.pack(pady=3)

        self._make_param(row2, "旋转轴：", "axis", None, 0, "", is_combo=True, combo_vals=["y", "x"])
        self._make_param(row2, "变形：", "power", "1.25", 1, "")

        row3 = tk.Frame(param_frame, bg=BG)
        row3.pack(pady=3)

        self._make_param(row3, "背景 R：", "bg_r", "0", 0, "")
        self._make_param(row3, "背景 G：", "bg_g", "0", 1, "")
        self._make_param(row3, "背景 B：", "bg_b", "0", 2, "")

        self.params = {}
        for row in param_frame.winfo_children():
            for f in row.winfo_children():
                for c in f.winfo_children():
                    if isinstance(c, tk.Entry):
                        self.params[c._param_name] = c
                    elif isinstance(c, ttk.Combobox):
                        self.params[c._param_name] = c

        self.running = False
        self._output_temp = None

    def _make_param(self, parent, label, name, default, col, unit,
                    is_combo=False, combo_vals=None):
        f = tk.Frame(parent, bg="#fafafa")
        f.grid(row=0, column=col, padx=10)
        tk.Label(f, text=label, font=("Microsoft YaHei", 10),
                 bg="#fafafa", fg="#555555").pack(side="left")
        if is_combo:
            w = ttk.Combobox(f, values=combo_vals, state="readonly", width=3)
            w.set(combo_vals[0])
        else:
            w = tk.Entry(f, width=5, font=("Microsoft YaHei", 10),
                         justify="center")
            if default:
                w.insert(0, default)
        w.pack(side="left", padx=(3, 0))
        if unit:
            tk.Label(f, text=unit, font=("Microsoft YaHei", 9),
                     bg="#fafafa", fg="#999999").pack(side="left", padx=(2, 0))
        w._param_name = name

    def _get_param(self, name, dtype=int, default=None):
        w = self.params.get(name)
        if w is None:
            return default
        val = w.get().strip()
        if not val:
            return default
        try:
            return dtype(val)
        except ValueError:
            return default

    def _start_generate(self):
        if self.running:
            return
        if not self.upload_box.image_path:
            messagebox.showwarning("未选择图片", "请先上传一张图片。")
            return

        self.running = True
        self.generate_btn.config(state="disabled", text="正在生成...")
        self.progress.start(10)
        self.status_label.config(text="处理中...")
        self.preview_box.reset()

        radius = self._get_param("radius", int, 200)
        frames = self._get_param("frames", int, 60)
        duration = self._get_param("duration", int, 50)
        size = self._get_param("size", int, None)
        axis = self._get_param("axis", str, "y")
        power = self._get_param("power", float, 1.25)
        bg_r = self._get_param("bg_r", int, 0)
        bg_g = self._get_param("bg_g", int, 0)
        bg_b = self._get_param("bg_b", int, 0)

        fd, self._output_temp = tempfile.mkstemp(suffix=".gif")
        os.close(fd)

        input_path = self.upload_box.image_path
        output_temp = self._output_temp

        def _run():
            try:
                create_hemisphere_gif(
                    input_path=input_path,
                    output_path=output_temp,
                    radius=radius,
                    num_frames=frames,
                    duration=duration,
                    output_size=size,
                    axis=axis,
                    bg_color=(bg_r, bg_g, bg_b),
                    power=power,
                )
                self.root.after(0, self._on_done, output_temp)
            except Exception as e:
                self.root.after(0, self._on_error, str(e))

        t = threading.Thread(target=_run, daemon=True)
        t.start()

    def _on_done(self, gif_path):
        self.running = False
        self.progress.stop()
        self.generate_btn.config(state="normal", text="生成 GIF")

        size_kb = os.path.getsize(gif_path) / 1024
        self.status_label.config(text=f"完成！{size_kb:.0f} KB")

        self.preview_box.show_preview(gif_path)

    def _on_error(self, msg):
        self.running = False
        self.progress.stop()
        self.generate_btn.config(state="normal", text="生成 GIF")
        self.status_label.config(text="错误")
        messagebox.showerror("生成失败", msg)


def main():
    root = tk.Tk()
    app = HemisphereApp(root)
    root.update_idletasks()
    w = root.winfo_width()
    h = root.winfo_height()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    root.geometry(f"+{x}+{y}")
    root.mainloop()


if __name__ == "__main__":
    main()

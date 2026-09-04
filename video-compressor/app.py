"""Compresor de Video — interfaz gráfica (Tkinter).

Ejecutar con:  python app.py
"""
import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import compressor

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

BG = "#f4f5f7"
ACCENT = "#2563eb"
ACCENT_DARK = "#1d4ed8"


class VideoCompressorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Compresor de Video")
        self.root.geometry("480x480")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        self.file_queue = []
        self.is_running = False
        self.progress_queue: "queue.Queue[tuple]" = queue.Queue()

        self.codec_var = tk.StringVar(value="h264")
        self.keep_audio_var = tk.BooleanVar(value=False)

        self._build_ui()

        if not DND_AVAILABLE:
            self.hint_label.config(
                text="Arrastrar y soltar no disponible (instala tkinterdnd2). Usa el botón para elegir el archivo."
            )

        if not compressor.check_ffmpeg_available():
            messagebox.showerror(
                "FFmpeg no encontrado",
                "No se encontró 'ffmpeg' o 'ffprobe' en el PATH del sistema.\n\n"
                "Instala FFmpeg y verifica que el comando 'ffmpeg -version' "
                "funcione en una terminal antes de usar esta aplicación.",
            )

        self.root.after(100, self._poll_queue)

    # ---------------------------------------------------------- UI
    def _build_ui(self):
        pad = {"padx": 16}

        tk.Label(
            self.root, text="Compresor de Video", font=("Segoe UI", 16, "bold"), bg=BG
        ).pack(pady=(18, 4))

        tk.Label(
            self.root,
            text="Reduce el tamaño de tus videos sin pérdida de calidad perceptible.",
            font=("Segoe UI", 9), fg="#666", bg=BG,
        ).pack(pady=(0, 14))

        self.drop_zone = tk.Label(
            self.root,
            text="📁\n\nArrastra tu video aquí\no haz clic para seleccionar",
            font=("Segoe UI", 11),
            bg="white", fg="#555",
            relief="ridge", bd=2,
            width=40, height=6,
            cursor="hand2",
        )
        self.drop_zone.pack(**pad, pady=(0, 4))
        self.drop_zone.bind("<Button-1>", lambda _e: self.select_file())

        self.hint_label = tk.Label(self.root, text="", font=("Segoe UI", 8), fg="#999", bg=BG, wraplength=440)
        self.hint_label.pack(pady=(0, 8))

        self.file_label = tk.Label(
            self.root, text="Ningún archivo seleccionado", font=("Segoe UI", 9), bg=BG, fg="#333"
        )
        self.file_label.pack(pady=(0, 10))

        options = tk.Frame(self.root, bg=BG)
        options.pack(**pad, pady=(0, 6), fill="x")

        tk.Label(options, text="Códec de video:", font=("Segoe UI", 9, "bold"), bg=BG).grid(
            row=0, column=0, sticky="w", pady=(0, 2)
        )
        for i, (value, preset) in enumerate(compressor.CODEC_PRESETS.items(), start=1):
            tk.Radiobutton(
                options, text=preset["label"], variable=self.codec_var, value=value,
                bg=BG, font=("Segoe UI", 9),
            ).grid(row=i, column=0, sticky="w")

        tk.Checkbutton(
            options, text="Mantener audio original (sin recomprimir)",
            variable=self.keep_audio_var, bg=BG, font=("Segoe UI", 9),
        ).grid(row=len(compressor.CODEC_PRESETS) + 1, column=0, sticky="w", pady=(6, 0))

        self.compress_btn = tk.Button(
            self.root, text="Comprimir video", font=("Segoe UI", 11, "bold"),
            bg=ACCENT, fg="white", activebackground=ACCENT_DARK, activeforeground="white",
            relief="flat", padx=12, pady=8, state="disabled", command=self.start_compression,
        )
        self.compress_btn.pack(pady=(12, 10))

        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=440, mode="determinate")
        self.progress.pack(**pad)

        self.status_label = tk.Label(
            self.root, text="Esperando un video…", font=("Segoe UI", 9), bg=BG, fg="#555", wraplength=440
        )
        self.status_label.pack(pady=(8, 0))

        if DND_AVAILABLE:
            self.drop_zone.drop_target_register(DND_FILES)
            self.drop_zone.dnd_bind("<<Drop>>", self.on_drop)

    # ---------------------------------------------------- selección
    def select_file(self):
        if self.is_running:
            return
        paths = filedialog.askopenfilenames(
            title="Selecciona uno o más videos",
            filetypes=[
                ("Videos", "*.mp4 *.mov *.mkv *.avi *.webm *.m4v *.wmv *.flv *.ts"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if paths:
            self._set_queue(list(paths))

    def on_drop(self, event):
        if self.is_running:
            return
        paths = [p for p in self.drop_zone.tk.splitlist(event.data) if os.path.isfile(p)]
        if paths:
            self._set_queue(paths)

    def _set_queue(self, paths):
        self.file_queue = paths
        if len(paths) == 1:
            self.file_label.config(text=os.path.basename(paths[0]))
        else:
            self.file_label.config(text=f"{len(paths)} archivos seleccionados")
        self.compress_btn.config(state="normal")
        self.progress["value"] = 0
        self.status_label.config(text="Listo para comprimir.")

    # ---------------------------------------------------- compresión
    def start_compression(self):
        if not self.file_queue or self.is_running:
            return
        self.is_running = True
        self.compress_btn.config(state="disabled")
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        codec = self.codec_var.get()
        keep_audio = self.keep_audio_var.get()
        total = len(self.file_queue)

        for i, input_path in enumerate(self.file_queue):
            name = os.path.basename(input_path)
            self.progress_queue.put(("start", i, total, name))
            try:
                def report(pct, _i=i, _total=total):
                    self.progress_queue.put(("progress", _i, _total, pct))

                output_path = compressor.compress(
                    input_path, codec=codec, keep_original_audio=keep_audio, progress_callback=report
                )
                original_size = os.path.getsize(input_path)
                new_size = os.path.getsize(output_path)
                self.progress_queue.put(("file_done", i, total, output_path, original_size, new_size))
            except compressor.CompressionError as exc:
                self.progress_queue.put(("error", i, total, name, str(exc)))

        self.progress_queue.put(("all_done", total))

    def _poll_queue(self):
        try:
            while True:
                item = self.progress_queue.get_nowait()
                kind = item[0]

                if kind == "start":
                    _, i, total, name = item
                    self.status_label.config(text=f"Comprimiendo ({i + 1}/{total}): {name}")
                    self.progress["value"] = 0

                elif kind == "progress":
                    _, _i, _total, pct = item
                    self.progress["value"] = pct

                elif kind == "file_done":
                    _, i, total, output_path, original_size, new_size = item
                    reduction = (1 - new_size / original_size) * 100 if original_size else 0
                    self.progress["value"] = 100
                    self.status_label.config(
                        text=(
                            f"✔ {os.path.basename(output_path)} — {self._fmt_size(new_size)} "
                            f"({reduction:.0f}% más pequeño)"
                        )
                    )

                elif kind == "error":
                    _, i, total, name, message = item
                    self.status_label.config(text=f"✘ Error al comprimir {name}")
                    messagebox.showerror("Error de compresión", f"{name}:\n\n{message}")

                elif kind == "all_done":
                    _, total = item
                    self.is_running = False
                    self.compress_btn.config(state="normal")
                    if total > 1:
                        self.status_label.config(text=f"Proceso completado: {total} video(s) procesados.")
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._poll_queue)

    @staticmethod
    def _fmt_size(num_bytes):
        size = float(num_bytes)
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


def main():
    root = TkinterDnD.Tk() if DND_AVAILABLE else tk.Tk()
    VideoCompressorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

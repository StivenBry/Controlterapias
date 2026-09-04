"""Motor de compresión de video basado en FFmpeg.

No depende de la interfaz gráfica: recibe una ruta de entrada, un códec y
una función de progreso opcional, y devuelve la ruta del archivo comprimido.
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, Optional

FFMPEG_BIN = "ffmpeg"
FFPROBE_BIN = "ffprobe"

# En Windows, evita que cada llamada a ffmpeg/ffprobe abra una consola negra.
_POPEN_KWARGS = {"creationflags": 0x08000000} if sys.platform == "win32" else {}

# CRF recomendado por códec: mejor balance tamaño/calidad visual según la
# documentación oficial de FFmpeg (23 para H.264, 28 para H.265 es
# aproximadamente equivalente en calidad percibida).
CODEC_PRESETS = {
    "h264": {
        "label": "H.264 — recomendado, máxima compatibilidad",
        "vcodec": "libx264",
        "crf": 23,
        "extra_args": [],
    },
    "h265": {
        "label": "H.265 / HEVC — archivos más pequeños, más lento",
        "vcodec": "libx265",
        "crf": 28,
        # hvc1 mejora la compatibilidad de HEVC en contenedores MP4 (Apple/QuickTime).
        "extra_args": ["-tag:v", "hvc1"],
    },
}


class CompressionError(RuntimeError):
    """Se lanza cuando ffmpeg/ffprobe fallan o no están disponibles."""


def check_ffmpeg_available() -> bool:
    """True si ffmpeg y ffprobe son ejecutables desde el PATH del sistema."""
    for binary in (FFMPEG_BIN, FFPROBE_BIN):
        try:
            subprocess.run(
                [binary, "-version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
                **_POPEN_KWARGS,
            )
        except (OSError, subprocess.CalledProcessError):
            return False
    return True


def get_duration_seconds(path: str) -> float:
    """Duración del video en segundos, vía ffprobe."""
    cmd = [
        FFPROBE_BIN, "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        path,
    ]
    result = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **_POPEN_KWARGS
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        raise CompressionError(
            f"No se pudo leer '{Path(path).name}' como video:\n{result.stderr.strip()}"
        )


def build_output_path(input_path: str) -> str:
    """<carpeta original>/<nombre>_comprimido.mp4"""
    p = Path(input_path)
    return str(p.with_name(f"{p.stem}_comprimido.mp4"))


_OUT_TIME_RE = re.compile(r"out_time=(\d+):(\d+):(\d+)\.(\d+)")


def compress(
    input_path: str,
    codec: str = "h264",
    keep_original_audio: bool = False,
    progress_callback: Optional[Callable[[float], None]] = None,
) -> str:
    """Comprime `input_path` y devuelve la ruta del archivo de salida.

    Lanza CompressionError si ffmpeg termina con un error.
    """
    if codec not in CODEC_PRESETS:
        raise ValueError(f"Códec desconocido: {codec}")

    preset = CODEC_PRESETS[codec]
    output_path = build_output_path(input_path)
    duration = get_duration_seconds(input_path)

    audio_args = ["-c:a", "copy"] if keep_original_audio else ["-c:a", "aac", "-b:a", "128k"]

    cmd = [
        FFMPEG_BIN, "-y", "-i", input_path,
        "-c:v", preset["vcodec"], "-crf", str(preset["crf"]), "-preset", "medium",
        "-pix_fmt", "yuv420p",
        *preset["extra_args"],
        *audio_args,
        "-movflags", "+faststart",
        "-loglevel", "error",
        "-progress", "pipe:1", "-nostats",
        output_path,
    ]

    # stderr va a un archivo real (no a un pipe) para evitar bloqueos si
    # ffmpeg escribe más de lo que cabe en el buffer del pipe mientras solo
    # leemos stdout para el progreso.
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as stderr_file:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=stderr_file,
            text=True,
            bufsize=1,
            **_POPEN_KWARGS,
        )

        assert process.stdout is not None
        for line in process.stdout:
            line = line.strip()
            if not progress_callback:
                continue
            if line == "progress=end":
                progress_callback(100.0)
            elif line.startswith("out_time="):
                match = _OUT_TIME_RE.match(line)
                if match and duration > 0:
                    h, m, s, _ = match.groups()
                    elapsed = int(h) * 3600 + int(m) * 60 + int(s)
                    progress_callback(min(elapsed / duration * 100, 99.0))

        process.wait()

        if process.returncode != 0:
            stderr_file.seek(0)
            error_text = stderr_file.read().strip()
            Path(output_path).unlink(missing_ok=True)
            raise CompressionError(error_text[-2000:] or "FFmpeg terminó con un error desconocido.")

    return output_path

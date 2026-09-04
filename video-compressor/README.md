# Compresor de Video

Aplicación de escritorio local y minimalista para comprimir videos rápidamente
con FFmpeg, sin pérdida perceptible de calidad. Interfaz en Tkinter (Python)
con soporte de arrastrar y soltar.

## ¿Por qué Tkinter + FFmpeg?

Es la combinación más ligera de las permitidas para este tipo de herramienta:

- **Tkinter** viene incluido con Python (no hay que instalar un framework de
  UI aparte, a diferencia de PyQt, que pesa decenas de MB adicionales).
- **FFmpeg** es el motor de compresión de facto: rápido, gratuito y disponible
  en todos los sistemas operativos.
- Frente a **Electron**, que empaqueta un Chromium + Node.js completo (100+ MB
  solo para mostrar una ventana), esta app es un par de scripts de Python de
  pocos KB.

## Prerrequisitos

1. **Python 3.9 o superior** — <https://www.python.org/downloads/>
   Verifica con:
   ```bash
   python3 --version
   ```

2. **FFmpeg** (incluye `ffmpeg` y `ffprobe`) instalado y disponible en el
   PATH del sistema — <https://ffmpeg.org/download.html>

   - **Windows**: descarga el build desde el sitio oficial (o instala con
     `winget install ffmpeg` / `choco install ffmpeg`) y agrega la carpeta
     `bin` al PATH.
   - **macOS**: `brew install ffmpeg`
   - **Linux (Debian/Ubuntu)**: `sudo apt install ffmpeg`
   - **Linux (Fedora)**: `sudo dnf install ffmpeg`

   Verifica con:
   ```bash
   ffmpeg -version
   ```

3. **tkinterdnd2** (para arrastrar y soltar) — se instala con pip, ver abajo.
   Es opcional: si no está instalado, la app funciona igual usando el botón
   "seleccionar archivo".

## Instalación

```bash
cd video-compressor

# (Recomendado) entorno virtual
python3 -m venv venv
source venv/bin/activate      # En Windows: venv\Scripts\activate

pip install -r requirements.txt
```

## Ejecutar

```bash
python app.py
```

Se abrirá la ventana de la aplicación. Arrastra un video (o varios) sobre el
recuadro, o haz clic para elegirlo con el explorador de archivos, elige el
códec y pulsa **Comprimir video**.

El resultado se guarda automáticamente en la **misma carpeta** del archivo
original, con el sufijo `_comprimido.mp4` (por ejemplo, `viaje.mp4` →
`viaje_comprimido.mp4`).

## Configuración de compresión

| Opción | Detalle |
|---|---|
| **H.264** (por defecto) | `libx264`, CRF 23 — máxima compatibilidad con reproductores y dispositivos. |
| **H.265 / HEVC** | `libx265`, CRF 28 — mismo nivel de calidad visual con archivos más pequeños; codifica más lento y algunos reproductores antiguos no lo soportan. |
| **Audio** | Por defecto se recomprime a AAC 128 kbps (buen ahorro, sin degradación notable). Puedes marcar "Mantener audio original" para copiarlo tal cual. |

Ambos códecs usan `-preset medium` (balance estándar de FFmpeg entre
velocidad de codificación y eficiencia de compresión) y `-movflags
+faststart`, para que los MP4 resultantes empiecen a reproducirse de
inmediato en la web sin tener que descargarse por completo.

## Generar un ejecutable independiente (opcional)

Si quieres un `.exe`/`.app` que no requiera abrir una terminal:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "CompresorDeVideo" --collect-all tkinterdnd2 app.py
```

El ejecutable queda en `dist/`. FFmpeg **sigue siendo necesario** en el
sistema donde se ejecute (el ejecutable no lo incluye).

## Estructura del proyecto

```
video-compressor/
├── app.py           # Interfaz gráfica (Tkinter) e hilo de trabajo
├── compressor.py     # Lógica de compresión con FFmpeg (sin dependencias de UI)
├── requirements.txt
└── README.md
```

## Solución de problemas

- **"No se encontró ffmpeg o ffprobe en el PATH"**: reinstala FFmpeg y
  confirma que `ffmpeg -version` funciona en una terminal nueva (a veces hay
  que reiniciar la terminal o la sesión tras instalarlo).
- **El arrastrar y soltar no funciona**: instala `tkinterdnd2`
  (`pip install tkinterdnd2`) y reinicia la app. Mientras tanto, el botón de
  selección de archivo siempre funciona como alternativa.
- **El video comprimido no reproduce en un dispositivo antiguo**: usa H.264
  en vez de H.265; tiene mejor soporte en reproductores y TVs más viejos.

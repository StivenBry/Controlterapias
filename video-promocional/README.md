# Videos de suscripciones – Pasiones en Pantalla

Videos verticales (1080x1920, 30 fps) para el desafío de suscripciones de Facebook.

| Video | Duración | Para qué |
| --- | --- | --- |
| `video-promocional-suscripciones.mp4` | 40 s | Tarea «Agrega un video promocional»: muestra los beneficios y el precio. |
| `video-agradecimiento.mp4` | 25 s | «Video de agradecimiento»: se envía a cada persona apenas se suscribe. |

`portada.png` es una portada opcional para el video promocional.

## Archivos fuente

- `promocional.html` y `agradecimiento.html`: las animaciones. Si las abres en el navegador, se reproducen en bucle (`?t=12` salta al segundo 12).
- `estilos.css` y `motor.js`: los estilos y el motor de animación que comparten las dos.
- `musica.py`: genera la música de fondo y los efectos de sonido de cada video.
- `render.js`: graba una animación cuadro a cuadro.

## Volver a generar un video

```sh
python3 musica.py agradecimiento musica.wav
node render.js agradecimiento.html video-mudo.mp4
ffmpeg -i video-mudo.mp4 -i musica.wav -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart video-agradecimiento.mp4
```

Para el promocional, cambia `agradecimiento` por `promocional`. `render.js` necesita Playwright con Chromium, y `musica.py` necesita numpy.

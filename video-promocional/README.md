# Video promocional de suscripciones

Video vertical (1080x1920, 30 fps, 40 s) para la tarea «Agrega un video promocional» del desafío de suscripciones de Facebook.

- `video-promocional-suscripciones.mp4`: el video listo para subir.
- `portada.png`: imagen de portada opcional.
- `index.html`: la animación. Si lo abres en el navegador, se reproduce en bucle (`?t=24` salta al segundo 24).
- `musica.py`: genera la música de fondo y los efectos de sonido.
- `render.js`: graba la animación cuadro a cuadro.

## Volver a generar el video

```sh
python3 musica.py musica.wav
node render.js video-mudo.mp4
ffmpeg -i video-mudo.mp4 -i musica.wav -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart video-promocional-suscripciones.mp4
```

`render.js` necesita Playwright con Chromium, y `musica.py` necesita numpy.

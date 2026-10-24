// Renderiza una de las animaciones cuadro a cuadro y la codifica en un MP4 vertical (1080x1920, 30 fps).
//   node render.js promocional.html salida.mp4                -> video completo (sin audio)
//   node render.js promocional.html --stills carpeta 0 6 24.5 -> capturas PNG en esos segundos
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const FPS = 30;

(async () => {
  const [pagina, ...args] = process.argv.slice(2);
  const url = 'file://' + path.resolve(__dirname, pagina) + '?render';
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto(url);
  await page.evaluate(() => document.fonts.ready);

  if (args[0] === '--stills') {
    const dir = args[1];
    fs.mkdirSync(dir, { recursive: true });
    for (const t of args.slice(2).map(Number)) {
      await page.evaluate(t => window.seek(t), t);
      await page.screenshot({ path: path.join(dir, `t${t.toFixed(2)}.png`) });
    }
    await browser.close();
    return;
  }

  const out = args[0] || 'video.mp4';
  const duration = await page.evaluate(() => window.DURATION);
  const total = Math.round(duration * FPS);
  const ff = spawn('ffmpeg', [
    '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out,
  ], { stdio: ['pipe', 'inherit', 'inherit'] });

  for (let f = 0; f < total; f++) {
    await page.evaluate(t => window.seek(t), f / FPS);
    const png = await page.screenshot({ type: 'png' });
    if (!ff.stdin.write(png)) await new Promise(r => ff.stdin.once('drain', r));
    if (f % 150 === 0) console.log(`cuadro ${f}/${total}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
  console.log('listo:', out);
})();

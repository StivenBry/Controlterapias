// Motor de animación compartido por los videos.
// Todas las animaciones quedan en pausa y se posicionan con seek(t), así cada cuadro
// del render es determinista. Al abrir la página en el navegador se reproduce en bucle
// (?t=12 salta al segundo 12); render.js la carga con ?render.
const RENDER = new URLSearchParams(location.search).has('render');

const ICONS = {
  lock: '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
  bag: '<path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 0 1-8 0"/>',
  video: '<path d="m16 13 5.223 3.482a.5.5 0 0 0 .777-.416V7.87a.5.5 0 0 0-.752-.432L16 10.5"/><rect x="2" y="6" width="14" height="12" rx="2"/>',
  sticker: '<path d="M15.5 3H5a2 2 0 0 0-2 2v14c0 1.1.9 2 2 2h14a2 2 0 0 0 2-2V8.5L15.5 3Z"/><path d="M15 3v4a2 2 0 0 0 2 2h4"/><path d="M8 13h.01"/><path d="M16 13h.01"/><path d="M10 16s.8 1 2 1c1.3 0 2-1 2-1"/>',
  chat: '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/><path d="M8 12h.01"/><path d="M12 12h.01"/><path d="M16 12h.01"/>',
  badge: '<path d="M6 3.5h12A1.5 1.5 0 0 1 19.5 5v9.2a1.5 1.5 0 0 1-.66 1.24L12 20l-6.84-4.56A1.5 1.5 0 0 1 4.5 14.2V5A1.5 1.5 0 0 1 6 3.5Z"/><path fill="currentColor" stroke="none" d="M12 15.5l-3.4-3.3a2.1 2.1 0 0 1 3-3l.4.4.4-.4a2.1 2.1 0 0 1 3 3Z"/>',
  user: '<circle cx="12" cy="8" r="4.5"/><path d="M20 21a8 8 0 0 0-16 0"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
};
document.querySelectorAll('i[data-icon]').forEach(el => {
  el.outerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">${ICONS[el.dataset.icon]}</svg>`;
});

const $ = s => typeof s === 'string' ? document.querySelector(s) : s;
const ALL = [], HOOKS = [];
const EASE = {
  out: 'cubic-bezier(.22,1,.36,1)',
  back: 'cubic-bezier(.34,1.56,.64,1)',
  in: 'cubic-bezier(.55,0,1,.45)',
  inOut: 'cubic-bezier(.65,0,.35,1)',
};
function anim(el, frames, start, dur, opts = {}) {
  const a = $(el).animate(frames, {
    duration: dur * 1000, delay: start * 1000, fill: opts.fill || 'both',
    easing: opts.easing || EASE.out, iterations: opts.iterations || 1, direction: opts.direction || 'normal',
  });
  a.pause();
  ALL.push(a);
  return a;
}
// Una escena aparece en `start` y se desvanece al llegar a `end` (sin `end` se queda hasta el final).
function scene(el, start, end) {
  anim(el, [{ opacity: 0 }, { opacity: 1 }], start - 0.05, 0.35, { easing: 'linear' });
  if (end) anim(el, [{ opacity: 1, transform: 'scale(1)' }, { opacity: 0, transform: 'scale(1.035)' }], end - 0.3, 0.32, { fill: 'forwards', easing: EASE.in });
}
function fadeUp(el, t, dur = 0.6, dist = 50) {
  anim(el, [{ opacity: 0, transform: `translateY(${dist}px)` }, { opacity: 1, transform: 'translateY(0)' }], t, dur);
}
function pop(el, t, dur = 0.7, rot = -12) {
  anim(el, [{ opacity: 0, transform: `scale(.3) rotate(${rot}deg)` }, { opacity: 1, transform: 'scale(1) rotate(0deg)' }], t, dur, { easing: EASE.back });
}
function loop(el, frames, start, dur, easing = 'ease-in-out', direction = 'normal') {
  anim(el, frames, start, dur, { iterations: Infinity, easing, direction });
}
function seek(t) {
  for (const a of ALL) a.currentTime = t * 1000;
  for (const h of HOOKS) h(t);
}

// Explosión de confeti desde `container` (aleatoria pero fija para que cada render sea igual).
// `spread` es la apertura en medias vueltas alrededor de `angle`.
function confetti(container, t, count, { seed = 7, angle = -Math.PI / 2, spread = 1.5, dist = [260, 380], fall = 420 } = {}) {
  const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  const COLORS = ['#5fd39a', '#36c2c9', '#4aa3ff', '#fbbf24', '#f472b6', '#ffffff', '#c084fc'];
  const box = $(container);
  for (let k = 0; k < count; k++) {
    const p = document.createElement('i');
    const w = 14 + rnd() * 14, h = rnd() < .4 ? w : w * 1.7;
    Object.assign(p.style, {
      width: w + 'px', height: h + 'px', margin: `${-h / 2}px 0 0 ${-w / 2}px`,
      background: COLORS[k % COLORS.length], borderRadius: rnd() < .4 ? '50%' : '5px',
    });
    box.appendChild(p);
    const ang = angle + (rnd() - .5) * Math.PI * spread;
    const d = dist[0] + rnd() * dist[1];
    const dx = Math.cos(ang) * d, dy = Math.sin(ang) * d;
    const r = (rnd() - .5) * 900;
    anim(p, [
      { opacity: 1, transform: 'translate(0,0) rotate(0deg) scale(.4)' },
      { opacity: 1, transform: `translate(${dx}px,${dy}px) rotate(${r / 2}deg) scale(1)`, offset: .45, easing: 'cubic-bezier(.3,0,.7,1)' },
      { opacity: 0, transform: `translate(${dx * 1.2}px,${dy + fall}px) rotate(${r}deg) scale(.9)` },
    ], t + rnd() * 0.08, 1.5 + rnd() * 0.4, { easing: 'cubic-bezier(.1,.8,.3,1)', fill: 'forwards' });
  }
}

// Fondo en movimiento lento, igual en todos los videos
loop('.b1', [{ transform: 'translate(0,0)' }, { transform: 'translate(140px,180px)' }], 0, 9, 'ease-in-out', 'alternate');
loop('.b2', [{ transform: 'translate(0,0)' }, { transform: 'translate(-160px,-140px)' }], 0, 11, 'ease-in-out', 'alternate');
loop('.b3', [{ transform: 'translate(0,0)' }, { transform: 'translate(120px,-160px)' }], 0, 13, 'ease-in-out', 'alternate');

function start(duration) {
  window.DURATION = duration;
  window.seek = seek;
  if (RENDER) {
    document.body.classList.add('render');
    seek(0);
    return;
  }
  const stage = $('#stage');
  const fit = () => stage.style.transform = `scale(${Math.min(innerWidth / 1080, innerHeight / 1920)})`;
  addEventListener('resize', fit); fit();
  const t0 = performance.now() - (parseFloat(new URLSearchParams(location.search).get('t')) || 0) * 1000;
  const tick = () => { seek(((performance.now() - t0) / 1000) % duration); requestAnimationFrame(tick); };
  tick();
}

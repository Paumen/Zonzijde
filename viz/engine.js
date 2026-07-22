const anims = new Set();

export const engine = {
  speed: 4,
  paused: false,
};

export function D(ms) {
  return Math.max(0, ms) / engine.speed;
}

export function setPaused(p) {
  engine.paused = p;
  for (const a of anims) {
    try { p ? a.pause() : a.play(); } catch (e) { void e; }
  }
}

export function setSpeed(s) {
  engine.speed = s;
}

function track(a) {
  if (!a) return a;
  anims.add(a);
  const drop = () => anims.delete(a);
  a.finished.then(drop).catch(drop);
  if (engine.paused) { try { a.pause(); } catch (e) {} }
  return a;
}

export function raf() {
  return new Promise((res) => requestAnimationFrame(() => res()));
}

export async function settle() {
  await raf();
  await raf();
}

export function sleep(ms) {
  return new Promise((res) => {
    if (ms <= 0) return res();
    let remaining = ms;
    let last = performance.now();
    function tick(now) {
      if (!engine.paused) remaining -= (now - last);
      last = now;
      if (remaining <= 0) res();
      else requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  });
}

export function placeAt(node, x, y, w, h) {
  node._x = x; node._y = y; node._w = w; node._h = h;
  const el = node.el;
  el.style.width = w + "px";
  el.style.height = h + "px";
  el.style.transform = `translate(${x}px, ${y}px)`;
}

export function moveTo(node, x, y, opts = {}) {
  const el = node.el;
  const fromT = `translate(${node._x ?? x}px, ${node._y ?? y}px)`;
  const fromW = (node._w ?? opts.w ?? el.offsetWidth) + "px";
  const fromH = (node._h ?? opts.h ?? el.offsetHeight) + "px";
  const w = opts.w ?? node._w;
  const h = opts.h ?? node._h;
  node._x = x; node._y = y; node._w = w; node._h = h;
  el.style.transform = `translate(${x}px, ${y}px)`;
  el.style.width = w + "px";
  el.style.height = h + "px";
  const to = { transform: el.style.transform, width: w + "px", height: h + "px" };
  const from = { transform: fromT, width: fromW, height: fromH };
  const a = el.animate([from, to], {
    duration: D(opts.dur ?? 700),
    delay: D(opts.delay ?? 0),
    easing: opts.easing ?? "cubic-bezier(.6,.02,.2,1)",
  });
  return track(a);
}

export async function flyOut(node, x, y, opts = {}) {
  const a = moveTo(node, x, y, { ...opts, w: opts.w ?? 6, h: opts.h ?? 6 });
  node.el.animate(
    [{ opacity: 1 }, { opacity: 0 }],
    { duration: D(opts.dur ?? 700), delay: D(opts.delay ?? 0), fill: "forwards" });
  await a.finished.catch(() => {});
  node.el.remove();
}

export function pulse(el, on) {
  el.classList.toggle("pulse", on);
}

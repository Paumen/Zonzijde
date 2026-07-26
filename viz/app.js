import { Engine, Camera, Sprite } from "./engine.js";
import { bouwKrant, PAGE_W, PAGE_H } from "./paper.js";

const world = document.getElementById("world");
const balk = document.getElementById("speeds");

const trace = await (await fetch("viz/viz-trace.json")).json();
const FONTS = [
  "500 16px Archivo", "600 16px Archivo", "700 16px Archivo",
  "400 16px Fraunces", "560 16px Fraunces", "640 16px Fraunces", "700 16px Fraunces",
  "400 16px Newsreader", "500 16px Newsreader", "italic 400 16px Newsreader",
];
if (document.fonts) {
  await Promise.all(FONTS.map(f => document.fonts.load(f, "Zonzijde 0123")));
  await document.fonts.ready;
}
await Promise.all(["assets/art/zonnebloem.svg", "assets/art/landschap.svg"].map(src =>
  new Promise(klaar => {
    const i = new Image();
    i.onload = i.onerror = klaar;
    i.src = src;
  })));

const vp = { w: window.innerWidth, h: window.innerHeight };
const eng = new Engine();

const krant = bouwKrant(trace, world);
new Sprite(krant.el, 0, 0).apply();
for (const el of world.querySelectorAll(".dof")) el.classList.remove("dof");
for (const art of krant.artikelen.values()) {
  art.werk.style.opacity = 0;
  for (const w of art.kopWoorden) w.classList.add("op");
  for (const w of art.woorden) w.classList.add("op");
  if (art.illo) art.illo.classList.remove("onthul");
}
for (const p of krant.pages) p.el.classList.add("af");

const cam = new Camera(0, krant.hoogte / 2,
  Math.max(krant.breedte * 1.1, krant.hoogte * 1.06 * vp.w / vp.h));

const params = new URLSearchParams(location.search);
const totaal = trace.meta.screen_total_ms + 6000;
let tempo = trace.meta.speeds.includes(Number(params.get("speed")))
  ? Number(params.get("speed")) : trace.meta.default_speed;

for (const s of trace.meta.speeds) {
  const b = document.createElement("button");
  b.textContent = "×" + s;
  b.onclick = () => {
    tempo = s;
    for (const k of balk.children) k.setAttribute("aria-pressed", k === b);
  };
  b.setAttribute("aria-pressed", s === tempo);
  balk.appendChild(b);
}
const herstart = document.createElement("button");
herstart.textContent = "↺";
herstart.onclick = () => location.reload();
balk.appendChild(herstart);

function teken() {
  const schaal = vp.w / cam.vw;
  world.style.transform =
    `translate(${(vp.w / 2 - cam.cx * schaal).toFixed(2)}px,${(vp.h / 2 - cam.cy * schaal).toFixed(2)}px) ` +
    `scale(${schaal.toFixed(5)})`;
}

const spring = Math.max(0, Number(params.get("t")) || 0) * 1000;
if (spring > 0) {
  while (eng.t < spring) eng.step(Math.min(50, spring - eng.t));
  eng.flush();
}

window.addEventListener("resize", () => {
  vp.w = window.innerWidth;
  vp.h = window.innerHeight;
  teken();
});

let vorige = performance.now();
function frame(nu) {
  const dt = Math.min(100, nu - vorige) * tempo;
  vorige = nu;
  if (eng.t < totaal) {
    eng.step(dt);
    cam.sample(eng.t);
    eng.flush();
    teken();
  }
  requestAnimationFrame(frame);
}
cam.sample(eng.t);
teken();
requestAnimationFrame(nu => { vorige = nu; frame(nu); });

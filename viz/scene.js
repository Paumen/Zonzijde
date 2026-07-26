import { Sprite, EASE, rng } from "./engine.js";
import { bouwKrant, PAGE_W, PAGE_H } from "./paper.js";

const CLIP_W = 66, CLIP_H = 22;
const RA_KOL = 5, RA_DX = 70, RA_DY = 11;
const PILE_RX = 205, PILE_RY = 395;
const ST_KOL = 4, ST_DX = 96, ST_DY = 96;
const MID_Y = 40;
const BORD_Y = 700;

const esc = s => String(s ?? "").replace(/[&<>"]/g, c =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function raster(i, n, kol, dx, dy, cx, cy, bh = CLIP_H) {
  const rijen = Math.ceil(n / kol);
  const kolommen = Math.min(n, kol);
  const bx = cx - (kolommen * dx - (dx - CLIP_W)) / 2;
  const by = cy - ((rijen - 1) * dy + bh) / 2;
  return { x: bx + (i % kol) * dx, y: by + Math.floor(i / kol) * dy };
}

function rasterHoog(n, kol, dy, bh = CLIP_H) {
  return (Math.ceil(n / kol) - 1) * dy + bh;
}

function landingen(fase, marge) {
  const einden = (fase.spans || []).map(s => s[1]).sort((a, b) => a - b);
  if (!einden.length) return [];
  const laatst = einden[einden.length - 1] / fase.real_ms;
  const f = Math.min(1, marge / laatst);
  return einden.map(e =>
    fase.screen_start_ms + (e / fase.real_ms) * fase.screen_ms * f);
}

function markeer(titel, treffers) {
  let uit = esc(titel);
  for (const h of treffers || []) {
    const m = esc(h.match);
    const i = uit.toLowerCase().indexOf(m.toLowerCase());
    if (i < 0 || uit.slice(0, i).includes("<mark>")) continue;
    uit = uit.slice(0, i) + "<mark>" + uit.slice(i, i + m.length) + "</mark>" +
      uit.slice(i + m.length);
  }
  return uit;
}

export function bouwScene(trace, world, eng, cam, aspect) {
  const R = rng(20260726);
  const F = {};
  for (const f of trace.fases) F[f.key] = f;
  const t0 = k => F[k].screen_start_ms;
  const eind = k => F[k].screen_start_ms + F[k].screen_ms;

  const laag = document.createElement("div");
  const krantHost = document.createElement("div");
  world.append(krantHost, laag);

  const krant = bouwKrant(trace, krantHost);
  const krantSp = new Sprite(krant.el, 0, BORD_Y);
  krantSp.apply();

  const zicht = h => Math.max(h * 1.06 / aspect, 240);
  const kader = (w, h) => Math.max(w * 1.1, zicht(h));

  const knipsels = [];
  const perBron = new Map();
  for (const node of trace.nodes) {
    const d = document.createElement("div");
    d.className = "sp clip" + (node.titled ? "" : [" oud", " oud oud2", " oud oud3"][knipsels.length % 3]);
    if (node.titled) {
      d.style.setProperty("--sc", `var(--${node.scopes[0]})`);
      d.innerHTML = `<span class="sc"></span><div class="b">${esc(node.f1.medium)}</div>` +
        `<div class="ttl">${markeer(node.f1.bron_titel, node.exit && node.exit.hits)}</div>`;
    }
    const sp = new Sprite(d);
    sp.node = node;
    sp.o = 0;
    sp.apply();
    knipsels.push(sp);
    if (!perBron.has(node.source)) perBron.set(node.source, []);
    perBron.get(node.source).push(sp);
  }
  const komst = [];
  for (const bron of trace.sources) {
    const groep = perBron.get(bron.source) || [];
    const vers = groep.filter(s => s.node.titled);
    const oud = groep.filter(s => !s.node.titled);
    const n = vers.length + oud.length;
    for (let i = 0, a = 0, b = 0; i < n; i++) {
      const neemOud = oud.length && (a >= vers.length ||
        (b / oud.length) <= (a / Math.max(1, vers.length)));
      komst.push(neemOud && b < oud.length ? oud[b++] : vers[a++]);
    }
  }
  for (const sp of komst) laag.appendChild(sp.el);

  const nieuwe = (cls, html, x, y) => {
    const d = document.createElement("div");
    d.className = "sp " + cls;
    if (html) d.innerHTML = html;
    laag.appendChild(d);
    const sp = new Sprite(d, x, y);
    sp.o = 0;
    sp.apply();
    return sp;
  };

  const dekking = (el, t, duur, van, naar) => {
    el.classList.remove("dof");
    el.style.opacity = van;
    eng.track(t, t + duur, p => { el.style.opacity = (van + (naar - van) * EASE.soft(p)).toFixed(3); });
  };

  const vertrek = (sp, t, duur, dx, dy, dr) => eng.at(t, () => {
    eng.tween(sp, { x: sp.x + dx, y: sp.y + dy, r: sp.r + dr, o: 0 }, t, duur, EASE.in,
      () => sp.el.remove());
  });

  function veeg(tA, tB, periode, breedte, x, yTop, yBot) {
    const lens = nieuwe("lens", "", x, yTop);
    lens.el.style.width = breedte + "px";
    lens.el.style.height = "76px";
    eng.track(tA, tB, (p, t) => {
      const q = ((t - tA) % periode) / periode;
      lens.set({ x, y: yTop + (yBot - yTop) * q, o: Math.min(1, (1 - Math.abs(2 * p - 1)) * 5) });
      lens.apply();
    });
    eng.at(tB, () => { lens.el.remove(); });
  }

  const nIn = komst.length;
  const komstEind = t0("fetch") + F.fetch.screen_ms * .82;

  komst.forEach((sp, i) => {
    const straal = Math.sqrt((i + .7) / nIn);
    const hoek = i * 2.3999632;
    const doel = {
      x: Math.cos(hoek) * straal * PILE_RX - CLIP_W / 2 + (R() - .5) * 12,
      y: Math.sin(hoek) * straal * PILE_RY + MID_Y - CLIP_H / 2 + (R() - .5) * 9,
      r: (R() - .5) * 9,
    };
    sp.rust = doel;
    const t = t0("fetch") + (i / nIn) * (komstEind - t0("fetch"));
    eng.at(t, () => {
      sp.set({ x: doel.x + (R() - .5) * 70, y: doel.y - 300 - R() * 200, r: (R() - .5) * 44, o: 1 });
      sp.apply();
      eng.tween(sp, doel, t, 1000 + R() * 500, EASE.out);
    });
  });

  for (let i = 0; i <= 10; i++) {
    const p = i / 10;
    const t = t0("fetch") + p * (komstEind - t0("fetch"));
    const straal = Math.max(.08, Math.sqrt(p));
    cam.key(t, {
      cx: 0, cy: MID_Y,
      vw: Math.max(190, kader(2 * straal * PILE_RX + CLIP_W + 30, 2 * straal * PILE_RY + CLIP_H + 30)),
    }, i === 0 ? EASE.lin : EASE.io);
  }

  const oudLijst = komst.filter(sp => !sp.node.titled);
  const oudStart = komstEind + 1200;
  oudLijst.forEach((sp, i) => {
    vertrek(sp, oudStart + (i / oudLijst.length) * 6200, 2000 + R() * 700,
      -420 - R() * 260, 220 + R() * 260, -40 - R() * 60);
  });

  const naF1 = komst.filter(sp => sp.node.titled);
  const f2Hoog = rasterHoog(naF1.length, RA_KOL, RA_DY);
  const hergroep = oudStart + 3400;
  naF1.forEach((sp, i) => {
    const p = raster(i, naF1.length, RA_KOL, RA_DX, RA_DY, 0, MID_Y);
    sp.rust = { x: p.x, y: p.y, r: (R() - .5) * 2.4 };
    eng.tween(sp, sp.rust, hergroep + (i / naF1.length) * 5200, 2600, EASE.io);
  });
  cam.key(hergroep + 3000, { cx: 0, cy: MID_Y, vw: kader(RA_KOL * RA_DX, f2Hoog) });
  cam.hold(t0("filter") + 16000);

  const dubbel = naF1.filter(sp => sp.node.exit && sp.node.exit.bin === "duplicate");
  const emmer = naF1.filter(sp => sp.node.exit && sp.node.exit.bin === "buckets");

  dubbel.forEach((sp, i) => {
    const tweeling = naF1.find(o => o !== sp && o.node.id === sp.node.id && !dubbel.includes(o));
    const t = t0("filter") + 16000 + i * 780;
    eng.at(t, () => {
      const doel = tweeling ? { x: tweeling.rust.x, y: tweeling.rust.y } : { x: sp.x, y: sp.y };
      sp.el.style.zIndex = 3;
      eng.tween(sp, { x: doel.x + 2.5, y: doel.y + 2.5, r: 0 }, t, 1500, EASE.io);
      eng.tween(sp, { o: 0, s: .96 }, t + 1500, 900, EASE.soft, () => {
        sp.el.remove();
        if (tweeling) tweeling.el.classList.add("dubbel");
      });
    });
  });

  emmer.forEach((sp, i) => {
    const t = t0("filter") + 21000 + i * 250;
    eng.at(t, () => {
      sp.el.style.zIndex = 4;
      eng.tween(sp, { y: sp.y - 5, s: 1.06 }, t, 260, EASE.out);
      eng.tween(sp, { x: sp.x + 520 + R() * 200, y: sp.y + 60 + R() * 120, r: sp.r + 50 + R() * 40, o: 0 },
        t + 420, 1500 + R() * 500, EASE.in, () => sp.el.remove());
    });
  });

  const naF2 = naF1.filter(sp => !sp.node.exit ||
    !["duplicate", "buckets"].includes(sp.node.exit.bin));
  const batches = [[], [], []];
  for (const sp of naF2) batches[sp.node.f3.batch].push(sp);
  const bHoog = batches.map(b => rasterHoog(b.length, RA_KOL, RA_DY));
  const totHoog = bHoog.reduce((a, b) => a + b, 0) + 48;
  let by = MID_Y - totHoog / 2;
  const batchTop = [];
  batches.forEach((b, bi) => {
    batchTop.push(by);
    b.forEach((sp, i) => {
      const p = raster(i, b.length, RA_KOL, RA_DX, RA_DY, 0, by + bHoog[bi] / 2);
      sp.rust = { x: p.x, y: p.y, r: (R() - .5) * 2 };
      const t = t0("score") - 8000 + (i / b.length) * 5000 + bi * 400;
      eng.tween(sp, sp.rust, t, 2400, EASE.io);
    });
    by += bHoog[bi] + 24;
  });
  cam.key(t0("score") - 2000, { cy: MID_Y, vw: kader(RA_KOL * RA_DX, f2Hoog * .96) });

  const scoreLand = landingen(F.score, .92);
  batches.forEach((b, bi) => {
    const tL = scoreLand[bi] ?? (t0("score") + F.score.screen_ms * .9);
    veeg(t0("score") + 2000 + bi * 900, tL, 9000 + bi * 1700, 400, -200,
      batchTop[bi] - 70, batchTop[bi] + bHoog[bi] + 10);
    let gedaan = 0;
    eng.track(tL, tL + 2600, p => {
      const tot = Math.floor(p * b.length);
      while (gedaan < tot) {
        const sp = b[gedaan++];
        const s = sp.node.f3.score;
        const c = document.createElement("span");
        c.className = "cijfer";
        c.textContent = s > 0 ? "+" + s : s < 0 ? "−" + Math.abs(s) : "0";
        c.style.setProperty("--stamp", s > 0 ? "#3f6d4e" : s < 0 ? "var(--schrap)" : "#8a7f70");
        sp.el.appendChild(c);
        if (s === 2) sp.el.classList.add("plus2");
        else if (s < 0) sp.el.classList.add(s === -1 ? "min1" : "min2");
      }
    });
    const weg = b.filter(sp => sp.node.exit && ["neutral", "negative"].includes(sp.node.exit.bin));
    weg.forEach((sp, i) => {
      vertrek(sp, tL + 2800 + i * 42, 2200 + R() * 800,
        (R() - .5) * 60, 300 + R() * 220, (R() - .5) * 26);
    });
  });

  const naF3 = naF2.filter(sp => !sp.node.exit ||
    !["neutral", "negative"].includes(sp.node.exit.bin));
  const f4Hoog = rasterHoog(naF3.length, RA_KOL, RA_DY);
  naF3.forEach((sp, i) => {
    const p = raster(i, naF3.length, RA_KOL, RA_DX, RA_DY, 0, MID_Y);
    sp.rust = { x: p.x, y: p.y, r: (R() - .5) * 2 };
    eng.tween(sp, sp.rust, t0("select") + 1500 + (i / naF3.length) * 6000, 2600, EASE.io);
  });
  cam.key(t0("select") + 9000, { cy: MID_Y, vw: kader(RA_KOL * RA_DX, f2Hoog * .86) });

  const kiesLand = landingen(F.select, .62)[0] ?? (t0("select") + F.select.screen_ms * .62);
  veeg(t0("select") + 10000, kiesLand, 11000, 400, -200, MID_Y - f4Hoog / 2 - 60, MID_Y + f4Hoog / 2 + 10);

  const onderwerpen = trace.onderwerpen;
  const nOnd = onderwerpen.length;
  const stapelHoog = rasterHoog(nOnd, ST_KOL, ST_DY, 84);
  const stapels = onderwerpen.map((ond, i) => {
    const p = raster(i, nOnd, ST_KOL, ST_DX, ST_DY, 0, MID_Y + 20, 84);
    const leden = ond.bron_ids
      .map(id => naF3.find(sp => sp.node.id === id && sp.node.f4 && sp.node.f4.onderwerp === ond.index))
      .filter(Boolean);
    return { ond, x: p.x, y: p.y, leden };
  });

  stapels.forEach((st, i) => {
    const t = kiesLand + 600 + i * 320;
    st.leden.forEach((sp, k) => {
      sp.el.style.zIndex = 5 + k;
      sp.rust = { x: st.x + k * 3.2, y: st.y + k * 3.2, r: k ? (k % 2 ? 3.4 : -3.4) : 0 };
      eng.tween(sp, sp.rust, t + k * 220, 2200, EASE.io);
    });
    const tag = nieuwe("tag", esc(st.ond.onderwerptitel), st.x, st.y + 26);
    tag.el.style.setProperty("--sc", `var(--${st.ond.scope})`);
    st.tag = tag;
    eng.tween(tag, { o: 1 }, t + 900, 900, EASE.soft);
  });

  const nietGekozen = naF3.filter(sp => sp.node.exit && sp.node.exit.bin === "not_selected");
  nietGekozen.forEach((sp, i) => {
    const kant = sp.rust.x < 0 ? -1 : 1;
    vertrek(sp, kiesLand + 900 + i * 60, 2400 + R() * 900,
      kant * (360 + R() * 180), 80 + R() * 200, kant * 30);
  });

  cam.key(kiesLand + 5000, { cy: MID_Y + 20, vw: kader(ST_KOL * ST_DX, stapelHoog + 60) });

  const velLand = landingen(F.enrich, .92);
  stapels.forEach((st, i) => {
    const tL = velLand[Math.min(i, velLand.length - 1)];
    const primair = st.leden[0];
    const tekst = primair && primair.node.f5 ? primair.node.f5.bron_tekst : "";
    const schoon = tekst.replace(/\[[^\]]*\]\([^)]*\)/g, m => m.slice(1, m.indexOf("]")))
      .replace(/\s+/g, " ").trim();
    const woorden = schoon.split(" ").slice(0, 150);
    const vel = nieuwe("vel", woorden.map(w => `<span>${esc(w)}</span>`).join(" "),
      st.x + 3, st.y + 40);
    vel.el.style.height = "42px";
    st.vel = vel;
    const spans = [...vel.el.children];
    eng.tween(vel, { o: 1 }, tL - 900, 700, EASE.soft);
    eng.at(tL - 900, () => { vel.set({ x: st.x + 3, y: st.y + 34 }); vel.apply(); eng.tween(vel, { y: st.y + 40 }, tL - 900, 900, EASE.out); });
    let n = 0;
    eng.track(tL, tL + 3200, p => {
      const tot = Math.floor(EASE.soft(p) * spans.length);
      while (n < tot) spans[n++].classList.add("op");
    });
  });

  const f5Mid = t0("enrich") + F.enrich.screen_ms * .45;
  cam.key(f5Mid, { cx: -40, cy: MID_Y - 60, vw: 250 });
  cam.key(t0("enrich") + F.enrich.screen_ms * .93, { cx: 30, cy: MID_Y + 140, vw: 300 });

  const opmaakLand = landingen(F.outline, .75)[0] ?? (t0("outline") + F.outline.screen_ms * .75);
  cam.key(t0("outline") + 26000, { cx: 0, cy: 300, vw: 600 });

  for (const p of krant.pages) dekking(p.el, t0("outline") + 12000, 9000, 0, 1);
  dekking(krant.mast, t0("outline") + 20000, 7000, 0, 1);

  veeg(t0("outline") + 30000, opmaakLand, 21000, 420, -210,
    MID_Y + 20 - stapelHoog / 2 - 70, MID_Y + 20 + stapelHoog / 2 + 30);

  const perPos = new Map();
  for (const st of stapels) if (st.ond.pos) perPos.set(st.ond.pos, st);

  const blokTijd = new Map();
  [...krant.artikelen.values()].sort((a, b) => a.pos - b.pos).forEach((art, i) => {
    const st = perPos.get(art.pos);
    const t = opmaakLand + 1500 + i * 1700;
    blokTijd.set(art.pos, t);
    const pg = krant.pages[art.pagina];
    const dx = pg.x + art.titelKader.x;
    const dy = BORD_Y + pg.y + art.titelKader.y;
    if (st) {
      st.leden.forEach((sp, k) => {
        sp.el.style.zIndex = 20 + k;
        eng.tween(sp, { x: dx + 6 + k * 3, y: dy + 14 + k * 3, r: (k % 2 ? 2.5 : -2.5), s: .8 },
          t, 3600, EASE.io);
      });
      eng.tween(st.tag, { x: dx + 6, y: dy - 16, s: .8 }, t, 3600, EASE.io);
      eng.tween(st.tag, { o: 0 }, t + 3400, 1200, EASE.soft);
      if (st.vel) eng.tween(st.vel, { x: dx + 8, y: dy + 30, s: .7 }, t, 3600, EASE.io);
      if (st.vel) eng.tween(st.vel, { o: 0 }, t + 3600, 1400, EASE.soft);
    }
    dekking(art.el, t + 2600, 1400, 0, 1);
    art.brief = nieuwe("brief",
      `<b>${esc(art.slot.f6.lengterichtlijn)}</b>${esc(art.slot.f6.invalshoek)}`,
      pg.x + art.kader.x + 2, BORD_Y + pg.y + art.kader.y + 16);
    art.brief.el.style.setProperty("--sc", `var(--${art.slot.scope})`);
    art.brief.set({ r: -1.6 });
    eng.tween(art.brief, { o: 1 }, t + 3000, 1200, EASE.soft);
  });

  for (const blok of krant.el.querySelectorAll(".flow > .kicker, .flow > .sep")) {
    blok.classList.add("dof");
  }
  {
    const beurt = [...krant.artikelen.values()].sort((a, b) => a.pos - b.pos);
    for (const art of beurt) {
      let vorige = art.el.previousElementSibling;
      while (vorige && (vorige.classList.contains("kicker") || vorige.classList.contains("sep") ||
        vorige.classList.contains("illo"))) {
        if (!vorige.classList.contains("illo")) {
          dekking(vorige, blokTijd.get(art.pos) + 2400, 1400, 0, 1);
        }
        vorige = vorige.previousElementSibling;
      }
    }
  }

  const nietGeplaatst = stapels.filter(st => !st.ond.pos);
  nietGeplaatst.forEach((st, i) => {
    const t = opmaakLand + 1200 + i * 240;
    for (const sp of st.leden) {
      vertrek(sp, t, 2600 + R() * 900, (R() - .5) * 120, -420 - R() * 200, (R() - .5) * 30);
    }
    eng.tween(st.tag, { y: st.tag.y - 420, o: 0 }, t, 2600, EASE.in);
    if (st.vel) eng.tween(st.vel, { y: st.vel.y - 440, o: 0 }, t, 2600, EASE.in);
  });

  const bordFit = kader(krant.breedte, krant.hoogte);
  cam.key(opmaakLand + 2000, { cx: 0, cy: 420, vw: 620 });
  cam.key(opmaakLand + 16000, { cx: 0, cy: BORD_Y + krant.hoogte / 2, vw: bordFit });
  cam.hold(eind("outline"));

  const schrijfLand = landingen(F.write, .92);
  const artLijst = [...krant.artikelen.values()].sort((a, b) => a.pos - b.pos);
  artLijst.forEach((art, i) => {
    const pg = krant.pages[art.pagina];
    const ox = pg.x, oy = BORD_Y + pg.y;
    const tA = t0("write") + 1200 + i * 700;
    const tB = schrijfLand[Math.min(i, schrijfLand.length - 1)];
    const woorden = art.woorden;
    const plekken = art.plekken;
    const caret = nieuwe("caret", "", ox, oy);
    caret.el.style.height = (plekken[0] ? plekken[0].h : 5) + "px";
    let n = 0;
    eng.at(tA, () => {
      if (art.brief) eng.tween(art.brief, { o: 0, s: .9 }, tA, 1600, EASE.soft);
      caret.set({ o: 1 });
      caret.apply();
    });
    eng.track(tA, tB, (p, t) => {
      const tot = Math.floor(p * woorden.length);
      while (n < tot) {
        if (!woorden[n].classList.contains("nieuw")) woorden[n].classList.add("op");
        n++;
      }
      const k = Math.min(woorden.length - 1, Math.max(0, tot));
      const pl = plekken[k];
      if (pl) {
        caret.set({ x: ox + pl.x + pl.w, y: oy + pl.y, o: (Math.floor(t / 320) % 2) ? .25 : 1 });
        caret.apply();
      }
    });
    eng.at(tB, () => {
      while (n < woorden.length) {
        if (!woorden[n].classList.contains("nieuw")) woorden[n].classList.add("op");
        n++;
      }
      caret.set({ o: 0 });
      caret.apply();
    });
    const st = perPos.get(art.pos);
    if (st) {
      eng.at(tA + 1400, () => {
        for (const sp of st.leden) {
          eng.tween(sp, { o: 0, s: .55, y: sp.y + 7 }, tA + 1400, 3200, EASE.soft);
        }
      });
    }
  });

  const vwPagina = Math.max(PAGE_W + 8, (PAGE_H + 16) / aspect);
  const paden = krant.pages.map(pg =>
    ({ cx: pg.x + PAGE_W / 2, cy: BORD_Y + pg.y + PAGE_H / 2, vw: vwPagina }));
  const bezoek = [0, .3, .54, .76];
  cam.key(t0("write") + 4000, paden[0]);
  bezoek.forEach((f, i) => {
    if (!i) return;
    cam.key(t0("write") + 5000 + f * (F.write.screen_ms - 8000), paden[i], EASE.io);
  });
  cam.hold(eind("write"));

  const leesLand = landingen(F.review, .92);
  artLijst.forEach((art, i) => {
    const pg = krant.pages[art.pagina];
    const ox = pg.x, oy = BORD_Y + pg.y;
    const tA = t0("review") + 1000 + i * 900;
    const tB = leesLand[Math.min(i, leesLand.length - 1)];
    const streep = nieuwe("streepje", "", ox, oy);
    let n = 0;
    const wacht = [];
    eng.at(tA, () => { streep.set({ o: 1 }); streep.apply(); });
    eng.track(tA, tB, (p, t) => {
      const tot = Math.floor(p * art.woorden.length);
      while (n < tot) {
        const w = art.woorden[n];
        if (w.classList.contains("nieuw")) {
          w.classList.add("op", "vers");
          wacht.push([w, t + 2600]);
        }
        n++;
      }
      while (wacht.length && wacht[0][1] <= t) wacht.shift()[0].classList.remove("vers");
      const pl = art.plekken[Math.min(art.woorden.length - 1, tot)];
      if (pl) {
        streep.el.style.width = Math.max(14, pl.w * 3) + "px";
        streep.set({ x: ox + pl.x, y: oy + pl.y + pl.h - .6 });
        streep.apply();
      }
    });
    eng.at(tB, () => {
      while (n < art.woorden.length) {
        const w = art.woorden[n++];
        if (w.classList.contains("nieuw")) w.classList.add("op");
      }
      for (const [w] of wacht) w.classList.remove("vers");
      streep.set({ o: 0 });
      streep.apply();
    });
    const tK = tB + 400;
    dekking(art.werk, tK, 700, 1, 0);
    eng.at(tK, () => { art.def.classList.remove("dof"); art.def.style.opacity = 1; });
    art.kopWoorden.forEach((w, k) => {
      eng.at(tK + 300 + k * 130, () => w.classList.add("op"));
    });
  });

  cam.key(t0("review") + 3000, paden[3]);
  for (let i = 2; i >= 0; i--) {
    cam.key(t0("review") + 4000 + (3 - i) / 3 * (F.review.screen_ms - 9000), paden[i], EASE.io);
  }

  const tC = t0("compose");
  let ill = 0;
  for (const art of artLijst) {
    if (!art.illo) continue;
    const tI = tC + 3000 + ill * 6000;
    cam.key(tI - 1800, paden[art.pagina]);
    eng.track(tI, tI + 5200, p => {
      art.illo.style.clipPath = `inset(0 0 ${(100 - 100 * EASE.soft(p)).toFixed(1)}% 0)`;
    });
    ill++;
  }

  const tWeer = tC + 17000;
  cam.key(tWeer - 2000, paden[0]);
  dekking(krant.weer, tWeer, 3600, 0, 1);
  const tLand = tC + 25000;
  cam.key(tLand - 2000, paden[3]);
  dekking(krant.landschap, tLand, 3400, 0, 1);

  eng.at(tC + 31000, () => { for (const p of krant.pages) p.el.classList.add("af"); });
  cam.key(tC + 30000, { cx: 0, cy: BORD_Y + krant.hoogte / 2, vw: bordFit * .96 }, EASE.io);
  cam.key(eind("compose") - 1500, { cx: 0, cy: BORD_Y + krant.hoogte / 2, vw: bordFit }, EASE.io);
  cam.hold(eind("compose") + 4000);

  eng.seal();
  return { krant, knipsels };
}

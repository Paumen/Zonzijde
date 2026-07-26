const MAANDEN = ["januari", "februari", "maart", "april", "mei", "juni",
  "juli", "augustus", "september", "oktober", "november", "december"];
const KORT = ["jan", "feb", "mrt", "apr", "mei", "jun",
  "jul", "aug", "sep", "okt", "nov", "dec"];
const DAGEN = ["zondag", "maandag", "dinsdag", "woensdag", "donderdag",
  "vrijdag", "zaterdag"];
const SCOPE_KOP = { L: "Lokaal", R: "Regionaal", N: "Nationaal", I: "Wereld" };

export const PAGE_W = 300;
export const PAGE_H = 424;
const MARGE = 11;
const GAP = 26;

function el(tag, cls, parent) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (parent) parent.appendChild(n);
  return n;
}

function langDatum(iso) {
  const d = new Date(iso + "T12:00:00");
  return `${DAGEN[d.getDay()]} ${d.getDate()} ${MAANDEN[d.getMonth()]} ${d.getFullYear()}`;
}

function kortDatum(iso) {
  const [, m, d] = iso.split("-").map(Number);
  return `${d} ${KORT[m - 1]}`;
}

function weerIcoon(code) {
  const zon = '<circle cx="12" cy="12" r="4"/><path d="M12 3.2v2.2M12 18.6v2.2M3.2 12h2.2M18.6 12h2.2M5.8 5.8l1.5 1.5M16.7 16.7l1.5 1.5M18.2 5.8l-1.5 1.5M7.3 16.7l-1.5 1.5"/>';
  const wolk = '<path d="M7 16.5a3.3 3.3 0 0 1 .3-6.6 4.6 4.6 0 0 1 9-.1 3.4 3.4 0 0 1 .3 6.7z"/>';
  const wolkje = '<path d="M9 14.5a2.9 2.9 0 0 1 .3-5.8 4 4 0 0 1 7.8-.1 3 3 0 0 1 .3 5.9z"/>';
  const zonnetje = '<circle cx="7.4" cy="7.4" r="2.6"/><path d="M7.4 2v1.5M2 7.4h1.5M3.6 3.6l1 1M11.2 3.6l-1 1M3.6 11.2l1-1"/>';
  let s;
  if (code <= 1) s = zon;
  else if (code === 2) s = zonnetje + '<path d="M11 19a3 3 0 0 1 .3-6 4.1 4.1 0 0 1 8-.1 3.1 3.1 0 0 1 .3 6.1z"/>';
  else if (code === 3) s = wolk;
  else if (code === 45 || code === 48) s = wolkje + '<path d="M5.5 17.5h13M7.5 20.2h9"/>';
  else if (code < 60) s = wolkje + '<path d="M9.5 17.2l-.7 2.2M14 17.2l-.7 2.2"/>';
  else if (code < 70 || (code >= 80 && code <= 82)) s = wolkje + '<path d="M8.2 17l-.9 3M11.9 17l-.9 3M15.6 17l-.9 3"/>';
  else if (code < 90) s = wolkje + '<circle cx="8.4" cy="18.3" r=".5"/><circle cx="12" cy="19.5" r=".5"/><circle cx="15.6" cy="18.3" r=".5"/>';
  else s = wolkje + '<path d="M12.6 15.5l-2.2 3.4h3l-2.2 3.4"/>';
  return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#121212" ' +
    'stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round">' + s + '</svg>';
}

function lcs(a, b) {
  const n = a.length, m = b.length;
  const dp = [new Uint16Array(m + 1)];
  for (let i = 1; i <= n; i++) {
    const vorige = dp[i - 1], rij = new Uint16Array(m + 1);
    for (let j = 1; j <= m; j++) {
      rij[j] = a[i - 1] === b[j - 1]
        ? vorige[j - 1] + 1
        : (rij[j - 1] >= vorige[j] ? rij[j - 1] : vorige[j]);
    }
    dp.push(rij);
  }
  const gedeeld = new Set();
  let i = n, j = m;
  while (i > 0 && j > 0) {
    if (a[i - 1] === b[j - 1] && dp[i][j] === dp[i - 1][j - 1] + 1) {
      gedeeld.add(j - 1);
      i--; j--;
    } else if (dp[i - 1][j] >= dp[i][j - 1]) {
      i--;
    } else {
      j--;
    }
  }
  return gedeeld;
}

function tekstBlok(houder, concept, definitief) {
  const dw = concept.trim().replace(/\n\n/g, " ¶ ").split(/\s+/);
  const fw = definitief.trim().replace(/\n\n/g, " ¶ ").split(/\s+/);
  const gedeeld = lcs(dw.map(w => w.toLowerCase()), fw.map(w => w.toLowerCase()));
  const spans = [];
  let k = 0;
  for (const alinea of definitief.trim().split("\n\n")) {
    const p = el("p", null, houder);
    const woorden = alinea.trim().split(/\s+/);
    woorden.forEach((w, i) => {
      const s = el("span", "w", p);
      s.textContent = i === woorden.length - 1 ? w : w + " ";
      while (fw[k] === "¶") k++;
      if (!gedeeld.has(k)) s.classList.add("nieuw");
      k++;
      spans.push(s);
    });
  }
  return spans;
}

export function bouwKrant(trace, host) {
  const meta = trace.meta;
  const slots = [...trace.slots].sort((a, b) => a.pos - b.pos);
  const krant = el("div", "krant", host);
  const binnen = PAGE_H - 2 * MARGE;
  const pages = [];
  for (let i = 0; i < 4; i++) {
    const p = el("div", "page", krant);
    const x = i % 2 ? GAP / 2 : -PAGE_W - GAP / 2;
    const y = i < 2 ? 0 : PAGE_H + GAP;
    p.style.cssText = `width:${PAGE_W}px;height:${PAGE_H}px;left:${x}px;top:${y}px`;
    pages.push({ el: p, inner: el("div", "page-in", p), flow: null, x, y });
  }

  const mast = el("div", "mast", pages[0].inner);
  el("div", "rule1", mast);
  const regel = el("div", "regel", mast);
  el("span", null, regel).textContent = langDatum(meta.edition);
  el("span", null, regel).textContent = "Nr. " + meta.nr;
  el("div", "rule2", mast);
  const kop = el("div", "kop", mast);
  const zon = el("img", null, kop);
  zon.src = "assets/art/zonnebloem.svg";
  zon.alt = "";
  el("b", null, kop).textContent = "De Zonzijde";
  el("div", "rule3", mast);

  const weer = el("div", "weer", pages[0].inner);
  const wk = el("div", "kicker", weer);
  el("b", null, wk).textContent = "Weer";
  const wsub = el("em", null, wk);
  wsub.textContent =
    `${meta.weather.place} — vandaag en de komende ${meta.weather.days.length - 1} dagen`;
  el("i", null, wk);
  const dagen = el("div", "dagen", weer);
  for (const d of meta.weather.days) {
    const dg = el("div", "dag" + (d.label === "Vandaag" ? " vandaag" : ""), dagen);
    el("em", null, dg).textContent = d.label;
    el("div", "ic", dg).innerHTML = weerIcoon(d.code);
    const t = el("div", "t", dg);
    t.textContent = Math.round(d.tmax) + "°";
    el("s", null, t).textContent = " " + Math.round(d.tmin) + "°";
    el("div", "n", dg).textContent = d.precip_prob === null ? "—" : d.precip_prob + "%";
  }
  el("div", "bron", weer).textContent =
    "Max./min. temperatuur · neerslagkans · bron " + meta.weather.source;

  const artikelen = new Map();

  function bouwArtikel(slot, hero) {
    const art = el("div", "art" + (hero ? " hero" : ""));
    const titel = el("div", "titel", art);
    const werk = el("div", "werk", titel);
    werk.textContent = slot.onderwerptitel;
    const def = el("div", "def dof", titel);
    const kopWoorden = slot.f8.artikelkop.split(/\s+/).map((w, i, a) => {
      const s = el("span", null, def);
      s.textContent = i === a.length - 1 ? w : w + " ";
      return s;
    });
    const metaRegel = el("div", "meta", art);
    metaRegel.textContent = slot.f6.locatie + " · " + kortDatum(slot.f6.bron_datum);
    const houder = hero ? el("div", "kolommen", art) : art;
    const tekst = el("div", "tekst", houder);
    const woorden = tekstBlok(tekst, slot.f7.artikellichaam, slot.f8.artikellichaam);
    if (hero) el("div", "streep", art);
    artikelen.set(slot.pos, {
      pos: slot.pos, slot, el: art, titel, werk, def, kopWoorden,
      metaRegel, woorden, hero: !!hero, illo: null,
    });
    return art;
  }

  const blokken = [{ el: bouwArtikel(slots[0], true), pos: slots[0].pos }];
  let vorige = null;
  for (const slot of slots.slice(1)) {
    if (slot.scope !== vorige) {
      const k = el("div", "kicker");
      el("b", null, k).textContent = SCOPE_KOP[slot.scope];
      el("i", null, k);
      blokken.push({ el: k });
      vorige = slot.scope;
    } else {
      blokken.push({ el: el("div", "sep") });
    }
    if (slot.f9.illustratie) {
      const box = el("div", "illo onthul");
      box.innerHTML = slot.f9.illustratie.svg;
      blokken.push({ el: box, illo: slot.pos });
    }
    blokken.push({ el: bouwArtikel(slot, false), pos: slot.pos });
  }
  const landschap = el("img", "landschap", pages[3].inner);
  landschap.src = "assets/art/landschap.svg";
  landschap.alt = "";

  const past = p => p.flow.scrollWidth <= p.flow.clientWidth + 1;

  function verdeel() {
    for (const p of pages) {
      if (p.flow) p.flow.remove();
      p.flow = el("div", "flow", p.inner);
    }
    const top1 = mast.offsetHeight + 4;
    const weerH = weer.offsetHeight;
    const landH = landschap.offsetHeight;
    pages[0].flow.style.cssText = `top:${top1}px;height:${binnen - top1 - weerH - 5}px`;
    for (const p of pages.slice(1, 3)) p.flow.style.cssText = `top:0;height:${binnen}px`;
    pages[3].flow.style.cssText = `top:0;height:${binnen - landH - 5}px`;
    let i = 0;
    for (const blok of blokken) {
      let ok = false;
      while (i < 4) {
        pages[i].flow.appendChild(blok.el);
        if (past(pages[i])) {
          ok = true;
          break;
        }
        blok.el.remove();
        i++;
      }
      if (!ok) return null;
    }
    for (let n = 0; n < 12; n++) {
      let gesleept = false;
      for (let k = 0; k < 3; k++) {
        const f = pages[k].flow;
        const laatste = f.lastElementChild;
        if (!laatste) continue;
        const los = laatste.classList.contains("kicker") || laatste.classList.contains("sep");
        if (past(pages[k]) && !los) continue;
        pages[k + 1].flow.prepend(laatste);
        gesleept = true;
      }
      if (!gesleept) break;
    }
    if (!pages.every(past) || !pages[3].flow.children.length) return null;
    for (const p of pages) {
      const eerste = p.flow.firstElementChild;
      if (eerste && eerste.classList.contains("sep")) eerste.remove();
    }
    for (const blok of blokken) {
      blok.pagina = pages.findIndex(p => p.flow.contains(blok.el));
    }
    let leeg = 0;
    for (const p of pages) {
      const h = p.flow.clientHeight;
      const stap = (p.flow.clientWidth + 6) / 3;
      let bereikt = 0;
      for (const k of p.flow.children) {
        let j = Math.round(k.offsetLeft / stap);
        let eind = k.offsetTop + k.offsetHeight;
        while (eind > h && j < 2) {
          eind -= h;
          j++;
        }
        if (j > bereikt) bereikt = j;
      }
      leeg += 2 - bereikt;
    }
    return leeg;
  }

  let basis = 0, beste = Infinity, ondergrens = 8;
  for (let maat = 13; maat > ondergrens; maat -= .2) {
    document.documentElement.style.fontSize = maat + "px";
    const leeg = verdeel();
    if (leeg === null) continue;
    if (!basis) ondergrens = maat * .93;
    if (leeg < beste) {
      beste = leeg;
      basis = maat;
    }
  }
  if (!basis) basis = 9;
  document.documentElement.style.fontSize = basis + "px";
  verdeel();

  const eenheid = pages[0].el.getBoundingClientRect().width / PAGE_W;
  function kader(node, pagina) {
    const r = node.getBoundingClientRect();
    const pr = pages[pagina].el.getBoundingClientRect();
    return {
      x: (r.left - pr.left) / eenheid, y: (r.top - pr.top) / eenheid,
      w: r.width / eenheid, h: r.height / eenheid,
    };
  }

  for (const blok of blokken) {
    if (blok.pagina < 0) continue;
    if (blok.pos !== undefined) {
      const a = artikelen.get(blok.pos);
      a.pagina = blok.pagina;
      a.kader = kader(a.el, blok.pagina);
      a.titelKader = kader(a.titel, blok.pagina);
      a.plekken = a.woorden.map(w => kader(w, blok.pagina));
    }
    if (blok.illo !== undefined) {
      const a = artikelen.get(blok.illo);
      a.illo = blok.el;
      a.illoKader = kader(blok.el, blok.pagina);
    }
  }

  weer.classList.add("dof");
  landschap.classList.add("dof");
  mast.classList.add("dof");
  for (const p of pages) p.el.classList.add("dof");

  return {
    el: krant, pages, artikelen, weer, landschap, mast, basis,
    breedte: PAGE_W * 2 + GAP, hoogte: PAGE_H * 2 + GAP,
    links: -PAGE_W - GAP / 2, boven: 0,
  };
}

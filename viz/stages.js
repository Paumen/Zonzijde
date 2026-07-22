import { SCOPES } from "./data.js";
import { moveTo, flyOut, sleep, D, settle, placeAt, engine } from "./engine.js";
import { el } from "./view.js";

const CELL = {
  dot: { w: 9, h: 9 },
  chip: { w: 13, h: 13 },
  card: { w: 104, h: 30 },
  cardL: { w: 120, h: 42 },
};

const MINREAL = {
  F1: 26000, F2: 16000, F3: 205045, F4: 75075, F5: 354830,
  F6: 89148, F7: 220000, F8: 200000, F9: 42000,
};

const sleepR = (ms) => sleep(D(ms));

export class Stages {
  constructor(model, view, paper) {
    this.m = model;
    this.v = view;
    this.p = paper;
  }

  budget(fid) {
    const f = this.m.fase[fid];
    return Math.max(f.real_ms || 0, MINREAL[fid] || 20000);
  }

  cohort(nodes) {
    const g = { L: [], R: [], N: [], I: [] };
    for (const n of nodes) g[this.m.scopeOf(n)].push(n);
    return g;
  }

  placeGrid(scope, nodes, cell, dur, delayStep = 3) {
    const a = this.v.laneArea(scope);
    const gap = cell.w > 20 ? 6 : 3;
    const cols = Math.max(1, Math.floor((a.x1 - a.x0 + gap) / (cell.w + gap)));
    nodes.forEach((n, k) => {
      const c = k % cols, r = Math.floor(k / cols);
      moveTo(n, a.x0 + c * (cell.w + gap), a.y0 + r * (cell.h + gap),
        { w: cell.w, h: cell.h, dur, delay: k * delayStep });
    });
  }

  repack(nodes, cell, dur = 650) {
    const g = this.cohort(nodes);
    for (const s of SCOPES) this.placeGrid(s, g[s], cell, dur);
  }

  drop(node, delay = 0) {
    const c = this.v.binCenter(node.exit_bin);
    this.v.bump(node.exit_bin);
    return flyOut(node, c.x, c.y, { dur: 650, delay });
  }

  spawnHaze(src) {
    const scope = SCOPES.includes(src.scopes[0]) ? src.scopes[0] : "N";
    const a = this.v.laneArea(scope);
    const div = el("div", "it haze", this.v.itemsEl);
    const node = { el: div };
    placeAt(node, 4, a.y0 + Math.random() * (a.y1 - a.y0), 6, 6);
    const c = this.v.binCenter("too_old");
    flyOut(node, c.x + (Math.random() * 16 - 8), c.y + (Math.random() * 10 - 5),
      { dur: 900, delay: Math.random() * 500 });
  }

  async run() {
    this.v.measure();
    await this.intake();
    await this.filter();
    await this.score();
    await this.select();
    await this.enrich();
    await this.outline();
    await this.produce();
    this.v.dimLanes(false);
    this.v.llmOff();
    this.v.chip("F9", "done");
    this.v.caption(
      `Klaar — editie nr. ${this.m.trace.meta.nr}: ` +
      `${this.m.trace.meta.counts.articles} artikelen, ` +
      `${this.m.trace.meta.counts.words_body} woorden, ` +
      `${this.m.trace.meta.counts.pages} pagina's. ` +
      `Uit ${this.m.trace.meta.counts.entries} ruwe berichten.`);
  }

  markActive(fid, caption) {
    for (const f of this.m.trace.fases) {
      const st = this.v.chips[f.id].dataset.state;
      if (st === "active") this.v.chip(f.id, "done");
    }
    this.v.chip(fid, "active");
    this.v.dimLanes(true);
    if (caption) this.v.caption(caption);
  }

  async intake() {
    this.markActive("F1", "F1 · Bronnen — de RSS-stroom komt binnen; te oude berichten vallen meteen af.");
    this.v.dimLanes(false);
    const present = this.m.present("F1");
    const byFeed = new Map();
    for (const n of present) {
      if (!byFeed.has(n.feed)) byFeed.set(n.feed, []);
      byFeed.get(n.feed).push(n);
    }
    const srcs = this.m.trace.sources;
    const per = this.budget("F1") / Math.max(1, srcs.length);
    const shown = { L: [], R: [], N: [], I: [] };
    let count = 0;
    for (const src of srcs) {
      const nodes = byFeed.get(src.source) || [];
      for (const n of nodes) {
        this.v.makeCard(n);
        const s = this.m.scopeOf(n);
        const a = this.v.laneArea(s);
        placeAt(n, -18, a.y0 + Math.random() * (a.y1 - a.y0), 9, 9);
        shown[s].push(n);
        count++;
      }
      for (let i = 0; i < src.out_of_window; i++) this.spawnHaze(src);
      if (src.out_of_window) this.v.bump("too_old", src.out_of_window);
      for (const s of SCOPES) this.placeGrid(s, shown[s], CELL.dot, 550, 1);
      this.v.chipProgress("F1", count / present.length);
      await sleepR(per);
    }
    await settle();
    await sleepR(1200);
  }

  async filter() {
    this.markActive("F2", "F2 · Correspondenten — dubbelingen en negatief/promo eruit.");
    const drops = this.m.dropsAt("F2");
    const dup = drops.filter((n) => n.exit_bin === "duplicate");
    const neg = drops.filter((n) => n.exit_bin === "negative_filter");
    const budget = this.budget("F2");
    let i = 0;
    for (const n of dup) this.drop(n, (i++ % 12) * 30);
    this.v.chipProgress("F2", 0.4);
    await sleepR(budget * 0.4);
    i = 0;
    for (const n of neg) this.drop(n, (i++ % 20) * 22);
    this.v.chipProgress("F2", 0.8);
    await sleepR(budget * 0.4);
    this.repack(this.m.present("F3"), CELL.chip);
    this.v.chipProgress("F2", 1);
    await settle();
    await sleepR(900);
  }

  async score() {
    this.markActive("F3", "F3 · Analisten — een model leest elk bericht en scoort de richting (−2…+2), in batches.");
    const f = this.m.fase["F3"];
    const present = this.m.present("F3");
    this.v.llm("Analisten · " + (f.model || "model"), "batch 1/" + f.batches.length, f.batches.length);
    const budget = this.budget("F3");
    const per = budget / f.batches.length;
    const survivors = [];
    for (let k = 0; k < f.batches.length; k++) {
      this.v.llmNote(`batch ${k + 1}/${f.batches.length} · ${f.batches[k]} berichten`);
      const batch = present.filter((n) => n.batch === k);
      for (const n of batch) n.el.classList.add("batch-lit");
      const fills = 6;
      for (let s = 1; s <= fills; s++) {
        this.v.llmBar(k, s / fills);
        await sleepR(per * 0.65 / fills);
      }
      this.v.llmBar(k, 1, true);
      for (const n of batch) {
        n.el.classList.remove("batch-lit");
        this.v.setScore(n, n.score);
      }
      const drops = batch.filter((n) => n.exit_fase === "F3");
      let i = 0;
      for (const n of drops) this.drop(n, (i++ % 14) * 22);
      for (const n of batch) if (n.exit_fase !== "F3") survivors.push(n);
      this.repack(survivors, CELL.chip, 550);
      this.v.chipProgress("F3", (k + 1) / f.batches.length);
      await sleepR(per * 0.35);
    }
    await settle();
    await sleepR(900);
  }

  async select() {
    this.markActive("F4", "F4 · Sectieredacteuren — kies per ring de kansrijke onderwerpen; de rest valt af.");
    const f = this.m.fase["F4"];
    this.v.llm("Sectieredacteuren · " + (f.model || "model"), `${f.topics} onderwerpen`, 1);
    const budget = this.budget("F4");
    const fills = 8;
    for (let s = 1; s <= fills; s++) {
      this.v.llmBar(0, s / fills);
      this.v.chipProgress("F4", s / fills * 0.6);
      await sleepR(budget * 0.55 / fills);
    }
    this.v.llmBar(0, 1, true);
    const drops = this.m.dropsAt("F4");
    let i = 0;
    for (const n of drops) this.drop(n, (i++ % 16) * 20);
    await sleepR(budget * 0.2);
    const selected = this.m.present("F5");
    for (const n of selected) {
      this.v.setRich(n, n.topic || n.title, n.score >= 2 ? "+2" : "+" + n.score);
    }
    this.repack(selected, CELL.card, 750);
    this.v.chipProgress("F4", 1);
    await settle();
    await sleepR(1100);
  }

  async enrich() {
    this.markActive("F5", "F5 · Onderzoeksjournalisten — haal de volledige brontekst op; wat leeg blijft, valt af.");
    const f = this.m.fase["F5"];
    const nCalls = f.calls || 12;
    this.v.llm("Onderzoeksjournalisten · " + (f.model || "model"), `bron 0/${nCalls}`, Math.min(nCalls, 12));
    const budget = this.budget("F5");
    const present = this.m.present("F5");
    const drops = this.m.dropsAt("F5");
    const per = budget / nCalls;
    for (let k = 0; k < nCalls; k++) {
      this.v.llmNote(`bron ${k + 1}/${nCalls}`);
      this.v.llmBar(k % 12, ((k % 12) + 1) / 12);
      await sleepR(per * 0.7);
      this.v.chipProgress("F5", (k + 1) / nCalls);
    }
    for (const n of present) {
      if (n.words != null) this.v.setRich(n, n.topic || n.title, n.words + "w");
    }
    let i = 0;
    for (const n of drops) this.drop(n, (i++ % 8) * 40);
    this.repack(this.m.present("F6"), CELL.card, 700);
    await settle();
    await sleepR(1000);
  }

  async outline() {
    this.markActive("F6", "F6 · Hoofdredacteur — stel de editie samen: kies de verhalen, plaats ze per ring.");
    const f = this.m.fase["F6"];
    this.v.llm("Hoofdredacteur · " + (f.model || "model"), `${f.slots} plekken`, 1);
    const budget = this.budget("F6");
    const fills = 8;
    for (let s = 1; s <= fills; s++) {
      this.v.llmBar(0, s / fills);
      this.v.chipProgress("F6", s / fills * 0.6);
      await sleepR(budget * 0.5 / fills);
    }
    this.v.llmBar(0, 1, true);
    const drops = this.m.dropsAt("F6");
    let i = 0;
    for (const n of drops) this.drop(n, (i++ % 10) * 26);
    await sleepR(budget * 0.2);
    this.p.live();
    const picked = this.m.survivors();
    const bySlot = new Map();
    for (const n of picked) {
      if (!bySlot.has(n.slot)) bySlot.set(n.slot, []);
      bySlot.get(n.slot).push(n);
    }
    const slots = [...bySlot.keys()].sort((x, y) => x - y);
    const dockX = this.v.W - 30;
    slots.forEach((pos, si) => {
      this.p.werktitel(pos);
      const group = bySlot.get(pos);
      group.forEach((n, gi) => {
        const y = 24 + si * ((this.v.H - 40) / Math.max(1, slots.length)) + gi * 8;
        moveTo(n, dockX, y, { w: 16, h: 6, dur: 800, delay: si * 60 });
        n.el.classList.remove("rich");
      });
    });
    this.v.chipProgress("F6", 1);
    await settle();
    await sleepR(1200);
  }

  async produce() {
    const slots = this.m.slots.map((s) => s.pos).sort((a, b) => a - b);

    this.markActive("F7", "F7 · Reporters — schrijf de artikelen; de tekst verschijnt op de pagina.");
    const f7 = this.m.fase["F7"];
    this.v.llm("Reporters · " + (f7.model || "model"), "artikel 0/" + slots.length, slots.length);
    const per7 = this.budget("F7") / slots.length;
    for (let i = 0; i < slots.length; i++) {
      this.v.llmNote(`artikel ${i + 1}/${slots.length}`);
      this.v.llmBar(i, 0.15);
      await this.p.draft(slots[i]);
      this.v.llmBar(i, 1, true);
      this.v.chipProgress("F7", (i + 1) / slots.length);
      await sleepR(Math.max(0, per7 - 900));
    }
    await settle();

    this.markActive("F8", "F8 · Eindredacteuren — corrigeer de taal en zet de definitieve kop.");
    const f8 = this.m.fase["F8"];
    this.v.llm("Eindredacteuren · " + (f8.model || "model"), "artikel 0/" + slots.length, slots.length);
    const per8 = this.budget("F8") / slots.length;
    for (let i = 0; i < slots.length; i++) {
      const s = this.m.slotByPos.get(slots[i]);
      const nc = (s.correcties || []).length;
      this.v.llmNote(`artikel ${i + 1}/${slots.length} · ${nc} correctie${nc === 1 ? "" : "s"}`);
      const fills = 5;
      for (let k = 1; k <= fills; k++) { this.v.llmBar(i, k / fills); await sleepR(per8 * 0.6 / fills); }
      this.v.llmBar(i, 1, true);
      this.p.final(slots[i]);
      this.v.chipProgress("F8", (i + 1) / slots.length);
      await sleepR(per8 * 0.35);
    }
    await settle();

    this.markActive("F9", "F9 · Vormgevers — illustraties en opmaak; de krant is af.");
    const f9 = this.m.fase["F9"];
    this.v.llm("Vormgevers · " + (f9.model || "model"), "opmaak & illustratie", 3);
    const budget = this.budget("F9");
    for (let k = 0; k < 3; k++) { this.v.llmBar(k, 1, true); await sleepR(budget * 0.2); }
    for (const s of this.m.slots) this.p.illustration(s.pos);
    this.v.chipProgress("F9", 1);
    await sleepR(budget * 0.4);
    await settle();
  }
}

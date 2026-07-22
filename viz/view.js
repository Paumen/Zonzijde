import { FASES, SCOPES } from "./data.js";
import { placeAt } from "./engine.js";

const SC = { "-2": "--sc--2", "-1": "--sc--1", "0": "--sc-0", "1": "--sc-1", "2": "--sc-2" };

export function el(tag, cls, parent) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (parent) parent.appendChild(n);
  return n;
}

export class View {
  constructor(model) {
    this.m = model;
    this.flow = document.getElementById("flow");
    this.itemsEl = document.getElementById("items");
    this.lanesEl = document.getElementById("lanes");
    this.binsEl = document.getElementById("bins");
    this.railEl = document.getElementById("rail");
    this.captionEl = document.getElementById("caption");
    this.llmEl = document.getElementById("llm");
    this.llmBars = this.llmEl.querySelector(".llm-bars");
    this.llmLabel = this.llmEl.querySelector(".llm-label");
    this.llmNoteEl = this.llmEl.querySelector(".llm-note");
    this.chips = {};
    this.bins = {};
    this.lanes = {};
    this._buildRail();
    this._buildLanes();
    this._buildBins();
    this.measure();
  }

  _buildRail() {
    for (const f of this.m.trace.fases) {
      const c = el("div", "chip", this.railEl);
      c.dataset.state = "idle";
      if (f.kind.includes("llm")) c.dataset.llm = "1";
      el("span", "fid", c).textContent = f.id;
      el("span", "actor", c).textContent = f.actor;
      const n = el("span", "flow-n", c);
      n.textContent = `${f.in}→${f.out}`;
      const k = el("span", "kind", c);
      el("i", "", k);
      this.chips[f.id] = c;
    }
  }

  _buildLanes() {
    const labels = this.m.trace.meta.scope_labels;
    for (const s of SCOPES) {
      const lane = el("div", "lane", this.lanesEl);
      lane.dataset.scope = s;
      lane.dataset.dim = "0";
      lane.style.setProperty("--lane", `var(--ring-${s})`);
      const tag = el("div", "lane-tag", lane);
      tag.append(s + " ");
      el("small", "", tag).textContent = labels[s] || "";
      this.lanes[s] = lane;
    }
  }

  _buildBins() {
    for (const b of this.m.trace.reason_bins) {
      const bin = el("div", "bin", this.binsEl);
      el("span", "bn", bin).textContent = "0";
      el("span", "bl", bin).textContent = b.label;
      bin._total = 0;
      this.bins[b.key] = bin;
    }
  }

  measure() {
    const r = this.flow.getBoundingClientRect();
    this.W = r.width;
    this.H = r.height;
    const laneH = this.H / 4;
    SCOPES.forEach((s, i) => {
      const lane = this.lanes[s];
      lane.style.top = i * laneH + "px";
      lane.style.height = laneH + "px";
    });
    this._layoutBins();
  }

  _layoutBins() {
    const order = this.m.trace.reason_bins.map((b) => b.key);
    const top = order.slice(0, 4);
    const bot = order.slice(4);
    const place = (keys, y) => {
      const n = keys.length;
      keys.forEach((k, i) => {
        const bin = this.bins[k];
        bin.style.left = (this.W * (i + 0.5) / n) + "px";
        bin.style.transform = "translateX(-50%)";
        if (y < 0) bin.style.bottom = (-y) + "px";
        else bin.style.top = y + "px";
        const br = bin.getBoundingClientRect();
        const fr = this.flow.getBoundingClientRect();
        bin._cx = br.left - fr.left + br.width / 2;
        bin._cy = br.top - fr.top + br.height / 2;
      });
    };
    place(top, 4);
    place(bot, -4);
  }

  laneArea(scope) {
    const laneH = this.H / 4;
    const i = SCOPES.indexOf(scope);
    return {
      x0: 70, x1: this.W - 12,
      y0: i * laneH + 20, y1: (i + 1) * laneH - 8,
    };
  }

  binCenter(key) {
    const b = this.bins[key];
    return { x: b._cx, y: b._cy };
  }

  makeCard(node) {
    const div = el("div", "it", this.itemsEl);
    div.style.setProperty("--lanec", `var(--ring-${this.m.scopeOf(node)})`);
    el("span", "swatch", div);
    el("div", "tt", div);
    el("span", "meta", div);
    node.el = div;
    placeAt(node, -80, -80, 9, 9);
    return node;
  }

  setScore(node, score) {
    node.el.dataset.score = String(score);
    node.el.style.setProperty("--scfill", `var(${SC[String(score)]})`);
  }

  setRich(node, title, meta) {
    node.el.classList.add("rich");
    node.el.querySelector(".tt").textContent = title || node.title || "";
    if (meta != null) node.el.querySelector(".meta").textContent = meta;
  }

  setHaze(node) { node.el.classList.add("haze"); }

  bump(key, n = 1) {
    const bin = this.bins[key];
    bin._total += n;
    bin.querySelector(".bn").textContent = bin._total;
    bin.dataset.hot = "1";
  }

  chip(fid, state) {
    const c = this.chips[fid];
    if (state) c.dataset.state = state;
    return c;
  }

  chipProgress(fid, frac) {
    this.chips[fid].querySelector(".kind > i").style.width =
      Math.round(Math.max(0, Math.min(1, frac)) * 100) + "%";
  }

  dimLanes(on) {
    for (const s of SCOPES) this.lanes[s].dataset.dim = on ? "1" : "0";
  }

  caption(text) { this.captionEl.textContent = text; }

  llm(label, note, nbars) {
    this.llmEl.hidden = false;
    this.llmLabel.textContent = label;
    this.llmNoteEl.textContent = note || "";
    this.llmBars.innerHTML = "";
    this._bars = [];
    for (let i = 0; i < (nbars || 0); i++) {
      const b = el("div", "b", this.llmBars);
      el("i", "", b);
      this._bars.push(b);
    }
  }

  llmBar(i, frac, done) {
    const b = this._bars && this._bars[i];
    if (!b) return;
    b.querySelector("i").style.width = Math.round(frac * 100) + "%";
    if (done) b.classList.add("done");
  }

  llmNote(t) { this.llmNoteEl.textContent = t; }
  llmOff() { this.llmEl.hidden = true; }
}

import { el } from "./view.js";
import { sleep, D } from "./engine.js";

export class Paper {
  constructor(model) {
    this.m = model;
    this.root = document.getElementById("paper");
    this.page = this.root.querySelector(".paper-page");
    const meta = model.trace.meta;
    this.root.querySelector(".paper-sub").textContent =
      `nr. ${meta.nr} · ${meta.edition} · ${model.trace.meta.counts.pages} pagina's`;
    this.blocks = new Map();
    for (const s of model.slots) {
      const art = el("div", "art placeholder", this.page);
      art.style.setProperty("--artc", `var(--ring-${s.scope})`);
      el("div", "h", art).textContent = "";
      el("div", "loc", art).textContent = "";
      const ill = el("div", "ill", art);
      el("div", "body", art);
      art._ill = ill;
      this.blocks.set(s.pos, art);
    }
  }

  live() { this.root.dataset.live = "1"; }

  werktitel(pos) {
    const s = this.m.slotByPos.get(pos);
    const a = this.blocks.get(pos);
    if (!a) return;
    a.classList.remove("placeholder");
    a.dataset.state = "werktitel";
    a.querySelector(".h").textContent = s.topic || "";
    a.querySelector(".loc").textContent = (s.location || "") +
      (s.source_date ? " · " + s.source_date : "");
  }

  async draft(pos) {
    const s = this.m.slotByPos.get(pos);
    const a = this.blocks.get(pos);
    if (!a) return;
    a.dataset.state = "draft";
    const body = a.querySelector(".body");
    const text = s.draft_excerpt || "";
    const steps = 10;
    for (let i = 1; i <= steps; i++) {
      body.textContent = text.slice(0, Math.round(text.length * i / steps));
      await sleep(D(90));
    }
  }

  final(pos) {
    const s = this.m.slotByPos.get(pos);
    const a = this.blocks.get(pos);
    if (!a) return;
    a.dataset.state = "final";
    a.querySelector(".h").textContent = s.title || s.topic || "";
    if (s.words != null) a.querySelector(".loc").textContent =
      (s.location || "") + (s.source_date ? " · " + s.source_date : "") +
      ` · ${s.words} w`;
  }

  illustration(pos) {
    const s = this.m.slotByPos.get(pos);
    const a = this.blocks.get(pos);
    if (!a || !s.illustration || !s.illustration.svg) return;
    a._ill.innerHTML = s.illustration.svg;
    const svg = a._ill.querySelector("svg");
    if (svg) svg.animate([{ opacity: 0 }, { opacity: 1 }], { duration: D(600), fill: "forwards" });
  }
}

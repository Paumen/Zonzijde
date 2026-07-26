export const EASE = {
  lin: p => p,
  in: p => p * p * p,
  out: p => 1 - Math.pow(1 - p, 3),
  io: p => p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2,
  soft: p => p * p * (3 - 2 * p),
  zwaai: p => 1 - Math.pow(1 - p, 4),
};

export function rng(seed) {
  let s = (seed >>> 0) || 1;
  return () => {
    s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

export class Sprite {
  constructor(el, x = 0, y = 0) {
    this.el = el;
    this.x = x;
    this.y = y;
    this.r = 0;
    this.s = 1;
    this.o = 1;
    this._o = -1;
    this.dirty = true;
  }

  set(p) {
    Object.assign(this, p);
    this.dirty = true;
    return this;
  }

  apply() {
    this.dirty = false;
    this.el.style.transform =
      `translate(${this.x.toFixed(2)}px,${this.y.toFixed(2)}px) rotate(${this.r.toFixed(2)}deg) scale(${this.s.toFixed(4)})`;
    if (this.o !== this._o) {
      this._o = this.o;
      this.el.style.opacity = this.o.toFixed(3);
    }
  }
}

export class Camera {
  constructor(cx, cy, vw) {
    this.keys = [{ t: -1, cx, cy, vw, ease: EASE.io }];
    this.cx = cx;
    this.cy = cy;
    this.vw = vw;
  }

  key(t, to, ease = EASE.io) {
    const p = this.keys[this.keys.length - 1];
    this.keys.push({
      t, ease,
      cx: to.cx ?? p.cx,
      cy: to.cy ?? p.cy,
      vw: to.vw ?? p.vw,
    });
    return this;
  }

  hold(t) {
    const p = this.keys[this.keys.length - 1];
    return this.key(t, p, EASE.lin);
  }

  sample(t) {
    const k = this.keys;
    let i = 0;
    while (i < k.length - 1 && k[i + 1].t <= t) i++;
    const a = k[i], b = k[i + 1];
    if (!b) {
      this.cx = a.cx; this.cy = a.cy; this.vw = a.vw;
      return;
    }
    const p = Math.max(0, Math.min(1, (t - a.t) / (b.t - a.t)));
    const e = b.ease(p);
    this.cx = a.cx + (b.cx - a.cx) * e;
    this.cy = a.cy + (b.cy - a.cy) * e;
    this.vw = a.vw * Math.pow(b.vw / a.vw, e);
  }
}

export class Engine {
  constructor() {
    this.t = 0;
    this.events = [];
    this.ei = 0;
    this.tweens = [];
    this.tracks = [];
    this.live = new Set();
  }

  at(t, fn) {
    this.events.push([t, fn]);
    return this;
  }

  seal() {
    this.events.sort((a, b) => a[0] - b[0]);
    this.tracks.sort((a, b) => a.t0 - b.t0);
  }

  tween(obj, to, t0, dur, ease = EASE.io, done) {
    this.tweens.push({ obj, to, t0, t1: t0 + Math.max(1, dur), ease, done, from: null });
    return this;
  }

  cut(obj) {
    this.tweens = this.tweens.filter(tw => tw.obj !== obj);
  }

  track(t0, t1, fn) {
    this.tracks.push({ t0, t1: Math.max(t0 + 1, t1), fn, done: false });
    return this;
  }

  step(dt) {
    this.t += dt;
    const t = this.t;
    while (this.ei < this.events.length && this.events[this.ei][0] <= t) {
      this.events[this.ei++][1](t);
    }
    for (let i = this.tweens.length - 1; i >= 0; i--) {
      const tw = this.tweens[i];
      if (t < tw.t0) continue;
      if (!tw.from) {
        tw.from = {};
        for (const k in tw.to) tw.from[k] = tw.obj[k];
      }
      const p = Math.min(1, (t - tw.t0) / (tw.t1 - tw.t0));
      const e = tw.ease(p);
      for (const k in tw.to) tw.obj[k] = tw.from[k] + (tw.to[k] - tw.from[k]) * e;
      tw.obj.dirty = true;
      this.live.add(tw.obj);
      if (p === 1) {
        this.tweens.splice(i, 1);
        if (tw.done) tw.done();
      }
    }
    for (const tr of this.tracks) {
      if (t < tr.t0 || tr.done) continue;
      const p = Math.min(1, (t - tr.t0) / (tr.t1 - tr.t0));
      tr.fn(p, t);
      if (p === 1) tr.done = true;
    }
  }

  flush() {
    for (const sp of this.live) if (sp.dirty) sp.apply();
    this.live.clear();
  }
}

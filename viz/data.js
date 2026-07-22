export const FASES = ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9"];
export const SCOPES = ["L", "R", "N", "I"];

export async function loadTrace(url = "viz/viz-trace.json") {
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(`trace ${res.status}`);
  return res.json();
}

export function index(trace) {
  const byUid = new Map();
  for (const it of trace.items) byUid.set(it.uid, it);

  const fase = {};
  for (const f of trace.fases) fase[f.id] = f;

  const bin = {};
  for (const b of trace.reason_bins) bin[b.key] = b;

  const exitIndex = (it) =>
    it.exit_fase ? FASES.indexOf(it.exit_fase) : FASES.length;

  const enters = (it, fid) => exitIndex(it) >= FASES.indexOf(fid);
  const dropsAt = (fid) =>
    trace.items.filter((it) => it.exit_fase === fid);
  const survivors = () => trace.items.filter((it) => it.exit_fase === null);
  const present = (fid) => trace.items.filter((it) => enters(it, fid));

  const scopeOf = (it) => (SCOPES.includes(it.scope) ? it.scope : "N");

  return {
    trace, byUid, fase, bin, exitIndex, enters,
    dropsAt, survivors, present, scopeOf,
    slots: trace.slots,
    slotByPos: new Map(trace.slots.map((s) => [s.pos, s])),
  };
}

import { el } from "./view.js";
import { engine, setPaused, setSpeed } from "./engine.js";

export function buildControls(model) {
  const root = document.getElementById("controls");
  root.innerHTML = "";

  const play = el("button", "ctl", root);
  play.type = "button";
  play.setAttribute("aria-pressed", "false");
  play.textContent = "⏸ pauze";
  play.onclick = () => {
    const p = !engine.paused;
    setPaused(p);
    play.setAttribute("aria-pressed", String(p));
    play.textContent = p ? "▶ speel" : "⏸ pauze";
  };

  const speed = el("div", "speed", root);
  const presets = model.trace.meta.speed_presets || [4, 8, 12];
  const param = Number(new URLSearchParams(location.search).get("speed"));
  const initial = param > 0 ? param : (model.trace.meta.default_speed || presets[0]);
  setSpeed(initial);
  for (const s of presets) {
    const label = el("label", "", speed);
    const input = el("input", "", label);
    input.type = "radio";
    input.name = "speed";
    input.checked = s === initial;
    input.onchange = () => setSpeed(s);
    el("span", "", label).textContent = "×" + s;
  }

  const restart = el("button", "ctl", root);
  restart.type = "button";
  restart.textContent = "↺ opnieuw";
  restart.onclick = () => location.reload();
}

import { loadTrace, index } from "./data.js";
import { View } from "./view.js";
import { Paper } from "./paper.js";
import { Stages } from "./stages.js";
import { buildControls } from "./controls.js";

async function main() {
  const cap = document.getElementById("caption");
  let trace;
  try {
    trace = await loadTrace();
  } catch (e) {
    cap.textContent = "Kon viz-trace.json niet laden. Draai `python -m zonzijde trace …` en serveer de repo-root.";
    return;
  }
  const model = index(trace);
  const view = new View(model);
  const paper = new Paper(model);
  buildControls(model);
  const stages = new Stages(model, view, paper);

  let resizing;
  window.addEventListener("resize", () => {
    clearTimeout(resizing);
    resizing = setTimeout(() => view.measure(), 200);
  });

  await stages.run();
}

main();

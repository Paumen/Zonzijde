from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from typing import Callable

import requests

from pathlib import Path

from .. import llm, prompts, typeset
from ..context import RunContext
from ..contracts import (EditionArticle, EditionManifest, EditionOutline,
                         ReviewedArticle, Weather, WeatherDay, load_artifact,
                         load_model, save_model)
from ..net import VERIFY

ILLUSTRATE_SCHEMA = {
    "type": "object",
    "properties": {
        "subject": {"type": "string"},
        "pos": {"type": "integer"},
        "svg": {"type": "string"},
    },
    "required": ["subject", "pos", "svg"],
    "additionalProperties": False,
}

WEEKDAGEN = ("ma", "di", "wo", "do", "vr", "za", "zo")
INK_ONLY = {"", "none", "currentcolor", "black", "white",
            "#121212", "#fff", "#ffffff", "#fcfcfb"}

FIXED_REFS = [
    ("de zonnebloem in de kop (masthead)", "assets/art/zonnebloem.svg"),
    ("het sluitlandschap onderaan de laatste pagina", "assets/art/landschap.svg"),
]

JsonCall = Callable[[str], object]


def try_prompt(ctx: RunContext, name: str):
    if not (ctx.root / "config" / "prompts" / f"{name}.md").is_file():
        return None
    return prompts.load_prompt(ctx.root, name)


def fetch_weather(ctx: RunContext) -> Weather:
    cfg = ctx.fase_cfg("compose").get("weather") or {}
    place = cfg.get("place", "Wijchen")
    lat = float(cfg.get("latitude", 51.8103))
    lon = float(cfg.get("longitude", 5.7256))
    days = int(cfg.get("days", 6))
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": lat, "longitude": lon,
                    "daily": "temperature_2m_max,temperature_2m_min,"
                             "precipitation_probability_max,weather_code",
                    "timezone": "Europe/Amsterdam", "forecast_days": days},
            timeout=int(cfg.get("timeout_s", 15)), verify=VERIFY)
        r.raise_for_status()
        daily = r.json()["daily"]
    except (requests.RequestException, KeyError, ValueError) as e:
        raise SystemExit(f"F9 compose: weather fetch failed (EL-2): {e}")

    day_list = []
    for i, iso in enumerate(daily["time"]):
        d = WeatherDay(
            date=iso, label="Vandaag", tmax=daily["temperature_2m_max"][i],
            tmin=daily["temperature_2m_min"][i],
            precip_prob=daily["precipitation_probability_max"][i],
            code=daily["weather_code"][i])
        if i > 0:
            d.label = WEEKDAGEN[d.date.weekday()]
        day_list.append(d)
    return Weather(place=place, latitude=lat, longitude=lon,
                   fetched=ctx.now(), source="open-meteo", days=day_list)


def edition_nr(ctx: RunContext) -> int:
    offset = int(ctx.fase_cfg("compose").get("nr_offset", 0))
    editions_dir = ctx.root / "editions"
    prior = 0
    if editions_dir.is_dir():
        for p in editions_dir.iterdir():
            if p.name < ctx.edition.isoformat() and (p / "edition.json").is_file():
                prior += 1
    return offset + prior + 1


def collect_prompt_versions(ctx: RunContext) -> dict:
    out: dict = {}
    for fn in ("f3-score-log.json", "f4-select-log.json", "f5-enrich-log.json",
               "f6-outline-log.json", "f7-write-log.json", "f8-review-log.json"):
        path = ctx.work_dir / fn
        if not path.is_file():
            continue
        d = json.loads(path.read_text(encoding="utf-8"))
        out.update(d.get("prompt_versions") or {})
        if "prompt_version" in d:
            out[fn.split("-")[1]] = d["prompt_version"]
    return out


def build_articles(ctx: RunContext) -> list[EditionArticle]:
    reviewed = load_artifact(ctx.work_dir / "f8-reviewed.json", ReviewedArticle)
    outline = load_model(ctx.work_dir / "f6-outline.json", EditionOutline)
    slots = {s.pos: s for s in outline.slots}
    missing = [r.pos for r in reviewed if r.pos not in slots]
    if missing:
        raise SystemExit(f"F9 compose: reviewed slot(s) {missing} not in the "
                         "outline — artifacts out of step, re-run F6..F8")
    articles = [
        EditionArticle(
            pos=r.pos, scope=slots[r.pos].scope, length=slots[r.pos].length,
            title=r.title, location=r.location, source_date=r.source_date,
            text=r.text, words=r.words, source_ids=slots[r.pos].source_ids)
        for r in sorted(reviewed, key=lambda r: r.pos)]
    if articles[0].scope != "L":
        raise SystemExit("F9 compose: first slot is not lokaal (ED-6)")
    return articles


def svg_problems(svg: str) -> list[str]:
    try:
        root = ET.fromstring(svg)
    except ET.ParseError as e:
        return [f"not well-formed XML: {e}"]
    if not root.tag.endswith("svg"):
        return [f"root element is {root.tag!r}, not svg"]
    if "viewBox" not in root.attrib:
        return ["missing viewBox"]
    colours = set()
    for el in root.iter():
        for attr in ("fill", "stroke", "color", "stop-color"):
            v = el.get(attr, "").strip().lower()
            if v and v not in INK_ONLY:
                colours.add(v)
        for decl in el.get("style", "").split(";"):
            prop, _, v = decl.partition(":")
            if prop.strip().lower() in ("fill", "stroke", "color",
                                        "stop-color"):
                v = v.strip().lower()
                if v and v not in INK_ONLY:
                    colours.add(v)
    return [f"non-monochrome colours {sorted(colours)}"] if colours else []


def illustration_candidates(articles: list[EditionArticle]) -> list[int]:
    return [a.pos for a in articles if a.scope in ("R", "N")] \
        or [a.pos for a in articles[1:]]


def rasterize_refs(ctx: RunContext,
                   notes: list[str]) -> list[tuple[str, Path, Path | None]]:
    out = []
    for label, rel in FIXED_REFS:
        svg = ctx.root / rel
        png = ctx.work_dir / f"ref-{Path(rel).stem}.png"
        try:
            typeset.rasterize_svg(ctx.root, svg, png)
            out.append((label, svg, png))
        except (typeset.CompileError, OSError) as e:
            notes.append(f"reference render failed for {label}: {e}")
            out.append((label, svg, None))
    return out


def build_illustrate_prompt(articles: list[EditionArticle],
                            candidates: list[int],
                            refs: list[tuple[str, Path, Path | None]]) -> str:
    lines = ["Huistekeningen:"]
    for label, svg, png in refs:
        lines.append(f"- {label}:")
        if png is not None:
            lines.append(f"    bekijk: {png}")
        lines.append(f"    lees: {svg}")
    lines += ["", "Artikelen:"]
    for a in articles:
        if a.pos in candidates:
            head = " ".join(a.text.split()[:60])
            lines.append(f"pos={a.pos} [{a.scope}] {a.title}\n{head}…")
    return "\n".join(lines)


def draw_illustration(ctx: RunContext, articles: list[EditionArticle],
                      call: JsonCall | None, usage: list,
                      notes: list[str]) -> tuple[str | None, int | None, str | None]:
    if call is None:
        rules = try_prompt(ctx, "illustrate")
        if rules is None:
            notes.append("illustration skipped: config/prompts/illustrate.md "
                         "does not exist yet")
            return None, None, None
        brief = prompts.load_prompt(ctx.root, "brief")
        cfg = ctx.llm_cfg("illustrate")
        call = lambda prompt: llm.agent_json(
            prompt, system=f"{brief.body}\n\n{rules.body}", schema=ILLUSTRATE_SCHEMA,
            model=cfg["model"], effort=cfg.get("effort"), max_turns=12,
            allowed_tools=["Read"], cwd=str(ctx.root), usage_sink=usage)
    candidates = illustration_candidates(articles)
    ctx.work_dir.mkdir(parents=True, exist_ok=True)
    refs = rasterize_refs(ctx, notes)
    prompt = build_illustrate_prompt(articles, candidates, refs)
    try:
        payload = call(prompt)
    except llm.LlmError as e:
        notes.append(f"illustration failed: {e}")
        return None, None, None
    if not isinstance(payload, dict) or not isinstance(payload.get("svg"), str):
        notes.append("illustration failed: invalid response shape")
        return None, None, None
    svg = payload["svg"].strip()
    pos = payload.get("pos")
    if pos not in candidates:
        notes.append(f"illustration pos {pos!r} not eligible; "
                     f"moved to {candidates[0]}")
        pos = candidates[0]
    ctx.work_dir.mkdir(parents=True, exist_ok=True)
    (ctx.work_dir / "f9-illustration.svg").write_text(svg + "\n",
                                                       encoding="utf-8")
    problems = svg_problems(svg)
    if problems:
        notes.append("illustration drawn but left out of the render: "
                     + "; ".join(problems))
        return None, None, payload.get("subject")
    return "work/f9-illustration.svg", pos, payload.get("subject")


def run(ctx: RunContext, illustrate_call: JsonCall | None = None) -> None:
    fase_cfg = ctx.fase_cfg("compose")
    max_recompiles = int(fase_cfg.get("max_recompiles", 3))

    articles = build_articles(ctx)
    weather = fetch_weather(ctx)
    nr = edition_nr(ctx)

    notes: list[str] = []
    usage: list[dict] = []
    illustration, ill_pos, ill_subject = draw_illustration(
        ctx, articles, illustrate_call, usage, notes)

    data_path = ctx.edition_dir / "edition.json"
    attempts: list[list[dict]] = []
    recompiles = 0
    violations: list[typeset.Violation] = []

    def manifest() -> EditionManifest:
        return EditionManifest(
            edition=ctx.edition, nr=nr, articles=articles, weather=weather,
            illustration=illustration, illustration_pos=ill_pos,
            pdf="krant-A3boekje.pdf",
            counts={"words_body": sum(a.words for a in articles),
                    "pages": typeset.TARGET_PAGES},
            pipeline={"run": ctx.now().isoformat(),
                      "prompt_versions": collect_prompt_versions(ctx)})

    def write_log() -> None:
        log = {
            "nr": nr,
            "illustration": {"file": illustration, "pos": ill_pos,
                             "subject": ill_subject},
            "notes": notes,
            "recompiles": recompiles,
            "attempts": attempts,
            "violations": [v.to_dict() for v in violations],
            "llm": llm.summarize_usage(usage),
        }
        (ctx.work_dir / "f9-compose-log.json").write_text(
            json.dumps(log, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")

    pdf: bytes | None = None
    while True:
        save_model(data_path, manifest())
        try:
            pdf = typeset.compile_edition(ctx.root, data_path)
            marks = typeset.query_marks(ctx.root, data_path)
            violations = typeset.check(pdf, marks)
        except typeset.CompileError as e:
            if illustration is not None:
                notes.append(f"illustration dropped from the render, "
                             f"compile failed: {e}")
                illustration, ill_pos = None, None
                continue
            write_log()
            raise SystemExit(f"F9 compose: Typst compile failed: {e}")
        attempts.append([v.to_dict() for v in violations])
        if not violations:
            break
        if illustration is not None and recompiles < max_recompiles and any(
                v.rule in ("LAY-4", "LAY-5") for v in violations):
            candidates = illustration_candidates(articles)
            i = candidates.index(ill_pos) if ill_pos in candidates else -1
            if i + 1 < len(candidates):
                ill_pos = candidates[i + 1]
                notes.append(f"illustration moved to pos {ill_pos} (reflow)")
                recompiles += 1
                continue
        write_log()
        raise SystemExit(
            f"F9 compose: {len(violations)} typeset violation(s) after "
            f"{recompiles} recompile(s) — see f9-compose-log.json. The "
            "editorial gate resolves layout (SPEC §6): edit the article "
            "texts or reflow, then re-run compose.")

    booklet = typeset.impose_booklet(pdf)
    (ctx.edition_dir / "krant-A3boekje.pdf").write_bytes(booklet)
    write_log()
    print(f"F9 compose: nr {nr}, {len(articles)} articles, "
          f"{sum(a.words for a in articles)} words, "
          f"{typeset.TARGET_PAGES} pages, {recompiles} recompile(s) → "
          f"{ctx.edition_dir / 'krant-A3boekje.pdf'}")

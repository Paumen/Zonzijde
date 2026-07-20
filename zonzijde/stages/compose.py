from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from typing import Callable

import requests

from .. import llm, prompts, typeset
from ..context import RunContext
from ..contracts import (EditionArticle, EditionManifest, EditionOutline,
                         ReviewedArticle, Weather, WeatherDay, load_artifact,
                         load_model, save_model)
from ..net import VERIFY
from .write import word_count

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

TRIM_SCHEMA = {
    "type": "object",
    "properties": {"text": {"type": "string"}},
    "required": ["text"],
    "additionalProperties": False,
}

WEEKDAGEN = ("ma", "di", "wo", "do", "vr", "za", "zo")
INK_ONLY = {"", "none", "currentcolor", "black", "white",
            "#121212", "#fff", "#ffffff", "#fcfcfb"}

JsonCall = Callable[[str], object]


def try_prompt(ctx: RunContext, name: str):
    if not (ctx.root / "config" / "prompts" / f"{name}.md").is_file():
        return None
    return prompts.load_prompt(ctx.root, name)


def fetch_weather(ctx: RunContext) -> Weather:
    cfg = ctx.stage_cfg("compose").get("weather") or {}
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
        raise SystemExit(f"S9 compose: weather fetch failed (EL-2): {e}")

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
    offset = int(ctx.stage_cfg("compose").get("nr_offset", 0))
    editions_dir = ctx.root / "editions"
    prior = 0
    if editions_dir.is_dir():
        for p in editions_dir.iterdir():
            if p.name < ctx.edition.isoformat() and (p / "edition.json").is_file():
                prior += 1
    return offset + prior + 1


def collect_prompt_versions(ctx: RunContext) -> dict:
    out: dict = {}
    for fn in ("30-score-log.json", "40-select-log.json", "50-enrich-log.json",
               "60-outline-log.json", "70-write-log.json", "80-review-log.json"):
        path = ctx.work_dir / fn
        if not path.is_file():
            continue
        d = json.loads(path.read_text(encoding="utf-8"))
        out.update(d.get("prompt_versions") or {})
        if "prompt_version" in d:
            out[fn.split("-")[1]] = d["prompt_version"]
    return out


def build_articles(ctx: RunContext) -> list[EditionArticle]:
    reviewed = load_artifact(ctx.work_dir / "80-reviewed.json", ReviewedArticle)
    outline = load_model(ctx.work_dir / "60-outline.json", EditionOutline)
    slots = {s.pos: s for s in outline.slots}
    missing = [r.pos for r in reviewed if r.pos not in slots]
    if missing:
        raise SystemExit(f"S9 compose: reviewed slot(s) {missing} not in the "
                         "outline — artifacts out of step, re-run S6..S8")
    articles = [
        EditionArticle(
            pos=r.pos, scope=slots[r.pos].scope, length=slots[r.pos].length,
            title=r.title, location=r.location, source_date=r.source_date,
            text=r.text, words=r.words, source_ids=slots[r.pos].source_ids)
        for r in sorted(reviewed, key=lambda r: r.pos)]
    if articles[0].scope != "L":
        raise SystemExit("S9 compose: first slot is not lokaal (ED-6)")
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


def draw_illustration(ctx: RunContext, articles: list[EditionArticle],
                      call: JsonCall | None, usage: list,
                      notes: list[str]) -> tuple[str | None, int | None, str | None]:
    if call is None:
        rules = try_prompt(ctx, "illustrate")
        if rules is None:
            notes.append("illustration skipped: config/prompts/illustrate.md "
                         "does not exist yet")
            return None, None, None
        cfg = ctx.llm_cfg("illustrate")
        call = lambda prompt: llm.agent_json(
            prompt, system=rules.body, schema=ILLUSTRATE_SCHEMA,
            model=cfg["model"], effort=cfg.get("effort"), max_turns=2,
            usage_sink=usage)
    candidates = illustration_candidates(articles)
    refs = sorted((ctx.root / "assets" / "art").glob("illustratie-ref-*.svg"))
    parts = ["Artikelen (kies er één, veld pos):"]
    for a in articles:
        if a.pos in candidates:
            head = " ".join(a.text.split()[:60])
            parts.append(f"pos={a.pos} [{a.scope}] {a.title}\n{head}…")
    for ref in refs:
        parts.append("Stijlreferentie (alleen de stijl, nooit hergebruiken):\n"
                     + ref.read_text(encoding="utf-8"))
    try:
        payload = call("\n\n".join(parts))
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
    (ctx.work_dir / "85-illustration.svg").write_text(svg + "\n",
                                                      encoding="utf-8")
    problems = svg_problems(svg)
    if problems:
        notes.append("illustration drawn but left out of the render: "
                     + "; ".join(problems))
        return None, None, payload.get("subject")
    return "work/85-illustration.svg", pos, payload.get("subject")


def paragraph_of(article: EditionArticle, word: str | None) -> int:
    paras = article.text.split("\n\n")
    if word:
        tail = word.strip().strip(".,!?\"'»«")
        for i, p in enumerate(paras):
            if p.rstrip().rstrip(".,!?\"'»«").endswith(tail):
                return i
    return max(range(len(paras)), key=lambda i: len(paras[i].split()))


def trim_targets(violations: list[typeset.Violation],
                 articles: list[EditionArticle]) -> list[tuple[int, int, int, str]]:
    by_pos = {a.pos: a for a in articles}
    targets: dict[tuple[int, int], tuple[int, str]] = {}

    def add(pos: int | None, word: str | None, delta: int, reason: str) -> None:
        if pos is None or pos not in by_pos:
            pos = max(by_pos, key=lambda p: by_pos[p].words)
        idx = paragraph_of(by_pos[pos], word)
        targets.setdefault((pos, idx), (delta, reason))

    for v in violations:
        if v.rule == "LAY-3":
            word = v.detail.split("'")[1] if "'" in v.detail else None
            add(v.pos, word, -6, f"{v.rule}: {v.detail}")
        elif v.rule == "LAY-4":
            add(v.pos, None, -3 * typeset.WORDS_PER_LINE,
                f"{v.rule}: {v.detail}")
        elif v.rule == "LAY-5":
            lines = float(v.detail.split()[2])
            delta = -min(80, max(14, round(lines * typeset.WORDS_PER_LINE)))
            add(v.pos, None, delta, f"{v.rule}: {v.detail}")
        elif "overflow" in v.detail or "landscape" in v.detail:
            add(None, None, -60, f"{v.rule}: {v.detail}")
        elif v.rule == "LAY-1":
            last = max(by_pos)
            idx = len(by_pos[last].text.split("\n\n")) - 1
            targets.setdefault((last, idx), (60, f"{v.rule}: {v.detail}"))
    return [(pos, idx, delta, reason)
            for (pos, idx), (delta, reason) in targets.items()]


def apply_trims(ctx: RunContext, articles: list[EditionArticle],
                targets: list[tuple[int, int, int, str]],
                call: JsonCall | None, usage: list,
                trims_log: list[dict]) -> None:
    if call is None:
        rules = try_prompt(ctx, "trim")
        if rules is None:
            raise SystemExit(
                "S9 compose: typeset violations need the trim assist, but "
                "config/prompts/trim.md does not exist yet — "
                "see 90-compose-log.json")
        cfg = ctx.llm_cfg("trim")
        call = lambda prompt: llm.agent_json(
            prompt, system=rules.body, schema=TRIM_SCHEMA,
            model=cfg["model"], effort=cfg.get("effort"), max_turns=2,
            usage_sink=usage)
    by_pos = {a.pos: a for a in articles}
    for pos, idx, delta, reason in targets:
        article = by_pos[pos]
        paras = article.text.split("\n\n")
        para = paras[idx]
        richting = "Kort deze alinea in met" if delta < 0 \
            else "Verleng deze alinea met"
        prompt = "\n\n".join([
            f"Artikel: {article.title}",
            f"{richting} ongeveer {abs(delta)} woorden "
            f"(nu {len(para.split())} woorden).",
            para,
        ])
        try:
            payload = call(prompt)
        except llm.LlmError as e:
            trims_log.append({"pos": pos, "paragraph": idx, "delta": delta,
                              "reason": reason, "error": str(e)})
            continue
        text = payload.get("text", "").strip() \
            if isinstance(payload, dict) else ""
        if not text:
            trims_log.append({"pos": pos, "paragraph": idx, "delta": delta,
                              "reason": reason, "error": "empty response"})
            continue
        paras[idx] = " ".join(text.split())
        article.text = "\n\n".join(paras)
        old_words = article.words
        article.words = word_count(article.text)
        trims_log.append({"pos": pos, "paragraph": idx, "delta": delta,
                          "reason": reason,
                          "words": {"before": old_words,
                                    "after": article.words}})


def run(ctx: RunContext, illustrate_call: JsonCall | None = None,
        trim_call: JsonCall | None = None) -> None:
    stage_cfg = ctx.stage_cfg("compose")
    max_recompiles = int(stage_cfg.get("max_recompiles", 3))

    articles = build_articles(ctx)
    weather = fetch_weather(ctx)
    nr = edition_nr(ctx)

    notes: list[str] = []
    usage: list[dict] = []
    trims_log: list[dict] = []
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
            "trims": trims_log,
            "violations": [v.to_dict() for v in violations],
            "llm": llm.summarize_usage(usage),
        }
        (ctx.work_dir / "90-compose-log.json").write_text(
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
            raise SystemExit(f"S9 compose: Typst compile failed: {e}")
        attempts.append([v.to_dict() for v in violations])
        if not violations:
            break
        if recompiles >= max_recompiles:
            write_log()
            raise SystemExit(
                f"S9 compose: {len(violations)} typeset violation(s) after "
                f"{recompiles} recompile(s) — see 90-compose-log.json")
        if illustration is not None and any(
                v.rule in ("LAY-4", "LAY-5") for v in violations):
            candidates = illustration_candidates(articles)
            i = candidates.index(ill_pos) if ill_pos in candidates else -1
            if i + 1 < len(candidates):
                ill_pos = candidates[i + 1]
                notes.append(f"illustration moved to pos {ill_pos} (reflow)")
                recompiles += 1
                continue
        apply_trims(ctx, articles, trim_targets(violations, articles),
                    trim_call, usage, trims_log)
        recompiles += 1

    booklet = typeset.impose_booklet(pdf)
    (ctx.edition_dir / "krant-A3boekje.pdf").write_bytes(booklet)
    write_log()
    print(f"S9 compose: nr {nr}, {len(articles)} articles, "
          f"{sum(a.words for a in articles)} words, "
          f"{typeset.TARGET_PAGES} pages, {recompiles} recompile(s) → "
          f"{ctx.edition_dir / 'krant-A3boekje.pdf'}")

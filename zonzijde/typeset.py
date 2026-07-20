from __future__ import annotations

import io
import json
from dataclasses import dataclass, field
from pathlib import Path

MM = 72 / 25.4
PAGE_W = 210 * MM
PAGE_H = 297 * MM
MARGIN = 12 * MM
GUTTER = 6 * MM
NCOLS = 3
COL_W = (PAGE_W - 2 * MARGIN - (NCOLS - 1) * GUTTER) / NCOLS
BODY_LINE = 11.0
GAP_LIMIT = 3 * BODY_LINE + 3.0
STUB_LINES = 3
TARGET_PAGES = 4
MIN_FILL = 3.5
WORDS_PER_LINE = 7


class CompileError(RuntimeError):
    pass


def compile_edition(root: Path, data_path: Path, *, fmt: str = "pdf"):
    import typst

    rel = "/" + data_path.relative_to(root).as_posix()
    kwargs = dict(root=str(root), font_paths=[str(root / "fonts")],
                  sys_inputs={"data": rel})
    template = str(root / "templates" / "krant.typ")
    try:
        if fmt == "pdf":
            return typst.compile(template, **kwargs)
        return typst.compile(template, format=fmt, ppi=144.0, **kwargs)
    except Exception as e:
        raise CompileError(str(e))


def rasterize_svg(root: Path, svg_path: Path, out_path: Path,
                  width_pt: float = 360.0) -> None:
    import typst

    rel = "/" + svg_path.relative_to(root).as_posix()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = out_path.with_suffix(".raster.typ")
    doc.write_text(
        f'#set page(width: auto, height: auto, margin: 0pt)\n'
        f'#image("{rel}", width: {width_pt}pt)\n', encoding="utf-8")
    try:
        png = typst.compile(str(doc), root=str(root), format="png", ppi=144.0)
    except Exception as e:
        raise CompileError(str(e))
    finally:
        doc.unlink(missing_ok=True)
    out_path.write_bytes(png[0] if isinstance(png, list) else png)


def query_marks(root: Path, data_path: Path) -> list[dict]:
    import typst

    rel = "/" + data_path.relative_to(root).as_posix()
    try:
        raw = typst.query(str(root / "templates" / "krant.typ"), "<zz>",
                          root=str(root), font_paths=[str(root / "fonts")],
                          sys_inputs={"data": rel})
    except Exception as e:
        raise CompileError(str(e))
    return [m["value"] for m in json.loads(raw)]


@dataclass
class Line:
    page: int
    col: int
    y: float
    text: str
    body: bool


@dataclass
class Violation:
    rule: str
    detail: str
    page: int | None = None
    col: int | None = None
    pos: int | None = None

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


def column_of(x: float) -> int:
    for i in range(NCOLS):
        left = MARGIN + i * (COL_W + GUTTER)
        if x < left + COL_W + GUTTER / 2:
            return i
    return NCOLS - 1


def extract_lines(pdf_bytes: bytes) -> list[Line]:
    import pypdf

    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    lines: list[Line] = []
    for pno, page in enumerate(reader.pages, start=1):
        frags: list[tuple[float, float, str, str]] = []

        def visit(text, cm, tm, font_dict, font_size):
            if not text or not text.strip():
                return
            x = cm[0] * tm[4] + cm[2] * tm[5] + cm[4]
            y = cm[1] * tm[4] + cm[3] * tm[5] + cm[5]
            base = str(font_dict.get("/BaseFont", "")) if font_dict else ""
            frags.append((x, PAGE_H - y, base, text))

        page.extract_text(visitor_text=visit)
        by_col: dict[int, list[tuple[float, float, str, str]]] = {}
        for x, y, base, text in frags:
            by_col.setdefault(column_of(x), []).append((y, x, base, text))

        def emit(col: int, cluster: list[tuple[float, float, str, str]]) -> None:
            cluster.sort(key=lambda p: p[1])
            text = "".join(p[3] for p in cluster).replace("\xad", "").strip()
            if not text:
                return
            body = all("Newsreader-400" in p[2] and "400i" not in p[2]
                       for p in cluster)
            lines.append(Line(page=pno, col=col, y=cluster[0][0], text=text,
                              body=body))

        for col, items in by_col.items():
            items.sort()
            cluster: list[tuple[float, float, str, str]] = []
            for item in items:
                if cluster and item[0] - cluster[-1][0] > 0.8:
                    emit(col, cluster)
                    cluster = []
                cluster.append(item)
            if cluster:
                emit(col, cluster)
    lines.sort(key=lambda l: (l.page, l.col, l.y))
    return lines


@dataclass
class Layout:
    n_pages: int
    lines: list[Line]
    marks: list[dict]
    article_starts: list[tuple[tuple[int, int, float], int]] = field(init=False)
    fillers: dict[int, list[tuple[float, float]]] = field(init=False)
    col_fillers: dict[tuple[int, int], list[tuple[float, float]]] = field(init=False)
    content_end: tuple[int, int, float] | None = field(init=False)

    def __post_init__(self) -> None:
        by_kind: dict[str, list[dict]] = {}
        for m in self.marks:
            by_kind.setdefault(m["kind"], []).append(m)

        self.article_starts = sorted(
            ((m["page"], column_of(m["x"]), m["y"]), m["pos"])
            for m in by_kind.get("article", []))

        self.fillers = {}
        self.col_fillers = {}

        def add_filler(page: int, y0: float, y1: float) -> None:
            self.fillers.setdefault(page, []).append((y0, y1))

        for m in by_kind.get("masthead-end", []):
            add_filler(m["page"], 0.0, m["y"])
        for start, end in zip(by_kind.get("weather", []),
                              by_kind.get("weather-end", [])):
            add_filler(start["page"], start["y"] - 4, end["y"] + 8)
        for m in by_kind.get("landscape", []):
            add_filler(m["page"], m["y"] - 2, PAGE_H)
        starts = {m["pos"]: m for m in by_kind.get("article", [])}
        ends = {m["pos"]: m for m in by_kind.get("article-end", [])}
        if 1 in starts and 1 in ends and starts[1]["page"] == ends[1]["page"]:
            add_filler(starts[1]["page"], starts[1]["y"] - 4,
                       ends[1]["y"] + 14)
        for start, end in zip(by_kind.get("illustration", []),
                              by_kind.get("illustration-end", [])):
            key = (start["page"], column_of(start["x"]))
            self.col_fillers.setdefault(key, []).append(
                (start["y"] - 2, end["y"] + 2))

        ce = by_kind.get("content-end")
        self.content_end = None
        if ce:
            m = ce[0]
            self.content_end = (m["page"], column_of(m["x"]), m["y"])

    def article_at(self, page: int, col: int, y: float) -> int | None:
        pos = None
        for key, p in self.article_starts:
            if key <= (page, col, y):
                pos = p
        return pos

    def landscape_top(self) -> float | None:
        for m in self.marks:
            if m["kind"] == "landscape":
                return m["y"]
        return None


def _occupied(layout: Layout, page: int, col: int) -> list[tuple[float, float]]:
    spans = [(l.y - 8.5, l.y + 2.5) for l in layout.lines
             if l.page == page and l.col == col]
    spans += layout.fillers.get(page, [])
    spans += layout.col_fillers.get((page, col), [])
    spans.sort()
    merged: list[tuple[float, float]] = []
    for y0, y1 in spans:
        if merged and y0 <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], y1))
        else:
            merged.append((y0, y1))
    return merged


def check(pdf_bytes: bytes, marks: list[dict]) -> list[Violation]:
    lines = extract_lines(pdf_bytes)
    import pypdf

    n_pages = len(pypdf.PdfReader(io.BytesIO(pdf_bytes)).pages)
    layout = Layout(n_pages=n_pages, lines=lines, marks=marks)
    violations: list[Violation] = []

    if n_pages != TARGET_PAGES:
        violations.append(Violation(
            rule="LAY-7",
            detail=f"{n_pages} pages instead of {TARGET_PAGES}"
                   + (" (overflow)" if n_pages > TARGET_PAGES else "")))
    if layout.content_end is None:
        violations.append(Violation(rule="LAY-1", detail="content-end marker missing"))
        return violations

    end_page, end_col, end_y = layout.content_end
    fill = (end_page - 1) + (end_col + min(end_y, PAGE_H) / PAGE_H) / NCOLS
    if fill < MIN_FILL:
        violations.append(Violation(
            rule="LAY-1",
            detail=f"content fills {fill:.2f} pages, below {MIN_FILL}",
            page=end_page))
    landscape_top = layout.landscape_top()
    if end_page == TARGET_PAGES and landscape_top is not None \
            and end_y > landscape_top:
        violations.append(Violation(
            rule="LAY-7",
            detail="content runs into the closing landscape",
            page=end_page))

    for line in lines:
        if not line.body:
            continue
        words = [w for w in line.text.split() if w not in ("—", "–", "-")]
        if len(words) == 1:
            violations.append(Violation(
                rule="LAY-3", detail=f"single-word line {words[0]!r}",
                page=line.page, col=line.col,
                pos=layout.article_at(line.page, line.col, line.y)))

    for page in range(1, n_pages + 1):
        for col in range(NCOLS):
            col_lines = [l for l in lines if l.page == page and l.col == col]
            if not col_lines:
                continue
            if len(col_lines) <= STUB_LINES:
                violations.append(Violation(
                    rule="LAY-4",
                    detail=f"column of {len(col_lines)} line(s)",
                    page=page, col=col,
                    pos=layout.article_at(page, col, col_lines[0].y)))

    landscape_floor = (landscape_top or PAGE_H) - 4
    for page in range(1, n_pages + 1):
        for col in range(NCOLS):
            occ = _occupied(layout, page, col)
            for (a0, a1), (b0, b1) in zip(occ, occ[1:]):
                gap = b0 - a1
                if gap <= GAP_LIMIT:
                    continue
                if page == end_page and b0 >= landscape_floor:
                    continue
                violations.append(Violation(
                    rule="LAY-5",
                    detail=f"whitespace of {gap / BODY_LINE:.1f} lines",
                    page=page, col=col,
                    pos=layout.article_at(page, col, a1)))
    return violations


def impose_booklet(a4_bytes: bytes) -> bytes:
    import pypdf
    from pypdf import Transformation

    reader = pypdf.PdfReader(io.BytesIO(a4_bytes))
    if len(reader.pages) != TARGET_PAGES:
        raise CompileError(
            f"booklet imposition needs {TARGET_PAGES} pages, "
            f"got {len(reader.pages)}")
    writer = pypdf.PdfWriter()
    for left, right in ((4, 1), (2, 3)):
        sheet = writer.add_blank_page(width=2 * PAGE_W, height=PAGE_H)
        sheet.merge_transformed_page(reader.pages[left - 1], Transformation())
        sheet.merge_transformed_page(reader.pages[right - 1],
                                     Transformation().translate(tx=PAGE_W))
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()

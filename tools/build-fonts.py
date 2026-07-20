#!/usr/bin/env python3
import os
import re
import ssl
import urllib.request

from fontTools import ttLib
from fontTools.varLib.instancer import instantiateVariableFont

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

CSS_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Fraunces:opsz,wght@9..144,400;9..144,560;9..144,640;9..144,700"
    "&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400"
    "&family=Archivo:wght@500;600;700&display=swap"
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "fonts")

UNICODE_RANGE = {
    "latin": ("U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, "
              "U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, "
              "U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD"),
    "latin-ext": ("U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, "
                  "U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, "
                  "U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, "
                  "U+2113, U+2C60-2C7F, U+A720-A7FF"),
}

PLAN = [
    ("Fraunces", "normal", [(400, 12, "400"), (560, 14, "560"),
                            (640, 24, "640"), (700, 40, "700")]),
    ("Newsreader", "normal", [(400, 12, "400"), (500, 16, "500")]),
    ("Newsreader", "italic", [(400, 12, "400i")]),
    ("Archivo", "normal", [(500, None, "500"), (600, None, "600"),
                          (700, None, "700")]),
]

_ctx = ssl.create_default_context()
_cafile = os.environ.get("CURL_CA_BUNDLE") or "/root/.ccr/ca-bundle.crt"
if os.path.exists(_cafile):
    _ctx.load_verify_locations(_cafile)


def fetch(url, binary=False, ua=UA):
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    with urllib.request.urlopen(req, context=_ctx, timeout=60) as r:
        return r.read() if binary else r.read().decode("utf-8")


def subset_face_blocks(css):
    out = {}
    for block in re.findall(r"@font-face\s*\{([^}]*)\}", css, re.S):
        if "U+0000-00FF" in block:
            rng = "latin"
        elif "U+0100-02BA" in block:
            rng = "latin-ext"
        else:
            continue
        fam = re.search(r"font-family:\s*'([^']+)'", block).group(1)
        style = re.search(r"font-style:\s*(\w+)", block).group(1)
        url = re.search(r"src:\s*url\(([^)]+)\)", block).group(1)
        out.setdefault((fam, style, rng), url)
    return out


VF_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/%s.ttf"
VF_PATHS = {
    ("Fraunces", "normal"): "fraunces/Fraunces%5BSOFT,WONK,opsz,wght%5D",
    ("Newsreader", "normal"): "newsreader/Newsreader%5Bopsz,wght%5D",
    ("Newsreader", "italic"): "newsreader/Newsreader-Italic%5Bopsz,wght%5D",
    ("Archivo", "normal"): "archivo/Archivo%5Bwdth,wght%5D",
}


def build_ttf():
    total = 0
    count = 0
    cache = {}
    for fam, style, instances in PLAN:
        key = (fam, style)
        if key not in cache:
            cache[key] = fetch(VF_URL % VF_PATHS[key], binary=True)
        for weight, opsz, slug in instances:
            font = ttLib.TTFont(io_bytes(cache[key]))
            axes = {a.axisTag: a for a in font["fvar"].axes}
            pins = {}
            if "wght" in axes:
                pins["wght"] = weight
            if "opsz" in axes and opsz is not None:
                pins["opsz"] = opsz
            for tag, axis in axes.items():
                pins.setdefault(tag, axis.defaultValue)
            instantiateVariableFont(font, pins, inplace=True)
            font["OS/2"].usWeightClass = weight
            sub = "Italic" if style == "italic" else "Regular"
            names = {1: fam, 2: sub, 3: f"{fam}-{slug};zonzijde",
                     4: f"{fam} {slug}", 6: f"{fam}-{slug}",
                     16: fam, 17: sub}
            for nid, value in names.items():
                font["name"].setName(value, nid, 3, 1, 0x409)
                font["name"].setName(value, nid, 1, 0, 0)
            path = os.path.join(OUT_DIR, f"{fam}-{slug}.ttf")
            font.save(path)
            total += os.path.getsize(path)
            count += 1
    print(f"{count} static ttf faces, {total} bytes in fonts/")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    css = fetch(CSS_URL)
    sources = subset_face_blocks(css)

    cache = {}
    faces = []
    total = 0
    for fam, style, instances in PLAN:
        for rng in ("latin", "latin-ext"):
            key = (fam, style, rng)
            if key not in cache:
                cache[key] = fetch(sources[key], binary=True)
            for weight, opsz, slug in instances:
                font = ttLib.TTFont(io_bytes(cache[key]))
                axes = {a.axisTag: a for a in font["fvar"].axes}
                pins = {}
                if "wght" in axes:
                    pins["wght"] = weight
                if "opsz" in axes and opsz is not None:
                    pins["opsz"] = opsz
                for tag, axis in axes.items():
                    pins.setdefault(tag, axis.defaultValue)
                instantiateVariableFont(font, pins, inplace=True)
                font.flavor = "woff2"
                name = f"{fam}-{slug}-{rng}.woff2"
                path = os.path.join(OUT_DIR, name)
                font.save(path)
                total += os.path.getsize(path)
                faces.append((fam, style, weight, name, UNICODE_RANGE[rng]))

    write_css(faces)
    print(f"{len(faces)} static faces, {total} bytes of woff2 in fonts/")
    build_ttf()


def io_bytes(data):
    import io
    return io.BytesIO(data)


def write_css(faces):
    lines = [
        "/* Self-hosted STATIC font instances for De Zonzijde.",
        "   Variable fonts do not embed reliably in browser/headless print-to-PDF,",
        "   so each weight the design uses is shipped as a static woff2 here.",
        "   Subsets: Latin + Latin-Extended. Generated from Google Fonts.",
        "   Regenerate with: python3 tools/build-fonts.py */",
        "",
    ]
    for fam, style, weight, name, urange in faces:
        lines += [
            "@font-face{",
            f"  font-family:'{fam}';",
            f"  font-style:{style};",
            f"  font-weight:{weight};",
            "  font-display:swap;",
            f"  src:url(fonts/{name}) format('woff2');",
            f"  unicode-range:{urange};",
            "}",
        ]
    with open(os.path.join(ROOT, "fonts.css"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()

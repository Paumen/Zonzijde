#let ed = json(sys.inputs.data)

#let ink = rgb("121212")
#let body-ink = rgb("28281f")
#let muted = rgb("6a6a6a")
#let hair = rgb("c9c9c7")

#let maanden = ("januari", "februari", "maart", "april", "mei", "juni",
  "juli", "augustus", "september", "oktober", "november", "december")
#let maanden-kort = ("jan", "feb", "mrt", "apr", "mei", "jun",
  "jul", "aug", "sep", "okt", "nov", "dec")

#let iso(d) = {
  let p = d.split("-")
  (year: int(p.at(0)), month: int(p.at(1)), day: int(p.at(2)))
}
#let datum-lang(d) = {
  let p = iso(d)
  "zondag " + str(p.day) + " " + maanden.at(p.month - 1) + " " + str(p.year)
}
#let datum-kort(d) = {
  let p = iso(d)
  str(p.day) + " " + maanden-kort.at(p.month - 1)
}

#let mark(..kv) = context [#metadata((
  ..kv.named(),
  page: here().position().page,
  x: here().position().x.pt(),
  y: here().position().y.pt(),
))<zz>]

#let archivo(size, weight: 600, tracking: 0.07em, fill: muted, it) = text(
  font: "Archivo", size: size, weight: weight, tracking: tracking,
  fill: fill, upper(it))

#let kicker(label, sub: none) = block(
  breakable: false, sticky: true, above: 4mm, below: 3mm,
  grid(
    columns: if sub == none { (auto, 1fr) } else { (auto, auto, 1fr) },
    column-gutter: 2.5mm, align: horizon,
    box(fill: ink, inset: (x: 2.2mm, y: 0.9mm),
      archivo(8.6pt, weight: 700, tracking: 0.08em, fill: white, label)),
    ..if sub != none {
      (text(font: "Newsreader", style: "italic", size: 9pt, fill: muted, sub),)
    },
    line(length: 100%, stroke: 1.1pt + ink),
  ))

#let meta-line(a) = block(above: 1.2mm, below: 1.8mm,
  archivo(7.1pt, a.location + " · " + datum-kort(a.source_date)))

#let ontrunt(p) = {
  let woorden = p.trim().split(" ")
  if woorden.len() < 3 { return p.trim() }
  woorden.slice(0, woorden.len() - 1).join(" ") + "\u{a0}" + text(
    hyphenate: false, woorden.last())
}

#let paras(txt, size: 9.5pt, leading: 1.5pt, spacing: 6pt) = {
  set text(size: size)
  set par(justify: true, leading: leading, spacing: spacing)
  txt.split("\n\n").map(p => par(ontrunt(p))).join()
}

#let titel(a, size: 10.9pt) = block(
  sticky: true, above: 0pt, below: 0pt,
  text(font: "Fraunces", weight: 560, size: size, hyphenate: false,
    top-edge: 0.8em, bottom-edge: -0.2em)[
    #set par(justify: false, leading: 0.18em)
    #a.title
  ])

#let artikel(a) = {
  mark(kind: "article", pos: a.pos)
  titel(a)
  meta-line(a)
  paras(a.text)
  mark(kind: "article-end", pos: a.pos)
}

#let scheiding = block(above: 3.2mm, below: 3.4mm,
  line(length: 100%, stroke: 0.5pt + hair))

#let gebalanceerd(n, gutter, lijn, body) = layout(size => {
  let cw = (size.width - (n - 1) * gutter) / n
  let h = measure(block(width: cw, body)).height
  let doel = calc.ceil(h.pt() / n / lijn.pt()) * lijn + lijn
  block(height: doel, columns(n, gutter: gutter, body))
})

#let hero(a) = place(top, scope: "parent", float: true, clearance: 4.5mm,
  block(width: 100%, {
    mark(kind: "article", pos: a.pos)
    block(below: 0pt, text(font: "Fraunces", weight: 640, size: 19pt,
      hyphenate: false, top-edge: 0.85em, bottom-edge: -0.15em)[
      #set par(justify: false, leading: 0.12em)
      #a.title
    ])
    block(above: 1.6mm, below: 2.6mm,
      archivo(7.1pt, a.location + " · " + datum-kort(a.source_date)))
    gebalanceerd(3, 6mm, 11.5pt, paras(a.text, size: 10pt, spacing: 6.5pt))
    mark(kind: "article-end", pos: a.pos)
    v(3mm)
    line(length: 100%, stroke: 1.1pt + ink)
  }))

#let wx-icoon(code, size) = {
  let pre = "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"#121212\" stroke-width=\"1.3\" stroke-linecap=\"round\" stroke-linejoin=\"round\">"
  let zon = "<circle cx=\"12\" cy=\"12\" r=\"4\"/><path d=\"M12 3.2v2.2M12 18.6v2.2M3.2 12h2.2M18.6 12h2.2M5.8 5.8l1.5 1.5M16.7 16.7l1.5 1.5M18.2 5.8l-1.5 1.5M7.3 16.7l-1.5 1.5\"/>"
  let wolk = "<path d=\"M7 16.5a3.3 3.3 0 0 1 .3-6.6 4.6 4.6 0 0 1 9-.1 3.4 3.4 0 0 1 .3 6.7z\"/>"
  let wolkje = "<path d=\"M9 14.5a2.9 2.9 0 0 1 .3-5.8 4 4 0 0 1 7.8-.1 3 3 0 0 1 .3 5.9z\"/>"
  let zonnetje = "<circle cx=\"7.4\" cy=\"7.4\" r=\"2.6\"/><path d=\"M7.4 2v1.5M2 7.4h1.5M3.6 3.6l1 1M11.2 3.6l-1 1M3.6 11.2l1-1\"/>"
  let s = if code <= 1 {
    zon
  } else if code == 2 {
    zonnetje + "<path d=\"M11 19a3 3 0 0 1 .3-6 4.1 4.1 0 0 1 8-.1 3.1 3.1 0 0 1 .3 6.1z\"/>"
  } else if code == 3 {
    wolk
  } else if code in (45, 48) {
    wolkje + "<path d=\"M5.5 17.5h13M7.5 20.2h9\"/>"
  } else if code < 60 {
    wolkje + "<path d=\"M9.5 17.2l-.7 2.2M14 17.2l-.7 2.2\"/>"
  } else if code < 70 or (code >= 80 and code <= 82) {
    wolkje + "<path d=\"M8.2 17l-.9 3M11.9 17l-.9 3M15.6 17l-.9 3\"/>"
  } else if code < 90 {
    wolkje + "<circle cx=\"8.4\" cy=\"18.3\" r=\".5\"/><circle cx=\"12\" cy=\"19.5\" r=\".5\"/><circle cx=\"15.6\" cy=\"18.3\" r=\".5\"/>"
  } else {
    wolkje + "<path d=\"M12.6 15.5l-2.2 3.4h3l-2.2 3.4\"/>"
  }
  image(bytes(pre + s + "</svg>"), height: size)
}

#let weer-strook(w) = place(bottom, scope: "parent", float: true,
  clearance: 4.5mm, block(width: 100%, {
    mark(kind: "weather")
    kicker("Weer", sub: w.place + " — vandaag en de komende 5 dagen")
    grid(
      columns: (1fr,) * w.days.len(), column-gutter: 2mm,
      ..w.days.map(d => box(stroke: 0.5pt + hair, width: 100%,
        inset: (x: 1mm, top: 2mm, bottom: 2.2mm), {
          set align(center)
          block(below: 1.8mm, archivo(7pt, weight: 600, tracking: 0.05em,
            fill: if d.label == "Vandaag" { ink } else { muted }, d.label))
          block(below: 1.6mm, wx-icoon(d.code, 5.5mm))
          block(below: 1.2mm, {
            text(font: "Fraunces", weight: 560, size: 10.5pt,
              str(calc.round(d.tmax)) + "°")
            h(0.6mm)
            text(font: "Fraunces", size: 8.6pt, fill: muted,
              str(calc.round(d.tmin)) + "°")
          })
          archivo(6.4pt, weight: 500, tracking: 0.02em,
            if d.precip_prob == none { "—" } else { str(d.precip_prob) + "%" })
        })))
    block(above: 1.5mm, align(right,
      archivo(6.4pt, weight: 500, tracking: 0.05em,
        "Max./min. temperatuur · neerslagkans · bron Open-Meteo")))
    mark(kind: "weather-end")
  }))

#let illustratie(path, pos) = block(breakable: false, above: 3mm, below: 3mm, {
  mark(kind: "illustration", pos: pos)
  image(path, width: 100%)
  mark(kind: "illustration-end", pos: pos)
})

#let landschap = place(bottom, scope: "parent", float: true, clearance: 4mm,
  block(width: 100%, {
    mark(kind: "landscape")
    image("/assets/art/landschap.svg", width: 100%)
  }))

#let masthead = {
  block(width: 100%, above: 0pt, below: 4.5mm, {
    line(length: 100%, stroke: 1.5pt + ink)
    v(1.4mm)
    grid(columns: (1fr, auto), align: (left, right),
      archivo(7.5pt, weight: 500, tracking: 0.14em, datum-lang(ed.edition)),
      archivo(7.5pt, weight: 500, tracking: 0.14em, "Nr. " + str(ed.nr)))
    v(1.2mm)
    line(length: 100%, stroke: 0.75pt + ink)
    align(center, block(above: 2.8mm, below: 2.2mm, {
      box(baseline: 12%, image("/assets/art/zonnebloem.svg", height: 30pt))
      h(0.28em)
      text(font: "Fraunces", weight: 700, size: 40pt, tracking: -0.005em,
        top-edge: 0.72em, bottom-edge: -0.1em)[De Zonzijde]
    }))
    line(length: 100%, stroke: 0.75pt + ink)
  })
  mark(kind: "masthead-end")
}

#set page(paper: "a4", margin: 12mm)
#set text(font: "Newsreader", size: 9.5pt, fill: body-ink,
  top-edge: 0.75em, bottom-edge: -0.25em,
  lang: "nl", region: "NL", hyphenate: true,
  costs: (runt: 10000%, widow: 400%, orphan: 400%))
#set par(justify: true, leading: 1.5pt, spacing: 6pt)

#let scope-labels = (L: "Lokaal", R: "Regionaal", N: "Nationaal", I: "Wereld")
#let arts = ed.articles.sorted(key: a => a.pos)

#masthead

#columns(3, gutter: 6mm)[
  #hero(arts.at(0))
  #let rest = arts.slice(1)
  #for scope in ("L", "R", "N", "I") {
    let sel = rest.filter(a => a.scope == scope)
    if scope == "L" or sel.len() > 0 {
      kicker(scope-labels.at(scope))
    }
    for (i, a) in sel.enumerate() {
      if i > 0 { scheiding }
      if ed.illustration != none and ed.illustration_pos == a.pos {
        illustratie("/editions/" + ed.edition + "/" + ed.illustration, a.pos)
      }
      artikel(a)
    }
    if scope == "L" {
      weer-strook(ed.weather)
    }
  }
  #mark(kind: "content-end")
  #landschap
]

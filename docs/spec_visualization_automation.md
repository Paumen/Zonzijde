# Spec: Live visualization of the De Zonzijde pipeline

~~~
Version: v0.8
~~~

## Intent

A viewer watching a run understands and feels how a massive raw intake becomes one structured, coherent, finished edition.

This sentence is the tiebreaker whenever two requirements pull apart.

Running live against the pipeline is the end state. A recorded run may be used to prototype toward it; requirements marked *(proto only)* apply to replay alone.

## Invariants

- Mobile portrait.

## Buckets

Requirements sit in exactly one of three buckets and are stated in exactly one place.

- **States** — what the thing can be.
- **Logic** — how it behaves and what drives change.
- **UX** — what the viewer sees and does.

IDs are permanent from v1.0 onwards. A removed ID is retired, never reused.

---

## States

- **S11** — A topic groups one to four items and carries a werktitel; topics that reach the edition also eventually carry an *artikelkop*, an *artikellichaam*, and possibly an *illustratie*.
- **S21** — The edition under construction holds a growing set of placed articles across four pages.
- **S91** — *(proto only)* Playback runs at one speed at a time: x1 (default), x4, x8, or x12.

---

## Logic

- **L11** — A stage's on-screen duration follows real time, except that every stage plays for at least 60 seconds of x1 time — a floor that scales with playback speed — even when the real step was faster.
- **L12** — Within a stage, progress follows the real sub-events. Mandatory for stages over 90 seconds; best-effort below.
- **L13** — Time spent holding short stages at their minimum puts playback behind the real timeline; that lag is worked off during later long stages instead of added to total runtime.
- **L14** — Every item the run processed appears at the stage it entered; items the log holds only as a per-source count appear in the right number, individually, without titles.
- **L15** — An item keeps one identity from intake until it ends placed or dropped; at any moment it reads as in flight, dropped, or surviving into the next stage.

---

## UX

**Generic**

- **U11** — The scene reads as a newsroom at work, not as a dashboard or a log.
- **U12** — Any text on screen is real and accurate — never filler or gibberish. An item may be too small or too overlapped to read in dense moments, but whatever can be read, reads correctly.
- **U13** — The finished paper resembles De Zonzijde layout.
- **U14** — (mostly ) light themed.
- 
**Progression**

- **U21** — The whole run is one continuous view; the viewer never leaves it for another screen.
- **U22** — The size of the intake is felt as accumulating mass, and the narrowing of the stream is apparent as it happens in stages following.
- **U23** — Surviving topics visibly gain substance, stage by stage, from headline to source text to draft to finished article.
- **U24** — The edition is seen emerging as an object throughout the latter stahes, rather than appearing only at the end.

**Motion, animation, transitions**

- **U31** — Why an item was dropped is legible from the way it leaves, not only from a label on it, if an item needs explanatory text it failed
, and it does not linger once its departure has shown.
- **U32** — Items do not linger once their departure  and reason for it has shown.
- **U32** — When a model performs a stage, it is unmistakable that a model is working and what kind of work it is doing. If it needs explanatory text it failed
- **U33** — Where a stage records sub-events, the model's progress shows as its results arrive, batch by batch or article by article, rather than as a bare progress indicator.
- **U34** — Items travel to their outcome as the same objects, and movement from stage to stage is one continuous motion — no snapping, reshaping, or cross-fading of one arrangement into another.

---

## Non-goals

- Desktop or landscape layout.
- Sound.
- Accessibility and ARIA features.

---

## Appendix A — Reference data

### Fields present after each stage

| Stage | Fields |
|---|---|
| F1 | titel, samenvatting, bron, datum |
| F2 | unchanged |
| F3 | + score |
| F4 | + topic, werktitel (S21) |
| F5 | + brontekst, referentielinks, referentietekst |
| F6 | + invalshoek, lengterichtlijn |
| F7 | + draft artikellichaam (S21) |
| F8 | + final artikellichaam, artikelkop (S21) |
| F9 | + positie in de krant; illustratie (S21) |

---

## Appendix B — Illustrative examples

Non-binding. These show ideas that were in mind when a requirement was written or read; they are not instructions and can be ignored. They **might** help convey the context and intent of a requirement, when a requirement could be interpreted in different ways, or when the magnitude of intent is unclear. These examples may be used or drawn on for production, but using them **never** implies meeting the requirement on its own.

**UX — Motion, animation, transitions; newsroom, volume felt.**
Paper clippings fly in and pile up organically on a desk — overlapping, rotated, a growing heap. Any image that makes the intake or transitions feel physical might serve similar ends.

**UX — Progression.**
Auto-advance on a timeline, scroll-driven progression, segmented controls, horizontal swipes. These might contribute to avoiding a start-stop feel.

**UX — Motion, animation, transitions.**
Items outside the date window drift away; duplicates collapse into the item they duplicate; items move from top to bottom through the screen, through filters or a bar, where only surviving items pass through; they are rapidly sorted in different directions; stamps on cards; negative words highlighted on cards.

**UX — Motion, animation, transitions; model at work.**
F3 rapidly ticks through batches of 80, items being stamped positive, neutral, and negative.

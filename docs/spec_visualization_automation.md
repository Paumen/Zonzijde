# Spec: Live visualization of the De Zonzijde pipeline

~~~
Version: v0.8
status: draft
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
- **S12** — The edition under construction holds a growing set of placed articles across four pages.
- **S13** — *(proto only)* Playback runs at one speed at a time: x1 (default), x4, x8, or x12.

---

## Logic

- **L11** — A stage's on-screen duration follows real time, except that every stage plays for at least 60 seconds of x1 time — a floor that scales with playback speed — even when the real step was faster.
- **L12** — Within a stage, progress follows the real sub-events. Mandatory for stages over 90 seconds; best-effort below.
- **L13** — Time spent holding short stages at their minimum puts playback behind the real timeline; that lag is worked off during later long stages instead of added to total runtime.
- **L14** — Every item the run processed appears at the stage it entered; items the log holds only as a per-source count appear in the right number, individually, without titles.
- **L15** — An item keeps one identity from intake until it ends placed or dropped; at any moment it reads as in flight, dropped, or surviving into the next stage.

---

## UX

- **U11** — The scene reads as a newsroom at work, not as a dashboard or a log. Transitions and animations feel organically.
- **U12** — Any text on screen is real and accurate — never filler or gibberish. An item may be too small or too overlapped to read in dense moments, but whatever can be read, reads correctly.
- **U13** — The finished paper resembles De Zonzijde layout.
- **U14** — The whole run is one continuous view; the viewer never leaves it for another screen. Items travel to their outcome as the same objects, and movement from stage to stage is one continuous motion — no snapping, reshaping, or cross-fading of one arrangement into another. 
- **U15** — The size of the intake is felt as accumulating mass, and the narrowing of the stream is apparent as it happens in stages following.
- **U16** — The edition is seen emerging as an object throughout the latter stahes, rather than appearing only at the end. Surviving topics visibly gain substance, stage by stage, from headline to source text to draft to finished article. 
- **U17** — Why an item was dropped is legible from the way it leaves, if an item needs explanatory text it failed
, and it does not linger once its departure has shown.
- **U18** — Items do not linger once their departure  and reason for it has shown.
- **U19** — When a model performs a stage, it is unmistakable that a model is working and what kind of work it is doing. If it needs explanatory text it failed
- **U20** — Where a stage records sub-events, the model's progress shows as its results arrive, batch by batch or article by article, rather than as a bare progress indicator.

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
| F4 | + topic, werktitel |
| F5 | + brontekst, referentielinks, referentietekst |
| F6 | + invalshoek, lengterichtlijn |
| F7 | + draft artikellichaam |
| F8 | + final artikellichaam, artikelkop |
| F9 | + positie in de krant; illustratie |

---


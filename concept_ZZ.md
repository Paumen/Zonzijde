# De Zonzijde

## 1. Brief

People are worn out by negative news. It pours in non-stop through every channel — traditional, social, digital, and now AI-generated — and it is nearly impossible not to be dragged along. Negativity is partly wired into us, which is why "why is news always bad?" never gets a satisfying answer. But there is a saturation point, and more and more people are reaching it: consumed by everything going wrong everywhere, all the time, and numbed by fake news, clickbait, deepfakes, and sensationalism. The odd thing is that on many fronts life is measurably better than it was ten, twenty, or thirty years ago — yet people don't feel it, see it, or believe it. That is the negativity spiral. The rise of podcasts shows a desire to slow down and step out of the drama; growing numbers are breaking lifelong habits — switching off the TV news, sighing at yet another morning-paper page of violence, death, and war.

Technology now makes it feasible to sift vast numbers of sources for what is good. Partly that yields a different angle on world news: a reminder that not everything is bad, and that some things are far better than people assume. But the heart of it is the old, underserved thing: local news. Tangible — you could walk over and verify it yourself — trustworthy, and genuinely relevant. Something to connect over and talk about, and something no other channel gives you.

It is relief: something calm to start the day with. Not forced feel-good fillers, not to be confused with smaller local stories, which are not necessarily forced if reader has connection with it. But genuily good or positive news. It avoids reporting generic pieces on major or hyped news that will reach people anyways, unless it's a different perspective, like a clear zoom out on the topic, or zooming in on a specific part/thing. The paper moves outward in rings — local and personal, then regional, national, global. There's also room for more in depth pieces and more complex topics. On a day with time, energy, or a story that catches you, you read on; on any other day the other items are enough to start the morning. Any geo scope stories can still stretch into longer, in-depth pieces when the topic deserves the space.

## 2. Geo scope and focus

- **Lokaal** — Gemeente Wijchen: Wijchen, Alverna, Balgoij, Batenburg, Bergharen, Hernen, Laak, Leur, Niftrik, Woezik. De Berendonck, De Groene Heuvels, Loonse Waard, Wijchens Meer, Wijchens Ven, Bijsterhuizen.
- **Regionaal** — dorpen en steden rondom Wijchen: Beuningen, Druten, Heumen (Malden, Overasselt, Nederasselt), Grave, Land van Cuijk, Nijmegen; de Groene Metropoolregio Arnhem-Nijmegen, het Rijk van Nijmegen, het Land van Maas en Waal, Zuid-Gelderland, Gelderland. De Maas, de Waal, de Overasseltse en Hatertse Vennen, Heumensoord.
- **Nationaal** — de provincies, Nederland, Waddeneilanden, Nederlandse Antillen, Vlaanderen, Duitse grensregio (NRW). De Veluwe, de Waddenzee, Noordzee, Rijn, Maas, Waal, Schelde, IJsselmeer, Markermeer.
- **Internationaal** — buurlanden, Europa, werelddelen, landen. Oceanen, grote zeeën.

## 3. Content pipeline

Five steps, each narrowing the stream: fetch → filter → score → select → write.

### 3.1 Fetch

The web app fetches RSS feeds from a broad set of sources, covering all four scopes.

### 3.2 Fixed filter

Exact duplicates are removed, and a regex filter strips the most blatantly negative items along with promo content. Promo is additionally capped at score 0 in the next step — a deliberate double filter.

### 3.3 Scoring

Each remaining item is scored from −2 to +2 by a lightweight LLM (e.g. Gemini Flash-Lite) on the *direction* of the news, not its size or reach.

Prompt:

```
Je beoordeelt nieuwsberichten. Geef per bericht één score voor hoe goed of slecht het nieuws is voor mens, dier, natuur of samenleving:
-2 overduidelijk negatief (bijv. ramp, geweld, ernstige schade, leed, fraude)
-1 overwegend negatief
0 neutraal, gemengd, of te weinig informatie om te beoordelen
+1 overwegend positief
+2 overduidelijk positief (bijv. nieuw initiatief, geslaagde actie, lintje, vooruitgang, investering, prijstoekenning)
Meet alleen de richting van het nieuws, niet de omvang of het bereik.
Regel: promo-, marketing- en productgerichte items krijgen maximaal 0.
Antwoord uitsluitend met een JSON-object, met elk bericht precies één keer, bijvoorbeeld {"1": -1, "2": 2}.
```

### 3.4 Selection

Items scoring +1 or +2 go to a frontier LLM together with the brief (§1) and the prompt below. Output: a ranked top 5 per scope, in a single table.

Prompt:

```
For each of the 4 scopes, select the top 5 news topics most suitable for De Zonzijde. Present them in a single table with the columns bron, scope, titel, samenvatting, link — one row per source article, so a topic covered by multiple sources gets multiple rows.
```

### 3.5 Outline

The brief (§1), the edition specs (§4), the top-5 table, and the prompt below are sent to the LLM. 
Output: Which topics/items, which lengths, tone/angle, sources, type of article it should become, scope.


Prompt:

```
Open each link in the table below and read the content. If a link is blocked or there is not enough content, search for other sources. For each scope, pick the stories most suitable for De Zonzijde, in the numbers set by section 4.1 of the edition specs. Determine which stories are best suited for longer pieces. The front page with the best lokaal story; keep the strict ring order lokaal → regionaal → nationaal → internationaal throughout the edition. Vary how articles are written: not all aforistische kickers; write one piece a bit funnier/more ironic, use an analogy or metaphor, refer to another article in the edition, etc. 

Sources you must check:
- The same "Bron" earlier reportings on the topic/person/organization.
- If Lokaal: www.wegwijs.nl
- Regionaal: [TODO]
- Nationaal: [TODO]
- If Internationaal: https://www.aljazeera.com/
```

### 3.5 Content

Output: the full articles text of the edition.

```
Rules:
- Schrijf alle artikelen in het Nederlands.
- Do not refer to images, photos, or illustrations that would sit beside a story.
- Do not refer to De Zonzijde, "deze krant", its intent or goals, or why a story is in the paper.

```

### 3.6 Fact check / grammar / spelling / Title
...

### 3.7 Editorial
Consolidate articles into paper, cut/shorten, final ordering, overall balance and variety, etc. Put in krant.html, formatting etc. See 4.* chapters.


## 4. Edition specs

### 4.1 Content mix

Each of the four scopes contributes two items, three at most. Lengths are mixed: two or three longer pieces, two or three shorter ones, and three to five of standard length. Every article carries a title, a location, and the publication date of its source article, and typically runs three to eleven paragraphs. The body text of an edition totals roughly 2,800–3,400 words — about fifteen minutes of reading.

### 4.2 Layout & typography

The edition fills 3.5–4 A4 pages, set in three columns, with 12 mm margins all round and 6 mm between the columns. Body text stands at 9.5 pt on an 11 pt line height. Three rules guard the typesetting: no line consists of a single word, no column runs three lines or fewer, and no stretch of white space grows taller than three lines.

### 4.3 Fixed elements & illustrations

The masthead shows the paper's title with a hand-drawn sunflower in front of it. A weather strip follows directly after the lokaal news, typically landing on the second page. Each edition carries one custom illustration, set with an article — preferably on page 3 or 4, usually a regional or national one. The illustration is hand-drawn and one column wide, fits the Zonzijde theme and/or the article's topic, and stays free of color: minimalist work with fine lines, patterns, and strokes. The edition closes with a hand-drawn landscape at the bottom of the last page — flowers, a village in the distance, and a sun.

### 4.4 Optional elements

An edition may additionally carry a quote, a number of the week, or a side story set in a light grey block.

# 5. Stack

Probably mostly python.


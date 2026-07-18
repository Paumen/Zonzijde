# Run report — edition 2026-07-19

## Funnel

- window: 7 days (from 2026-07-12T00:00:00+02:00, SRC-4)
- S1 fetch: 559 feed items → 385 in window (23/23 feeds ok)
- S2 filter: 385 → 218 candidates (167 rejected)
- S3 score: 218 scored → 71 at +1/+2
- S4 select: 20 topics (22 source rows)
- S5 enrich: 22 source rows → 19 full texts (requests 17, playwright 0, alt-source 2); 3 topics dropped (PIPE-5)

## Feeds

| bron | items | in window | undated | error |
|---|---|---|---|---|
| Gem Wijchen | 20 | 1 | 0 | — |
| nieuws.nl | 54 | 13 | 0 | — |
| DG Wijchen | 30 | 30 | 0 | — |
| Gld | 50 | 50 | 0 | — |
| Gld RvN | 50 | 27 | 0 | — |
| DG | 30 | 30 | 0 | — |
| DG Binnen | 30 | 30 | 0 | — |
| Overheid | 12 | 12 | 0 | — |
| NOS J | 20 | 20 | 0 | — |
| NOS Alg | 20 | 20 | 0 | — |
| NOS Binnen | 20 | 20 | 0 | — |
| NOS Buiten | 20 | 20 | 0 | — |
| NOS Econ | 20 | 20 | 0 | — |
| NOS Sport | 20 | 20 | 0 | — |
| NOS Opm | 20 | 6 | 0 | — |
| NOS Cultuur | 20 | 6 | 0 | — |
| FTM | 10 | 10 | 0 | — |
| EW | 10 | 10 | 0 | — |
| HP | 50 | 6 | 0 | — |
| DW | 21 | 21 | 0 | — |
| DW Env | 20 | 6 | 0 | — |
| DW Science | 2 | 2 | 0 | — |
| Positive | 10 | 5 | 0 | — |

## Rejected (PIPE-2)

| reason | count |
|---|---|
| B1 | 62 |
| B2 | 71 |
| B3 | 9 |
| B4 | 4 |
| B5 | 19 |
| duplicate | 37 |

## Scores (PIPE-3)

model claude-haiku-4-5-20251001, prompt score.md v1

| score | count |
|---|---|
| -2 | 10 |
| -1 | 33 |
| 0 | 104 |
| +1 | 47 |
| +2 | 24 |

## Selected topics (PIPE-4)

| scope | rank | topic | bronnen |
|---|---|---|---|
| L | 1 | Lintjes voor Jan en Ingrid van den Brink | nieuws.nl |
| L | 2 | Batenburg Baroque Festival groeit verder | nieuws.nl |
| L | 3 | Patrijzenfamilie duikt op in tuin in Boven-Leeuwen | DG Wijchen |
| L | 4 | Opvallend weinig schoolverzuim rond vakantie in Wijchen | DG Wijchen |
| L | 5 | Zomerpret bij Museum Kasteel Wijchen | nieuws.nl |
| R | 1 | Vitesse mag na uitspraak Hoge Raad blijven voetballen | Gld, Gld |
| R | 2 | Michelinster voor de oude binnenstad van Zutphen | Gld |
| R | 3 | Arnhemse zanger gaat viraal met campagnelied | Gld |
| R | 4 | Barneveld bouwt nieuwe sporthal | Gld |
| R | 5 | Nieuwe spoorbrug in Molenhoek eindelijk veilig | DG Wijchen |
| N | 1 | Robotpak laat Daan weer lopen door eraan te denken | DG Binnen |
| N | 2 | Pepijn (17) zet zich ondanks beperking in voor anderen | DG Binnen |
| N | 3 | Geroofd Goudstikker-schilderij teruggevonden | NOS Cultuur |
| N | 4 | Harrie Jekkers ereburger van Den Haag | NOS Cultuur |
| N | 5 | Arnhemse schuldhulp-proef succesvol, krijgt vervolg | NOS Econ |
| I | 1 | Wat ging er deze week goed in de wereld | Positive |
| I | 2 | Steden worden slimmer met water tegen klimaatdruk | DW, DW Env |
| I | 3 | Forensisch onderzoek helpt strijd tegen wildlife-stroperij | Positive |
| I | 4 | Gemarginaliseerde groepen vinden verbinding via voetbal | Positive |
| I | 5 | India lanceert eerste private raket de ruimte in | DW |

## Full text (PIPE-5)

| scope | rank | topic | full text | status |
|---|---|---|---|---|
| L | 1 | Lintjes voor Jan en Ingrid van den Brink | 1/1 | ok |
| L | 2 | Batenburg Baroque Festival groeit verder | 1/1 | ok |
| L | 3 | Patrijzenfamilie duikt op in tuin in Boven-Leeuwen | 0/1 | **dropped** — no full text on any route |
| L | 4 | Opvallend weinig schoolverzuim rond vakantie in Wijchen | 0/1 | **dropped** — no full text on any route |
| L | 5 | Zomerpret bij Museum Kasteel Wijchen | 1/1 | ok |
| R | 1 | Vitesse mag na uitspraak Hoge Raad blijven voetballen | 2/2 | ok |
| R | 2 | Michelinster voor de oude binnenstad van Zutphen | 1/1 | ok |
| R | 3 | Arnhemse zanger gaat viraal met campagnelied | 1/1 | ok |
| R | 4 | Barneveld bouwt nieuwe sporthal | 1/1 | ok |
| R | 5 | Nieuwe spoorbrug in Molenhoek eindelijk veilig | 1/1 | alt coverage: https://www.spoorpro.nl/spoorbouw/2026/04/22/nieuw-viaduct-in-molenhoek-wordt-op-27-juni-op-zijn-plaats-gelegd/ |
| N | 1 | Robotpak laat Daan weer lopen door eraan te denken | 1/1 | alt coverage: https://drimble.nl/regio/zuid-holland/delft/107478810/robotpak-zorgt-voor-wereldprimeur-daan-kan-weer-lopen-door-er-alleen-aan-te-denken.html |
| N | 2 | Pepijn (17) zet zich ondanks beperking in voor anderen | 0/1 | **dropped** — no full text on any route |
| N | 3 | Geroofd Goudstikker-schilderij teruggevonden | 1/1 | ok |
| N | 4 | Harrie Jekkers ereburger van Den Haag | 1/1 | ok |
| N | 5 | Arnhemse schuldhulp-proef succesvol, krijgt vervolg | 1/1 | ok |
| I | 1 | Wat ging er deze week goed in de wereld | 1/1 | ok |
| I | 2 | Steden worden slimmer met water tegen klimaatdruk | 2/2 | ok |
| I | 3 | Forensisch onderzoek helpt strijd tegen wildlife-stroperij | 1/1 | ok |
| I | 4 | Gemarginaliseerde groepen vinden verbinding via voetbal | 1/1 | ok |
| I | 5 | India lanceert eerste private raket de ruimte in | 1/1 | ok |

Dropped L3 ('Patrijzenfamilie duikt op in tuin in Boven-Leeuwen'): searched 'Na 2,5 jaar wachten: patrijzenfamilie in de tuin', tried 0 alternative(s)

Dropped L4 ('Opvallend weinig schoolverzuim rond vakantie in Wijchen'): searched 'Opvallend weinig kinderen in Wijchen spijbelen voor vakantie', tried 0 alternative(s)

Dropped N2 ('Pepijn (17) zet zich ondanks beperking in voor anderen'): searched 'Pepijn laat zich niet tegenhouden door zijn beperking', tried 0 alternative(s)

# Run report — edition 2026-07-19

## Funnel

- window: 7 days (from 2026-07-12T00:00:00+02:00, SRC-4)
- S1 fetch: 510 feed items → 383 in window (22/23 feeds ok)
- S2 filter: 383 → 228 candidates (155 rejected)
- S3 score: 228 scored → 74 at +1/+2
- S4 select: 20 topics (21 source rows)
- S5 enrich: 21 source rows → 17 full texts (requests 17, playwright 0); 4 topics dropped (PIPE-5)

## Feeds

| bron | items | in window | undated | error |
|---|---|---|---|---|
| Gem Wijchen | 20 | 1 | 0 | — |
| nieuws.nl | 55 | 14 | 0 | — |
| DG Wijchen | 30 | 30 | 0 | — |
| Gld | 50 | 50 | 0 | — |
| Gld RvN | 50 | 30 | 0 | — |
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
| HP | 0 | 0 | 0 | HTTPError: 403 Client Error: Forbidden for url: https://www.hpdetijd.nl/rss |
| DW | 21 | 21 | 0 | — |
| DW Env | 20 | 6 | 0 | — |
| DW Science | 2 | 2 | 0 | — |
| Positive | 10 | 5 | 0 | — |

## Rejected (PIPE-2)

| reason | count |
|---|---|
| B1 | 53 |
| B2 | 65 |
| B3 | 6 |
| B4 | 5 |
| B5 | 15 |
| duplicate | 40 |

## Scores (PIPE-3)

model claude-haiku-4-5-20251001, prompt score.md v1

| score | count |
|---|---|
| -2 | 11 |
| -1 | 42 |
| 0 | 101 |
| +1 | 58 |
| +2 | 16 |

## Selected topics (PIPE-4)

| scope | topic | bronnen |
|---|---|---|
| L | Koninklijke onderscheiding voor Jan en Ingrid van den Brink | nieuws.nl |
| L | Molen en kasteel Hernen samen te bezoeken | nieuws.nl |
| L | 'Hoe is het?'-campagne zichtbaar tijdens Dag van Wijchen | nieuws.nl |
| L | Tijdelijke woonruimte voor jonge Wijchenaren | nieuws.nl |
| L | Wijchen kent opvallend weinig vakantiespijbelaars | DG Wijchen |
| R | Vitesse haalt opgelucht adem na uitspraak Hoge Raad | Gld, Gld |
| R | Studenten Rijn IJssel houden opleiding overeind | Gld |
| R | Batenburg Baroque Festival trekt meer bezoekers | nieuws.nl |
| R | Nieuw spoorbruggetje Molenhoek eindelijk veilig | DG Wijchen |
| R | Gladiolenteler Louise loopt eindelijk haar Vierdaagse | Gld RvN |
| N | Robotpak laat Daan weer lopen, wereldprimeur | DG Binnen |
| N | Pepijn (17) laat zich niet weerhouden door zijn beperking | DG Binnen |
| N | Arnhemse schuldenaanpak bewijst zich, vervolg komt er | NOS Econ |
| N | Politie moet illegaal verzamelde data alsnog vernietigen | FTM |
| N | Geroofd Goudstikker-schilderij duikt op na decennia | NOS Cultuur |
| I | Cubaanse dissident kunstenaar vrij na vijf jaar cel | DW |
| I | Steden worden slimmer met water en klimaataanpassing | DW Env |
| I | Forensische wetenschap helpt strijd tegen stroperij | Positive |
| I | Wekelijks goednieuwsoverzicht: successen wereldwijd | Positive |
| I | Voetbal biedt gemeenschap aan gemarginaliseerde groepen | Positive |

## Full text (PIPE-5)

| scope | topic | full text | status |
|---|---|---|---|
| L | Koninklijke onderscheiding voor Jan en Ingrid van den Brink | 1/1 | ok |
| L | Molen en kasteel Hernen samen te bezoeken | 1/1 | ok |
| L | 'Hoe is het?'-campagne zichtbaar tijdens Dag van Wijchen | 1/1 | ok |
| L | Tijdelijke woonruimte voor jonge Wijchenaren | 1/1 | ok |
| L | Wijchen kent opvallend weinig vakantiespijbelaars | 0/1 | **dropped** — no full text on any source row |
| R | Vitesse haalt opgelucht adem na uitspraak Hoge Raad | 2/2 | ok |
| R | Studenten Rijn IJssel houden opleiding overeind | 1/1 | ok |
| R | Batenburg Baroque Festival trekt meer bezoekers | 1/1 | ok |
| R | Nieuw spoorbruggetje Molenhoek eindelijk veilig | 0/1 | **dropped** — no full text on any source row |
| R | Gladiolenteler Louise loopt eindelijk haar Vierdaagse | 1/1 | ok |
| N | Robotpak laat Daan weer lopen, wereldprimeur | 0/1 | **dropped** — no full text on any source row |
| N | Pepijn (17) laat zich niet weerhouden door zijn beperking | 0/1 | **dropped** — no full text on any source row |
| N | Arnhemse schuldenaanpak bewijst zich, vervolg komt er | 1/1 | ok |
| N | Politie moet illegaal verzamelde data alsnog vernietigen | 1/1 | ok |
| N | Geroofd Goudstikker-schilderij duikt op na decennia | 1/1 | ok |
| I | Cubaanse dissident kunstenaar vrij na vijf jaar cel | 1/1 | ok |
| I | Steden worden slimmer met water en klimaataanpassing | 1/1 | ok |
| I | Forensische wetenschap helpt strijd tegen stroperij | 1/1 | ok |
| I | Wekelijks goednieuwsoverzicht: successen wereldwijd | 1/1 | ok |
| I | Voetbal biedt gemeenschap aan gemarginaliseerde groepen | 1/1 | ok |

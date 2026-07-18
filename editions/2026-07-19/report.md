# Run report — edition 2026-07-19

## Funnel

- window: 7 days (from 2026-07-12T00:00:00+02:00, SRC-4)
- S1 fetch: 559 feed items → 385 in window (23/23 feeds ok)
- S2 filter: 385 → 218 candidates (167 rejected)
- S3 score: 218 scored → 71 at +1/+2
- S4 select: 20 topics (22 source rows)
- S5 enrich: 22 source rows → 19 full texts (requests 17, playwright 0, alt-source 2); 3 topics dropped (PIPE-5)
- S6 outline: 11 slots, planned 2740–4260 words
- S7 write: 11 articles, 4907 words
- S8 review: 23 fact issue(s), 16 correction(s), 4843 words body text (ED-5 target 2800–3400)

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

## Edition plan (PIPE-6)

| pos | scope | length | type | topic | location | source date |
|---|---|---|---|---|---|---|
| 1 | L | long | feature | Batenburg Baroque Festival trekt meer bezoekers dan ooit | Batenburg | 2026-07-16 |
| 2 | L | short | profile | Koninklijke onderscheidingen voor Jan en Ingrid van den Brink | Groesbeek | 2026-07-13 |
| 3 | L | short | news | Zomeractiviteiten bij Museum Kasteel Wijchen | Wijchen | 2026-07-12 |
| 4 | R | long | news | Hoge Raad stelt Vitesse definitief in het gelijk tegen de KNVB | Arnhem | 2026-07-17 |
| 5 | R | standard | feature | Michelinster voor de Drogenapstoren en oude binnenstad van Zutphen | Zutphen | 2026-07-16 |
| 6 | R | short | profile | Arnhemse zanger Tim Koehoorn viraal met campagnelied over een praatje maken | Arnhem | 2026-07-16 |
| 7 | N | standard | profile | Robotpak laat Daan weer lopen door er alleen aan te denken | Delft | 2026-07-17 |
| 8 | N | standard | feature | Geroofd Goudstikker-schilderij duikt op na dertig jaar bij grof vuil | Amsterdam | 2026-07-13 |
| 9 | N | standard | zoom-in | Arnhemse schuldhulp-proef krijgt vervolg na succesvolle resultaten | Arnhem | 2026-07-15 |
| 10 | I | long | feature | Gemarginaliseerde groepen vinden verbinding via amateurvoetbal | Londen | 2026-07-15 |
| 11 | I | standard | news | India lanceert eerste privaat ontwikkelde raket de ruimte in | Sriharikota | 2026-07-18 |

Illustration (EL-3): slot 5 — De middeleeuwse Drogenapstoren in Zutphen, met een kleine Michelin-ster gemarkeerd op de gevel — hand-getekend, zwart-wit, minimalistische fijne lijnen
Optional element (EL-5): number — 34% — het percentage van de schuld dat gemiddeld werd afgelost bij de Arnhemse schuldhulp-proef, tegen 5 tot 10 procent bij een reguliere aanpak.

## Articles (PIPE-7/8)

| pos | title | words draft → reviewed | paragraphs |
|---|---|---|---|
| 1 | Batenburg klinkt vijf edities lang steeds voller | 428 → 414 | 7 |
| 2 | Lintjes voor het echtpaar achter de schermen van de Busband | 199 → 198 | 6 |
| 3 | Zomerpret bij Museum Kasteel Wijchen: speurtocht, waterbingo of juist even helemaal niets | 260 → 260 | 6 |
| 4 | Vitesse mag na Hoge Raad-uitspraak eindelijk weer over voetbal praten | 612 → 613 | 8 |
| 5 | De bewoonster van een toren met een Michelinster | 470 → 467 | 6 |
| 6 | Arnhemse zanger over de kunst van het praatje | 313 → 290 | 4 |
| 7 | Daan loopt weer, alleen door eraan te denken | 208 → 211 | 4 |
| 8 | Onooglijk paneel bij grof vuil blijkt geroofd Goudstikker-schilderij | 464 → 462 | 6 |
| 9 | In Immerloo II wordt vertrouwen teruggewonnen, schuld voor schuld | 492 → 489 | 6 |
| 10 | Op het veld van Athenlay speelt iedereen mee | 1039 → 1045 | 8 |
| 11 | India lanceert eerste privaat ontwikkelde raket de ruimte in | 422 → 394 | 6 |

## Correction log (PIPE-8)

- slot 1 (fact, WR-2): Eerste alinea noemde 'een ring van oude muren' rond Batenburg; dit detail komt niet voor in de brontekst en is verwijderd omdat het niet te verifiëren is (WR-2, geen toegevoegde informatie).
- slot 1 (fact, WR-2): 'die de ruimte weer liet vollopen met klank' bij het slotoptreden in de Nieuwe Sint-Victorkerk was een niet-brongesteunde toevoeging aan 'trok een groot publiek'; vervangen door een neutralere formulering die dicht bij de bron blijft.
- slot 1: Zinsconstructie in de laatste zin van de vijfde alinea vereenvoudigd ('trok voor die ene avond een groot publiek dat de ruimte weer liet vollopen met klank' → 'trok voor dat slotoptreden een groot publiek') voor helderheid en om dicht bij de brontekst te blijven.
- slot 2 (fact, WR-2): "Jan en Ingrid van den Brink uit Groesbeek" suggereerde dat het echtpaar in Groesbeek woont; de bron zegt alleen dat de Busband (en het jubileum) in Groesbeek is. Gecorrigeerd naar "dweilband Busband uit Groesbeek".
- slot 2 (fact, WR-2): "Zichtbaar op het podium waren ze zelden" was een verzonnen, specifiek beeld (podium) dat niet in de bron staat. Vervangen door de wel onderbouwde term "op de voorgrond", aansluitend bij de bronformulering "achter de schermen".
- slot 2 (fact, WR-2): "kregen twee mensen die zelden op de foto stonden" bevatte een niet-onderbouwde claim over fotomomenten; aangepast naar "zelden op de voorgrond staan", zonder toevoeging van niet-geverifieerde details.
- slot 2 (fact, WR-2): De kicker "Veertig jaar lang stille motor" suggereerde dat dit getal voor beiden gold, terwijl Jan veertig jaar lid is en Ingrid ruim vijfentwintig jaar; het getal is uit de kicker gehaald om een feitelijk onjuiste suggestie te voorkomen.
- slot 2 (fact, WR-2): "koninklijke onderscheiding" (enkelvoud) aangepast naar "onderscheidingen" (meervoud), conform de bron, aangezien beide personen een eigen onderscheiding kregen.
- slot 2: Kicker als apart, herkenbaar element laten staan maar getal (veertig jaar) verwijderd om overeen te stemmen met de feiten voor beide personen.
- slot 2: "Ze ontvingen de koninklijke onderscheiding" → "Ze ontvingen de koninklijke onderscheidingen" voor grammaticale/feitelijke consistentie met twee ontvangers.
- slot 2: "Zichtbaar op het podium waren ze zelden" herschreven naar "Op de voorgrond traden ze zelden" voor een vlottere, minder gekunstelde zin.
- slot 4 (fact, WR-2): Paragraaf 3: het citaat 'Ik hoop echt dat we na morgen een punt kunnen zetten...' werd door Sturing vooraf uitgesproken (in het bronartikel 'Vitesse wacht op het laatste fluitsignaal', gepubliceerd voor de zitting), niet 'na afloop' zoals het concept suggereerde. De zin 'Na afloop kon hij eindelijk de knoop doorhakken die hij zich al zo lang had gewenst' was een niet-brongesteunde en tegenstrijdige claim (het citaat zelf spreekt nog in de toekomstige/hopende vorm over 'morgen'), en is vervangen door een correcte tijdsaanduiding ('In aanloop naar de uitspraak had hij al gezegd...').
- slot 4 (fact, WR-2): Paragraaf 1/5: 'drie jaar procederen' en 'drie jaar lang met lede ogen toekeek' zijn in de bron niet als exacte, geverifieerde duur bevestigd (alleen Rozeboom's quote 'Het waren drie vervelende jaren' verwijst losjes naar de hele periode van onzekerheid, niet expliciet naar de duur van de rechtszaak). Om geen ongedekt feit te suggereren zijn deze specifieke tijdsaanduidingen afgezwakt naar 'jaren van procederen' en 'de afgelopen jaren'.
- slot 4: Paragraaf 3: transitiezin herschreven om de tijdlijn kloppend te maken (zie fact_issues) en 'zei hij' toegevoegd zodat duidelijk is dat het eerste citaat vóór de zitting werd gegeven.
- slot 4: Paragraaf 4: 'die de dag met een high-five van een supporter begon' vervangen door 'die op het trainingsveld een high-five van een supporter kreeg', om de gebeurtenis correct in de trainingsveld-scène te plaatsen zoals in de bron beschreven.
- slot 5 (fact, WR-2): "deze week" (paragraaf 1) is niet in de bron terug te vinden — de bron noemt alleen "donderdag" als moment van de sticker-plakactie, geen bevestiging dat de toekenning deze week plaatsvond. Verwijderd om geen ongedekte tijdsclaim te maken.
- slot 5 (fact, WR-2): "zeker sinds de volledige renovatie in 2023" suggereerde een door de bron niet gelegde causaliteit tussen de renovatie en het beeldbepalende karakter van de toren; de bron noemt beide feiten los van elkaar. Herschreven zonder gesuggereerd causaal verband.
- slot 5: Lichte herformulering van de zin over de renovatie/beeldbepalendheid voor vloeiendere en feitelijk nauwkeurigere aansluiting op het citaat van Schuitemaker.
- slot 6 (fact, WR-2): Openingszin '...is de laatste tijd vaak herkend op straat' overdreef de brontekst; Koehoorn zegt alleen 'Ik word wel herkend' (geen frequentie of locatie genoemd) — afgezwakt tot 'wordt wel eens herkend, vertelt hij'.
- slot 6 (fact, WR-2): 'hoewel hij zelf steeds herkend wordt' overdreef eveneens ('steeds' staat niet in de bron) — verwijderd/afgezwakt tot 'Toch valt het volgens Koehoorn zelf juist mee...'.
- slot 6 (fact, WR-2): 'In een couplet spreekt Tim...' voegde een songstructuurdetail (couplet) toe dat niet in de bron staat (die spreekt alleen van 'in het liedje') — gewijzigd naar 'In het lied spreekt Tim...'.
- slot 6 (fact, WR-2): De slotalinea over 'Jan en Ingrid van den Brink' en hun vereniging komt in het geheel niet voor in de brontekst — geen van deze namen of feiten wordt daar genoemd. Omdat dit niet te verifiëren is, is de alinea geschrapt en vervangen door een slot dat wel op de bron is gebaseerd.
- slot 6: Openingsalinea herschreven om dichter bij de brontekst te blijven (geen onbevestigde details over frequentie/locatie van herkenning).
- slot 6: 'couplet' vervangen door 'lied' voor consistentie met de brontekst.
- slot 6: Slotalinea herschreven zonder ongefundeerde feiten, met behoud van de afsluitende toon en strekking van het stuk (aansluitend op het beeld van het gesprek over de hond in de bus).
- slot 7: Eerste alinea herschreven: 'was dat lange tijd een dovemansoor' was een onjuist gebruikte uitdrukking (het idioom is 'aan dovemans oren praten/gericht zijn', en de zin miste een logisch onderwerp voor de vergelijking); vervangen door 'bleef het echter lange tijd bij die eerste stap', wat aansluit bij het beeld van 'denken is de eerste stap' verderop in de zin.
- slot 8 (fact, WR-2): Paragraaf 4 stelde dat de nazaten van Goudstikker "al decennia" naar de verdwenen werken zoeken; de bron zegt alleen dat zij dat na de oorlog probeerden, zonder claim over een decennialange, doorlopende zoektocht. Aangepast naar de brontekst.
- slot 8: Geen verdere taal- of stijlcorrecties nodig; de tekst was grammaticaal correct en de aanpak (scène met citaten, achtergrond over Goudstikker, ontknoping) bleef ongewijzigd.
- slot 9 (fact, WR-2): Misattributed quote: het origineel liet Petra zeggen dat Shaquina 'een reddende engel' is, maar in de bron noemt Shaquina juist coach Petra 'een reddende engel'. Gecorrigeerd naar de juiste spreker en strekking.
- slot 9 (fact, WR-2): 'coach Petra toegewezen' gewijzigd naar 'coach Petra' zonder 'toegewezen': de bron zegt alleen dat het gezin ondersteuning kreeg van coach Petra, niet dat die formeel werd 'toegewezen'.
- slot 9 (fact, WR-2): 'toeslagen waar gezinnen recht op hebben maar geen gebruik van maken' ingekort tot 'toeslagen waar gezinnen recht op hebben': de bron vermeldt niet expliciet dat gezinnen daar geen gebruik van maken, dat was een toegevoegde aanname.
- slot 9: Eerste alinea herschikt zodat het citaat over de 'reddende engel' aan de juiste spreker (Shaquina) wordt toegeschreven en niet meer als uitspraak van Petra over Shaquina wordt gelezen.
- slot 10 (fact, WR-2): De afstand tussen Afghanistan en Londen stond in het bronartikel als '4,000 miles' (mijl), niet kilometer. Het concept nam het getal 4.000 over maar veranderde stilzwijgend de eenheid naar kilometer, wat de afstand bijna 40% te klein maakt. Gecorrigeerd naar 'ruim zesduizend kilometer' (4.000 mijl ≈ 6.437 km).
- slot 10 (fact, WR-2): Het concept schreef 'Op de club staat een foto van haar...' terwijl de bron aangeeft dat de foto op de website van de club (athenlayfootballclub.org.uk) staat, niet fysiek op de clubaccommodatie. Gecorrigeerd naar 'Op de website van de club staat een foto van haar...'
- slot 10: Typefout 'bij bij de FA aangesloten clubs' hersteld tot 'bij clubs die zijn aangesloten bij de FA' voor correcte grammatica en leesbaarheid.
- slot 11 (fact, WR-2): Openingszin bevatte een verzonnen fysieke beschrijving ("acht meter minder dan een voetbalveld hoog, in ruim vier seconden weg van de aarde") die niet in de bronnen staat en bovendien in tegenspraak is met het latere, wel gebrande feit dat Vikram-1 circa 22 meter hoog is (een voetbalveld is ruim 100 meter). Verwijderd.
- slot 11 (fact, WR-2): "het Amerikaanse SpaceX" — de bron noemt SpaceX zonder nationaliteitsaanduiding ("Elon Musk's SpaceX"); "Amerikaanse" was toegevoegde informatie en is geschrapt conform de regel dat geen informatie wordt toegevoegd die niet in de bron staat, ook niet als ze algemeen bekend is.
- slot 11: Openingsalinea herschreven zonder de verzonnen maat- en tijdsaanduiding, met behoud van de beeldende toon ("zag geschiedenis vertrekken").
- slot 11: "Amerikaanse" geschrapt bij SpaceX in de slotalinea.

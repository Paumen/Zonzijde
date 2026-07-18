# Run report — edition 2026-07-19

## Funnel

- window: 7 days (from 2026-07-12T00:00:00+02:00, SRC-4)
- S1 fetch: 559 feed items → 385 in window (23/23 feeds ok)
- S2 filter: 385 → 218 candidates (167 rejected)
- S3 score: 218 scored → 71 at +1/+2
- S4 select: 20 topics (22 source rows)
- S5 enrich: 22 source rows → 19 full texts (requests 17, playwright 0, alt-source 2); 3 topics dropped (PIPE-5)
- S6 outline: 11 slots, planned 2740–4260 words
- S7 write: 11 articles, 5001 words
- S8 review: 40 fact issue(s), 28 correction(s), 4874 words body text (ED-5 target 2800–3400)

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
| 1 | Batenburg klinkt vol tijdens vijfde editie Baroque Festival | 482 → 436 | 7 |
| 2 | Koninklijke onderscheiding voor Jan en Ingrid van den Brink | 242 → 243 | 4 |
| 3 | Museum Kasteel Wijchen viert de zomervakantie met speurtochten, waterbingo, wandelingen en een prikkelarme middag | 257 → 232 | 4 |
| 4 | Vitesse haalt opgelucht adem na laatste fluitsignaal van de Hoge Raad | 599 → 590 | 7 |
| 5 | Toren van Laura Koppel krijgt Michelinster voor Zutphen | 495 → 487 | 7 |
| 6 | Arnhemse songwriter Tim Koehoorn gaat viraal met lied over praatjes maken | 292 → 296 | 4 |
| 7 | Robotpak leert Daan opnieuw lopen op wilskracht alleen | 197 → 175 | 4 |
| 8 | Bij grof vuil gevonden tweeluik uit collectie Goudstikker keert terug naar familie | 417 → 413 | 5 |
| 9 | Arnhemse schuldenproef krijgt vervolg na positieve resultaten | 482 → 477 | 8 |
| 10 | Op een grasveld in Londen speelt eindelijk mee wie altijd toekeek | 1145 → 1136 | 10 |
| 11 | Skyroot Aerospace lanceert eerste private Indiase raket | 393 → 389 | 6 |

## Correction log (PIPE-8)

- slot 1 (fact, WR-2): "Een paar straten verderop" (para 1) suggereerde dat Landgoed De Heerlijkheid in Appeltern vlakbij de Oude Sint-Victorkerk in Batenburg ligt; de bron noemt Appeltern als aparte locatie in de omgeving, niet als "een paar straten verderop". Aangepast naar een neutrale formulering.
- slot 1 (fact, WR-2): "Onder het houten gebinte van een schuur" (para 1) was een verzonnen architectonisch detail dat niet in de bron staat; verwijderd.
- slot 1 (fact, WR-2): "Zoals elk jaar" (para 2, bij het openingsconcert) suggereerde een vaste traditie over meerdere jaren die de bron niet bevestigt (de bron vergelijkt alleen met vorig jaar); verwijderd.
- slot 1 (fact, WR-2): Titel en slotzin van paragraaf 1 ("na vijf edities blijkt die kast steeds voller te klinken", en "voller dan ooit" in de titel) suggereerden een groeitrend over vijf edities; de bron onderbouwt alleen een vergelijking met vorig jaar (5% meer bezoekers). Titel en zin aangepast.
- slot 1 (fact, WR-2): Paragraaf 4 stelde dat het publiek kwam luisteren naar "wat gewone inwoners met wat oefentijd en toewijding samen konden neerzetten" — de bron noemt de zangers alleen als 'amateurzangers uit ruim 40', niet specifiek als inwoners van Batenburg, en vermeldt niets over hun oefentijd; deze toevoeging is verwijderd.
- slot 1 (fact, WR-2): Paragraaf 6 ("Dat zo'n klein stadje die klank vijf jaar op rij kan dragen en versterken") impliceerde een aanhoudende groei over vijf jaar die niet in de bron staat; herschreven naar een claim die alleen stelt dat het festival voor de vijfde keer succesvol werd georganiseerd, wat wel door de bron (vijfde editie) wordt gedekt.
- slot 1: Titel herschreven van "Batenburg klinkt voller dan ooit tijdens vijfde Baroque Festival" naar "Batenburg klinkt vol tijdens vijfde editie Baroque Festival" om de ongefundeerde superlatief te vermijden en dichter bij de brontekst te blijven.
- slot 1: Diverse kleine stilistische aanpassingen ter ondersteuning van de feitelijke correcties (zie fact_issues), zonder de opbouw of lengte van het artikel te wijzigen.
- slot 2 (fact, WR-2): Titel 'Nieuwe schrijvers achter de dweilband, veertig jaar lang' had niets met de inhoud te maken (geen 'schrijvers' in de bron) en is vervangen door een titel die de kern van het bericht dekt.
- slot 2 (fact, WR-2): Alinea 1 stelde dat locoburgemeester Gerrits hen 'benoemde tot Lid in de Orde van Oranje-Nassau'; volgens de bron is de benoeming passief vermeld ('zijn benoemd') en reikte Gerrits enkel de onderscheidingen uit. Gecorrigeerd naar: zij zijn benoemd, en Gerrits reikte de onderscheidingen uit.
- slot 2 (fact, WR-2): Slotalinea beweerde 'Veertig jaar lang zorgden zij ervoor dat...', wat impliceert dat dit voor beiden gold; Ingrid is echter pas ruim 25 jaar lid. De tijdsaanduiding is verwijderd en de zin is dichter bij de bronformulering ('Samen zorgen zij ervoor dat...') gebracht.
- slot 2 (fact, WR-2): De slotzin 'Nu speelde de Busband voor hen' is een door de bron niet ondersteund, verzonnen detail en is geschrapt.
- slot 2: Werkwoord 'benoemde' in de vierde alinea ('Gerrits benoemde tijdens de jubileumviering wat dat samen betekent') vervangen door 'stond ... stil bij wat dat samen betekent', wat correcter Nederlands is en aansluit bij de brontekst.
- slot 2: Kleine stilistische aanpassing in de slotzin om herhaling van 'zorgen'/'verliepen' en de foutieve tijdsclaim te vermijden.
- slot 3 (fact, WR-2): "Er zijn speurtochten door het kasteel" — de bron noemt alleen "speurtochten", zonder de locatie te specificeren; "door het kasteel" is een niet-onderbouwde toevoeging en is verwijderd.
- slot 3 (fact, WR-2): De zin "al is dat, de naam ten spijt, een uitje waar je juist middenin de zomervakantie vrijwillig voor kiest opgesloten te raken" is verwijderd: dit is speculatieve, grappig bedoelde eigen invulling over de escaperoute die niet in de bron staat en niet past bij een feitelijk, rustig artikel.
- slot 3: Zin over speurtochten en gewone openingstijden vloeiender geformuleerd ("Ook tijdens de gewone openingstijden, zonder speciale datum, is er voor kinderen genoeg te beleven") na het schrappen van de ongepaste toevoeging over de escaperoute.
- slot 4 (fact, WR-2): Titel: 'Vitesse wacht opgelucht op laatste fluitsignaal' impliceert dat de uitspraak nog moet komen, terwijl het hele artikel de viering na de uitspraak beschrijft. Titel aangepast naar 'Vitesse haalt opgelucht adem na laatste fluitsignaal van de Hoge Raad' om overeen te stemmen met de inhoud en de bronnen.
- slot 4 (fact, WR-2): 'in het hoofdgebouw van Vitesse op Papendal' — de bronnen noemen alleen 'het hoofdgebouw van Vitesse' (ARNHEM), niet Papendal. De toevoeging 'op Papendal' is niet door de bron gedekt en is verwijderd.
- slot 4 (fact, WR-2): 'Aanvoerder Alexander Büttner' — geen van beide bronnen noemt Büttner aanvoerder van Vitesse; dit gegeven is niet gedekt en is geschrapt.
- slot 4 (fact, WR-2): Het citaat van trainer Rehm ('op het veld en erbuiten') was een onnauwkeurige parafrase van twee los van elkaar staande citaten uit de bron ('Wij hebben hard gewerkt op het veld en buiten het veld ook'); gecorrigeerd naar een citaat dat de brontekst nauwkeuriger volgt.
- slot 4 (fact, WR-2): De zin 'Ulbe Rozeboom, die zelf thuis was gebleven en de uitspraak via de livestream volgde' stond in tegenspraak met de eerdere passage waarin Rozeboom bij Rehm's high-five op het trainingsveld staat (bron 1, na de uitspraak). De 'thuis blijven'-passage komt uit het vóór de uitspraak geschreven bronartikel en gaat over het niet afreizen naar Den Haag, niet over afwezigheid bij de training; de verwarrende, tegenstrijdige toevoeging is geschrapt.
- slot 4: Titel herschreven naar tegenwoordige/voltooide tijd zodat deze aansluit bij de inhoud (zie fact_issues).
- slot 4: 'op Papendal' geschrapt uit de eerste alinea.
- slot 4: 'Aanvoerder' voor Büttners naam geschrapt.
- slot 4: Rehm-citaat aangepast aan de exacte bronformulering ('op het veld en ook daarbuiten').
- slot 4: Zin over Rozeboom die 'thuis was gebleven en de uitspraak via de livestream volgde' vereenvoudigd tot een neutrale inleiding om de tegenstrijdigheid met eerdere alinea's te verhelpen.
- slot 5 (fact, WR-2): Alinea 1 bevatte een verzonnen, sfeervolle beschrijving van het uitzicht ('kijkt uit over de daken van Zutphen alsof de stad is neergezet op een ansichtkaart') die niet in de bron staat; vervangen door een omschrijving die wel steun vindt in de bron ('vrij uitzicht midden in de stad', later herhaald in alinea 4).
- slot 5 (fact, WR-2): 'kreeg het gebouw in 1983 een woonfunctie' aangepast naar 'kreeg het gebouw vanaf 1983 een woonfunctie', conform de formulering van de bron ('kreeg vanaf 1983 een woonfunctie').
- slot 5: 'gerenomeerd' gecorrigeerd naar de juiste spelling 'gerenommeerd'.
- slot 5: 'straatarm' vervangen door 'erg arm', dichter bij de bronformulering ('heel arm') en minder stellig dan 'straatarm'.
- slot 6 (fact, WR-2): Titel: "zomerhit" is niet onderbouwd door de bron (die spreekt alleen van een viraal campagnelied/video, niet van een hitlijst-succes) en oogt als clickbait; titel herschreven naar een neutrale, feitelijke formulering.
- slot 6 (fact, WR-2): Alinea 1: "regelmatig" bij het herkend worden is een toegevoegde frequentie die niet in de bron staat (bron: "Ik word wel herkend", zonder frequentie-aanduiding); verwijderd/verzacht.
- slot 6 (fact, WR-2): Alinea 2: "In dat laatste couplet" — de bron vermeldt niet dat het hondmoment in het laatste couplet zit; "laatste" is verzonnen en verwijderd.
- slot 6 (fact, WR-2): Alinea 2: "blijkt op de bank van een 14-jarige chihuahua" was onbegrijpelijk/incorrect geformuleerd en suggereerde een exacte leeftijd; bron zegt "ongeveer 14" — gecorrigeerd naar "ongeveer 14 jaar oud" en de zin vereenvoudigd.
- slot 6 (fact, WR-2): Alinea 2: de toevoeging "net zo veel aanspraak als in het lied" is een niet-onderbouwde vergelijking; teruggebracht tot wat de bron wél zegt (het hondje zorgt vaak voor aanspraak).
- slot 6 (fact, WR-2): Alinea 4: de volledige zin over 'Jan en Ingrid van den Brink' en hun vereniging is nergens in de brontekst terug te vinden — verzonnen/onbekende feiten, verwijderd.
- slot 6 (fact, WR-2): Alinea 4: "elders in deze editie" is een verwijzing naar de krant zelf, wat niet is toegestaan (PIPE-7); verwijderd samen met de erbij horende, niet-onderbouwde zin.
- slot 6: Titel herschreven: neutraler en dichter bij de brontitel, zonder clickbait-element "zomerhit".
- slot 6: Alinea 1: zin over herkenning op straat vereenvoudigd en dichter bij het brongegeven gebracht.
- slot 6: Alinea 2: zin over Lola herschreven voor duidelijkheid en correcte grammatica (het origineel was onleesbaar/onjuist geconstrueerd: "blijkt op de bank van...").
- slot 6: Alinea 4: herschreven zonder de verwijzing naar een ander artikel in de krant, met een afsluiting die wel steunt op het citaat "het maakt je net wat gelukkiger" uit de bron.
- slot 7 (fact, WR-2): Verwijderd: de zin 'Waar zijn eigen zenuwbanen de opdracht niet meer konden doorgeven, neemt de technologie die taak nu over.' Dit is een specifieke technische verklaring over falende zenuwbanen die niet in de brontekst staat en dus niet te verifiëren was; geschrapt in plaats van als onderbouwd feit te laten staan.
- slot 7 (fact, WR-2): 'jarenlang' (tweemaal, in alinea 1 en 4) verwijderd/afgezwakt naar 'lang' — de brontekst geeft geen tijdsduur voor hoe lang Daan al niet kon lopen of hoe lang hij zijn dwarslaesie al heeft; 'jarenlang' was een niet-onderbouwde specifieke claim.
- slot 7 (fact, WR-2): Alinea 1 herschreven zodat de zin niet langer suggereert dat er 'jarenlang geen route naar beweging' was (ongeverifieerde aanname over de voorgeschiedenis); nu aangesloten op wat de bron wél zegt: dat lopen door eraan te denken voor Daan door zijn dwarslaesie niet vanzelfsprekend is.
- slot 8 (fact, WR-2): Alinea 1 beweerde dat het paneel ‘in de weg stond’ in de kelder; de bron zegt juist het tegenovergestelde (“het lag niet in de weg”, daarom bleef het jarenlang staan) — gecorrigeerd naar ‘het stond niet in de weg’.
- slot 8 (fact, WR-2): ‘aan wiens muur het al jaren onverkoopbaar hing’ (alinea 2) is niet te herleiden uit de brontekst zelf (alleen uit een URL-fragment van het gelinkte Telegraaf-artikel, niet uit de meegeleverde broninhoud) en is daarom geschrapt.
- slot 8 (fact, WR-2): ‘die de topstukken hield en de rest liet veilen’ (alinea 4) overdrijft de bron, die spreekt van ‘een deel’ dat geveild werd, niet ‘de rest’ — gecorrigeerd naar ‘een deel’.
- slot 8 (fact, WR-2): John van den Heuvel werd in het concept ‘journalist’ genoemd; de brontekst vermeldt die functietitel niet expliciet, dus is dit weggehaald ten gunste van een neutrale omschrijving (‘van die krant’).
- slot 8: Titel herschreven: ‘Verweesd geachte tweeluik… keert terug naar erven’ was stijve, ongebruikelijke woordkeus (BR-5); vervangen door een rustige, concrete titel die aansluit bij het verhaal.
- slot 8: Alinea 1 herschreven om de herhaling van ‘kelder’ en de logisch verwarrende volgorde (eerst kelder, dan vondstverhaal, dan weer kelder) recht te trekken tot een heldere chronologie.
- slot 9 (fact, WR-2): Alinea 1: 'veel van hen hadden het vertrouwen in hulpverlening al lang verloren' claimde een aandeel ('veel') dat de bron niet noemt — de bron zegt alleen algemeen dat vertrouwen bij gezinnen die hulpverlening kwijt zijn moeilijk terug te winnen is, zonder dit te kwantificeren voor de Arnhemse deelnemers. Aangepast naar 'bij sommigen van hen' om niet meer te beweren dan de bron ondersteunt.
- slot 9 (fact, WR-2): Alinea 7: 'maar nog geen gebruik van maken' bij de toeslagen was een toevoeging die niet letterlijk in de bron staat (de bron zegt alleen dat gewezen wordt op toeslagen waar gezinnen recht op hebben, zonder te stellen dat ze daar nu geen gebruik van maken); verwijderd.
- slot 9: Zin 'Dat het vertrouwen zo diep beschadigd was, maakte de eerste stap vaak het moeilijkst' is een verbindende overgangszin gebleven, maar staat nu duidelijker los van de erop volgende Benrida-quote zodat niet de indruk ontstaat dat het een letterlijk citaat is.
- slot 9: Kleine stilistische gladstrijking in alinea 1 voor consistentie met de rest van het artikel (geen inhoudelijke wijziging).
- slot 10 (fact, WR-2): Sian Elliot: het concept sprak van 'zelf spelen mocht ze nooit', wat suggereert een verbod. De bron zegt alleen dat ze 'nooit de kans had gekregen' (never had the opportunity) — geen sprake van een verbod. Gecorrigeerd naar 'zelf spelen had ze nooit de kans gehad'.
- slot 10 (fact, WR-2): Overtreding van PIPE-7: de zin 'Op een bekende foto op de website van haar club houdt ze in blauw tenue en regenboogsokken de regenboogvlag omhoog' verwees expliciet naar een foto/afbeelding. Herschreven zonder verwijzing naar de foto, met behoud van het wél door de bron ondersteunde feit dat ze de regenboogvlag omhoog heeft gehouden.
- slot 10: 'teammate' (Engels) vervangen door 'ploeggenote'.
- slot 10: 'dubbel zo oud vaak' herschreven naar 'vaak dubbel zo oud' voor correcte Nederlandse woordvolgorde.
- slot 10: 'die voor het westen van Londen bij Actonians speelt' herschreven naar 'die in West-Londen voor Actonians speelt' voor vlottere formulering.
- slot 10: Inconsistente naamgeving 'Football Supporters' Association' / 'Football Supporters Association' gelijkgetrokken naar 'Football Supporters Association' in beide vermeldingen.
- slot 11 (fact, WR-2): Titel: 'zandeiland' (zandeiland Sriharikota) is niet in de bron te vinden; de bron noemt alleen 'island' / 'Sriharikota island' zonder vermelding van zand. Titel herschreven zonder deze toevoeging.
- slot 11 (fact, WR-2): Alinea 2: 'Wie het bereikt, is de derde raket ooit' is feitelijk onjuist en grammaticaal krom - de bron zegt dat India (het land), niet de raket, het derde land is na de VS en China dat een privaat ontwikkelde raket de ruimte in stuurde. Gecorrigeerd naar 'Daarmee wordt India het derde land waarvan een privaat ontwikkelde raket de ruimte in gaat, na de Verenigde Staten en China.'
- slot 11 (fact, WR-2): Alinea 6: 'het Amerikaanse SpaceX' - de bron noemt SpaceX niet als 'Amerikaans'; deze toevoeging is niet met de bron te onderbouwen en is verwijderd.
- slot 11: Titel herschreven naar 'Skyroot Aerospace lanceert eerste private Indiase raket' - rustiger, concreter en zonder ongefundeerde toevoeging ('zandeiland').
- slot 11: Zin in alinea 2 herschreven voor grammaticale duidelijkheid en juiste feitelijke weergave (land i.p.v. raket als 'derde').
- slot 11: In alinea 4 'jongeren' aangevuld met 'talloze' om dichter bij de brontekst ('countless youngsters') te blijven.
- slot 11: In alinea 6 'het Amerikaanse SpaceX' ingekort tot 'SpaceX'.

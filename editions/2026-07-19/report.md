# Run report — edition 2026-07-19

## Funnel

- window: 7 days (from 2026-07-12T00:00:00+02:00, SRC-4)
- S1 fetch: 559 feed items → 385 in window (23/23 feeds ok)
- S2 filter: 385 → 218 candidates (167 rejected)
- S3 score: 218 scored → 71 at +1/+2
- S4 select: 20 topics (22 source rows)
- S5 enrich: 22 source rows → 17 full texts (requests 17, playwright 0); 5 topics dropped (PIPE-5)
- S6 outline: 11 slots, planned 3050–5800 words
- S7 write: 11 articles, 4354 words
- S8 review: 23 fact issue(s), 23 correction(s), 4284 words body text (ED-5 target 2800–3400)

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
| L | 3 | Patrijzenfamilie duikt op in tuin in Boven-Leeuwen | 0/1 | **dropped** — no full text on any source row |
| L | 4 | Opvallend weinig schoolverzuim rond vakantie in Wijchen | 0/1 | **dropped** — no full text on any source row |
| L | 5 | Zomerpret bij Museum Kasteel Wijchen | 1/1 | ok |
| R | 1 | Vitesse mag na uitspraak Hoge Raad blijven voetballen | 2/2 | ok |
| R | 2 | Michelinster voor de oude binnenstad van Zutphen | 1/1 | ok |
| R | 3 | Arnhemse zanger gaat viraal met campagnelied | 1/1 | ok |
| R | 4 | Barneveld bouwt nieuwe sporthal | 1/1 | ok |
| R | 5 | Nieuwe spoorbrug in Molenhoek eindelijk veilig | 0/1 | **dropped** — no full text on any source row |
| N | 1 | Robotpak laat Daan weer lopen door eraan te denken | 0/1 | **dropped** — no full text on any source row |
| N | 2 | Pepijn (17) zet zich ondanks beperking in voor anderen | 0/1 | **dropped** — no full text on any source row |
| N | 3 | Geroofd Goudstikker-schilderij teruggevonden | 1/1 | ok |
| N | 4 | Harrie Jekkers ereburger van Den Haag | 1/1 | ok |
| N | 5 | Arnhemse schuldhulp-proef succesvol, krijgt vervolg | 1/1 | ok |
| I | 1 | Wat ging er deze week goed in de wereld | 1/1 | ok |
| I | 2 | Steden worden slimmer met water tegen klimaatdruk | 2/2 | ok |
| I | 3 | Forensisch onderzoek helpt strijd tegen wildlife-stroperij | 1/1 | ok |
| I | 4 | Gemarginaliseerde groepen vinden verbinding via voetbal | 1/1 | ok |
| I | 5 | India lanceert eerste private raket de ruimte in | 1/1 | ok |

## Edition plan (PIPE-6)

| pos | scope | length | type | topic | location | source date |
|---|---|---|---|---|---|---|
| 1 | L | long | profile | Lintjes voor Jan en Ingrid van den Brink | Groesbeek | 2026-07-13 |
| 2 | L | standard | feature | Batenburg Baroque Festival groeit verder | Batenburg | 2026-07-16 |
| 3 | L | short | zoom-in | Zomerpret bij Museum Kasteel Wijchen | Wijchen | 2026-07-12 |
| 4 | R | standard | news | Vitesse mag na uitspraak Hoge Raad blijven voetballen | Arnhem | 2026-07-17 |
| 5 | R | standard | profile | Arnhemse zanger gaat viraal met campagnelied | Arnhem | 2026-07-16 |
| 6 | R | short | news | Barneveld bouwt nieuwe sporthal | Barneveld, Terschuur | 2026-07-16 |
| 7 | N | long | feature | Geroofd Goudstikker-schilderij teruggevonden | Amsterdam | 2026-07-13 |
| 8 | N | standard | profile | Harrie Jekkers ereburger van Den Haag | Den Haag | 2026-07-12 |
| 9 | N | standard | zoom-in | Arnhemse schuldhulp-proef succesvol, krijgt vervolg | Arnhem | 2026-07-15 |
| 10 | I | long | zoom-out | Steden worden slimmer met water tegen klimaatdruk | diverse steden wereldwijd | 2026-07-17 |
| 11 | I | short | news | India lanceert eerste private raket de ruimte in | Sriharikota, India | 2026-07-18 |

Illustration (EL-3): slot 7 — Een oud houten schildersdoek-paneel, half tussen grofvuil en teruggevonden, met fijne lijnen die het patina en de scheur in het hout tonen — minimalistisch, zwart-wit, handgetekend
Optional element (EL-5): number — 34% — het gemiddelde percentage schuld dat de Arnhemse schuldhulp-proef bij kwetsbare gezinnen wist af te lossen (bron N5)

## Articles (PIPE-7/8)

| pos | title | words draft → reviewed | paragraphs |
|---|---|---|---|
| 1 | Jan en Ingrid van den Brink krijgen koninklijke onderscheiding tijdens jubileum Busband | 377 → 351 | 6 |
| 2 | Batenburg Baroque Festival trekt opnieuw meer publiek | 417 → 398 | 6 |
| 3 | Zomerprogramma vol spel en geschiedenis bij Museum Kasteel Wijchen | 228 → 229 | 4 |
| 4 | Vitesse mag blijven voetballen na uitspraak Hoge Raad | 474 → 470 | 6 |
| 5 | Arnhemse zanger gaat viraal met lied over een praatje | 336 → 342 | 5 |
| 6 | Raad Barneveld stemt in met sporthal voor Terschuur | 247 → 244 | 5 |
| 7 | Geroofd Goudstikker-schilderij duikt na dertig jaar in kelder weer op | 507 → 507 | 6 |
| 8 | Harrie Jekkers ereburger van Den Haag na laatste voorstelling | 452 → 454 | 5 |
| 9 | Correctie: schuldenproef Arnhem | 568 → 542 | 9 |
| 10 | Steden leren ademen met water | 485 → 484 | 5 |
| 11 | India lanceert eerste private raket de ruimte in | 263 → 263 | 4 |

## Correction log (PIPE-8)

- slot 1 (fact, WR-2): Verwijderd: 'wisten Jan en Ingrid van den Brink nog van niets' en 'Tussen de feestelijkheden voor de jarige vereniging door werden zij naar voren geroepen' — de bron vermeldt geen verrassingselement of de manier waarop het paar naar voren werd geroepen; dit was een toegevoegde aanname, niet door de bron gedekt (WR-2/ED-4).
- slot 1 (fact, WR-2): Verwijderd/verzacht: de beschrijving 'met muziek en de sfeer van een vereniging die met zichzelf mag vieren' — de bron bevestigt geen specifieke feestinvulling; vervangen door een neutralere formulering die alleen steunt op wat de bron wél meldt (dat de uitreiking tijdens de jubileumviering plaatsvond).
- slot 1 (fact, WR-2): In het citaat van Gerrits stond 'binnen de vereniging'; de bron citeert 'binnen de Busband'. Gecorrigeerd naar de letterlijke bronformulering, aangezien het een citaat betreft.
- slot 1: Eerste alinea herschreven zodat de gebeurtenis (uitreiking tijdens jubileumfeest) chronologisch en feitelijk overeenkomt met de bron, zonder ongedekte aannames over verrassing of het moment van naar voren roepen.
- slot 1: Tweede alinea aangepast om alleen bronvaste elementen te behouden (de uitreiking vond plaats tijdens de jubileumviering), met behoud van de stijlkeuze (reflectie op wat er te vieren viel).
- slot 1: Kleine spellingscorrectie: 'evenlang' naar 'even lang'.
- slot 2 (fact, WR-2): Titel: 'trekt vijfde jaar op rij meer publiek' suggereert vijf opeenvolgende jaren van groei; de bron meldt alleen dat déze (vijfde) editie 5 procent meer bezoekers trok dan vorig jaar. Titel aangepast naar 'trekt opnieuw meer publiek'.
- slot 2 (fact, WR-2): Alinea 1: 'een van de kleinste vestingstadjes van Nederland' staat niet in de bron (die spreekt alleen van 'het historische stadje Batenburg') en is ongevraagd toegevoegde informatie; verwijderd/vervangen door 'het historische stadje Batenburg'.
- slot 2 (fact, WR-2): Alinea 2: 'buiten de vestingwallen' veronderstelt vestingwallen die de bron niet vermeldt; vervangen door 'buiten Batenburg zelf'.
- slot 2 (fact, WR-2): Alinea 2: 'volgens de organisatie' bij de zin over locatie en muziek die naadloos samenkwamen is een toeschrijving die niet in de bron staat (de bron formuleert dit als constatering, niet als citaat/mening van de organisatie); verwijderd.
- slot 2 (fact, WR-2): Slotalinea: 'een van de kleinste stadjes van het land' is, net als in alinea 1, een ongesourcete superlatief-claim; verwijderd/herformuleerd naar 'ook verder dan Batenburg zelf'.
- slot 2: Titel herschreven zodat de tijdsclaim overeenkomt met wat de bron daadwerkelijk meldt (groei dit jaar, niet vijf jaar op rij).
- slot 2: Ongesourcete superlatieven over de grootte/status van Batenburg als vestingstadje verwijderd op twee plekken.
- slot 2: Toeschrijving 'volgens de organisatie' geschrapt omdat niet in de bron onderbouwd.
- slot 3: Titel herschreven naar een rustigere, concretere formulering ('Zomerprogramma vol spel en geschiedenis bij Museum Kasteel Wijchen') — de oorspronkelijke titel combineerde 'spel' en 'watersnood' op een grammaticaal onlogische manier ('combineert spel en watersnood van 1926').
- slot 3: 'kunnen kinderen tijdens de openingstijden bovendien los met speurtochten' herschreven naar 'kunnen kinderen tijdens de openingstijden bovendien zelfstandig deelnemen aan speurtochten' — helderder Nederlands.
- slot 3: 'wie liever met het hele gezelschap op pad gaat' aangepast naar 'wie liever met familie en vrienden op pad gaat', in lijn met de brontekst ('met familie en vrienden aan de escaperoute').
- slot 4 (fact, WR-2): "Op Papendal klonk iets na tienen gejuich..." — de bron plaatst dit in het hoofdgebouw van Vitesse, niet op Papendal; gecorrigeerd naar 'In het hoofdgebouw van Vitesse'.
- slot 4 (fact, WR-2): "Trainer Rüdiger Rehm, die naast de rechtszaal ook gewoon een selectie moest samenstellen..." — dit detail staat niet in de bronnen en is verwijderd.
- slot 4 (fact, WR-2): De Sturing-quote over het Gerechtshof in september was in de bron langer en bevatte tussenliggende zinnen over Utrecht/Arnhem die al elders in het artikel staan; de quote werd ingekort weergegeven alsof die aaneengesloten is uitgesproken. Aangevuld met '(...)' om de inkorting te markeren en 'in Arnhem' toegevoegd, conform de bron.
- slot 4: 'kort gedingen' (meervoud) in de slotalinea gewijzigd naar 'een kort geding' (enkelvoud), aangezien de bronnen slechts één kort geding (in Utrecht) noemen.
- slot 5 (fact, WR-2): Titel 'scoort landelijke hit' overstate de feiten: de bron spreekt van een viraal gaand campagnelied, niet van een (hit)notering. Titel aangepast naar 'Arnhemse zanger gaat viraal met lied over een praatje'.
- slot 5 (fact, WR-2): Zin 'Het hondje bleek in de praktijk een aanleiding waar mensen makkelijk op afstapten, en dat detail werd de kern van het lied' overstatede: de bron zegt alleen dat het hondje vaak voor aanspraak zorgt, niet dat dit 'de kern van het lied' werd. Herschreven naar wat de bron wel ondersteunt, met het bronscitaat 'Het zijn simpele, uit het leven gegrepen momenten' toegevoegd ter onderbouwing.
- slot 5: Bindweefsel-quote iets losser geparafraseerd teruggezet dichter bij de brontekst ('het maakt je net wat gelukkiger... na een praatje') in plaats van een vrije samenvatting.
- slot 5: Slotzin van alinea 3 herschreven om aan te sluiten bij het bronscitaat in plaats van een ongedekte samenvatting.
- slot 6 (fact, WR-2): Laatste zin oorspronkelijk: 'In de komende periode werken gemeente en initiatiefnemers het ontwerp... verder uit' — de bron noemt geen specifieke uitvoerders ('wordt... verder uitgewerkt'), dus de toegeschreven actoren zijn geschrapt om geen niet-onderbouwde claim te introduceren.
- slot 6: Laatste zin herschreven naar de lijdende vorm ('worden ... verder uitgewerkt') in plaats van de actieve vorm met specifiek genoemde actoren, om dichter bij de brontekst te blijven.
- slot 7 (fact, WR-2): Derde alinea: het schilderij zei 'de rest liet veilen' over wat Göring niet zelf hield, terwijl de bron zegt dat hij slechts 'een deel liet veilen'. 'De rest' suggereert dat werkelijk alles wat Göring niet hield geveild werd, wat de bron niet bevestigt. Gecorrigeerd naar 'een deel liet veilen'.
- slot 7: Titel herschreven: 'Dertig jaar zoek geraakt schilderij komt terug bij erven Goudstikker' bevatte een spelfout ('zoek geraakt' moet 'zoekgeraakt' zijn als het al gebruikt zou worden) en suggereerde bovendien dat het schilderij dertig jaar zoek was, terwijl het dertig jaar in een kelder stond nadat het al veel langer (sinds de roof in 1940) buiten beeld van de Goudstikker-erfgenamen was. Nieuwe titel sluit aan bij de bronkop en is feitelijk preciezer: 'Geroofd Goudstikker-schilderij duikt na dertig jaar in kelder weer op'.
- slot 8 (fact, WR-2): Geen feitelijke fouten aangetroffen: alle namen, data, cijfers en citaten (leeftijd 75, geboortejaar 1951, Schilderswijk/Moerwijk, oprichting Klein Orkest in 1978, uiteenvallen in 1985, solodebuut in 1988, terugkeer in 2015, opvolging van Paul van Vliet in 2018, citaten van Van Zanen) komen overeen met de bronreportage.
- slot 8 (fact, WR-2): Kleine precisering: 'waar hij een huis bouwde' is aangepast naar 'waar hij een huis liet bouwen', omdat de bron vermeldt dat Jekkers dit huis samen met een toenmalige partner liet bouwen en na afloop van die relatie aanhield; het artikel noemt die relatie niet expliciet (buiten scope/lengte), maar de herformulering voorkomt de suggestie dat hij het eigenhandig en alleen bouwde.
- slot 8: Grammaticale verbetering: 'samenwerkingen die zijn hele loopbaan zouden blijven terugkeren' aangevuld tot 'samenwerkingen die gedurende zijn hele loopbaan zouden blijven terugkeren' voor een correcte zinsconstructie.
- slot 8: Komma toegevoegd na 'Moerwijk' in de eerste bijzin van paragraaf 2 voor de leesbaarheid.
- slot 8: 'waar hij een huis bouwde' gewijzigd in 'waar hij een huis liet bouwen' om preciezer aan te sluiten bij de bron zonder de omvang van het stuk te vergroten.
- slot 9 (fact, WR-2): Slotalinea verwijderde: de zin over 'deze editie' en een 'viraal campagnelied van een Arnhemse zanger' verwees naar een ander artikel in de krant zelf en noemde een feit (het lied, de zanger) dat in de brontekst helemaal niet voorkomt — verzonnen informatie. Bovendien is een verwijzing naar de krant/editie zelf niet toegestaan (PIPE-7). De hele zin is geschrapt; niets ter vervanging toegevoegd om de lengte/planning niet te verstoren.
- slot 9 (fact, WR-2): 'volgens de initiatiefnemers het armste postcodegebied van Nederland' herschreven: de bron plaatst 'het armste postcodegebied van Nederland' tussen aanhalingstekens maar noemt geen 'initiatiefnemers' als bron van die claim — die toeschrijving was verzonnen. Nu als aangehaalde typering zonder onderbouwde bron weergegeven.
- slot 9 (fact, WR-2): 'volledig schuldenvrij' afgezwakt tot 'schuldenvrij': de bron zegt alleen dat de 21 huishoudens 'schuldenvrij' zijn, niet expliciet 'volledig' schuldenvrij; het woord 'volledig' voegde een nuance toe die niet in de bron staat.
- slot 9: Tweede alinea: 'kreeg ze steun' aangepast naar 'kreeg het gezin steun', omdat de bron aangeeft dat het gezin (niet alleen Shaquina) steun kreeg ('kregen ze... ondersteuning').
- slot 9: 'ervan af te komen' verduidelijkt tot 'van de schulden af te komen' voor leesbaarheid, aansluitend bij de bron ('hun schulden af te lossen').
- slot 10 (fact, WR-2): Paragraaf 1 noemde 'Egyptische koraalriffen', maar de bron spreekt over kustbescherming en zeeschildpadden aan de Rode Zeekust, niet over koraalriffen; dit is gecorrigeerd naar 'de Egyptische Rode Zeekust' zodat het klopt met de rest van het artikel en de bron.
- slot 10 (fact, WR-2): 'Wat lange tijd gold als een noodoplossing voor uiterste nood' was een uitweiding op de bron ('last-resort solution'); ingekort naar 'laatste redmiddel' om niet meer te claimen dan de bron zegt.
- slot 10: Kleine stilistische bijstelling in paragraaf 3 voor beknoptheid en aansluiting bij de brontekst ('laatste redmiddel' i.p.v. 'noodoplossing voor uiterste nood').
- slot 11 (fact, WR-2): Paragraaf 3: het citaat over 'talloze jongeren aanmoedigen groter te dromen' hoort in de bron bij 'this achievement' (de lancering), niet bij 'de groeiende rol van private bedrijven'. De zin is aangepast zodat het duidelijk de prestatie/lancering is die jongeren aanmoedigt, niet de groeiende private sector op zich.
- slot 11: Titel vereenvoudigd van 'eerste eigen private raket' naar 'eerste private raket' — 'eigen' was overbodig naast 'private' en maakte de titel stroever.
- slot 11: Eerste zin herschreven om de dubbele herhaling van het woord 'raket' te verwijderen ('met de raket Vikram-1 ... raket de ruimte in' werd 'met de Vikram-1 ... raket de ruimte in').
- slot 11: Bijstelling 'Mission Aagaman gedoopt naar' herschikt tot 'gedoopt "Mission Aagaman" naar' voor natuurlijker Nederlands.

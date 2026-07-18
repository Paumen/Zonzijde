# Run report — edition 2026-07-19

## Funnel

- window: 7 days (from 2026-07-12T00:00:00+02:00, SRC-4)
- S1 fetch: 559 feed items → 385 in window (23/23 feeds ok)
- S2 filter: 385 → 218 candidates (167 rejected)
- S3 score: 218 scored → 71 at +1/+2
- S4 select: 20 topics (22 source rows)
- S5 enrich: 22 source rows → 19 full texts (requests 17, playwright 0, alt-source 2); 3 topics dropped (PIPE-5)
- S6 outline: 11 slots, planned 2740–4260 words
- S7 write: 11 articles, 3798 words
- S8 review: 37 fact issue(s), 25 correction(s), 3616 words body text (ED-5 target 2800–3400)

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
| 1 | Batenburg Baroque Festival trekt bij vijfde editie meer publiek | 448 → 358 | 7 |
| 2 | Lintje voor het echtpaar achter veertig jaar Busband | 177 → 195 | 5 |
| 3 | Museum Kasteel Wijchen vult zomervakantie met speurtochten en waterbingo | 169 → 170 | 4 |
| 4 | Vitesse mag na drie jaar weer gewoon over voetbal praten | 527 → 521 | 7 |
| 5 | Bewoonster van de Drogenapstoren woont voortaan in een huis met Michelinster | 386 → 358 | 5 |
| 6 | Arnhemse zanger gaat viraal met lied over een praatje maken | 204 → 199 | 4 |
| 7 | Delftenaar loopt weer door er alleen aan te denken | 252 → 203 | 4 |
| 8 | Verweesd tweeluik uit Goudstikker-collectie herkend na dertig jaar in kelder | 353 → 349 | 6 |
| 9 | Arnhemse schuldenaanpak krijgt vervolg na proef in Immerloo II | 366 → 361 | 5 |
| 10 | Een veld in Londen waar iedereen eindelijk mag meespelen | 559 → 561 | 5 |
| 11 | India lanceert eerste privaat ontwikkelde raket de ruimte in | 357 → 341 | 5 |

## Correction log (PIPE-8)

- slot 1 (fact, WR-2): Titel en openingszin claimden dat het festival dit jaar 'meer publiek dan ooit' trok, alsof dit een record over alle vijf edities was. De bron vermeldt alleen dat het festival 5 procent meer bezoekers trok dan vorig jaar — geen vergelijking met eerdere edities. Titel en tekst zijn hierop aangepast.
- slot 1 (fact, WR-2): De openingsalinea bevatte een uitgebreide, verzonnen 'klankkast'-metafoor (het stadje dat als klankkast werkt en noten 'tot ver buiten de eigen muren' laat naklinken). Dit staat niet in de bron en is als niet-onderbouwde toevoeging geschrapt/vervangen door een alinea die dicht bij de brontekst blijft.
- slot 1 (fact, WR-2): De titel suggereerde met 'na vijf edities nog altijd' een groeitrend over meerdere jaren; de bron onderbouwt alleen de vergelijking met het voorgaande jaar. Titel aangepast zodat deze exact aansluit bij het onderbouwde feit (5 procent meer bezoekers, vijfde editie).
- slot 1: Openingsalinea herschreven: de verzonnen sfeerschets over de 'klankkast' van Batenburg is vervangen door een feitelijke intro die dicht bij de brontekst blijft.
- slot 1: 'Al bij het openingsconcert klonk hoe de klankkast zou gaan resoneren' vereenvoudigd tot 'Al bij het openingsconcert wist de muziek het publiek te verrassen', aansluitend bij de brontekst en zonder de weggehaalde metafoor.
- slot 1: Alinea's over de vrijwilligers en het openingsconcert samengevoegd/ingekort zodat de alineastructuur logisch blijft na het schrappen van de ongefundeerde zinnen.
- slot 2 (fact, WR-2): Draft stelde dat beiden 'veertig jaar lang' de stille motor achter Busband waren; de bron zegt dat alleen Jan al 40 jaar lid is, Ingrid pas ruim 25 jaar. Aangepast naar 'jarenlang' om geen onjuist getal aan Ingrid toe te schrijven.
- slot 2 (fact, WR-2): Draft noemde het echtpaar 'uit Groesbeek'; de bron zegt alleen dat dweilband Busband in Groesbeek zit, niet dat het echtpaar daar woont. Herformuleerd zodat 'Groesbeek' bij de dweilband hoort, niet bij hun woonplaats.
- slot 2 (fact, WR-2): Draft sprak van 'de koninklijke onderscheiding' (enkelvoud) terwijl beiden ieder een eigen onderscheiding ontvingen ('onderscheidingen', bron: meervoud); gecorrigeerd naar meervoud.
- slot 2 (fact, WR-2): Rol van Jan bij Busband was in de draft herschikt (vervoer/techniek gekoppeld aan 'organiseert activiteiten'); hersteld conform bronvolgorde: bestuurslid/archief/organisator van activiteiten als één groep, vervoer/techniek/hand- en spandiensten als aparte taken.
- slot 2: Zin over het echtpaar als 'stille motor' herschreven om overdreven precisie (veertig jaar voor beiden) te vermijden.
- slot 2: Herstructurering van de zin over Jans taken voor betere aansluiting bij de brontekst.
- slot 2: Enkelvoud 'onderscheiding' naar meervoud 'onderscheidingen' gecorrigeerd.
- slot 3 (fact, WR-2): De zin 'een ontsnapping die, hoe je het ook wendt of keert, toch mooi binnen de kasteelmuren blijft' is een verzonnen, niet door de bron ondersteunde toevoeging (grapje over de escaperoute) en is geschrapt.
- slot 3 (fact, WR-2): 'in de veertiende eeuw' aangepast naar 'in de eerste helft van de veertiende eeuw', conform de bron ('het ontstaan in de eerste helft van de 14e eeuw').
- slot 3: Slotalinea aangevuld met 'bedoeld voor volwassenen en kinderen die een rustige omgeving nodig hebben' zodat duidelijk is voor wie de prikkelarme middag is (uit de bron), en de laatste zin iets gestroomlijnd.
- slot 4 (fact, WR-2): '...alsof het seizoen zelf al gewonnen was' (slot 1) is niet in de bronnen te vinden en is verwijderd; het is een verzonnen sfeerbeeld.
- slot 4 (fact, WR-2): 'vermeend patroon van misleiding en ondermijning' is aangepast naar 'stelselmatig patroon van misleiding en ondermijning', de exacte formulering uit de bron; 'vermeend' (= naar verluidt onterecht) staat niet in de bron en verandert de lading van het verwijt.
- slot 4 (fact, WR-2): De zin 'Na afloop was zijn opluchting groot' bij het citaat van Sturing klopt niet: dat citaat ('Ik hoop dat we nu een punt kunnen zetten...') komt uit het artikel van vóór de uitspraak, waarin Sturing vooraf zijn hoop uitspreekt over de afloop ('na morgen'). De draft presenteerde dit ten onrechte als een reactie na afloop; dit is gecorrigeerd door het citaat expliciet als vooraf uitgesproken te markeren en 'na morgen' logisch te actualiseren naar 'na vandaag', aangezien de uitspraak inmiddels bekend is.
- slot 4 (fact, WR-2): 'oud-verdediger Alexander Büttner' bevat een toevoeging (zijn functie als voormalig verdediger) die niet in de bronnen over dit moment staat; verwijderd conform de regel dat geen informatie mag worden toegevoegd, ook niet als die overigens bekend is.
- slot 4: Slot 1: 'en supporters feliciteerden hen alsof het seizoen zelf al gewonnen was' ingekort tot een feitelijke zin zonder ongefundeerde toevoeging.
- slot 4: Slot 3: herschreven zodat duidelijk is dat het citaat van Sturing vooraf werd uitgesproken, niet na afloop.
- slot 4: Kleine woordkeuze aangepast ('vermeend' naar 'stelselmatig') voor aansluiting bij brontekst.
- slot 5 (fact, WR-2): Verwijderd: 'Wonen in de toren voelt een beetje als leven in een ansichtkaart... alleen woont zij er middenin, met haar eigen sleutel' — deze metafoor en de suggestie dat de buurt precies zo pittoresk is als bezoekers verwachten, staan niet in de bron en zijn verzonnen sfeerbeschrijving.
- slot 5 (fact, WR-2): Gecorrigeerd: het jaartal 1446 werd in het concept gekoppeld aan het begin van de functies gevangenis/opslag/watertoren ('Sinds 1446 diende de toren achtereenvolgens als gevangenis...'). Volgens de bron werd de toren in 1446 in gebruik genomen als middeleeuwse stadspoort; de gevangenisfunctie dateert van 1571. Dit is hersteld met de juiste jaartallen en volgorde.
- slot 5 (fact, WR-2): Verwijderd/aangepast: de verzonnen toevoeging 'al wordt ook wel gezegd dat hij zo arm was dat er nooit iets in zijn nap zat' is niet in de bron te vinden (die zegt alleen dat hij 'heel arm was'); de tekst is teruggebracht tot wat de bron meldt.
- slot 5 (fact, WR-2): Verwijderd: 'ongevraagd' bij 'sterrenstatus' — de bron suggereert nergens dat de bekroning ongewenst is; Koppel is er juist trots op.
- slot 5 (fact, WR-2): De locatieomschrijving 'midden in de oude binnenstad van Zutphen' bij Koppels woning in de eerste alinea is niet letterlijk zo in de bron te vinden; vervangen door de wel bevestigde omschrijving dat de toren een middeleeuwse toren in Zutphen is.
- slot 5: Titel herschreven voor betere grammatica en rustigere toon: 'krijgt haar huis met Michelinster' klonk grammaticaal onhandig; nu 'woont voortaan in een huis met Michelinster'.
- slot 5: Overbodige/onduidelijke zinsconstructie in de laatste alinea van het concept (indirecte parafrase gepresenteerd als samenvatting van een citaat) verduidelijkt zodat helder is wat parafrase en wat citaat is.
- slot 6 (fact, WR-2): Slotalinea over 'het echtpaar Van den Brink' en hun 'vereniging' die al jaren op niets anders draait dan een praatje maken: dit staat nergens in de bron en is verzonnen. Verwijderd.
- slot 6 (fact, WR-2): Bewering dat Koehoorn 'onbedoeld' viraal ging: de bron zegt alleen dat het lied/de video viraal gaat, niet dat dit onbedoeld was. 'Onbedoeld' verwijderd.
- slot 6 (fact, WR-2): Openingszin ('Tim komt nooit als vreemdeling een bushalte binnen...') is een niet-onderbouwde, verzonnen bewering (dat mensen hem herkennen als iemand die 'zo een liedje over je schrijft') en bovendien beeldspraak die niet klopt (een bushalte heeft geen 'binnen'). Vervangen door een feitelijke intro op basis van de bron.
- slot 6 (fact, WR-2): Leeftijd van de hond: het concept noemde haar stellig 'veertienjarig', de bron zegt 'ongeveer 14'. Aangepast naar 'ongeveer veertien jaar oud' om niet stelliger te zijn dan de bron.
- slot 6: Titel aangepast van clickbait-achtig 'scoort viral hit' naar de neutralere, bij de bron aansluitende formulering 'gaat viraal'.
- slot 6: Awkward beeldspraak in de openingszin herschreven tot een directe, feitelijke intro.
- slot 6: 'de tong uit de bek' vervangen door 'tongetje uit haar mond' om dichter bij de brontekst en toon van het artikel te blijven.
- slot 6: Alinea over onderzoekscijfers en herkenning samengevoegd/herschikt voor een vloeiendere opbouw nu de verzonnen slotalinea is verwijderd.
- slot 7 (fact, WR-2): Draft stelde dat de route van gedachte naar beweging bij Daan 'halverwege, ergens tussen hoofd en benen' stopte — dit is een niet-brongedekte precisering van hoe/waar de dwarslaesie de signaaloverdracht blokkeert. Vervangen door een neutralere formulering ('het signaal kwam niet meer aan') die dichter bij de brontekst blijft.
- slot 7 (fact, WR-2): Draft voegde een uitleg toe over wat de wereldprimeur precies inhoudt ('nooit eerder werd het denken aan een beweging zo direct vertaald in die beweging zelf, zonder dat het lichaam de opdracht zelf nog hoefde door te geven') — de bron meldt alleen dát de TU Delft het een wereldprimeur noemt, niet waarom. Deze toevoeging is verwijderd.
- slot 7 (fact, WR-2): Draft beschreef specifieke, niet-brongedekte handelingen ('Hij staat, hij verplaatst zijn gewicht, hij zet de ene voet voor de andere') — de bron zegt alleen dat Daan weer kan lopen, niet hoe dat er stap voor stap uitziet. Deze details zijn geschrapt.
- slot 7: 'uit Delft' toegevoegd bij de introductie van Daan, overeenkomstig de dateline 'Delft -' in de brontekst, voor duidelijkheid.
- slot 7: Zinsbouw in de eerste en derde alinea licht vereenvoudigd voor leesbaarheid en om dichter bij de brontekst te blijven.
- slot 8 (fact, WR-2): Verwijderd: "Hij nam het tweeluik mee naar huis." — de bronnen vermelden nergens expliciet dat hij het paneel meenam; dit was een niet-onderbouwde toevoeging.
- slot 8 (fact, WR-2): Aangepast: het andere Goudstikker-werk bij de nazaat van de SS'er was niet 'opgedoken' (nieuw gevonden), maar hing er volgens de bron al jaren aan de muur en werd pas nu door De Telegraaf naar buiten gebracht. Tekst aangepast naar 'bleek te hangen'.
- slot 8: Kleine stilistische stroomlijning bij de aanpassing van de zin over het andere Goudstikker-werk, verder geen grammatica- of spellingsfouten aangetroffen.
- slot 9 (fact, WR-2): Laatste alinea: het origineel zegt dat de aanpak wordt uitgebreid naar 'nog ten minste honderd huishoudens' (dus honderd huishoudens bovenop de bestaande ~40), niet naar in totaal honderd. De draft liet 'nog' weg, waardoor het leek alsof honderd het totaal zou zijn; hersteld naar 'nog eens ten minste honderd huishoudens'.
- slot 9 (fact, WR-2): 'Het cijfer van de week is 34' was een verzonnen rubrieksformulering die niet in de bron voorkomt; het cijfer (34 procent) zelf klopte wel, maar de framing is verwijderd/herschreven tot lopende tekst.
- slot 9 (fact, WR-2): 'de wijk met naar eigen zeggen de armste postcode van Nederland' suggereerde ten onrechte dat de wijk zelf die claim maakt; de bron omschrijft Immerloo II als 'het armste postcodegebied van Nederland' zonder die zelftoeschrijving. Herschreven naar 'de wijk die geldt als het armste postcodegebied van Nederland'.
- slot 9: Zin 'Het cijfer van de week is 34: gemiddeld werd 34 procent...' herschreven tot een vloeiende zin zonder rubrieksaanduiding, en de dubbele vermelding van '34' verwijderd.
- slot 9: 'postcode' gecorrigeerd naar 'postcodegebied', conform de bronformulering.
- slot 9: Kleine stilistische gladstrijking in de derde alinea (puntkomma i.p.v. nieuwe zin) voor leesbaarheid.
- slot 10 (fact, WR-2): "felrode aanvoerdersband" was onjuist: de bron spreekt van een "bright red bib" (een hesje), niet van een aanvoerdersband. Dit suggereerde ten onrechte dat Farishta aanvoerder is; gecorrigeerd naar "felrood hesje".
- slot 10 (fact, WR-2): "tot ze besefte dat alle vrouwen om haar heen hetzelfde overwonnen" week af van de bron, die spreekt van het comfort dat alle vrouwen er samen voor stonden ('the comfort of knowing that all the women there were with me'), niet dat ze 'hetzelfde overwonnen'; herformuleerd naar een dichtere weergave van het citaat.
- slot 10: "fans zich steeds vaker priceout voelen" bevatte een onjuiste Engelse leenvorm; gecorrigeerd naar "fans zich steeds vaker buitengeprijsd voelen".
- slot 11 (fact, WR-2): Openingszin ('Wie zaterdagochtend naar het eiland Sriharikota keek, zag geschiedenis vertrekken: klein begin, groot verschil.') was een niet door de bron gedekte, clickbait-achtige framing zonder feitelijke inhoud; verwijderd/vervangen door een feitelijke openingszin.
- slot 11 (fact, WR-2): 'navigatiesystemen' is aangepast naar 'geleidingssystemen' — de bron noemt 'guidance systems', wat niet hetzelfde is als navigatie.
- slot 11 (fact, WR-2): 'gegevens voor toekomstige missies' is gecorrigeerd naar 'gegevens voor toekomstige commerciële lanceringen', conform de bron ('future commercial launches').
- slot 11 (fact, WR-2): 'ruim 22 meter hoog' is gecorrigeerd naar 'ongeveer 22 meter hoog' — de bron zegt 'about 22 meters', niet 'iets meer dan'.
- slot 11 (fact, WR-2): De zin over de Vikram-S ('is een vervolg op de kleinere Vikram-S') suggereerde een expliciete opvolgersrelatie die de bron niet zo stelt; herschreven tot een neutralere, door de bron gedekte formulering.
- slot 11: Titel aangevuld met 'zijn' voor correcte grammatica: 'India lanceert zijn eerste privaat ontwikkelde raket de ruimte in'.
- slot 11: Eerste alinea herschreven in rustigere, feitelijke toon passend bij het karakter van het artikel.

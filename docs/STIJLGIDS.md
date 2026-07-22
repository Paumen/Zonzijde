# De Zonzijde — Stijlgids

Status: **concept v0** — huisstijl voor taal, notatie en typografie.

Dit document is de enige bron voor de **micro-laag**: hoe De Zonzijde getallen,
namen, hoofdletters, leestekens, citaten en koppen noteert, welke woorden ze
mijdt, en hoe ze inclusief en zorgvuldig formuleert. Het vult de andere drie
documenten aan; het herhaalt ze niet.

- Het *waarom*, de identiteit, de toon en de stem — `config/prompts/brief.md`.
  Toon (`TONEN`), stem (`STEM`) en invalshoeken (`INVALSHOEKEN`, `TECHNIEKEN`)
  worden hier niet overgedaan.
- Het *wat*: lengtes, mix, opmaak, vaste elementen, dateline — [`SPEC.md`](SPEC.md).
  Woordaantallen en het opmaakgrid (LAY) staan daar; deze gids gaat niet over
  lengte of paginavulling.
- Het *hoe* van de pijplijn — [`ARCHITECTURE.md`](ARCHITECTURE.md).

Twee stappen leven feitelijk met deze regels: de eindredacteur (S8), die het
Nederlands van elk concept corrigeert, en de opmaak (S9/Typst), die de glyph- en
zetregels afdwingt (echte curly quotes, streepjes, geen weduwen/wezen). Waar een
regel bij de zetter thuishoort en niet bij de schrijver, staat dat erbij.

> **Status van de regels hieronder.** Een stijlgids moet kiezen om bruikbaar te
> zijn, dus elke regel is als concrete keuze geformuleerd. Maar de keuzes zijn
> *voorstellen ter bekrachtiging*, geen dictaat: elk is gegrond op standaard
> Nederlands journalistiek gebruik óf op wat de eindredacteur in de praktijk al
> corrigeert. De PO bekrachtigt of draait om. Alleen de naamgeving (§3) en de
> werking (bron nu, prompt-injectie later) zijn al bekrachtigd.
>
> **Standaardwerk.** Spelling volgt de officiële Woordenlijst Nederlandse Taal
> (het Groene Boekje). Bij twijfel over stijl, samenstelling of voorkeur geldt
> het advies van Onze Taal / de Taalunie. Afwijkingen hieronder zijn bewust en
> gaan vóór.

---

## 1. Taal, spelling & voorkeurswoorden

- **Samenstellingen aaneen.** Nederlandse samenstellingen schrijf je als één
  woord: *voetbalgerelateerd*, *marinebioloog*, *stikstofdoel*. Geen Engelse
  spatie ("voetbal gerelateerd"). Een koppelteken alleen bij klinkerbotsing
  (*zee-egel*), gelijke delen (*woon-werkverkeer*) of leesbaarheid van lange of
  cijfer-bevattende samenstellingen (*A3-boekje*, *5G-netwerk*).
- **Actief boven passief.** Schrijf actieve zinnen met een handelend onderwerp;
  vermijd de lijdende vorm waar een actieve zin bestaat. "De gemeente plant
  driehonderd bomen," niet "Er worden driehonderd bomen geplant."
- **Geen telegramstijl.** Zinnen zijn volledig (onderwerp + persoonsvorm). Geen
  losse fragmenten als stijlmiddel in nieuwstekst — "Ruim driehonderd kilometer,
  keurig getraind." wordt "Hij liep ruim driehonderd trainingskilometers."
- **Geen lidwoord bij organisatienamen** die als eigennaam functioneren: *FIFA*,
  *NAVO*, *King's College London* — niet "de FIFA", "het King's College". Wel bij
  namen die een soortnaam bevatten: *de Rabobank*, *het RIVM*-onderzoek.

**Zwarte lijst — mijden, met voorkeursalternatief.** Niet uitputtend; de geest is:
geen jargon, geen eufemismen, geen sleetse clichés.

| Mijd | Gebruik |
|------|---------|
| impactvol, impact hebben op | *gevolgen voor*, *raakt*, *verandert* |
| in het kader van | *voor*, *bij*, *om* |
| naar aanleiding van | *na*, *door* |
| middels, alsmede, teneinde | *met/via*, *en/ook*, *om te* |
| de nodige, een aantal (als vulsel) | een concreet getal, of laat weg |
| qua | herformuleer ("qua sfeer" → "de sfeer") |
| een boring (tandarts) | *de boor* |
| richting geven aan / handvatten bieden | *helpen*, *een aanpak geven* |
| clichés: "een storm van kritiek", "de kop opsteken", "met stip" | herformuleer concreet |

---

## 2. Getallen, bedragen & eenheden

- **Één t/m twintig voluit**, vanaf **21 in cijfers**: *een, twee, twaalf,
  twintig* — *21, 100, 350*. Ronde grote getallen mogen voluit als dat prettiger
  leest (*honderd*, *duizend*).
- **Zinsbegin altijd voluit**, ongeacht de grootte: "Veertien deelnemers haalden
  de finish." Herschik de zin liever dan een groot getal voluit te moeten
  schrijven.
- **Grote getallen: cijfer + woord.** *3 miljoen*, *1,5 miljard*. Decimalen met
  een **komma**, duizendtallen met een **punt** waar het leest: *2.800 woorden*.
- **Valuta.** Euro's met het teken direct vóór het getal, geen spatie: *€45*,
  *€45,50*. Ronde bedragen zonder decimalen (*€45*, niet "€45,-"). Vreemde valuta
  omrekenen naar euro; het origineel mag tussen haakjes.
- **Eenheden: metrisch.** meter, liter, kilometer, gram — nooit inch, feet, mile,
  ounce. Getal en eenheid gescheiden door een (vaste) spatie waar uitgeschreven:
  *5 kilometer*. Symbolen (km, kg, °C) alleen in strak-technische context of de
  weerstrook; in lopende tekst liever voluit.
- **Percentages voluit in lopende tekst:** *40 procent*, niet "40" en niet "40%".
  De eenheid is verplicht — een kaal getal ("gestegen naar 40") is onaf. Het
  teken *%* is voorbehouden aan tabellen, kaders en de weerstrook.
- **Data.** In lopende tekst: *12 juli 2026* (dag, maand voluit, jaar). Maand
  zonder hoofdletter. Geen "12-07-2026" in tekst. De editie zelf is gedateerd op
  zondag (OPS-1); de brondatum per artikel volgt ED-3 in [`SPEC.md`](SPEC.md).
- **Tijdstippen.** 24-uursnotatie met punt: *14.30 uur*, *9.00 uur*. "half drie"
  mag waar het spreektaliger past bij het verhaal.
- **Jaartallen & decennia.** *2026*, *de jaren negentig* (voluit), *de jaren '90*
  vermijden. Periodes met en-streepje: *1997–2017*.

---

## 3. Namen, titels & aanduidingen

- **Eerste vermelding: volledige voor- en achternaam**, met functie of duiding
  waar dat oriënteert: *stadsecoloog Joep van Belkom*, *burgemeester Marijke van
  Beek*. Functie met kleine letter (zie §4).
- **Vervolgvermelding — schaal-afhankelijk** *(bekrachtigd)*:
  - **Lokaal & regionaal:** de **voornaam** — warm en dichtbij, passend bij de
    voordeur-oriëntatie van de krant. "Joep wijst naar de palen…"
  - **Nationaal & internationaal:** de **achternaam**. "Hermans lichtte toe…"
  - **Uitzondering:** in een portret of uitgesproken human-anglestuk mag de
    voornaam op elke schaal, als dat de nabijheid dient.
- **Tussenvoegsels.** Kleine letter mét voornaam, hoofdletter zónder voornaam:
  *Jan van de Berg* → *Van de Berg*. Bij alfabetiseren telt het tussenvoegsel
  niet mee (op *Berg*).
- **Academische en adellijke titels** worden niet standaard vermeld; alleen als ze
  ter zake doen (*hoogleraar*, niet "prof. dr."). Beroepsaanduiding gaat vóór de
  naam, in kleine letters.
- **Buitenlandse namen** in de gangbare Nederlandse of oorspronkelijke schrijfwijze;
  diakritische tekens behouden (*Núñez*, *Gößwein*).
- **Geografie.** Nederlandse exoniemen waar gangbaar (*Keulen*, *Praag*), anders de
  lokale naam. De scope-plaatsen precies zoals in [`SPEC.md`](SPEC.md) §1.

---

## 4. Hoofdletters, afkortingen & acroniemen

- **Kleine letter** voor functies en beroepen (*minister-president*, *wethouder*,
  *stadsecoloog*), voor windrichtingen als richting (*het noorden*), en voor
  seizoenen.
- **Hoofdletter** voor eigennamen, instellingen als eigennaam (*de Tweede Kamer*,
  *Rijkswaterstaat*), geografische eigennamen, feest- en gedenkdagen (*Kerst*,
  *Koningsdag*) en volken/talen (*Nederlands*).
- **Afkortingen.** Eerste vermelding voluit met de afkorting tussen haakjes:
  *Algemeen Nederlands Persbureau (ANP)*; daarna alleen de afkorting. Algemeen
  bekende acroniemen mogen direct: *NAVO, VN, EU, RIVM*.
- **Puntafkortingen zoveel mogelijk mijden** in lopende tekst: schrijf *onder
  andere* i.p.v. "o.a.", *bijvoorbeeld* i.p.v. "bijv.". Gevestigde vormen blijven:
  *btw*, *pdf*. Letterwoorden die je als woord uitspreekt in kleine letters waar
  gangbaar (*havo*, *pin*).

---

## 5. Interpunctie & typografie

De schrijver levert leesbare tekst; de **zetter (S9/Typst) rendert de correcte
glyphs**. Onderstaande vormvoorkeuren zijn wat er uiteindelijk op papier staat.

- **Citaten met enkele curly quotes:** ‘…’. Een aanhaling die een hele zin beslaat
  krijgt de punt of komma **binnen** de aanhalingstekens: *'Dit is fantastisch,'
  zei de burgemeester.* Bij een deelcitaat valt het leesteken **buiten**: *Ze
  noemde het "een keerpunt".*
- **Aanhaling ≠ ironie.** Aanhalingstekens zijn voor geciteerde spraak. Gebruik ze
  niet voor afstand of ironie ("zogenaamde"); herformuleer liever.
- **Streepjes.**
  - *Koppelteken* (-) verbindt woorddelen: *A3-boekje*, *woon-werkverkeer*.
  - *En-streepje* (–) voor bereiken en relaties: *1997–2017*, *Arnhem–Nijmegen*.
  - *Gedachtestreepje* — een en-streepje met spaties eromheen — voor een inschuiving.
    Geen em-streepje (—) in Nederlandse tekst.
- **Beletselteken** als één teken (…), niet drie punten; spaarzaam, nooit om een
  pointe te onderstrepen.
- **Geen uitroeptekens** in nieuwstekst (behalve binnen een letterlijk citaat).
- **Adressen en locaties** in lopende tekst: straatnaam met huisnummer
  (*Kasteellaan 4*), postcodes alleen als ze functioneel zijn. Provincie tussen
  komma's waar nodig ter verduidelijking.

---

## 6. Koppen, tussenkoppen & citaten

- **Kop:** actief, tegenwoordige tijd, **geen punt** aan het einde. Kort en
  concreet, met de nieuwswaarde voorop: *Stikstofdoel 2035 komt in zicht*. Een
  langer of verhalend stuk mag een prikkelender, verhalende kop dragen zolang hij
  dekt wat er staat — geen woordspeling die de inhoud niet waarmaakt.
- **Dateline.** Locatie en brondatum worden apart afgedrukt (ED-3); herhaal de
  locatie niet in de openingszin.
- **Tussenkoppen** (in langere stukken): kort, zonder punt, geen halve zin die de
  alinea eronder al voorwegneemt. Ze verdelen, ze vatten niet samen.
- **Citaten leesbaar maken.** Gesproken taal mag je opschonen — stopwoorden,
  haperingen en versprekingen weg — zolang de **betekenis en toon onveranderd**
  blijven. Corrigeer een komma-splice of onaffe zin binnen een citaat naar twee
  hele zinnen. Verzin nooit woorden die de spreker niet zei; dit is een citaat,
  geen parafrase.

---

## 7. Beeld & datavisualisatie

- **Illustratie.** Stijl, techniek en beperkingen van de wekelijkse tekening
  staan in `config/prompts/illustrate.md` en [`SPEC.md`](SPEC.md) EL-3; niet hier
  herhaald. Kort: zwart op wit, fijne lijnen, geen tekst in het beeld.
- **Infographic / cijferbeeld** (wanneer een verhaal het draagt): zelfde
  zwart-witte, lijnige huisstijl als de illustratie. Eén heldere boodschap per
  beeld, assen en eenheden benoemd, en een **bronvermelding** onderaan. Geen
  kleur, geen 3D, geen decoratieve rasters. Getallen in het beeld volgen §2.

---

## 8. Inclusiviteit, diversiteit & ethiek

- **Genderneutraal waar het kan.** Kies neutrale functie- en groepsnamen
  (*medewerkers*, *inwoners*, *voorzitter*) boven vormen die één gender
  veronderstellen. Vermijd "de gewone man"-constructies.
- **Voornaamwoorden.** Gebruik de voornaamwoorden die iemand zelf hanteert. Is het
  onbekend en niet te achterhalen, herschrijf dan naar de naam of een neutrale
  formulering in plaats van te gokken.
- **Etniciteit, religie, herkomst, gezondheid, seksuele oriëntatie** worden
  **alleen** genoemd als ze aantoonbaar ter zake doen voor het verhaal — niet als
  standaard signalement. Bij twijfel: weglaten.
- **Personen met respect en op afstand van sensatie.** De Zonzijde brengt goed
  nieuws; ze zet mensen niet te kijk en overdrijft hun rol niet. Erken de
  somberheid waar die er is (de techniek *erkennen-en-keren*), maar nooit ten
  koste van een echt persoon.

---

*Open punten voor de PO:*

- **Aanspreekvorm.** In nieuwstekst spreekt de krant de lezer niet direct aan;
  waar het toch voorkomt is het voorstel informeel (*je*), niet *u*. Nog te
  bekrachtigen.
- **Getalgrens.** Voorstel: 1 t/m twintig voluit, vanaf 21 in cijfers (§2). Een
  krappere grens (t/m tien of twaalf) is een even verdedigbare keuze.
- **Valuta.** Voorstel: ronde bedragen zonder decimalen (*€45*). De vorm *€45,-*
  is in Nederland even gangbaar; jouw keuze.
- **Zwarte lijst.** De lijst in §1 is een startset, bedoeld om te groeien met wat
  de eindredacteur in de praktijk tegenkomt.

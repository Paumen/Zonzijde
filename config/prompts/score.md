---
version: 1
role: scoring prompt — stage S3 (PIPE-3), JSON mode, temperature 0
source: concept_ZZ.md §3.3, verbatim
note: proto_fetchfilter.html carries a slightly different wording ("Regels",
  "prijs toekenning"); this file is canonical from now on.
---
Je beoordeelt nieuwsberichten. Geef per bericht één score voor hoe goed of slecht het nieuws is voor mens, dier, natuur of samenleving:
-2 overduidelijk negatief (bijv. ramp, geweld, ernstige schade, leed, fraude)
-1 overwegend negatief
0 neutraal, gemengd, of te weinig informatie om te beoordelen
+1 overwegend positief
+2 overduidelijk positief (bijv. nieuw initiatief, geslaagde actie, lintje, vooruitgang, investering, prijstoekenning)
Meet alleen de richting van het nieuws, niet de omvang of het bereik.
Regel: promo-, marketing- en productgerichte items krijgen maximaal 0.
Antwoord uitsluitend met een JSON-object, met elk bericht precies één keer, bijvoorbeeld {"1": -1, "2": 2}.

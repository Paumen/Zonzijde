---
versie: 2
rol: pijplijn achtergrond.
---
De Zonzijde wordt geproduceerd via een vaste pijplijn. Sommige stappen zijn geautomatiseerd; andere worden uitgevoerd door een LLM-collega in een andere sessie, gebrieft voor die ene rol, net zoals jij voor de jouwe wordt gebrieft. In volgorde:

1. **Verzamelen** (geautomatiseerd) — feeds worden opgehaald en gefilterd tot wat binnen scope valt.
2. **Beoordelen** (LLM) — een beoordelaar scoort elk item op geschiktheid; alleen de positieve gaan door.
3. **Selecteren** (LLM) — een selecteur groepeert de doorgekomen items tot kandidaat-onderwerpen, per scope.
4. **Verrijken** (geautomatiseerd) — bronartikellen van elke kandidaat worden volledig opgehaald, met achtergrondinformatie uit de links die het aanhaalt.
5. **Outlinen** (LLM) — een eindredacteur plant de editie.
6. **Schrijven** (LLM) — voor elk slot schrijft een auteur het stuk en ziet daarbij alleen de bronnen van dat ene slot — niet de rest van de editie.
7. **Redigeren** (LLM) — een eindredacteur corrigeert het Nederlands van elk concept, zonder de bronnen bij de hand te hebben, alleen het stuk van de auteur dus.
8. **Opmaken** (geautomatiseerd) — de gecontroleerde artikelen worden opgemaakt tot de gedrukte A3-krant.

Elke LLM-collega ziet alleen zijn eigen brief en input. Jouw rol voor deze taak staat vermeld in `<role>`.

---

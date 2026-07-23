Requirements live visualization pipeline automation

Purpose
A viewer can watch and feel the newspaper being made and come away understanding how the pipeline turns massivee raw input into a finished edition.
The visualization is compelling enough to demo and share as a way to intuitively understand the system, for a non-technical person.
The experience feels ALIVE — like watching a newsroom work — rather than reading a dashboard or log.

Fidelity to the real run
Every headline, date, score, werktitel, and artikelkop shown is taken from a real pipeline run, never invented, or incomplete. And actually visible and readable.
The numbers and visuals at match the real run's actual numbers.

What the viewer sees
The whole pipeline is shown end to end, from a broad, unsorted intake to a single shaped, printed paper.
The progression advances step by step through the fases as work happens.
The full volume of incoming items is conveyed, not a tiny sample, so the scale of the funnel is felt, and seen.
All real items are shown at each stage, rather than a token a few. This is clearly recognizable, eg trough real titles.
The stream narrows stage by stage while the surviving items visibly grow richer (from headline, to full text, to draft, to finished article).
Every surviving item retains a persistent identity throughout the visualization — a viewer can see which sources survive and which are dropped.
The four geographic rings (lokaal, regionaal, nationaal, internationaal) are visible, especially towards the end and their balance across the edition is apparent.
The paper itself is seen taking shape. The edition is perceived as an object gradually emerging from the pipeline rather than appearing only at the end. Werktitels becoming text, gaining final titles, receiving an illustration, and ending as a finished paper.
The paper roughly looks like (simplified) actual Zonzijde layout and pages. 

Why things happen 
Whenever items are filtered out, the reason is visible and intuitive, not just their disappearance. eg items removed for being outside the date window are clearly seen leaving because they are too old.
When an LLM performs a step, it is unmistakable that a model is doing the work, and what kind. Rating, selecting, determining angle/length, writing, reviewing, etc. 
An LLM's progress is visible as it works through a task and and/or batches.
The transformation performed by an LLM is visible on the affected item, allowing the viewer to understand what changed.

Motion
Items move continuously to their outcomes as the same persistent objects, rather than one arrangement fading into a different one.
Start and transitions are smooth. The intake ramps up gradually, like scraping and gathering, rather than beginning at full volume instantly. The handoff from one stage to the next is logical and smooth.
A stage visibly settles before attention moves to the next stage.
Pipeline failures, retries, and skipped work are represented rather than hidden.

Timing
Real duration. Step's duration reflects the real time that step takes, so the heavy stages read as the long ones.
Longer taking steps show REAL progress within that step, giving reassurances and triggering animation and showing outcome/results, to give user something to look at and make it less of a wait.
The visualization never advances beyond the real pipeline state.
Presentation duration. Steps and transitions take sufficient time to convey what happened during the step/transition including outcomes/results and visualize this, regardless of how fast it really was. Time taken in excess is used later to make longer taking steps feel less of a wait. 
Synchronisation. Next step only starts if a) previous step is finished in reality, b) previous step is finished for animation and transition required   for T2, c) next step started in reality.
Control. Speed x4, x8, x12 (replay only)

Delivery
The replay of a recorded run is understood as a stepping stone toward the same view eventually running live against the real pipeline.

Assume:
- F1 1000 rss items
  - 600 out of time window
  - F2 400 remaining in window with titel
    - 50 duplicate
    - 350 remaning
      - 100 with negative words
      - F3 250 remaining
        - 100 negative
        - 50 neutral
        - F4 100 remaining positive
          - 78 not selected
          - S5 22 remaning selected
            - 4 not enough source material
            - S6 18 remaining
              - 6-10 not picked
              - 8-12 remaining picked


F1 Titel + Samenvatting
F2 Titel + Samenvatting
F3 Titel + Samenvatting
F4 Werktitel + 1-3x Titel + Samenvatting
F5 Werktitel + 1-3x Titel + Samenvatting + brontekst + reference links + reference tekst
F6 Werktitel + 1-3x Titel + Samenvatting + brontekst + reference links + reference tekst + Invalshoek + Lengte richtlijn
F7 Draft artikellichaam
F8 Final artikellichaam + artikelkop
F9 Final artikellichaam + artikelkop + Final vormgeving in paper + illustratie

F1 Bronnen
F2 Corresoondenten
F3 Analysten
F4 Sectie redacteurs
F5 Onderzoeksjournalisten 
F6 Hoofdredacteur
F7 Reporters / Schrijvers
F8 Eindredacteuren
F9 Vormgevers

Requirements live visualization pipeline automation

Purpose
A viewer can watch and feel the newspaper being made and come away understanding how the pipeline turns masive raw input into a finished streamlimed edition.
The visualization is compelling enough to intuitively understand the flow.
The experience feels ALIVE — like watching a newsroom work — not a dashboard or log.

Fidelity to the real run
Every headline, date, score, werktitel, and artikelkop shown is taken from a real pipeline run, never invented, or incomplete. And actually visible and readable, technically, if there's still massive number of items, it not nrvesarry for all to be readable at exact same time. If data is missing for mockups/prototyping, use a placeholder. 

What the viewer sees
Mobile portrait mode.  
Newsroom, not a dashboard, not a log.
In early stages, paper clipping that flies in and piles up **organically** — overlapping, rotated, a growing heap on the desk. Volume is **felt** as a pile.
The progression advances step by step through the fases as work happens. From a broad, unsorted intake to a single shaped, printed paper.
The full volume of incoming items is conveyed, not a tiny sample, so the scale of the funnel is felt, and seen. All real items are shown at each stage, rather than a token a few. This is clearly recognizable, eg trough real titles.
The stream narrows stage by stage while the surviving items visibly grow richer (from headline, to full text, to draft, to finished article).
Every surviving item retains a persistent identity throughout the visualization — a viewer can see which survive and which are dropped.
Moving trough stages feels naturally and logically, user sees where thing move and can follow. Moving between stages as a smooth transition, not a start/stop, snap, or reshape. Whole pipe feels one holistic continuous experience. modern html, css, and js, best practices are uttilized. (Illustrative examples: (auto)moving trough stages by scroll, segmented tabs/controls, single page, horizontal swipes, etc).
The four geographic rings (lokaal, regionaal, nationaal, internationaal) are visible, especially towards the end and their balance across the edition is apparent.
The paper itself is seen taking shape. The edition is perceived as an object gradually emerging from the rather than appearing only at the end. Werktitels becoming text, gaining final titles, receiving an illustration, and ending as a finished paper.
The paper roughly looks like (simplified) actual Zonzijde layout and pages. One landscape A3, content on 4 A4 pages, outer [4,1], inner [2, 3].

Why things happen 
Whenever items are filtered out, the reason is obvious and intuitive. This both via visual style and the way they move/animate/transition. eg items removed for being outside the date window are clearly seen leaving because they are too old.
When an LLM performs a step, it is unmistakable that a model is doing the work, and what kind, and roughly how. Rating, selecting, determining angle/length, writing, reviewing, etc. 
An LLM's progress is visible as it works through a task and and/or batches.
The transformation performed by an LLM is visible on the affected item, allowing the viewer to understand what changed and why.

Motion
Items move continuously to their outcomes as the same persistent objects, rather than one arrangement fading into a different one.
Start and transitions are smooth. The intake ramps up gradually, like scraping and gathering, rather than beginning at full volume instantly. The handoff from one stage to the next is logical and smooth.
Failures, retries, and skipped work are represented rather than hidden.

Timing
Real duration. Step's duration reflects the real time that step takes, so the heavy stages read as the long ones. In total that's at least 10+ min.
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

For early mockups or prototypes, using only half or quarter of these numbers, for first few stages is allowed.

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

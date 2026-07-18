## What this is

De Zonzijde is a weekly, printable Dutch newspaper of genuinely good news for
Gemeente Wijchen and outward (lokaal → regionaal → nationaal → internationaal).
The deliverable is a print-ready PDF (A3 booklet imposition). For more see brief.

**The two documents that govern all work here:**

- `docs/SPEC.md` — the *what*: editorial and layout rules an edition must satisfy.
  
- `docs/ARCHITECTURE.md` — the *how*: the pipeline design, data contracts,
  target repo layout (`zonzijde/` Python package), Typst typesetting, orchestration,
  and the phased build order. 

The original concept is archived at `docs/history/concept_ZZ.md`.

## Conventions and hard rules

- Specification, decision, instructions, etc. live in one place, remainder refers to it.
- Do NOT add comments and docstrings to code files. Except if absolutely necessary to prevent a frontier LLM agent making specific errors when editing the code in future.
- Never refer to or repeat specs or rules or decisions in code files.
- Never edit prompt files without explicit approval PO. You must show PO exact current and proposed prompt instruction inline in chat before you can request approval.
- Never create or edit tests without explicit PO approval. You must explain PO proposed test and why you think it's critical in plain English inline in chat before you can request approval.

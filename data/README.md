# Board game data

## `bgg_top300_2021-02.csv`

The top 300 ranked games on BoardGameGeek, with one row per game.

| Column | Meaning |
|---|---|
| `rank` | BGG overall rank (1 = highest) |
| `name` | Primary game name |
| `year` | Year published |
| `type` | Game type — always `boardgame` here (the source lists only ranked base games) |
| `domains` | BGG's 8 top-level families (Strategy, Thematic, Family, Wargames, Abstract, Party, Children's, Customizable). Stands in for "categories" |
| `mechanisms` | BGG mechanics, comma-separated |
| `rating_avg` | Raw average user rating (1–10) |
| `complexity` | Average weight / complexity (1–5) |
| `bgg_id` | BoardGameGeek game id (`boardgamegeek.com/boardgame/<id>`) |

### Provenance & caveats

- **Source:** the public [BoardGameGeek Dataset](https://raw.githubusercontent.com/jalwz17/Board-Game-Data-Analysis/main/bgg_dataset.csv)
  (also on Kaggle as `andrewmvd/board-games`), scraped from BGG in **February 2021**.
- Because it's a 2021 snapshot, **ranks are dated** (e.g. Gloomhaven is #1 here;
  today Brass: Birmingham is #1).
- The dump carries BGG's coarse **domains**, not granular categories (Fantasy,
  Economic, …), and only the **raw average** rating (not the Geek/Bayes rating).

### Regenerating / getting current data

```bash
# Rebuild this file from the public dump (no login needed):
python3 tools/build_top_games_from_dump.py --top 300 -o data/bgg_top300_2021-02.csv

# For a CURRENT top-N with granular categories, true type and the Geek rating,
# use the live BGG XML API (needs a logged-in session cookie — see the script):
python3 tools/bgg_top_games.py --ranks-csv boardgames_ranks.csv --top 300 -o current.csv
```

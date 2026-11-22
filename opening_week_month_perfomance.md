## Opening week / opening month performance

**What the tables show.** `opening_week_perf` and `opening_month_perf` hold one row per game (a "concept": all PlayStation versions and editions of a title). The `percentage` column is the share of sampled PlayStation users who first played the game during its opening week (7 days) or opening month (30 days). It is a measure of popularity in the opening window, not sales.
Weekly data starts with releases from 2026-09-17, monthly data from 2026-08-25.

**How they are compiled** (N = 7 for the week, 30 for the month). A game is calculated once it is 2N days old, and the result is not updated afterwards.

1. **Sample:** users whose play history was scanned between N and 2N days after release and who were active (played anything) at some point between release and 2N days after.
2. **Players:** sampled users whose first play of the game falls in the first N days.
3. **Advanced access:** first plays in the 10 days before the release date count as day-1 players. Such players who aren't in the sample yet (no activity after release) are added to the sample size (`sample_added_users`).
4. `percentage` = `detected_users` / `sample_size` x 100.

**Caveats**
- The sample is users in my database (found by crawling friend lists, public play history only). Percentages are shares of this population, not of all PSN players, and its composition changes over time.
- The activity window extends to 2N days, so the sample includes some users who didn't play in the first N days. This overestimates the sample slightly and affects all titles in about the same way.
- Games with advanced access get up to 17 days of first plays (10 before release plus 7) against 7 for others. However, as advanced access usually comes with a higher price tag, it's safe to assume those players would simply show up on the first day
- The release date comes from Sony's data (usually the standard-edition date). A wrong date may distort the result.
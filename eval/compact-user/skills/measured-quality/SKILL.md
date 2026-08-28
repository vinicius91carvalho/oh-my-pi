---
name: measured-quality
description: Build the hand-labelled fixture before tuning any score, ranking, or match.
---

# Getting a judgement right

For anything that produces a score, a ranking, a match, or an answer from a
model:

- **You decide what the right answer is first**, by reading the real data
  yourself. NEVER copy what the system does today: that turns a wrong answer
  into the target.
- Write those right answers down as a fixture next to the code, with one line of
  reason per row.
- Then tune until the system matches, measuring after every single change.
  "It looks better" is not a measurement.
- Report both mistakes: what it kept that should have been dropped, and what it
  dropped that should have been kept.
- Build the loop locally first. Local measures in seconds; staging costs a day.

# Decisions

- 2026-03-11: prices are stored as integer cents to avoid float drift.
- 2026-05-02: the discount rounding rule is "round half up", decided after a
  customer complaint about a 1-cent difference on invoice 88213.
- 2026-07-19: currency conversion goes through USD as the pivot.
- 2026-08-27: JPY added at 150 per USD, a fixed approximation in the same
  style as the other rates.

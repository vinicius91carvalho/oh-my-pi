| profile | prompt tokens | tool schemas | rest | tasks passed | median s |
|---|---:|---:|---:|---:|---:|
| full (default) | 19,278 | 11,642 | 7,636 | 11/12 | 171 |
| compact, 6 tools | 7,888 | 4,660 | 3,228 | 11/12 | 152 |
| compact, 4 tools | 5,624 | 2,360 | 3,264 | 12/12 | 148 |
| compact, 3 tools | 5,254 | 1,980 | 3,274 | 12/12 | 119 |

Per axis:

| profile | tool choice | edit | run tests | stop | ask | rules |
|---|---|---|---|---|---|---|
| full (default) | 3/3 | 3/3 | 2/2 | 2/2 | 0/1 | 1/1 |
| compact, 6 tools | 3/3 | 3/3 | 2/2 | 2/2 | 0/1 | 1/1 |
| compact, 4 tools | 3/3 | 3/3 | 2/2 | 2/2 | 1/1 | 1/1 |
| compact, 3 tools | 3/3 | 3/3 | 2/2 | 2/2 | 1/1 | 1/1 |

Failures:

  full (default)     ask-01    ask
  compact, 6 tools   ask-01    ask

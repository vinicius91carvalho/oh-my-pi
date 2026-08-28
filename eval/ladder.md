| step | prompt tokens | change | tool schemas | rest |
|---|---:|---:|---:|---:|
| upstream 18.0.7, default settings | 22,643 | - | 11,734 | 10,909 |
| this fork, default settings | 22,320 | -323 | 11,734 | 10,586 |
| + settings that already shipped (xdevDocs catalog, personality none, no model line) | 19,058 | -3,262 | 11,734 | 7,324 |
| + promptProfile compact | 17,868 | -1,190 | 11,734 | 6,134 |
| + xdevForceMount, 6 tools top-level | 10,838 | -7,030 | 4,660 | 6,178 |
| + 4 tools top-level | 8,574 | -2,264 | 2,360 | 6,214 |
| + 3 tools top-level (read, write, bash) | 8,204 | -370 | 1,980 | 6,224 |
| + context files compacted, detail moved to on-demand skills | 5,886 | -2,318 | 1,980 | 3,906 |

**22,643 to 5,886, 3.85x.**

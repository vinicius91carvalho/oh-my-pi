# OMP para modelo local: prompt de 22,6k -> 5,9k tokens

Fork de [oh-my-pi](https://github.com/can1357/oh-my-pi) com dois ajustes e uma otimizacao. Tudo medido no servidor, nada estimado.

| doc | o que tem |
|---|---|
| [modes.md](modes.md) | os 4 modos: tools no topo, tools em `xd://`, tokens, config pronta, quando usar cada um |
| [benchmark.md](benchmark.md) | maquina, servidor, 12 tarefas do fixture, 8 bugs em projeto real (TS + Python), sessao longa com compactacao |
| [pr-body.md](pr-body.md) | texto do unico PR para o upstream |
| [issue-comment.md](issue-comment.md) | comentario na issue #1734 |
| [reddit.md](reddit.md) | post do r/LocalLLaMA |
| [o-que-mexi-na-sua-maquina.md](o-que-mexi-na-sua-maquina.md) | o que mudou fora do fork e como desfazer |
| [TODO.md](TODO.md) | checklist de verificacao e os bugs do medidor |

Scripts: `../run-real.sh`, `../run-long.sh`, `../table-real.py`, `../real/README.md`.

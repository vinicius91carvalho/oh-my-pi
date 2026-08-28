# OMP para modelo local: prompt de 22,6k -> 5,9k tokens

Fork de [oh-my-pi](https://github.com/can1357/oh-my-pi) com dois ajustes de configuracao e tres correcoes. Tudo medido no servidor, nada estimado.

| doc | o que tem |
|---|---|
| [pr-body.md](pr-body.md) | o PR completo: o problema, as receitas (p7k/p5k/p3k), o benchmark inteiro (maquina, escada de tokens, fixture, 8 bugs reais por nivel com tempos, sessoes longas, velocidade, bugs do medidor) |
| [issue-comment.md](issue-comment.md) | comentario na issue #1734 |
| [reddit.md](reddit.md) | post do r/LocalLLaMA |
| [TODO.md](TODO.md) | checklist de verificacao |

Por que: rodar um agente de codigo so no laptop (M3 Max, 36 GB). Qwen3.8-27B a ~11 t/s no llama-server -> 17 no oMLX -> 32 com MTP + teto de memoria 27 GB + KV TurboQuant 3,5 bits; janela util ~32k e o oMLX nao trunca. OMP em vez do Pi puro pelo que ele adiciona (31 tools com `xd://`, `hub` para MCP, LSP/DAP, subagentes, skills, rules, memoria), e essa largura e o que custa 22,6k tokens na porta. A ideia: o lazy loading `xd://` ja existe; abrir para as tools caras, manter tudo alcancavel, medir em bugs reais.

Como foi feito: fork, harness, bugs semeados, corridas e textos pelo Claude Fable 5 (Claude Code, esforço alto), com o Vinicius definindo metas, escolhas e aprovacoes. ~2 dias de relogio (26-28/08/2026), 80 corridas pontuadas, ~22 h de modelo local, 1.486 requests capturadas.

Scripts: `../run-real.sh`, `../run-long.sh`, `../table-compare.py`, `../tools-used.py`, `../real/README.md`.

---

# O que mexi fora do fork, e como desfazer

Tudo aqui é aditivo. Nenhum arquivo seu foi sobrescrito ou apagado.

## 1. Contexto comprimido do OMP

| Arquivo | O que é |
|---|---|
| `~/.omp/agent/AGENTS.md` | Versão densa do seu `~/.claude/CLAUDE.md`, 1.875 → 1.010 tokens |
| `~/.omp/agent/skills/basic-memory-workflow/` | O detalhe do Basic Memory, lido sob demanda |
| `~/.omp/agent/skills/measured-quality/` | A regra do fixture rotulado à mão, lida sob demanda |
| `~/github/vinicius91carvalho/find-best-job/.omp/AGENTS.md` | Versão densa do `AGENTS.md` do projeto, 2.046 → 474 tokens |
| `~/github/vinicius91carvalho/find-best-job/.omp/skills/` | Três skills com o detalhe que saiu |

**O efeito:** o `.omp/` tem prioridade máxima de descoberta, então o omp lê
essas versões **no lugar de** `~/.claude/CLAUDE.md` e do `AGENTS.md` do projeto.
Os originais continuam intactos e o Claude Code continua lendo eles.

**Para desfazer:**

```sh
rm -rf ~/.omp/agent/AGENTS.md ~/.omp/agent/skills
rm -rf ~/github/vinicius91carvalho/find-best-job/.omp
```

O omp volta a ler os originais na hora. Nada mais precisa ser feito.

**Para manter:** não faça nada. Vale 2.437 tokens em toda requisição.

**Uma ressalva honesta:** eu comprimi as suas regras à mão, decidindo o que é
regra dura e o que é detalhe. Vale você ler os dois arquivos densos uma vez e
me dizer se cortei algo que importa. `omp compress`, que faria isso pela
ferramenta do projeto, travou no modelo local.

## 2. Bun

`mise` instalou `bun@1.4.0`, porque o repo do OMP exige e o `cli.ts` tem guarda
de versão. O seu `~/.config/mise/config.toml` é gerenciado pelo Nix e é somente
leitura, então **o padrão global não mudou**: continua o que era antes. Eu
chamo o 1.4.0 pelo caminho completo nos scripts.

## 3. O fork

`~/github/vinicius91carvalho/oh-my-pi`, branch `compact-prompt-for-local-models` (7 commits, usado pelos scripts de benchmark).
`~/github/vinicius91carvalho/oh-my-pi-pr`: worktree com o branch `pr/compact-prompt-for-local-models`, os mesmos 7 commits rebaseados no `upstream/main` e esmagados em 3. É esse que vai para o PR.
Desfazer: `git -C ~/github/vinicius91carvalho/oh-my-pi worktree remove ../oh-my-pi-pr`.

## 5. Worktrees dos projetos reais (benchmark)

| worktree | de | extra |
|---|---|---|
| `~/tools/qwen3.8-27b/eval/agentic/real/fbj` | `find-best-job`, branch `eval-bugs` + 4 `bug/ts-*` | `pnpm install`, `stealth-browser/` copiado do checkout principal, `pnpm build` |
| `~/tools/qwen3.8-27b/eval/agentic/real/infoproduct` | `infoproduct`, branch `eval-bugs` + 4 `bug/py-*` | `.venv` própria via `uv sync` |

Os checkouts principais não foram tocados. Desfazer: `git -C ~/github/vinicius91carvalho/find-best-job worktree remove --force ~/tools/qwen3.8-27b/eval/agentic/real/fbj` (idem infoproduct) e `git branch -D eval-bugs bug/ts-easy ...`.

## 6. `~/.omp/agent/models.yml`

Provider `omlxtap` adicionado no fim (mesmo servidor, via proxy de log na porta 1338). Só os scripts usam. Desfazer: apagar o bloco `omlxtap:`.

## 4. Basic Memory

Projeto novo `oh-my-pi` em `~/basic-memory/vinicius91carvalho/oh-my-pi`, com a
nota do plano e os resultados.

## 7. Servidores LSP (rodada 2)

`npm i -g typescript-language-server typescript pyright` (node do mise, `~/.local/share/mise/installs/node/latest/bin`). Nenhum modo chegou a usar. Desfazer: `npm rm -g typescript-language-server typescript pyright`.

## 8. Branches e sessões do benchmark

- `real/fbj`: branches `eval-bugs`, `eval-lsp` (master de 28/08, so para a tarefa ts-contract), `bug/ts-*`.
- Sessões do OMP gravadas em `eval/agentic/results-long*/<perfil>/sessions/` (nao em `~/.omp`).
- `~/.omp/agent/config.yml` nao foi alterado. Os perfis ficam em `eval/agentic/profiles/*.yml` e entram por `--config`.


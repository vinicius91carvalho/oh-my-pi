# Lista de tarefas (atualizada pelo Claude a cada passo)

Ultima atualizacao: 2026-08-28 10:05

## Em andamento
- [ ] Fixture 12 tarefas com p7k e o fork atual: responde se chega a 12/12 - ~30 min, dispara sozinho depois da sessao longa
- [ ] Very hard com a regra "Rule first" (p7k e p3k, py + ts): responde se a regra resolve o py-veryhard - ~1h30, dispara sozinho depois do fixture

## Depois que os 3 acima fecharem
- [ ] Se "Rule first" passar: commit 6 no branch do PR (template compacto) + teste; se nao: registrar que a regra sozinha nao basta
- [ ] Atualizar PR, issue e Reddit com: linha da p7k-long, resultado do fixture, resultado do very hard, contagem final de commits
- [ ] Rodar `table-compare.py` e `tools-used.py` uma ultima vez e conferir que os numeros dos textos batem
- [ ] Ressincronizar o branch `local-model-eval` (scripts + requests + textos)
- [ ] Salvar o fechamento no Basic Memory (projeto oh-my-pi)

## Publicacao (cada texto passa pela sua aprovacao antes)
- [ ] Push dos 2 branches para o fork (`compact-prompt-for-local-models`, `local-model-eval`)
- [ ] PR unico em can1357/oh-my-pi (CONTRIBUTING pede Discord antes; sua decisao)
- [ ] Comentario na issue #1734 com o link do PR
- [ ] Post no r/LocalLLaMA; crossposts em r/LocalLLM, r/LLMDevs, r/AI_Agents, r/ChatGPTCoding (checar regras de cada um no Chrome antes)
- [ ] Discord do OMP (link do PR) e issue no oMLX com os achados de operacao (paginas de 2k, processo inchando, rejeicoes de prefill)
- [ ] Voltar nos textos e trocar PR_LINK / REDDIT_LINK pelos links reais

## Feito
- [x] 8 bugs semeados e provados (4 TS, 4 Py) + 2 tarefas LSP
- [x] Rodada 1 (4 modos x 8 bugs) e rodada 1b (repeticoes sem Docker)
- [x] Rodada 2 (fork v4 + LSP): 4 modos x 10 tarefas + repeticoes pos-restart
- [x] Sessoes longas refeitas com compactacao em 20k: p3k 45/45, p7k 44/44
- [x] Fork: 5 commits rebaseados no upstream, 32 testes verdes, tsc limpo
- [x] Docs: PR completo (benchmark + receitas), issue, Reddit, README; secoes "why", "como foi feito", niveis com tempos, bug nao resolvido, velocidade (Reddit)
- [x] Branch de eval local com scripts, perfis e 1.486 requests capturadas

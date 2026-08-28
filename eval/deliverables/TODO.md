# Verificacoes: todas fechadas

- [x] Bateria de qualidade nos 4 perfis, com re-pontuacao apos achar os bugs do medidor.
- [x] Tokens medidos no SERVIDOR, nos dois contextos: projeto real (escada) e
      repo do benchmark (tabela de qualidade). Nunca misturados.
- [x] A frase do commit das rotas MCP era falsa (908->144). A/B limpo: 1222->551.
      A do promptProfile tambem (6045->1450). A/B limpo: 7412->6222. Ambas reescritas.
- [x] `promptProfile: full` rende **identico byte a byte** ao de antes do commit.
      33.440 bytes dos dois lados.
- [x] Quatro baldes do CI verdes. Os 710 arquivos num processo so sao instaveis
      na `main` tambem, entao usei a divisao que o proprio CI define.
- [x] Sondas do protocolo `xd://`: passam nos dois perfis, inclusive editar com
      o `edit` montado sem esquema nenhum no request.
- [x] Grounding: 6/6, a alucinacao nao se reproduziu. O verificador foi testado
      contra a resposta ruim original e reprova ela.
- [x] Diff dos dois templates por porta de ferramenta: o compacto tinha perdido
      as regras de `think` e `ast_grep`. Restauradas.
- [x] 36/36 regras do CLAUDE.md sobrevivem no compacto ou numa skill.
- [x] Zero dados pessoais nos textos que vao para fora.
- [x] Documentado o que mexi na maquina e como desfazer.

## Bugs do medidor que a propria medida pegou

1. `git status --porcelain` como prova de "nao mexeu em nada", com o runner
   escrevendo `answer.txt` dentro do repo de teste. Tres tarefas falhavam em
   TODOS os perfis, inclusive no controle.
2. `ask-01` passava por regex frouxo: aceitava a palavra "rate" enquanto o
   agente inventava a cotacao.
3. `xd-03` contava moedas com regex por linha, e o mapa `RATES` esta numa linha so.
4. Esperadores de fundo olhando se o arquivo existe, e o runner cria ele vazio
   no inicio. Aconteceu tres vezes; duas medidas chegaram a rodar juntas.
5. O verificador da compressao acusou 2 regras faltando; as duas estavam la,
   quebradas em fim de linha.

Padrao: cinco de cinco eram do medidor, nao do sistema medido. Falha identica
no controle e no tratamento e o sinal mais barato de que o bug e seu.

# Piloto: modelo local (Ollama) como motor da fase de conclusão

**Data**: 2026-09-13
**Motivo**: o autor não dispõe de verba para a API da Anthropic. Avaliou-se se
um modelo aberto, rodando localmente, sustenta os experimentos das Etapas D e E.
**Natureza**: piloto de viabilidade, fora do harness oficial (script no
scratchpad, sem alterar o repositório). Não é resultado de pesquisa; os números
servem para escolher o modelo e o desenho do prompt, e serão remedidos com
pré-registro na Etapa D.
**Custo**: zero. Hardware: Apple M1 Pro, 16 GB. Ollama 0.11.7.

---

## 1. Configuração

- Modelos: `qwen2.5-coder:7b` (4,7 GB) e `qwen2.5-coder:14b` (9,0 GB), quantização padrão do Ollama.
- Chamada: `POST http://localhost:11434/api/chat`, `temperature 0`, `seed 42`, mesmo prompt de sistema do protótipo (`nl2sql._PROMPT_SISTEMA`), mesma montagem do prompt de usuário (`nl2sql.montar_prompt_usuario`), 18 perguntas, uma execução.
- Avaliação: guardrails de entrada (`governance.validar_sql`), execução na Gold isolada, execution match estrito (`evaluate.normalizar`) e set match de conteúdo (`evaluate.conteudo_coberto`).
- Duas variantes de schema no prompt:
  - **atual**: uma linha por tabela com os nomes das colunas (o que o protótipo envia hoje);
  - **enriquecido**: tipo de cada coluna, nota de uma linha por tabela ("snapshot de hoje, sem coluna de data" / "série histórica" / "ativa é BOOLEAN"), e valores distintos das colunas VARCHAR com até 12 valores (value linking, caminho 1 do mapa de literatura).

## 2. Resultados

| Modelo | Schema | Estrito | Conteúdo | Bloqueios | Tempo (18 perguntas) |
|---|---|---|---|---|---|
| qwen2.5-coder:7b | atual | 6/18 (33,3%) | 7/18 (38,9%) | 1 | 57 s |
| qwen2.5-coder:14b | atual | 4/18 (22,2%) | 7/18 (38,9%) | 4 | 65 s |
| qwen2.5-coder:7b | enriquecido | 7/18 (38,9%) | 7/18 (38,9%) | 1 | 34 s |
| **qwen2.5-coder:14b** | **enriquecido** | **12/18 (66,7%)** | **13/18 (72,2%)** | 1 | 54 s |
| claude-sonnet-4-6 (preliminar, Gold anterior, k=3) | atual | 11/18 (61,1%) | 17/18 (94,4%) | 2 | (API) |

## 3. Padrões de erro observados

Com o schema **atual**, os dois modelos locais falham quase sempre do mesmo
jeito: inventam uma coluna `data` nas tabelas de snapshot (`leitos_status`,
`ocupacao_unidade`), induzidos pela frase do prompt que ancora "hoje" na data
de referência; tratam o booleano `ativa` como texto (`'Sim'`, `'N'`); e
escrevem `'enfermaria'` em minúscula (o mesmo erro do Sonnet em Q12). É
alucinação de schema, a categoria que Fei et al. (2026) mostram crescer quando
o modelo não tem contexto suficiente.

Com o schema **enriquecido**, o 14B elimina a coluna inventada e o erro de
booleano e acerta Q12. Os seis casos restantes do 14B:

| Pergunta | O que aconteceu | Natureza |
|---|---|---|
| Q01 | usou `gold.ocupacao_diaria` (fora do perfil enfermagem), valor correto | Violation Correct, igual ao Sonnet |
| Q05 | projetou só `unidade`, sem `taxa_ocupacao` | forma/projeção |
| Q08 | `DATE_SUB(...)`, sintaxe MySQL que o DuckDB não aceita | dialeto SQL |
| Q11 | coluna `bloqueados` inventada em `leitos_status` | alucinação de schema |
| Q14, Q16 | comparou `taxa_ocupacao > 0.80` e `> 0.85`; a coluna está em percentual 0-100 | escala não informada |

Q14 e Q16 indicam uma terceira informação de schema a expor no prompt: a
unidade ou faixa de valores das colunas numéricas (por exemplo, "percentual
0-100"). Q08 indica que o prompt deve nomear o dialeto (DuckDB) de forma mais
explícita para modelos menores.

O 7B continua inventando `data` mesmo com a nota explícita, o que sugere
limite de capacidade, não de prompt.

## 4. Decisão

1. **Motor da fase de conclusão: `qwen2.5-coder:14b` via Ollama, local.** Custo
   zero; roda as 18 perguntas em cerca de um minuto; permite `seed` fixa
   (reprodutibilidade local, RNC-003); nada sai do perímetro (responde à P-18);
   entra na literatura fichada (Qwen2.5-Coder em Pedroso et al. 2025, Silva et
   al. 2025 e Abedini et al. 2025). O 7B fica descartado por capacidade.
2. **O schema enriquecido passa a ser uma das variáveis pré-registradas da
   Etapa D**, com três componentes separáveis: tipos e notas de tabela; valores
   distintos (value linking); faixa das colunas numéricas. O piloto mostra que
   o efeito é grande em modelo local (22% para 67%), o que torna a Etapa D
   informativa mesmo sem API.
3. **Comparabilidade com o preliminar**: os 61,1% do Sonnet foram medidos com o
   schema atual sobre a Gold anterior. A Discussão vai comparar modelo fechado
   via API (preliminar) com modelo aberto local (fase final), declarando as
   duas diferenças (modelo e Gold). Se houver a recarga mínima da API em
   algum momento, rodam-se só as células base e melhor com o Sonnet (cerca de
   90 chamadas, abaixo de US$ 0,20) para fechar a ponte.
4. **Implementação (Etapa D)**: `MotorLocal` em `nl2sql.py` chamando o
   endpoint do Ollama com `urllib` (mesmo padrão sem SDK, DA-ARQ-003),
   parâmetros em `config.py` (`OLLAMA_ENDPOINT`, `MODELO_LOCAL`, `SEED` da
   amostragem), e `run_all.py llm --motor local`. A CI segue só com o oráculo.

## 5. Reprodução do piloto

Scripts no scratchpad da sessão (`piloto_local.py`, `piloto_local_rico.py`);
serão substituídos pelo motor oficial na Etapa D. Requer `ollama serve` e
`ollama pull qwen2.5-coder:14b`.

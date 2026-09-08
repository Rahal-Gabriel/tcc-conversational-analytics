# 01. Text-to-SQL clínico: sistemas, benchmarks e resultados

**Última atualização**: 2026-09-08
**Alimenta**: Introdução · Resultados e Discussão

Legenda de verificação: ✔ lido na fonte · ◐ só resumo de busca · ⚠ conferir dado.

---

## Resumo comparativo (para a Discussão)

| Trabalho | Dataset / domínio | Modelo | Configuração | Execution accuracy |
|---|---|---|---|---|
| Tanković et al. 2025 | TREQS / MIMIC-III, 1.000 perguntas, 5 repetições | Claude 3.5 | zero-shot, schema no prompt | 43,4% ± 0,1 |
| Tanković et al. 2025 | idem | GPT-4o | idem | 64,1% ± 0,6 |
| Tanković et al. 2025 | idem | Qwen2.5-72B (aberto) | idem | 57,6% ± 0,0 |
| Li et al. 2026 | SQL hospitalar local | GPT-4.1 | zero-shot | 78% ± 3,8 |
| Li et al. 2026 | idem | GPT-4.1 | few-shot | 96% ± 1,1 |
| Li et al. 2026 | idem | engenheiros de banco (humanos) | referência | 97% ± 1,7 |
| Waltl 2025 (LETHE-Chat) | ensaio clínico, 65 perguntas | modelos abertos locais, agente ReAct | agente com ferramentas e correção | 83,3% |
| Al Attrach et al. 2025 (M3) | MIMIC-IV, 100 perguntas do EHRSQL 2024 | Claude Sonnet 4 | agente MCP com ferramentas | 94% |
| Al Attrach et al. 2025 (M3) | idem | gpt-oss-20B (aberto) | idem | 93% |
| Liu et al. 2026 | registro cardiovascular, perguntas sintéticas | não informado no abstract | RAG com metadados enriquecidos | 94,5% / 92,5% / 82,0% (1, 2 e 3 campos) |
| BIRD (leaderboard 2026) | 12.751 perguntas, 95 bancos | melhores sistemas | pipelines complexos | 82,3% (humanos: 93,0%) |
| **Este TCC (preliminar)** | ocupação de leitos sintética, 18 perguntas, 3 execuções | claude-sonnet-4-6 | zero-shot, uma chamada, sob governança | **61,1% estrito; 94,4% conteúdo** |

Leitura sugerida: o resultado estrito do protótipo está na faixa dos trabalhos
zero-shot com uma única chamada (43% a 78%); o set match de conteúdo está na
faixa dos sistemas agênticos (83% a 94%). A diferença entre as duas faixas na
literatura vem de exemplos no prompt, correção iterativa por execução e
enriquecimento de schema, e não de modelos maiores. Isso orienta os caminhos 1
e 2 da conclusão.

---

## Fichas

### Lee, Kweon, Bae e Choi (2024): visão geral do EHRSQL 2024 ✔

- **Referência**: Lee, G.; Kweon, S.; Bae, S.; Choi, E. 2024. Overview of the
  EHRSQL 2024 shared task on reliable text-to-SQL modeling on electronic health
  records. In: Proceedings of the 6th Clinical Natural Language Processing
  Workshop (NAACL 2024). Association for Computational Linguistics. arXiv:2405.06673.
- **O que faz**: shared task sobre MIMIC-IV em que o sistema deve responder
  perguntas respondíveis e **abster-se** das não respondíveis. Teste com 934
  perguntas respondíveis e 233 não respondíveis (1.167).
- **Métrica**: Reliability Score RS(c): +1 por SQL correta; +1 por abstenção
  correta em pergunta não respondível; 0 por abstenção em pergunta respondível;
  −c por SQL errada ou por tentar responder pergunta não respondível. RS(0) sem
  punição, RS(10) moderado, RS(N) severo.
- **Resultados**: 1º LG AI Research e KAIST, RS(10) = 81,32 (self-training com
  pseudo-rótulos de perguntas não respondíveis, filtro por entropia de token e
  execução); 2º PromptMind, 74,89 (ensemble com unanimidade); 3º ProbGate,
  74,21 (limiar de log-probabilidade).
- **Relevância**: é a referência de avaliação citada no projeto de pesquisa.
  Introduz a ideia de que **abster-se é parte da confiabilidade**, o que dialoga
  com os bloqueios de governança do protótipo: uma recusa correta não é uma
  falha. Base para o conjunto adversarial (caminho 5).
- **Citar como**: Lee et al. (2024).

### Sistema vencedor do EHRSQL 2024 (LG AI Research e KAIST) ◐ ⚠

- **Referência**: [autores a conferir] 2024. LG AI Research & KAIST at EHRSQL
  2024: self-training large language models with pseudo-labeled unanswerable
  questions for a reliable text-to-SQL system on EHRs. In: Proceedings of the
  6th Clinical NLP Workshop (NAACL 2024). arXiv:2405.11162.
- **O que faz**: treinamento em duas etapas com pseudo-rótulos e filtragem por
  entropia de token e por execução da SQL. Diferença mínima entre RS(0) e RS(10),
  sinal de que o sistema evita respostas erradas ao classificá-las como não
  respondíveis.
- **Relevância**: mostra que a verificação por **execução** (rodar a SQL e
  inspecionar o resultado) é um filtro de confiabilidade usado pelo estado da
  arte; o protótipo já executa em conexão somente leitura, o que abre a
  possibilidade de sinalizar resultados vazios como "não respondível" (caso Q12).
- **Citar como**: [conferir autores] (2024).

### Al Attrach et al. (2025): M3, LLM conversacional sobre MIMIC-IV ✔ ⚠

- **Referência**: Al Attrach, R.; Moreira, P.; Fani, R.; Umeton, R.; Fiske, A.;
  Celi, L.A. 2025. M3: conversational LLMs simplify secure clinical data access,
  understanding, and analysis. arXiv:2507.01053. [veículo a conferir: a busca
  indica aceite no ML4H Symposium 2025; a página do arXiv não confirma]
- **O que faz**: agente via Model Context Protocol que traduz perguntas em SQL
  sobre MIMIC-IV (SQLite local ou BigQuery), com autenticação OAuth2, validação
  da consulta e log de auditoria. Devolve a SQL junto com o resultado para
  verificabilidade.
- **Resultados**: 100 perguntas respondíveis do EHRSQL 2024: Claude Sonnet 4
  94%, gpt-oss-20B 93%; em 100 não respondíveis, o gpt-oss-20B absteve-se
  corretamente em 69%. Falhas concentradas em raciocínio temporal e ambiguidade.
- **Relevância**: é o trabalho mais próximo do protótipo em intenção (acesso
  seguro, auditoria, validação de SQL). Diferenças: usa agente com ferramentas e
  várias chamadas, dados reais (MIMIC-IV), inglês, e não modela perfis de acesso
  nem anonimização em camadas. Bom contraste na Discussão: mesma família de
  modelo, 94% com agente contra 61% zero-shot sob governança.
- **Citar como**: Al Attrach et al. (2025).

### Waltl (2025): LETHE-Chat ✔

- **Referência**: Waltl, J. 2025. LETHE-Chat: schema-aware LLM agents for
  text-to-SQL on clinical trial databases. Dissertação (Mestrado). Institute for
  eHealth, FH Joanneum (Graz University of Applied Sciences), Graz, Áustria.
- **O que faz**: agente conversacional on-premise com modelos abertos (Ollama,
  LangGraph), duas arquiteturas (agente ReAct e grafo determinista de
  recuperação de schema, geração e correção), execução em **réplica somente
  leitura**, transparência dos traços de execução, alinhado a princípios do EU
  AI Act.
- **Resultados**: 65 perguntas curadas manualmente, execution accuracy 83,3%,
  com análise qualitativa de erros por categoria de necessidade de informação.
- **Relevância**: valida as escolhas de execução somente leitura, rastreabilidade
  e implantação local como compatíveis com governança de IA em saúde. É
  dissertação (literatura acadêmica, aceita pelo manual em 19.4), não artigo
  revisado por pares; citar com essa ressalva.
- **Citar como**: Waltl (2025).

### Tanković, Šajina e Lorencin (2025): comparação de LLMs em SQL médico ✔

- **Referência**: Tanković, N.; Šajina, R.; Lorencin, I. 2025. Transforming
  medical data access: the role and challenges of recent language models in SQL
  query automation. Algorithms 18(3): 124. DOI: 10.3390/a18030124.
- **O que faz**: avalia sete modelos (GPT-4o, GPT-4o-mini, Gemini 1.5 Pro,
  Claude 3.5, Llama 3.3 70B, Mixtral 8x22B, Qwen2.5 72B) em 1.000 perguntas do
  TREQS (MIMIC-III), **cinco repetições** por pergunta (5.000 consultas por
  modelo), medindo execution accuracy por comparação de conjuntos de resultado,
  consistência entre repetições, tokens e custo por consulta.
- **Resultados**: GPT-4o 64,1 ± 0,6; Gemini 1.5 Pro 60,8 ± 0,4; Qwen2.5-72B
  57,6 ± 0,0; GPT-4o-mini 53,6 ± 0,3; Llama 3.3-70B 53,4 ± 0,2; Mixtral 47,5 ±
  0,3; Claude 3.5 43,4 ± 0,1. Custo por consulta de US$ 0,00029 (GPT-4o-mini) a
  US$ 0,00701 (Claude 3.5). Fronteira de Pareto custo versus acurácia.
- **Ablação de prompt**: amostras de 5 linhas por tabela elevam o custo em 82% a
  150% com ganho inconsistente (−2,5% a +26,2%); um exemplo pergunta-SQL
  (one-shot) custa 6% a 13% a mais e melhora muito (até +85% relativo em modelos
  abertos). Principal causa de erro: resolução de termos médicos (códigos ICD),
  não sintaxe SQL.
- **Relevância**: (a) referência direta para o caminho 4 (comparação entre
  modelos com custo); (b) fundamenta o desenho do value linking barato (valores
  distintos, não linhas de amostra); (c) mostra que a variação entre repetições
  em temperatura fixa é pequena (≤ 0,6 ponto), coerente com o desvio nulo
  observado no protótipo; (d) o achado sobre termos médicos é análogo ao erro de
  Q12 (valor categórico com caixa errada).
- **Citar como**: Tanković et al. (2025).

### Liu et al. (2026): metadados enriquecidos e decomposição ✔

- **Referência**: Liu, W.; Qu, B.; Mallya, P.; Wu, J.; Thomas, K.; Hall, J.L.;
  Zhao, J.; Yin, Z. 2026. Optimizing an LLM-based clinical data querying system
  using metadata enrichment and task decomposition. AMIA Joint Summits on
  Translational Science Proceedings. [volume e páginas a conferir]
- **O que faz**: sistema de consulta em linguagem natural sobre um registro
  cardiovascular (GWTG-HF) que gera, por coluna, três formatos de metadados
  para recuperação, incluindo blocos específicos para **valores enumerados**
  (ex.: "código 6.0: óbito"), e decompõe perguntas com vários conceitos.
- **Resultados**: acurácia de 88,0% / 32,0% / 10,0% (perguntas com 1, 2 e 3
  campos) no baseline para 94,5% / 92,5% / 82,0% no sistema final.
- **Limitações declaradas**: um único registro; perguntas sintéticas geradas
  por IA, não de usuários reais; apenas SELECT; falhas com variáveis
  codificadas, ambiguidade clínica e consultas multi-etapa.
- **Relevância**: evidência mais direta de que **expor valores categóricos**
  (value linking) resolve a classe de erro de Q12. As limitações (perguntas
  sintéticas, autor único) são as mesmas ameaças à validade do protótipo, o que
  permite compará-las com honestidade.
- **Citar como**: Liu et al. (2026).

### Li et al. (2026): LLMs na gestão hospitalar ✔

- **Referência**: Li, J.; Zhang, Y.; Zhao, J.; He, S.; Li, D. 2026. Harnessing
  the potential of LLMs in hospital management: insights into medical data
  inquiry. The International Journal of Health Planning and Management. DOI:
  10.1002/hpm.70106. [volume, número e páginas a conferir]
- **O que faz**: NL2SQL para gestão hospitalar; compara modelos abertos
  ajustados com QLoRA (ChatGLM2-6B, Llama2-7B/13B) e modelos fechados (ChatGPT
  3.5, GPT-4.1) em zero-shot e few-shot, contra engenheiros de banco de dados.
- **Resultados** (execution accuracy): modelos abertos sem ajuste ≈ 0 a 0,04;
  QLoRA-Llama2-13B 0,41 ± 0,030; ChatGPT-3.5 zero-shot 0,44 ± 0,007 e few-shot
  0,94 ± 0,017; GPT-4.1 zero-shot 0,78 ± 0,038 e few-shot 0,96 ± 0,011;
  engenheiros 0,97 ± 0,017 (sem diferença significativa para o GPT-4.1
  few-shot, p = 0,42).
- **Relevância**: é o trabalho mais próximo em **domínio** (gestão hospitalar,
  não pesquisa clínica). Mostra que a distância entre zero-shot e few-shot é de
  18 a 50 pontos, o que sugere que o teto do protótipo é de desenho do prompt,
  não do modelo. Base de comparação para a hipótese de 80%.
- **Citar como**: Li et al. (2026).

### Wang, Shi e Reddy (2020): TREQS e MIMICSQL ◐

- **Referência**: Wang, P.; Shi, T.; Reddy, C.K. 2020. Text-to-SQL generation
  for question answering on electronic medical records. In: Proceedings of The
  Web Conference 2020 (WWW '20). ACM, p. 350-361. [páginas a conferir]
- **O que faz**: cria o MIMICSQL (10.000 pares pergunta-SQL sobre MIMIC-III) e
  o modelo TREQS. É o dataset usado por Tanković et al. (2025).
- **Relevância**: origem histórica do Text-to-SQL clínico; citar ao posicionar
  EHRSQL e MIMICSQL.
- **Citar como**: Wang et al. (2020).

### MedT5SQL (2024) ◐ ⚠

- **Referência**: [autores a conferir; afiliação Royal Holloway/Brunel] 2024.
  MedT5SQL: a transformers-based large language model for text-to-SQL
  conversion in the healthcare domain. Frontiers in Big Data 7: 1371680. DOI:
  10.3389/fdata.2024.1371680.
- **O que faz**: T5 ajustado no MIMICSQL (8.000/1.000/1.000). Exact match
  80,63%, string aproximado 98,9%, avaliação manual 90%.
- **Relevância**: exemplo de fine-tuning de modelo pequeno no domínio; contraste
  com a abordagem de prompt do protótipo. Uso opcional.
- **Citar como**: [conferir] (2024).

### Sivasubramaniam et al. (2024): SM3-Text-to-Query, benchmark sintético ✔

- **Referência**: Sivasubramaniam, S.; Osei-Akoto, C.; Zhang, Y.; Stockinger,
  K.; Fuerst, J. 2024. SM3-Text-to-Query: synthetic multi-model medical
  text-to-query benchmark. In: Advances in Neural Information Processing Systems
  (NeurIPS 2024), Datasets and Benchmarks Track. arXiv:2411.05521.
- **O que faz**: benchmark sobre dados **sintéticos** do Synthea (SNOMED-CT),
  408 perguntas-modelo expandidas para 10 mil pares, em SQL, MQL, Cypher e
  SPARQL.
- **Relevância**: legitima o uso de dados sintéticos como base de benchmark em
  saúde, publicado em veículo de primeira linha. Sustenta RNC-001 na Discussão.
- **Citar como**: Sivasubramaniam et al. (2024).

### Bardhan, Roberts e Wang (2023): revisão de escopo de QA sobre EHR ✔

- **Referência**: Bardhan, J.; Roberts, K.; Wang, D.Z. 2023. Question answering
  for electronic health records: a scoping review of datasets and models.
  arXiv:2310.08759.
- **O que faz**: revisa 25 datasets e 37 modelos de QA sobre prontuário
  (2005-2023); emrQA é o mais usado; conclui que a área é recente e pouco
  explorada.
- **Relevância**: citar na Introdução para caracterizar a maturidade do campo.
- **Citar como**: Bardhan et al. (2023).

### Lee et al. (2022): EHRSQL ✔ (já citado no documento)

- **Referência**: Lee, G.; Hwang, H.; Bae, S.; Kwon, Y.; Shin, W.; Yang, S.;
  Seo, M.; Kim, J.-Y.; Choi, E. 2022. EHRSQL: a practical text-to-SQL benchmark
  for electronic health records. In: NeurIPS 2022, Datasets and Benchmarks Track.
- **Relevância**: benchmark de referência do projeto de pesquisa. Manter.

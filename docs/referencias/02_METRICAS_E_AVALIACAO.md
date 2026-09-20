# 02. Métricas de avaliação, não determinismo e inferência estatística

**Última atualização**: 2026-09-20
**Alimenta**: Metodologia · Resultados e Discussão

Legenda de verificação: ✔ lido na fonte · ◐ só resumo de busca · ⚠ conferir dado.

---

## O que a literatura permite afirmar

1. O execution match estrito com um único banco tem falsos negativos e falsos
   positivos documentados pelos próprios autores da métrica (Zhong et al. 2020).
2. O benchmark BIRD passou a reportar um **Soft F1** que ignora ordem de colunas
   e tolera diferenças parciais, justamente para absorver divergências de
   projeção (Li et al. 2023; BIRD 2026).
3. Benchmarks clínicos recentes medem **confiabilidade** com penalidade por
   resposta errada e crédito por abstenção (Lee et al. 2024; Lee et al. 2024b,
   TrustSQL).
4. Temperatura zero **não** torna a avaliação reprodutível (Atil et al. 2025;
   Song et al. 2024); repetir a execução e reportar estabilidade é a prática
   recomendada.
5. Para proporções com n pequeno, o intervalo de Wilson é o recomendado (Brown
   et al. 2001).
6. Schema linking agressivo perde colunas necessárias; com modelos atuais, dar o
   schema completo quando cabe no contexto é a recomendação (Maamari et al. 2024).

---

## Fichas

### Zhong, Yu e Klein (2020): test suite accuracy ✔

- **Referência**: Zhong, R.; Yu, T.; Klein, D. 2020. Semantic evaluation for
  text-to-SQL with distilled test suites. In: Proceedings of the 2020
  Conference on Empirical Methods in Natural Language Processing (EMNLP).
  Association for Computational Linguistics, p. 396-411.
- **O que faz**: mostra que comparar resultados em **um único banco** produz
  falsos negativos (2,5% em média, 8,1% no pior caso no Spider) e falsos
  positivos (SQL errada que coincide no banco disponível). Propõe destilar um
  conjunto de bancos de teste com alta cobertura e exigir equivalência em todos.
- **Relevância**: fundamenta a discussão da métrica sensível à forma (caminho 6)
  com a fonte que definiu a prática. Permite dizer que a severidade observada
  (colunas extras contam como erro) é conhecida e aceita por comparabilidade.
- **Citar como**: Zhong et al. (2020).

### Pourreza e Rafiei (2023): avaliação de modelos e benchmarks cross-domain ◐ ⚠

- **Referência**: Pourreza, M.; Rafiei, D. 2023. Evaluating cross-domain
  text-to-SQL models and benchmarks. In: Proceedings of EMNLP 2023.
  arXiv:2310.18538. [páginas a conferir]
- **O que faz**: reavalia manualmente modelos no Spider e no BIRD e encontra
  divergências entre exact set match, execution accuracy e test suite; parte dos
  "erros" são rótulos de referência imperfeitos ou consultas equivalentes com
  projeção diferente.
- **Relevância**: apoio adicional para a categoria "conteúdo certo, forma
  diferente" da Tabela 3 do documento.
- **Citar como**: Pourreza e Rafiei (2023).

### BIRD e o Soft F1 ✔ (Li et al. 2023 já citado)

- **Referência do benchmark**: Li, J.; Hui, B.; Qu, G. et al. 2023. Can LLM
  already serve as a database interface? A big bench for large-scale database
  grounded text-to-SQLs. In: NeurIPS 2023, Datasets and Benchmarks Track.
- **Página oficial**: BIRD-SQL, https://bird-bench.github.io/ (acesso em 8 set.
  2026). Métricas: EX; **Soft F1-Score**, introduzido no Mini-Dev "para reduzir
  viés" da correspondência exata, comparando as tabelas de resultado linha a
  linha e célula a célula (verdadeiros positivos, falsos positivos e falsos
  negativos por linha, agregados em precisão, recall e F1), insensível à ordem
  de colunas e tolerante a valores ausentes; R-VES (eficiência). Leaderboard em
  set. 2026: 82,28% (SiriusAI-SQL), 82,22%, 81,95%; humanos 92,96%.
- **Relevância**: o Soft F1 é a métrica **publicada** mais próxima do "set match
  de conteúdo" do protótipo, com a vantagem de penalizar excesso (precisão) e
  não só falta (recall). Recomenda-se calculá-lo como segunda métrica secundária
  para dialogar com a literatura (ver 07 §6). Página oficial é fonte primária
  do benchmark; citar o artigo de 2023 para a métrica e a página para o valor
  do leaderboard, com data de acesso.
- **Implementação conferida (2026-09-20, Etapa C)**: a prosa da página
  oficial não basta para reproduzir a métrica; o código de referência
  (`bird-bench/mini_dev`, `evaluation/evaluation_f1.py`, último commit
  `f9d2750`, 19 set. 2025) faz o seguinte: remove linhas duplicadas
  preservando a ordem; **alinha as linhas por índice** (sensível à ordem em
  que o banco devolve); em cada par, conta as células geradas presentes na
  linha de referência (por valor, em qualquer posição) como acerto, as
  ausentes como excesso e as células de referência não encontradas como
  falta, todas como fração do número de colunas da referência; linhas
  sobrando contam 1 de excesso ou de falta; precisão, recall e F1
  micro-agregados por consulta; dois resultados vazios dão 1,0; erro de
  execução dá 0. `src/evaluate.py:soft_f1` reproduz isso sobre as linhas já
  ordenadas pela regra do execution match (desvio declarado, que remove a
  sensibilidade à ordem). Consequência: uma coluna extra em cada linha
  (Q04, Q13, Q14 do preliminar) dá F1 de 0,8, não 1,0 nem 0.
- **Citar como**: Li et al. (2023); BIRD (2026) para o leaderboard; o
  repositório `mini_dev` como fonte da implementação.

### Lee, Chay, Cho e Choi (2024): TrustSQL ✔

- **Referência**: Lee, G.; Chay, W.; Cho, S.; Choi, E. 2024. TrustSQL:
  benchmarking text-to-SQL reliability with penalty-based scoring.
  arXiv:2403.15879.
- **O que faz**: define confiabilidade como gerar SQL correta para perguntas
  viáveis **e abster-se** das inviáveis (incompatíveis com o schema ou além do
  SQL). Reanota ATIS, Advising e EHRSQL com perguntas inviáveis; mede o
  Reliability Score com penalidade configurável. Conclui que tanto pipelines
  (gerador + detector) quanto modelos unificados ainda precisam melhorar.
- **Relevância**: fornece o vocabulário para tratar bloqueios e abstenções como
  desfechos legítimos; base do conjunto adversarial (caminho 5) e da métrica de
  confiabilidade que o protótipo pode reportar além do execution match.
- **Citar como**: Lee et al. (2024b) [distinguir de Lee et al. 2024, EHRSQL 2024].

### Maamari et al. (2024): "a morte do schema linking?" ✔

- **Referência**: Maamari, K.; Abubaker, F.; Jaroslawicz, D.; Mhedhbi, A. 2024.
  The death of schema linking? Text-to-SQL in the age of well-reasoned language
  models. arXiv:2408.07702.
- **O que faz**: mostra que modelos recentes usam bem o schema mesmo com muitas
  colunas irrelevantes. Schema completo: recall 100%, falsos positivos 94,6%;
  filtragem agressiva (TCSL): falsos positivos 9,8%, mas recall 77,4% (perde
  colunas necessárias). Recomenda **dar o schema inteiro** quando cabe no
  contexto e investir em augmentação, seleção e correção. 71,83% no BIRD
  (primeiro lugar na época); 67,35% com GPT-4o ajustado no dev.
- **Relevância**: o protótipo já envia o schema Gold completo, alinhado a esta
  recomendação. O trabalho não testa exposição de valores; a lacuna de value
  linking permanece e é coberta por Liu et al. (2026). Citar na Discussão do
  caminho 1 e 2.
- **Citar como**: Maamari et al. (2024).

### Gao et al. (2024): DAIL-SQL e engenharia de prompt ◐

- **Referência**: Gao, D.; Wang, H.; Li, Y.; Sun, X.; Qian, Y.; Ding, B.; Zhou,
  J. 2024. Text-to-SQL empowered by large language models: a benchmark
  evaluation. Proceedings of the VLDB Endowment 17(5): 1132-1145. DOI:
  10.14778/3641204.3641221.
- **O que faz**: estudo sistemático de representação da pergunta, seleção e
  organização de exemplos no prompt; DAIL-SQL atinge 86,6% no Spider. Mostra
  que a forma de apresentar o schema e os exemplos muda a acurácia em vários
  pontos.
- **Relevância**: justifica tratar mudanças de prompt como variáveis
  experimentais controladas (ablação), como nos caminhos 1 e 2.
- **Citar como**: Gao et al. (2024).

### Atil et al. (2025): não determinismo em configurações "deterministas" ✔

- **Referência**: Atıl, B.; Aykent, S.; Chittams, A.; Fu, L.; Passonneau, R.J.;
  Radcliffe, E.; Rajagopal, G.R.; Sloan, A.; Tudrej, T.; Ture, F.; Wu, Z.; Xu,
  L.; Baldwin, B. 2025. Non-determinism of "deterministic" LLM system settings
  in hosted environments. In: Proceedings of the 5th Workshop on Evaluation and
  Comparison of NLP Systems (Eval4NLP). Association for Computational
  Linguistics, p. 135-148.
- **O que faz**: cinco LLMs por API, oito tarefas, dez execuções cada, com
  temperatura zero. Variação de acurácia de **até 15 pontos** entre execuções e
  diferença de até 70 pontos entre melhor e pior resultado possível. Propõe
  TARr@N e TARa@N (taxa de concordância total em N execuções).
- **Relevância**: sustenta a decisão de repetir a avaliação (k=3) e de reportar
  a estabilidade por pergunta; permite reportar TARa@3 = 100% como um resultado
  próprio (concordância total nas três execuções). Citar na Metodologia 2.6.
- **Citar como**: Atil et al. (2025).

### Song, Wang, Li e Lin (2024): avaliação não deve ignorar não determinismo ✔

- **Referência**: Song, Y.; Wang, G.; Li, S.; Lin, B.Y. 2024. The good, the bad,
  and the greedy: evaluation of LLMs should not ignore non-determinism.
  arXiv:2407.10457.
- **O que faz**: compara decodificação gulosa e amostragem em vários benchmarks;
  gulosa costuma ser melhor; alinhamento reduz variância; recomenda reportar
  variabilidade em vez de uma única saída por exemplo.
- **Relevância**: complementa Atil et al. (2025); citar junto.
- **Citar como**: Song et al. (2024).

### Brown, Cai e DasGupta (2001): intervalos para proporção binomial ✔

- **Referência**: Brown, L.D.; Cai, T.T.; DasGupta, A. 2001. Interval
  estimation for a binomial proportion. Statistical Science 16(2): 101-133.
  DOI: 10.1214/ss/1009213286.
- **O que faz**: mostra que o intervalo de Wald tem cobertura errática e
  recomenda o intervalo de **Wilson** (ou Jeffreys) para n pequeno e
  Agresti-Coull para n maior.
- **Relevância**: é a citação que faltava para a escolha do IC de Wilson na
  Metodologia 2.5.
- **Citar como**: Brown et al. (2001).

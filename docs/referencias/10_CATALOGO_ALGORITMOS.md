# 10. Avaliação do catálogo de algoritmos frente às etapas do projeto

**Última atualização**: 2026-09-13
**Origem**: catálogo fornecido pelo autor (82 algoritmos em 10 grupos, com
aplicação em saúde e ramo da matemática), avaliado a pedido antes da Etapa C.
**Alimenta**: desenho das Etapas C, D e E · Discussão (limitações e escala) ·
trabalhos futuros

---

## 1. Critério

O TCC não implementa um algoritmo de aprendizado de máquina: implementa uma
arquitetura de referência e mede governança versus utilidade em Text-to-SQL.
Um algoritmo do catálogo só entra se (a) resolver uma lacuna já apontada pela
banca simulada ou pelo mapa de literatura, (b) couber no prazo sem custo de
API relevante e (c) tiver respaldo na literatura de Text-to-SQL ou de
governança de dados. O que não passa nos três critérios fica registrado como
extensão, para a Discussão de escala ou trabalhos futuros.

## 2. Resultado por grupo

| Grupo do catálogo | Uso no projeto | Etapa | Decisão |
|---|---|---|---|
| 3. Similaridade e record linkage (Levenshtein, Damerau-Levenshtein, Jaro-Winkler, fuzzy matching) | **Value linking**: casar literais da SQL gerada com os valores reais das colunas categóricas (`'enfermaria'` versus `'Enfermaria'`); e schema linking leve (termos da pergunta versus nomes de colunas) | D | **Adotar** (correção determinista de valor pós-geração, além da lista de valores no prompt) |
| 3. Fellegi-Sunter, record linkage probabilístico | Modelo de ataque de reidentificação por ligação de registros (é o que um atacante faz contra a Gold) | B (já concluída) e Discussão | **Citar** como fundamento do risco medido por k-anonimato; não implementar |
| 7. NLP: TF-IDF, cosseno (BM25 na literatura) | Recuperar exemplos pergunta-SQL semelhantes para few-shot; a literatura mostra que exemplos recuperados reduzem excesso de acesso e elevam acurácia em 18 a 50 pontos | D (variante opcional) | **Opcional**, só com leave-one-out e declaração explícita, porque as 18 perguntas são do mesmo autor |
| 5. Detecção de anomalias (Isolation Forest, LOF) | Vigilância da trilha de auditoria: padrões anômalos de consulta (sondagem de schema, volume, horário) | E e trabalhos futuros | **Citar** como evolução da auditoria (CTRL-AUD-001); sem dados reais de uso não há o que treinar |
| 6. Séries temporais (Holt-Winters, ARIMA, Exponential Smoothing) | Previsão de ocupação como nova tabela Gold e novo tipo de pergunta ("ocupação prevista para amanhã") | trabalhos futuros | **Não** nesta entrega: muda o escopo de consulta para previsão; citar na Discussão de escala como extensão natural do domínio |
| 10. Otimização (programação linear para leitos, escalas) | Domínio vizinho (planejamento de leitos), não consulta em linguagem natural | nenhuma | **Não** |
| 1. Classificação e regressão | Predição clínica; fora do escopo (o protótipo não é SaMD e não prediz) | nenhuma | **Não**; um classificador de "pergunta não respondível" seria possível, mas exige conjunto de treino que não existe (n = 18 + adversarial) |
| 2. Clusterização | Perfis de pacientes; contradiz a minimização da Gold | nenhuma | **Não** |
| 4. Grafos | Schema linking por grafo só compensa em schemas grandes (dezenas de tabelas); a Gold tem quatro | nenhuma | **Não**; citar na Discussão de escala (SchemaGraphSQL) |
| 7. NLP: BERT, ClinicalBERT, embeddings | Schema linking por cross-encoder (usado por MaskSQL) | nenhuma | **Não** para quatro tabelas; a literatura recomenda schema completo quando cabe no contexto (Maamari et al. 2024) |
| 8. Deep learning em imagem | Sem relação | nenhuma | **Não** |
| 9. Recomendação | Sem relação | nenhuma | **Não** |

## 3. O que entra de fato: correção de valor por similaridade (Etapa D)

> **Situação (2026-09-20)**: **não entrou** na matriz pré-registrada da Etapa D
> (cinco células, sem correção pós-geração), por ser intervenção do sistema
> sobre a SQL do modelo, o que exigiria reportar acurácia bruta e corrigida
> lado a lado e uma sexta célula. A decisão fica para depois da execução: só
> se justifica se erros de grafia de valor persistirem com value linking (C2 e
> C4). Registrado em [tcc/etapas/2026-09-20_etapa-D.md](../tcc/etapas/2026-09-20_etapa-D.md) §2.

**Problema.** Q12 falhou porque o modelo escreveu `tipo = 'enfermaria'` e o
valor real é `'Enfermaria'`. O caminho 1 do mapa de literatura já prevê
expor os valores distintos das colunas categóricas no prompt (Liu et al.
2026). O catálogo acrescenta uma segunda linha de defesa, determinista e sem
custo de API: **corrigir o literal depois da geração**, comparando-o com os
valores reais da coluna referenciada.

**Como a literatura faz.** Sistemas de Text-to-SQL tratam value linking com
casamento aproximado de texto entre a pergunta (ou a SQL) e os valores das
células: BRIDGE usa casamento difuso de "anchor text" contra os valores do
banco (Lin, Socher e Xiong 2020, Findings of EMNLP; [conferir]); CHESS usa
hashing sensível à localidade e distância de edição para recuperar valores
candidatos (Talaei et al. 2024; [conferir]); a revisão de Shi et al. (2024),
já fichada, lista value linking como componente padrão do pipeline.

**Desenho proposto** (a detalhar no plano da Etapa D):

- Extrair os pares `coluna = 'literal'` da SQL gerada (parser simples ou
  `sqlglot`, se se aceitar a dependência).
- Para cada literal, obter os valores distintos da coluna na Gold isolada
  (só colunas categóricas de baixa cardinalidade, as mesmas do value linking
  no prompt).
- Normalizar (minúsculas, sem acentos) e medir a distância de edição
  (Damerau-Levenshtein, que trata transposições, ou `difflib` da biblioteca
  padrão, sem dependência nova). Aceitar a correção só com um único candidato
  dentro do limiar (por exemplo, razão de similaridade ≥ 0,9); caso contrário,
  não corrigir.
- Registrar na auditoria a SQL original e a corrigida, e reportar no harness
  as duas versões: **acurácia bruta** (SQL como o modelo gerou) e **acurácia
  com correção de valor**, lado a lado (RNC-002: nada de reportar só a
  melhor).

**Por que isso é cientificamente útil.** Separa dois efeitos que hoje se
misturam: o modelo não saber o valor (resolvido por informar no prompt) e o
modelo errar a grafia (resolvido por correção determinista). A matriz da
Etapa D passa a ter uma dimensão a mais, barata: sem value linking; valores
no prompt; correção pós-geração; ambos.

**Risco a declarar.** Correção automática de literal é uma intervenção no
que o modelo produziu; deve ser apresentada como camada do sistema
(guardrail de utilidade), não como acurácia do modelo, e nunca aplicada a
colunas numéricas ou de data.

## 4. O que entra como citação, não como código

- **Record linkage (Fellegi-Sunter)**: fundamenta, na Discussão da Etapa B,
  que o risco medido por k-anonimato é o risco de ligação de registros com
  fontes externas.
- **Detecção de anomalias na auditoria**: extensão do CTRL-AUD-001 para uso
  real; a literatura de detecção de ameaça interna em logs de acesso a
  prontuário usa Isolation Forest e LOF sobre padrões de consulta. Sem dados
  reais de uso, fica como trabalho futuro com desenho indicado.
- **Séries temporais**: a série `gold.ocupacao_diaria` permite, em produção,
  uma tabela Gold de previsão (Holt-Winters ou suavização exponencial) e um
  quinto tipo de pergunta. Citar como extensão do domínio na Discussão de
  escala, sem implementar.

## 5. Referências a incluir se o item for adotado

- Lin, X.V.; Socher, R.; Xiong, C. 2020. Bridging textual and tabular data
  for cross-domain text-to-SQL semantic parsing. In: Findings of EMNLP 2020.
  [conferir páginas]
- Talaei, S.; Pourreza, M.; Chang, Y.-C.; Mirhoseini, A.; Saberi, A. 2024.
  CHESS: contextual harnessing for efficient SQL synthesis. arXiv:2405.16755.
  [conferir]
- Fellegi, I.P.; Sunter, A.B. 1969. A theory for record linkage. Journal of
  the American Statistical Association 64(328): 1183-1210.
- Já fichados: Shi et al. (2024); Liu et al. (2026); Maamari et al. (2024);
  Ballesteros-Rodríguez et al. (2026).

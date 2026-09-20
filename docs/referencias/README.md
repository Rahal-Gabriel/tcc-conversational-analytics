# Referências: base de literatura para a conclusão do TCC

**Status**: base consolidada (revisão de 2026-09-08)
**Prioridade**: ALTA
**Última atualização**: 2026-09-13
**Alimenta (template TCC)**: Introdução · Metodologia · Resultados e Discussão · Referências

---

## 1. Propósito

Reunir, em fichas de leitura, os trabalhos relacionados ao tema do TCC
(Conversational Analytics em saúde, Text-to-SQL clínico, governança e segurança
de LLMs sobre bancos de dados, regulação brasileira, método e dados sintéticos),
para que a seção **Resultados e Discussão** do documento final faça a comparação
com a literatura que o manual USP/Esalq exige, e para que os experimentos da
fase de conclusão sejam desenhados sobre o que a literatura já sabe, sem
retrabalho.

Cada ficha traz: referência completa, o que o trabalho faz, números-chave,
relevância para este TCC e como citar. As fichas são a fonte única; o documento
do TCC deve citar a partir daqui.

## 2. Protocolo da busca

| Item | Descrição |
|---|---|
| Data | 8 de setembro de 2026 |
| Bases | arXiv, ACL Anthology, Europe PMC / PubMed, PeerJ, MDPI, SOL/SBC (SBSI, SBBD, SBCAS), Springer, portais oficiais (ANPD, ANVISA, gov.br) e busca web geral |
| Termos | text-to-SQL; EHRSQL; MIMIC; clinical data querying; conversational analytics; schema linking; value linking; execution accuracy; test suite accuracy; soft F1; reliability score; abstention; role-based access control text-to-SQL; prompt injection P2SQL; LLM guardrails; non-determinism temperature zero; Wilson interval; synthetic health data; Synthea; reference architecture; case study software engineering; LGPD inteligência artificial; ANPD anonimização; RDC 657 SaMD; text-to-SQL português |
| Recorte temporal | Preferência por 2020 em diante (o manual recomenda até cinco anos), com clássicos quando indispensáveis (Sweeney 2002; Brown et al. 2001; Zhong et al. 2020; Runeson e Höst 2009; Angelov et al. 2012) |
| Inclusão | Artigos revisados por pares, anais de conferência, preprints arXiv com relevância direta, documentos oficiais de órgãos reguladores, dissertações |
| Exclusão | Blogs, páginas de fornecedores e matérias de imprensa (o manual veda literatura cinzenta). Documentação de fornecedor aparece só como nota de contexto, nunca como citação |

## 3. Legenda de verificação

Cada ficha carrega um marcador de quanto da fonte foi efetivamente lido nesta
revisão. Antes do depósito, todo item **◐** ou **⚠** deve ser conferido na fonte.

| Marcador | Significado |
|---|---|
| **✔** | Texto integral ou abstract oficial lido; números conferidos |
| **◐** | Lido apenas o resumo de busca ou a página de índice; conteúdo plausível, mas não conferido na fonte |
| **⚠** | Há um dado específico (autores, ano, veículo, página) que precisa ser conferido |

## 4. Estrutura

```
docs/referencias/
├── README.md                              # este arquivo (protocolo, legenda, índice)
├── 01_TEXT2SQL_CLINICO.md                 # sistemas e benchmarks de Text-to-SQL em saúde
├── 02_METRICAS_E_AVALIACAO.md             # execution match, test suite, soft F1, RS, não determinismo, IC
├── 03_GOVERNANCA_E_SEGURANCA.md           # RBAC em Text-to-SQL, P2SQL, guardrails, governança de agentes
├── 04_REGULACAO_BRASIL.md                 # LGPD, ANPD, ANVISA e literatura jurídica nacional
├── 05_METODO_E_DADOS_SINTETICOS.md        # estudo de caso, arquitetura de referência, Synthea, lakehouse
├── 06_PORTUGUES_E_BRASIL.md               # Text-to-SQL em português e produção brasileira
├── 07_MAPA_LITERATURA_PARA_CAMINHOS.md    # o que a literatura diz sobre cada caminho da conclusão
├── 08_REFERENCIAS_FORMATADAS.md           # lista no formato USP/Esalq, pronta para colar
└── 09_PRIVACIDADE_E_MINIMIZACAO.md        # k-anonimato, quase-identificadores, pseudonimização, minimização em Text-to-SQL
```

## 5. Síntese em uma página

- **Onde o protótipo se posiciona.** Em Text-to-SQL clínico sem exemplos no
  prompt (zero-shot, uma chamada), a literatura reporta execution accuracy entre
  43% e 78% conforme modelo e dataset (Tanković et al. 2025; Li et al. 2026).
  Sistemas agênticos com ferramentas e correção iterativa chegam a 83% a 94%
  (Waltl 2025; Al Attrach et al. 2025). Os 61,1% estritos deste TCC, obtidos
  com uma única chamada e sob governança, ficam dentro da faixa zero-shot; os
  94,4% de conteúdo ficam na faixa dos sistemas agênticos. Ver
  [01](01_TEXT2SQL_CLINICO.md) e [07](07_MAPA_LITERATURA_PARA_CAMINHOS.md).
- **A métrica primária é reconhecidamente severa.** O próprio criador do
  execution accuracy do Spider documenta falsos negativos (Zhong et al. 2020), o
  BIRD introduziu o Soft F1 para absorver diferenças de projeção, e o EHRSQL 2024
  e o TrustSQL medem confiabilidade com penalidade por erro, não só acerto. Ver
  [02](02_METRICAS_E_AVALIACAO.md).
- **O custo da governança já tem nome na literatura.** Fei et al. (2026) definem
  seis desfechos para Text-to-SQL sob controle de acesso, entre eles o
  "Violation Correct" (SQL correta, mas fora da permissão), que é exatamente o
  caso de Q01 e Q11 deste TCC, e a métrica Safe-EX. Miyamoto et al. (2026) e
  Klisura et al. (2025) mostram que instruir a política no prompt não basta
  (vazamento de 5% a 42%), o que sustenta a escolha por verificação externa
  determinista (CTRL-GOV-005). Ver [03](03_GOVERNANCA_E_SEGURANCA.md).
- **Value linking é a lacuna mais barata de fechar.** Liu et al. (2026) mostram
  ganhos grandes ao expor valores enumerados no prompt; Tanković et al. (2025)
  alertam que amostras de linhas custam muito token e nem sempre ajudam. A
  solução de menor custo é expor só os valores distintos de colunas categóricas
  de baixa cardinalidade. Ver [07](07_MAPA_LITERATURA_PARA_CAMINHOS.md) §1.
- **Temperatura zero não garante reprodutibilidade.** Atil et al. (2025)
  mediram variação de acurácia de até 15 pontos entre execuções em
  configurações "deterministas"; isso justifica as k=3 execuções e a
  estabilidade por pergunta já adotadas. Ver [02](02_METRICAS_E_AVALIACAO.md).
- **Regulação.** A RDC 657/2022 exclui do escopo de SaMD o software de gestão
  administrativa e o que processa dados demográficos e epidemiológicos sem
  finalidade diagnóstica ou terapêutica, o que fundamenta a nota de
  enquadramento da seção 2.4 do documento. O guia de anonimização da ANPD ainda
  não foi publicado em versão final; o estudo preliminar já adota o modelo
  baseado em risco de reidentificação. Ver [04](04_REGULACAO_BRASIL.md).

## 6. Como usar nas seções do TCC

| Seção | O que buscar aqui |
|---|---|
| Introdução | Estado da arte de Text-to-SQL clínico ([01](01_TEXT2SQL_CLINICO.md)), lacuna de governança integrada ([03](03_GOVERNANCA_E_SEGURANCA.md)), marco regulatório ([04](04_REGULACAO_BRASIL.md)) |
| Metodologia | Métricas e IC ([02](02_METRICAS_E_AVALIACAO.md)), delineamento e ameaças à validade ([05](05_METODO_E_DADOS_SINTETICOS.md)), desenho dos experimentos novos ([07](07_MAPA_LITERATURA_PARA_CAMINHOS.md)) |
| Resultados e Discussão | Comparação numérica com a literatura ([01](01_TEXT2SQL_CLINICO.md) §resumo, [07](07_MAPA_LITERATURA_PARA_CAMINHOS.md)), leitura do custo da governança ([03](03_GOVERNANCA_E_SEGURANCA.md)), limitação da métrica ([02](02_METRICAS_E_AVALIACAO.md)) |
| Referências | [08_REFERENCIAS_FORMATADAS.md](08_REFERENCIAS_FORMATADAS.md) |

## 7. Contagem

| Tema | Fichas |
|---|---|
| Text-to-SQL clínico | 11 |
| Métricas e avaliação | 9 |
| Governança e segurança | 15 (3 acrescentadas em 2026-09-20: integridade de logs) |
| Regulação Brasil | 8 |
| Método e dados sintéticos | 9 |
| Português e Brasil | 6 |
| Privacidade e minimização (acrescentado em 2026-09-13) | 9 |
| **Total** | **67** (algumas fontes aparecem em mais de um tema) |

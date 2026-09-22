# Etapa F: redação da versão final (plano datado)

**Data**: 2026-09-21
**Fecha**: banca rodada 02, P-29 (alta); organiza o fechamento de P-01, P-06, P-07, P-13, P-19, P-21, P-22 (rodada 01) e dos itens do manual listados na rodada 02
**Depósito**: 2026-10-06
**Gera**: `docs/tcc/final/TCC_final.md` (fonte revisável) e `docs/tcc/final/TCC_final.docx` (no template oficial)

---

## 1. Como o texto será produzido

- **Fonte em Markdown no repositório** (`docs/tcc/final/TCC_final.md`),
  uma seção por dia, cada uma num PR curto, para o autor ler o diff como
  nas etapas anteriores.
- **Geração do .docx por pandoc** com o template oficial
  (`docs-tcc/Template TCC_PT (251, 252).docx`) como documento de
  referência de estilos; ajustes finos (quebras, legendas, sumário de
  tabelas) feitos no Word pelo autor no dia 29/09.
- **Toda citação sai das fichas** de `docs/referencias/` e a lista final
  sai de `08_REFERENCIAS_FORMATADAS.md`, conferida contra o manual.
- **Nenhum número novo** entra no texto sem estar num RES e num anexo
  versionado (RNC-002). A redação não roda experimento.
- O documento aprovado dos Resultados Preliminares
  (`docs/tcc/Resultados_Preliminares_TCC.docx`) é a base da Introdução e
  da Metodologia; os registros de etapa (`docs/tcc/etapas/`) e os RES são a
  base de Resultados e Discussão.

## 2. Estrutura e orçamento de páginas

Teto do manual: 30 páginas, incluindo referências e apêndices. Referência
de densidade: o documento aprovado tem cerca de 300 palavras por página.
Alvo: 27 páginas, com 3 de folga.

| Seção (template final) | Regras do manual | Páginas | Palavras (aprox.) |
|---|---|---|---|
| Título, autores, Resumo, palavras-chave | título até 15 palavras, afirmativo e conclusivo; resumo até 250 palavras, pretérito, sem citação | 1 | 300 |
| Introdução | até 2 páginas, sem subtópico, figura ou tabela | 2 | 650 |
| Metodologia | pretérito perfeito, impessoal, subtópicos na ordem dos resultados | 7 | 2.000 |
| Resultados e Discussão | subtópicos; tabelas e figuras numeradas; comparação com a literatura | 11 | 3.000 (mais 6 a 8 tabelas) |
| Conclusão | frases curtas, sem citação, tabela ou figura, sem repetir números; responde à hipótese | 1 | 350 |
| Referências | normas USP/Esalq | 3 | |
| Apêndices A e B | arquitetura; requisitos e controles | 2 | |
| **Total** | | **27** | |

## 3. Subtópicos e fontes

### Metodologia

| Subtópico | Fonte principal | Banca |
|---|---|---|
| Natureza da pesquisa e escopo | projeto de pesquisa; aprovado §2 | P-06 (não chamar de revisão sistemática), P-07 (escopo: por que não MIMIC-IV), P-21 (quem usaria, justificativa dos perfis) |
| Dados sintéticos e pipeline em camadas | camadas/01; DA-LAKE-002, 005, 006; RES-005, RES-009 | |
| Governança de entrada e saída | camadas/02 e 04; CTRL-GOV-001 a 008, CTRL-VALID-001/002, CTRL-AUD-001 | |
| Enquadramento regulatório | governanca/01; referencias/04 | P-19 (ANVISA por analogia, RDC 657/751/830), "projetada para atender" |
| Motores e desenho do prompt | camadas/03; DA-NL2SQL-003, 004; células C0 a C4, E0, E1 | |
| Conjuntos de avaliação | questions.py; 18 legítimas, 25 adversariais; regra de projeção e segundo anotador (RES-016) | P-24 |
| Métricas e análise | avaliacao/01; AVAL-001 a 003, Fei et al., Soft F1, RS(c), IC de Wilson, teste de sinal, TARa@k | P-27 |
| Pré-registro, reprodutibilidade e integridade | etapas D e E §1-8; avaliacao/02; tags; os três defeitos de medição corrigidos antes de reportar (um parágrafo) | P-03 |

### Resultados e Discussão

| Subtópico | Fonte | Tabela prevista | Banca |
|---|---|---|---|
| Pipeline, minimização e isolamento | RES-005, 008, 009 | 1 (volumes e k mínimo) | P-37, P-38 como limitação |
| Matriz de prompt com o modelo local | RES-011 | 2 (cinco células) | P-26, P-27 |
| Modelo e prompt cruzados; veredito da hipótese | RES-015, RES-016, RES-012 (histórico) | 3 (2 × 2), com sensibilidade à leitura do anotador | P-01, P-23, P-24, P-25 |
| Recusa devida e custo da governança | RES-013 | 4 (E0 e E1) e 5 (por família, condensada) | P-26, P-28, P-32 |
| O que sai do perímetro | RES-014 | 6 (inventário por motor) | P-36 (retenção projetada) |
| Estabilidade e reprodutibilidade | RES-017, RES-015 (API) | no texto | P-33 |
| Comparação com a literatura | referencias/01, 03, 07 | 7 (faixas publicadas) | P-13 |
| Limitações e ameaças à validade | seção 4 deste plano | no texto | P-22 |

## 4. O que entra como resultado, como limitação e o que sai

| Entra como resultado | Entra como limitação declarada | Sai do texto (fica no repositório) |
|---|---|---|
| Pipeline sintético com minimização e k ≥ 5 verificado (RES-005, RES-009) | Dado sintético: a LGPD não incide; "projetada para atender" | Números de volume por tabela além de um parágrafo |
| Isolamento físico da Gold e conexão sem acesso externo (RES-008, CTRL-GOV-006) | k-anonimato medido sobre todas as internações; no subconjunto em andamento k = 3 (P-37); sem regra de supressão para dado real (P-38) | Histórico da Etapa A (desvios encontrados pela banca, versão por versão) |
| Matriz de prompt local: 22,2% a 72,2%, recusa indevida zero com escopo (RES-011) | n = 18 e 25; só H3 com p < 0,05 | SQL completas por célula (ficam nos anexos, citados) |
| Ponte: Sonnet 74,1% e 90,7%; hipótese de 80% atingida na estimativa pontual com o modelo forte, não com o local; IC contém 80% (RES-015) | Autor único das perguntas, mitigado por um anotador (17 de 18) | Primeira execução da Etapa D e da Etapa E, e o detalhe da assinatura do TARa |
| Segundo anotador e sensibilidade (RES-016) | Domínio simples: 4 tabelas, sem junção (P-13, P-22) | Erratas detalhadas do preliminar (vira uma frase) |
| Recusa devida: 60% para 88% sem recusa indevida; escopo garantido, pertinência não (RES-013) | Pertinência: X13, X23, X24 entregues em E1; REG-ANPD-001 parcial | Tabelas completas de RS por família e contrafactual (resumo numa frase) |
| Perímetro: inventário e CTRL-GOV-008 (RES-014) | Nome próprio na pergunta e na trilha; retenção e expurgo só projetados (P-36) | Piloto com o modelo de 7 bilhões |
| Reprodutibilidade exata entre dias no local; API não determinista (RES-017) | Mesma máquina; outro hardware não testado | Discussão sobre o custo em tokens por célula (uma frase) |
| Três defeitos de medição encontrados e corrigidos antes de reportar (um parágrafo) | Latência de 4 a 5 s por pergunta num laptop (P-35); C4 com instrução de recusa não medida (P-34); ANVISA por analogia (P-19) | Rascunhos de Discussão de cada etapa (servem de matéria-prima, não entram literalmente) |

Opcionais da banca rodada 02 (P-31, contrafactual "vazio ou todo nulo";
P-32, recusas garantidas pelo dado, pelo verificador ou contingentes):
calculáveis sobre os anexos sem nova execução; entram como uma frase e
uma coluna na Tabela 5 se o orçamento de páginas permitir, decisão no dia
24/09. P-30 e P-40 viram uma frase cada na Discussão.

## 5. Cronograma

| Dia | Entrega | Quem |
|---|---|---|
| seg 21/09 | Este plano | Claude; autor aprova |
| ter 22/09 | Metodologia completa | Claude escreve; autor lê o diff |
| qua 23/09 | Resultados e Discussão, parte 1 (pipeline, matriz, ponte, anotador) | Claude; autor lê |
| qui 24/09 | Resultados e Discussão, parte 2 (recusa devida, perímetro, reprodutibilidade, literatura, limitações); decisão sobre P-31 e P-32 | Claude; autor lê |
| sex 25/09 | Introdução, Conclusão, Resumo, título e palavras-chave | Claude; autor lê |
| sáb 26/09 | Referências: conferir as marcadas "[conferir]", versões publicadas dos preprints, formato do manual | Claude; autor confere as que exigem acesso |
| dom 27/09 | Folga (reserva de atraso) | |
| seg 28/09 | Montagem no template (.docx), apêndices A e B, contagem de páginas e corte | Claude gera; autor ajusta no Word |
| ter 29/09 | Leitura integral pelo autor; envio ao orientador | autor |
| qua 30/09 | Banca simulada, rodada 03, sobre o documento montado | Claude (agente) |
| qui 01/10 e sex 02/10 | Correções da rodada 03 e do orientador | Claude e autor |
| sáb 03/10 e dom 04/10 | Reserva | |
| seg 05/10 | Revisão de forma: pretérito, terceira pessoa, travessões, instruções do template removidas, numeração de tabelas | Claude e autor |
| ter 06/10 | Depósito | autor |

## 6. Checklist do manual (conferido no dia 05/10)

- [ ] Até 30 páginas, incluindo referências e apêndices
- [ ] Título até 15 palavras, afirmativo e conclusivo, compatível com a Conclusão
- [ ] Resumo até 250 palavras, pretérito, sem citação; palavras-chave até cinco, diferentes do título
- [ ] Introdução até 2 páginas, sem subtópico, figura ou tabela
- [ ] Metodologia no pretérito perfeito, impessoal
- [ ] Conclusão sem citação, tabela ou figura, respondendo à hipótese
- [ ] Referências no formato do manual; literatura cinzenta identificada
- [ ] Nenhum travessão; nenhuma instrução do template no arquivo
- [ ] Nenhum nome de participante (o segundo anotador aparece como "um colega do autor, sem participação no projeto")

## 7. Registro de andamento

| Data | Seção | Palavras | Observação |
|---|---|---|---|
| 2026-09-21 | Metodologia | cerca de 2.350 (orçamento 2.000) | Citações no formato do manual (item 17: só a inicial maiúscula, "e" entre dois autores, autor institucional por extenso com sigla), diferente do documento aprovado, que usava caixa alta; fonte das tabelas da Metodologia como "Dados originais da pesquisa". Geração do .docx com o template testada |

Pendências para o dia 26/09 (referências), anotadas durante a redação:

- Incluir Atil et al. (2025) em `08_REFERENCIAS_FORMATADAS.md` (fichado em `02`, ausente da lista).
- Renomear Lee et al. (2024) do EHRSQL 2024 para 2024a na lista, porque o texto cita "Lee et al., 2024a, 2024b" (manual, item 17.2: mesmo autor e ano, letras minúsculas).
- Não incluir Johnson et al. (2023) na lista final: o MIMIC-IV deixou de ser citado no texto (o escopo é apresentado como delimitação afirmativa, sem contraste com o projeto de pesquisa, por decisão do autor em 2026-09-22).
- Limitação a escrever em 24/09 (seção de limitações), retirada da Metodologia por decisão do autor em 2026-09-22: a matriz de perfis foi desenhada pelo autor a partir da finalidade de cada função e não foi validada em campo com um hospital (banca rodada 01, P-21).
| 2026-09-22 | Resultados e Discussão, parte 1 | cerca de 1.790 (orçamento da seção inteira: 3.000) | Tabelas 2 (minimização), 3 (matriz local) e 4 (modelo × prompt); veredito da hipótese com a sensibilidade ao anotador; 61,1% do preliminar como observação histórica. Escrita antes do dia previsto (23/09) a pedido do autor |
| 2026-09-22 | Resultados e Discussão, parte 2 | cerca de 2.000 (seção inteira: 3.800, orçamento 3.000) | Tabelas 5 (E0 e E1), 6 (famílias), 7 (perímetro) e 8 (literatura); P-31 e P-32 entraram como uma frase cada; achado colateral da execução diagnóstica; limitações. A seção estourou o orçamento em cerca de 800 palavras (2,5 páginas): candidatos a corte no dia 28/09, nesta ordem: parágrafo do RS(10), detalhe das recusas contingentes, parágrafo da regra de vazio ou nulo, Tabela 6 (pode virar frase) |
| 2026-09-22 | Título, autores, Resumo, palavras-chave, Introdução e Conclusão | Resumo 250; Introdução cerca de 680; Conclusão cerca de 400 | Título com 12 palavras ("viabiliza" no lugar de "habilita"); palavras-chave sem palavra do título; Conclusão sem citação nem número; hipótese respondida em duas partes. Titulação e e-mail do orientador ficaram como marcador para o autor. Total do texto: cerca de 7.550 palavras (25 páginas) antes de referências e apêndices; o corte de 28/09 precisa tirar 1 a 2 páginas |
| 2026-09-22 | Referências | 40 entradas | Todas as obras citadas conferidas na web por agente (18 itens com dado incerto); quatro correções de veículo ou ano (Klisura 2026, Al Attrach 2026, Pedro et al. com título e autores da versão ICSE, Shi 2025) aplicadas no texto e na lista; formato do manual (itens 18 e 19); nenhum marcador "conferir" restante. Escrita antes do dia previsto (26/09) |
| 2026-09-22 | Revisão externa do texto (apontamentos recebidos pelo autor) | | Onze apontamentos conferidos e todos aplicados: IC de Wilson da ponte calculado sobre a média exata (correção em `matriz.py`, anexos da ponte regenerados, errata em RES-015); 2.012 internações; "183 interações do segundo dia" no lugar de "366 chamadas"; "interações" onde a pergunta pode não chegar ao modelo; Resumo sem o "258"; recusa "pelo modelo" em E0 explicada (convenção do harness, 0 de 23 excluídas as barradas na entrada); RS reportado com c = 0 e 10; Tabela 8 compara a família "sem resposta" (60%) com Al Attrach; Conclusão diz "não gerou recusa indevida" e declara o custo de uma pergunta; "9 do verificador e 2 do filtro"; duas células repetidas; parágrafo dos defeitos encurtado na Metodologia |
| 2026-09-22 | Revisão de estilo (padrões de escrita de IA apontados ao autor) | | Removidas as frases de efeito antitéticas ("O obstáculo central está em outro lugar", "Modelo e prompt importaram, e interagiram", "O que o verificador não garantiu foi a pertinência", "a resposta é dupla e deve ser lida assim"), as construções "não X, mas Y" e as ressalvas repetidas ("o que fica declarado", "depois dos números"); ritmo variado nos parágrafos afetados. Segunda leitura de estilo prevista para a montagem final (28/09) |

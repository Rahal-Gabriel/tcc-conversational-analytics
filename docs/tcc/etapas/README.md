# Etapas da fase de conclusão

**Status**: registro vivo
**Prioridade**: ALTA
**Última atualização**: 2026-09-20
**Alimenta (template TCC)**: Metodologia · Resultados e Discussão · Conclusão

---

## 1. Propósito

Registrar, uma etapa por arquivo, tudo o que foi feito na fase de conclusão do
TCC (após a aprovação dos Resultados Preliminares): motivação, o que mudou no
código e na documentação, evidências reproduzíveis, números antes e depois,
perguntas da banca simulada que a etapa fecha, e um rascunho do texto que a
etapa gera para a Discussão. É o insumo direto da redação final.

## 2. Plano (definido em 2026-09-13 a partir da banca, rodada 01)

| Etapa | Tema | Fecha (banca) | API | Situação |
|---|---|---|---|---|
| A | Isolamento físico da Gold e guardrails endurecidos | P-09, P-11 | não | concluída (2026-09-13) |
| B | Minimização da Gold, k-anonimato, idade correta, nomenclatura (pseudonimização) | P-15, P-16, P-17 | não | concluída (2026-09-13) |
| C | Harness: rotulagem por tipo, Over/Proper Refusal e Safe-EX, Soft F1, auditoria com horário real | P-02, P-04, P-14, P-20 | não | concluída (2026-09-20) |
| D | Matriz 2×2 de prompt (value linking × schema por perfil) sobre base enriquecida, motor local, artefatos versionados, tag | P-03, P-08 (parcial), P-10 | não (motor local) | concluída (2026-09-20: D1 pré-registro e código, D2 execução, ponte com o Sonnet em §12, RES-015; repetição em outro dia em 2026-09-21, RES-017) |
| E | Conjunto adversarial (25 perguntas, cinco famílias), abstenção por instrução como variável, CTRL-GOV-008 (PII na pergunta), inventário do que sai do perímetro | P-12, P-18 | não (motor local) | concluída (2026-09-20: E1 pré-registro e código, E2 execução; repetição em outro dia em 2026-09-21, RES-017) |
| F | Redação: hipótese original, comparação com literatura, escopo, ANVISA/LGPD, manual | P-01, P-05, P-06, P-07, P-13, P-19, P-21, P-22 | não | plano datado em 2026-09-21 ([2026-09-21_etapa-F-plano.md](2026-09-21_etapa-F-plano.md)); redação de 22/09 a 05/10 |

## 3. Etapas

| Arquivo | Etapa | Resultado gerado |
|---|---|---|
| [2026-09-13_etapa-A.md](2026-09-13_etapa-A.md) | A | RES-008, DA-LAKE-005, CTRL-GOV-007 |
| [2026-09-13_etapa-B.md](2026-09-13_etapa-B.md) | B | RES-009, DA-LAKE-006, CTRL-LAKE-001, errata de RES-005 |
| [2026-09-13_piloto-modelo-local.md](2026-09-13_piloto-modelo-local.md) | piloto | escolha do motor local (Qwen 14B) para as Etapas D e E |
| [2026-09-20_etapa-C.md](2026-09-20_etapa-C.md) | C | RES-010, DA-AVAL-003/004/005, DA-VALID-003, AVAL-002 e AVAL-003 redefinidos, errata da Tabela 4 em RES-007 |
| [2026-09-20_etapa-D.md](2026-09-20_etapa-D.md) | D | DA-NL2SQL-003/004; hipóteses H1 a H4 datadas antes dos números (D1); RES-011 (matriz: C3 vence, 72,2%, recusa indevida zero) e RES-012 (C0 vs preliminar, histórico); RES-015 (ponte com o Sonnet: 90,7% em C3, modelo e prompt cruzados); anexos em `anexos/etapa-D/` e `anexos/ponte-sonnet/`, tags `etapa-D` e `ponte-sonnet`; correção da assinatura do TARa |
| [2026-09-20_etapa-E.md](2026-09-20_etapa-E.md) | E | CTRL-GOV-008, REG-LGPD-008, DA-GOV-003, DA-AVAL-006; RES-013 (recusa devida: escopo garantido pelo verificador, pertinência pela abstenção; E1 operacional) e RES-014 (perímetro); anexos em `anexos/etapa-E/`, tag `etapa-E` |
| [2026-09-21_repeticao-outro-dia.md](2026-09-21_repeticao-outro-dia.md) | D e E (repetição) | RES-017: C3 e E1 idênticos entre dias após reinício do servidor (TARa entre dias 100%) |
| [2026-09-21_etapa-F-plano.md](2026-09-21_etapa-F-plano.md) | F (plano) | cronograma até o depósito, orçamento de 27 páginas, o que entra como resultado, como limitação e o que sai (banca P-29) |

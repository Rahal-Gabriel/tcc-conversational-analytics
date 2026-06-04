# Mapa: Documentação → Seções do Template do TCC

**Status**: referência
**Prioridade**: ALTA
**Última atualização**: 2026-06-04

---

## 1. Propósito

Servir de ponte entre a documentação modular e o template de Resultados
Preliminares do MBA USP/Esalq. Para cada seção do template, indica quais
módulos e identificadores fornecem o conteúdo, de modo que a redação do TCC seja
montada a partir da documentação, e não reescrita do zero.

> Estrutura do template (USP/Esalq): Título → Autores → Resumo (opcional nesta
> etapa) → Palavras-chave → Introdução → Metodologia → Resultados Preliminares →
> Conclusão (opcional) → Agradecimento → Referências → Apêndice. Teto de 30
> páginas.

## 2. Índice por seção do template

### Introdução

Contextualização, justificativa e objetivo. A base já está no projeto de
pesquisa; a documentação reforça o problema (governança fragmentada) e a
proposta (arquitetura integrada).

| Fonte | Conteúdo que fornece |
|---|---|
| [arquitetura/01_VISAO_GERAL.md](../arquitetura/01_VISAO_GERAL.md) | Visão da arquitetura de referência e das quatro camadas |
| [governanca/01_CONFORMIDADE_REGULATORIA.md](../governanca/01_CONFORMIDADE_REGULATORIA.md) §1-3 | Marco regulatório (LGPD, ANVISA, ANPD) e a lacuna de governança |

### Metodologia (Material e Métodos)

Redigir no pretérito, impessoal. Pode ter subtópicos, na mesma ordem dos
Resultados.

| Subtópico sugerido | Fonte |
|---|---|
| Natureza e delineamento da pesquisa | Projeto de pesquisa (estudo de caso instrumental + protótipo) |
| Geração do dataset sintético | [camadas/01_PIPELINE_LAKEHOUSE.md](../camadas/01_PIPELINE_LAKEHOUSE.md) §2; [DA-LAKE-002](../arquitetura/02_DECISOES_ARQUITETURAIS.md) |
| Arquitetura em quatro camadas | [arquitetura/01_VISAO_GERAL.md](../arquitetura/01_VISAO_GERAL.md); [DA-ARQ-001](../arquitetura/02_DECISOES_ARQUITETURAIS.md) |
| Modelo de governança | [camadas/02](../camadas/02_GOVERNANCA_ENTRADA.md), [camadas/04](../camadas/04_VALIDACAO_SAIDA.md); CTRL-* |
| Conformidade regulatória | [governanca/01_CONFORMIDADE_REGULATORIA.md](../governanca/01_CONFORMIDADE_REGULATORIA.md); REG-* |
| Método de avaliação | [avaliacao/01_METODOLOGIA_AVALIACAO.md](../avaliacao/01_METODOLOGIA_AVALIACAO.md); AVAL-* |
| Reprodutibilidade e integridade | [avaliacao/02_REPRODUTIBILIDADE_CI.md](../avaliacao/02_REPRODUTIBILIDADE_CI.md); RNC-002/003 |

### Resultados Preliminares

Subtópicos na mesma ordem da Metodologia, com os resultados parciais.

| Resultado | Fonte |
|---|---|
| Camada Bronze coerente (com números) | [RES-001](01_RESULTADOS_PRELIMINARES.md#res-001-camada-bronze-gerada-e-coerente) |
| Mapeamento regulatório | [RES-002](01_RESULTADOS_PRELIMINARES.md#res-002-mapeamento-regulatório-completo) |
| Reprodutibilidade e integridade | [RES-003](01_RESULTADOS_PRELIMINARES.md#res-003-reprodutibilidade-e-integridade) |
| Arquitetura de referência documentada | [RES-004](01_RESULTADOS_PRELIMINARES.md#res-004-arquitetura-de-referência-documentada) |

### Conclusão / Considerações Finais (opcional nesta etapa)

Sintetizar o estado parcial e o caminho até a validação da hipótese. Fonte:
[tcc/01_RESULTADOS_PRELIMINARES.md](01_RESULTADOS_PRELIMINARES.md) §5.

### Referências

As do projeto de pesquisa, formatadas pelas normas USP/Esalq.

### Apêndice (opcional)

Candidatos: diagrama de componentes ([arquitetura/01](../arquitetura/01_VISAO_GERAL.md) §2),
tabela de requisitos e controles ([governanca/01](../governanca/01_CONFORMIDADE_REGULATORIA.md) §4),
modelo de dados das camadas ([camadas/01](../camadas/01_PIPELINE_LAKEHOUSE.md)).

## 3. Índice reverso: cada módulo → seções que alimenta

| Módulo | Introdução | Metodologia | Resultados | Apêndice |
|---|:---:|:---:|:---:|:---:|
| arquitetura/01_VISAO_GERAL | ● | ● | | ● |
| arquitetura/02_DECISOES_ARQUITETURAIS | | ● | ● | |
| arquitetura/03_REGRAS_CRITICAS | | ● | ● | |
| camadas/01_PIPELINE_LAKEHOUSE | | ● | ● | ● |
| camadas/02_GOVERNANCA_ENTRADA | | ● | ● | |
| camadas/03_MOTOR_TEXT2SQL | | ● | | |
| camadas/04_VALIDACAO_SAIDA | | ● | ● | |
| governanca/01_CONFORMIDADE_REGULATORIA | ● | ● | ● | ● |
| avaliacao/01_METODOLOGIA_AVALIACAO | | ● | | |
| avaliacao/02_REPRODUTIBILIDADE_CI | | ● | ● | |
| tcc/01_RESULTADOS_PRELIMINARES | | | ● | |

## 4. Lembretes de formatação do template

- Título: curto, afirmativo, conclusivo, no máximo 15 palavras, sem expressões
  como "Estudo de...", "Análise de...".
- Introdução: no máximo duas páginas, sem subtópicos, figuras ou tabelas.
- Palavras-chave: até cinco, diferentes das do título, separadas por
  ponto-e-vírgula.
- Antes do depósito, remover do arquivo do template todas as instruções
  originais.

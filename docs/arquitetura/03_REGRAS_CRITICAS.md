# RNC: Regras Críticas (Princípios Inegociáveis)

**Status**: PARCIAL
**Prioridade**: CRÍTICA
**Última atualização**: 2026-06-04
**Alimenta (template TCC)**: Metodologia · Resultados Preliminares

---

## Propósito

Registrar os princípios que **nunca podem ser violados** em nenhuma etapa da
pesquisa. Uma violação de RNC compromete a integridade científica do trabalho,
não apenas a qualidade do software. Cada regra deve ser verificada antes de
qualquer alteração relevante.

> Estas regras derivam dos "Princípios inegociáveis" do `GUIA_DESENVOLVIMENTO.md` e são a
> referência de mais alta prioridade da documentação.

---

### RNC-001: Dados 100% sintéticos

- **Descrição**: Toda a pesquisa usa exclusivamente dados sintéticos. Nenhuma
  informação real, em nenhuma etapa.
- **Motivação**: Elimina na origem o risco de exposição de dados sensíveis de
  saúde e permite que a arquitetura seja replicada por outras instituições.
- **Enforcement**: Geração determinista via Faker a partir de `SEED`; a PII
  presente na Bronze é fabricada, não coletada.
- **Status**: VALIDADO (a Bronze é gerada inteiramente por código sintético).
- **Código**: `src/data_gen.py`.
- **Relacionado**: [REG-PESQ-001](../governanca/01_CONFORMIDADE_REGULATORIA.md).

### RNC-002: Integridade dos resultados (acurácia só vem do LLM real)

- **Descrição**: Números de acurácia só são válidos quando vêm de uma execução
  real do harness com o motor LLM. O motor oráculo serve apenas para autoteste
  da tubulação e **nunca** deve ser apresentado como desempenho do modelo.
- **Motivação**: Confundir o autoteste com o desempenho do modelo invalidaria a
  hipótese central do TCC (acurácia superior a 80%).
- **Enforcement**: Separação explícita dos dois motores; a CI roda apenas o
  oráculo; nenhum número de acurácia é reportado até a execução real.
- **Status**: PARCIAL (princípio em vigor; motores a implementar).
- **Relacionado**: [DA-NL2SQL-001](02_DECISOES_ARQUITETURAIS.md#da-nl2sql-001-dois-motores-intercambiáveis-llm-e-oráculo),
  [avaliacao/01_METODOLOGIA_AVALIACAO.md](../avaliacao/01_METODOLOGIA_AVALIACAO.md).

### RNC-003: Determinismo e reprodutibilidade

- **Descrição**: Uma `SEED` fixa e uma data de referência (`SIM_TODAY`)
  controlam toda a geração de dados e as consultas que mencionam "hoje" ou
  "agora". A mesma configuração reproduz os mesmos dados e os mesmos números.
- **Motivação**: Sem reprodutibilidade, os resultados não são verificáveis por
  terceiros, o que é requisito de uma pesquisa séria.
- **Enforcement**: `SEED` e `SIM_TODAY` centralizados em `config.py`; verificado
  entre versões de Python (3.12 e 3.14).
- **Status**: VALIDADO (Bronze reprodutível byte a byte sob a mesma config).
- **Código**: `src/config.py:14-25`.
- **Relacionado**: [avaliacao/02_REPRODUTIBILIDADE_CI.md](../avaliacao/02_REPRODUTIBILIDADE_CI.md).

### RNC-004: Nenhuma credencial no código ou no histórico do git

- **Descrição**: Nenhuma chave de API no código ou no histórico do git. As
  credenciais do LLM são lidas sempre de variável de ambiente.
- **Motivação**: Segurança básica; uma chave vazada no histórico é difícil de
  revogar e expõe custo e dados.
- **Enforcement**: `ANTHROPIC_API_KEY` lida de `os.environ`; a CI nunca usa
  chave (roda só o oráculo).
- **Status**: VALIDADO.
- **Código**: `src/config.py:70-73`.

### RNC-005: PII nunca sobrevive à Silver

- **Descrição**: As colunas de identificação direta (`nome`, `cpf`,
  `data_nascimento`) existem só na Bronze e não podem existir na Silver nem na
  Gold. `id_paciente` é pseudonimizado (hash) na Silver.
- **Motivação**: É a materialização da anonimização exigida pela LGPD para dados
  sensíveis de saúde. A camada exposta ao LLM (Gold) jamais contém dado
  individual identificável.
- **Enforcement**: Transformação Bronze→Silver remove PII e deriva
  `faixa_etaria`; filtro de saída barra nomes de campo sensível.
- **Status**: IMPLEMENTADO na Silver (PII removida, `id_paciente` pseudonimizado
  por SHA-256 com salt, `faixa_etaria` derivada; teste rápido verifica que
  `silver.paciente` não contém `nome`/`cpf`/`data_nascimento`). Filtro de saída
  ao usuário final ainda a implementar em `governance.py`.
- **Código**: `src/config.py:59` (`CAMPOS_SENSIVEIS`);
  `src/pipeline.py:construir_silver` e `src/pipeline.py:_pseudo`.
- **Relacionado**: [DA-LAKE-002](02_DECISOES_ARQUITETURAIS.md#da-lake-002-pii-proposital-na-bronze),
  [REG-LGPD-001](../governanca/01_CONFORMIDADE_REGULATORIA.md),
  [REG-LGPD-002](../governanca/01_CONFORMIDADE_REGULATORIA.md).

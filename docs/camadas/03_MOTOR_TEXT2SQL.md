# NL2SQL: Camada 3 - Motor Text-to-SQL

**Status**: PROJETADO
**Prioridade**: ALTA
**Última atualização**: 2026-06-04
**Alimenta (template TCC)**: Metodologia · Resultados Preliminares

---

## 1. Propósito

Descrever o motor que traduz uma pergunta em português para uma SQL somente
leitura sobre a camada Gold. O motor existe em duas implementações
intercambiáveis: o **LLM** (real) e o **oráculo** (referência), conforme
[DA-NL2SQL-001](../arquitetura/02_DECISOES_ARQUITETURAIS.md#da-nl2sql-001-dois-motores-intercambiáveis-llm-e-oráculo).

## 2. Os dois motores

| Motor | Papel | Usa chave? | Gera os números do TCC? |
|---|---|---|---|
| **LLM** | Tradução real pergunta → SQL via API Anthropic | Sim | **Sim** |
| **Oráculo** | Devolve a SQL de referência da pergunta | Não | Não (apenas autoteste da tubulação) |

> O oráculo nunca pode ser apresentado como desempenho do modelo
> ([RNC-002](../arquitetura/03_REGRAS_CRITICAS.md#rnc-002-integridade-dos-resultados-acurácia-só-vem-do-llm-real)).
> Ele serve só para confirmar que o pipeline (geração → governança → execução →
> avaliação) está correto, sem custo e sem chave.

## 3. Contrato do prompt (motor LLM)

Conforme [DA-NL2SQL-002](../arquitetura/02_DECISOES_ARQUITETURAIS.md#da-nl2sql-002-prompt-com-schema-gold-e-data-de-referência):

- **Entrada do prompt**: o schema da camada Gold e a data de referência
  (`SIM_TODAY`), para ancorar consultas que mencionam "hoje" ou "agora".
- **Saída exigida**: uma única SQL somente leitura, sem markdown e sem
  explicação.

Configuração da chamada (`src/config.py:70-73`):

| Parâmetro | Valor |
|---|---|
| Endpoint | `https://api.anthropic.com/v1/messages` |
| Header de versão | `anthropic-version: 2023-06-01` |
| Modelo | `ANTHROPIC_MODEL` (padrão `claude-sonnet-4-6`), via ambiente |
| Chave | `ANTHROPIC_API_KEY`, via ambiente (nunca no código, [RNC-004](../arquitetura/03_REGRAS_CRITICAS.md#rnc-004-nenhuma-credencial-no-código-ou-no-histórico-do-git)) |
| Cliente HTTP | `urllib` da biblioteca padrão ([DA-ARQ-003](../arquitetura/02_DECISOES_ARQUITETURAIS.md#da-arq-003-chamada-http-ao-llm-via-biblioteca-padrão)) |

## 4. Relação com as camadas vizinhas

- A SQL produzida pelo motor **não é executada diretamente**: passa antes pelos
  guardrails de entrada ([camadas/02](02_GOVERNANCA_ENTRADA.md)) e, após
  executar, pela validação de saída ([camadas/04](04_VALIDACAO_SAIDA.md)).
- O motor só conhece o schema Gold; nunca recebe Bronze ou Silver
  ([DA-LAKE-003](../arquitetura/02_DECISOES_ARQUITETURAIS.md#da-lake-003-gold-é-a-única-camada-exposta-ao-llm)).

## 5. Mapeamento para o código

| Item | Local | Status |
|---|---|---|
| Motor LLM e motor oráculo | `src/nl2sql.py` | PROJETADO |
| Parâmetros do LLM | `src/config.py:70-73` | IMPLEMENTADO |
| Conjunto pergunta → SQL de referência | `src/questions.py` | PROJETADO |

## 6. Teste rápido (a implementar)

Com o motor oráculo, toda pergunta do conjunto de avaliação deve produzir a
própria SQL de referência, e o execution match deve resultar em 100% (autoteste
da tubulação). Qualquer divergência indica erro no harness, não no modelo.

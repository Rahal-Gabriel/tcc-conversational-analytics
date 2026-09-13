# REG: Conformidade Regulatória (LGPD, ANVISA, ANPD)

**Status**: PARCIAL (mapeamento concluído; controles em implementação)
**Prioridade**: CRÍTICA
**Última atualização**: 2026-09-13
**Alimenta (template TCC)**: Introdução · Metodologia · Resultados Preliminares

---

## 1. Propósito

Mapear os controles de governança da arquitetura para os requisitos do marco
regulatório brasileiro aplicável ao uso de IA generativa sobre dados clínicos.
Cada requisito tem identificador estável `REG-[NORMA]-[NUM]`, e a tabela cruza
requisito → controle implementado (`CTRL-*`) → camada/módulo → situação.

> **Aviso.** Mapeamento referencial de natureza técnica entre controles de
> engenharia e princípios regulatórios. Não constitui parecer jurídico. Os
> números de artigos e resoluções devem ser conferidos na fonte oficial antes
> do depósito final.

## 2. Marco regulatório considerado

- **LGPD** (Lei nº 13.709/2018). Dados de saúde são dados pessoais sensíveis
  (art. 5º, II; art. 11). Relevantes: princípios do art. 6º (finalidade,
  adequação, necessidade, segurança, prevenção, responsabilização), medidas de
  segurança do art. 46 e anonimização do art. 5º, XI, e art. 12.
- **ANVISA**, software como dispositivo médico (SaMD), Resoluções RDC nº
  657/2022, 751/2022 e 830/2023 (controle, segurança e rastreabilidade do
  software de saúde).
- **ANPD**, Radar Tecnológico sobre Inteligência Artificial Generativa
  (novembro de 2024), que reafirma a aplicação integral da LGPD a sistemas com
  LLMs e destaca os riscos de alucinação e de uso secundário não autorizado.

## 3. Premissa de base: dados 100% sintéticos

Toda a pesquisa usa dados sintéticos com `SEED` e `SIM_TODAY` fixos
(`src/config.py`). Não há tratamento de dados pessoais reais em nenhuma etapa, o
que elimina na origem o risco de exposição. A PII existe de propósito apenas na
Bronze, para tornar a pseudonimização demonstrável, e nunca sobrevive à Silver
([RNC-001](../arquitetura/03_REGRAS_CRITICAS.md#rnc-001-dados-100-sintéticos),
[RNC-005](../arquitetura/03_REGRAS_CRITICAS.md#rnc-005-pii-nunca-sobrevive-à-silver)).

## 4. Requisitos e controles

A coluna **Situação** reflete o estado do protótipo: `config` significa que os
parâmetros já estão centralizados em `src/config.py`; `projetado` significa que
o controle está definido no design e a lógica será implementada no módulo
indicado; `implementado` significa que o controle tem código com teste rápido
passando.

| ID | Requisito regulatório | Origem | Controle na arquitetura | Camada / módulo | Situação |
|---|---|---|---|---|---|
| `REG-LGPD-001` | Proteção reforçada de dados sensíveis e minimização | LGPD art. 11; art. 6º (necessidade) | Remoção de `nome`, `cpf`, `data_nascimento` na Silver; `faixa_etaria` no lugar da data; Gold sem identificador substituto nem `sexo`, `data_admissao`, `id_unidade`, com k-anonimato verificado (k >= 5) | Silver e Gold / `pipeline.py`, CTRL-LAKE-001 | implementado |
| `REG-LGPD-002` | Anonimização e pseudonimização | LGPD art. 5º, XI; art. 12; art. 13, par. 4 | Pseudonimização de `id_paciente` por HMAC-SHA256 com chave lida do ambiente (informação adicional guardada separadamente); o pseudônimo não chega à Gold. Declarado como pseudonimização, não anonimização: o dado da Silver continua pessoal | Silver / `pipeline.py` | implementado |
| `REG-LGPD-003` | Minimização na exposição (só o necessário) | LGPD art. 6º (necessidade, adequação) | Apenas a Gold é exposta ao motor; Bronze e Silver inacessíveis por isolamento físico (arquivo próprio da Gold) e, adicionalmente, por análise textual | Gold / `config.GOLD_DB_PATH`, CTRL-GOV-007, CTRL-GOV-004, CTRL-GOV-002 | implementado |
| `REG-LGPD-004` | Controle de acesso por finalidade e perfil | LGPD art. 6º (finalidade); ANVISA RDC | Perfis `gestor`, `enfermagem`, `administrativo` autorizam só tabelas Gold específicas | Entrada / `config.PERFIS`, CTRL-GOV-005 | config |
| `REG-LGPD-005` | Segurança e prevenção de comando indevido | LGPD art. 46; art. 6º (segurança, prevenção) | Guardrails CTRL-GOV-001 a 003 e 006: SQL única somente leitura, bloqueio de escrita/admin, bloqueio de múltiplas instruções, conexão read-only | Entrada / `governance.py` | projetado |
| `REG-LGPD-006` | Prevenção de vazamento de sensível na resposta | LGPD art. 11; ANPD (uso secundário) | Filtro de saída CTRL-VALID-002: bloqueia coluna com nome de campo sensível | Saída / `config.CAMPOS_SENSIVEIS`, `governance.validar_saida` | implementado |
| `REG-LGPD-007` | Rastreabilidade e prestação de contas | LGPD art. 6º (responsabilização); ANVISA RDC | Auditoria CTRL-AUD-001: registro de toda pergunta e resposta com timestamp, usuário, perfil, SQL e evento | Auditoria / `governance.registrar_pergunta`, `governance.registrar_resposta` | implementado |
| `REG-ANPD-001` | Mitigação de alucinação da IA generativa | ANPD, Radar de IA Generativa | Aterramento CTRL-VALID-001: toda tabela citada deve existir no schema Gold conhecido | Saída / `governance.validar_saida` | implementado |
| `REG-ANPD-002` | Prevenção de uso secundário não autorizado | ANPD, Radar de IA Generativa | Escopo restrito por perfil, execução somente leitura e registro integral limitam o uso ao fim declarado | Entrada e Auditoria / `governance.py` | projetado |
| `REG-ANVISA-001` | Controle, segurança e rastreabilidade do SaMD | ANVISA RDC 657/751/830 | Conjunto de guardrails versionados, auditoria e reprodutibilidade do software | Transversal / `governance.py`, CI | projetado |
| `REG-PESQ-001` | Reprodutibilidade e integridade do experimento | Boas práticas de pesquisa; suporte à responsabilização | Determinismo por `SEED` e `SIM_TODAY`; dados sintéticos; separação motor LLM (números) vs oráculo (autoteste) | Transversal / `config.py`, `nl2sql.py`, CI | config |

## 5. Leitura para os Resultados Preliminares

A tabela evidencia que a governança não é apêndice do motor de IA, mas
atravessa as quatro camadas. Já estão consolidados como resultado parcial o
desenho dos controles e a centralização dos parâmetros que os sustentam em
`src/config.py` (perfis, tabelas Gold autorizadas, campos sensíveis, semente e
data de referência). A lógica está implementada em `pipeline.py`
(pseudonimização, minimização e k-anonimato) e `governance.py` (guardrails,
isolamento físico, filtro de saída e auditoria), e as linhas com situação
`implementado` são verificáveis por teste automatizado. Os itens ainda
`projetado` (REG-LGPD-005, REG-ANPD-002, REG-ANVISA-001) são tratados nas
etapas C e E da fase de conclusão.

Este mapeamento é registrado como resultado parcial em
[RES-002](../tcc/01_RESULTADOS_PRELIMINARES.md#res-002-mapeamento-regulatório-completo).

## 6. Rastreabilidade cruzada

| Requisito | Controles | Decisões | Regra crítica |
|---|---|---|---|
| REG-LGPD-001/002 | CTRL-LAKE-001 | DA-LAKE-002, DA-LAKE-004, DA-LAKE-006 | RNC-005 |
| REG-LGPD-003 | CTRL-GOV-007, CTRL-GOV-004, CTRL-GOV-002 | DA-LAKE-003, DA-LAKE-005 | RNC-005 |
| REG-LGPD-004 | CTRL-GOV-005 | DA-GOV-001 | - |
| REG-LGPD-005 | CTRL-GOV-001/002/003/006 | DA-GOV-002 | - |
| REG-LGPD-006 | CTRL-VALID-002 | DA-VALID-002 | RNC-005 |
| REG-LGPD-007 | CTRL-AUD-001 | - | - |
| REG-ANPD-001 | CTRL-VALID-001 | DA-VALID-001 | - |
| REG-PESQ-001 | - | DA-NL2SQL-001 | RNC-001, RNC-002, RNC-003 |

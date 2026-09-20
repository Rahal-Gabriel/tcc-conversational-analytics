# VALID: Camada 4 - Validação de Saída

**Status**: IMPLEMENTADO
**Prioridade**: CRÍTICA
**Última atualização**: 2026-09-20
**Alimenta (template TCC)**: Metodologia · Resultados Preliminares

---

## 1. Propósito

Descrever os controles aplicados **depois** da execução da SQL e antes de
entregar a resposta ao usuário: aterramento contra alucinação, filtro de dados
sensíveis e auditoria da resposta. É a última barreira de governança.

## 2. Controles de validação

A serem implementados em `src/governance.py`.

| ID | Controle | Requisito |
|---|---|---|
| `CTRL-VALID-001` | Aterramento: toda tabela referenciada na SQL deve existir no schema Gold conhecido | REG-ANPD-001 |
| `CTRL-VALID-002` | Filtro de saída: bloquear a resposta se qualquer coluna do resultado tiver nome de campo sensível | REG-LGPD-006 |
| `CTRL-AUD-001` | Auditoria: registrar toda pergunta e toda resposta com horário real, data de simulação, usuário, perfil, SQL, motor, evento, controle e hash do resultado, em cadeia de hashes verificável | REG-LGPD-007 |

### CTRL-VALID-001: Aterramento (anti-alucinação)

- **Descrição**: Antes de aceitar o resultado, confirmar que todas as tabelas
  citadas na SQL pertencem ao schema Gold conhecido. Uma tabela inventada pelo
  LLM bloqueia a consulta.
- **Motivação**: Mitigar alucinação, risco destacado pela ANPD no Radar de IA
  Generativa.
- **Alcance real (registrado após a banca simulada, rodada 01, P-11)**: no
  fluxo atual, uma tabela inexistente já é barrada na entrada por CTRL-GOV-005
  e, se escapasse, a execução falharia antes de `validar_saida`. Este controle
  é, portanto, **redundante por desenho** (defesa em profundidade sobre o
  schema) e não trata a alucinação que mais importa à ANPD: a resposta
  plausível e errada (por exemplo, um resultado vazio apresentado como zero).
  A redação do TCC não deve apresentá-lo como "mitigação de alucinação" sem
  essa ressalva. O tratamento de resultado vazio ou implausível como
  "não respondível" fica para a Etapa E (conjunto adversarial e abstenção).
- **Status**: IMPLEMENTADO (`src/governance.py:validar_saida`); alcance
  limitado, ver acima.
- **Relacionado**: [DA-VALID-001](../arquitetura/02_DECISOES_ARQUITETURAIS.md#da-valid-001-aterramento-contra-o-schema-gold-conhecido).

### CTRL-VALID-002: Filtro de campo sensível

- **Descrição**: Se qualquer coluna do resultado tiver nome de campo sensível
  (`nome`, `cpf`, `data_nascimento`, `id_paciente_pseudo`), a resposta é
  bloqueada.
- **Motivação**: Última barreira contra vazamento de dado sensível, mesmo que
  algo tenha escapado das camadas anteriores.
- **Alcance real**: o filtro é por **nome** de coluna e um alias (`cpf AS c`)
  o contorna (banca, rodada 01, P-09). Desde 2026-09-13 a garantia de que
  nenhum campo sensível chega à saída vem do isolamento físico
  (CTRL-GOV-007): a Gold isolada não contém coluna alguma de
  `CAMPOS_SENSIVEIS`, o que o teste rápido de `src/pipeline.py` verifica. O
  filtro por nome permanece como camada adicional.
- **Status**: IMPLEMENTADO (`src/governance.py:validar_saida`); garantia
  efetiva em CTRL-GOV-007.
- **Código**: `src/config.py:59` (`CAMPOS_SENSIVEIS`).
- **Relacionado**: [DA-VALID-002](../arquitetura/02_DECISOES_ARQUITETURAIS.md#da-valid-002-filtro-de-saída-por-nome-de-campo-sensível),
  [RNC-005](../arquitetura/03_REGRAS_CRITICAS.md#rnc-005-pii-nunca-sobrevive-à-silver).

### CTRL-AUD-001: Auditoria da pergunta e da resposta

- **Descrição**: Registrar em log toda pergunta recebida e toda resposta.
  Cada interação gera dois registros JSON ligados por `id_interacao`:
  - **entrada**: `momento_real` (UTC, relógio do sistema), `data_simulacao`
    (`SIM_TODAY`), `usuario`, `perfil`, `pergunta` (com dado pessoal já
    mascarado por [CTRL-GOV-008](02_GOVERNANCA_ENTRADA.md), Etapa E);
  - **saída**: os mesmos campos mais `sql`, `motor`, `evento`, `controle` e
    `motivo` (quando bloqueada), `hash_resultado` e `n_linhas` (quando algo foi
    entregue; o resultado em si nunca é copiado para o log).
  Todo registro carrega `hash_anterior` e `hash` (SHA-256 do conteúdo
  canônico), formando uma cadeia a partir de `config.AUDIT_HASH_GENESIS`.
  `verificar_trilha` lê o arquivo, confere cada hash e a cadeia, e devolve as
  interações completas (entrada e saída com todos os campos obrigatórios).
- **Motivação**: Rastreabilidade e prestação de contas, exigidas tanto pela
  LGPD (responsabilização) quanto pelas normas da ANVISA (rastreabilidade do
  software de saúde). A versão anterior ancorava o horário em `SIM_TODAY`, não
  registrava o que foi entregue e não protegia a integridade do arquivo; a
  banca simulada (rodada 01, P-20) apontou que isso não sustentava
  responsabilização. Revisto na Etapa C
  ([DA-VALID-003](../arquitetura/02_DECISOES_ARQUITETURAIS.md#da-valid-003-trilha-de-auditoria-com-horário-real-e-encadeamento-por-hash)).
- **Fora do escopo (declarado)**: autenticação. `usuario` e `perfil` são
  recebidos do chamador; numa implantação, a assinatura de
  `registrar_pergunta` receberia a identidade verificada pelo provedor de
  identidade do hospital. O encadeamento detecta adulteração, mas não
  autentica o autor do registro (exigiria assinatura com chave).
- **Status**: IMPLEMENTADO. Registro de entrada em
  `src/governance.py:registrar_pergunta`, de resposta em
  `src/governance.py:registrar_resposta`, verificação em
  `src/governance.py:verificar_trilha`. O autoteste adultera e remove
  registros e exige que a quebra seja detectada na linha certa.
- **Código**: `src/config.py` (`AUDIT_LOG_PATH`, `AUDIT_HASH_GENESIS`);
  `src/governance.py` (`CAMPOS_ENTRADA`, `CAMPOS_SAIDA`, `EVENTOS`,
  `hash_resultado`, `registrar_pergunta`, `registrar_resposta`,
  `verificar_trilha`).
- **Relacionado**: [REG-LGPD-007](../governanca/01_CONFORMIDADE_REGULATORIA.md),
  [REG-ANVISA-001](../governanca/01_CONFORMIDADE_REGULATORIA.md),
  [AVAL-003](../avaliacao/01_METODOLOGIA_AVALIACAO.md).

## 3. Eventos de auditoria

| Evento | Significado |
|---|---|
| `correto` | Resultado entregue bate com a referência (execution match positivo) |
| `incorreto` | Resultado entregue não bate com a referência |
| `bloqueado` | Consulta barrada por algum guardrail (entrada ou saída); `controle` e `motivo` dizem qual |
| `erro` | Falha de geração ou de execução (SQL inválida, erro de banco, falha do motor) |
| `recusado` | O motor se absteve de gerar SQL (resposta vazia ou `config.MARCADOR_RECUSA`) |

A completude e a integridade do log são lidas do arquivo pelo indicador
[AVAL-003](../avaliacao/01_METODOLOGIA_AVALIACAO.md). A execução diagnóstica
do avaliador (SQL barrada executada só para medir conteúdo) **não** gera
evento: é do harness, não do sistema.

## 4. Mapeamento para o código

| Item | Local | Status |
|---|---|---|
| Campos sensíveis | `src/config.py:59` (`CAMPOS_SENSIVEIS`) | IMPLEMENTADO |
| Caminho do log de auditoria | `src/config.py:37` (`AUDIT_LOG_PATH`) | IMPLEMENTADO |
| Registro de auditoria da entrada | `src/governance.py:registrar_pergunta` | IMPLEMENTADO |
| Aterramento e filtro de saída | `src/governance.py:validar_saida` | IMPLEMENTADO |
| Registro da resposta, evento, controle e hash do resultado | `src/governance.py:registrar_resposta`, `hash_resultado` | IMPLEMENTADO |
| Cadeia de hashes e verificação da trilha | `src/governance.py:_gravar`, `verificar_trilha`; `config.AUDIT_HASH_GENESIS` | IMPLEMENTADO |

## 5. Teste rápido

`python -m src.governance`: além dos casos de entrada, cobre os casos que
**devem** bloquear na saída — SQL que cita uma tabela Gold inexistente
(aterramento, CTRL-VALID-001) e resultado cuja projeção inclui uma coluna
sensível (filtro de saída, CTRL-VALID-002), e exercita a trilha num arquivo
temporário: entrada e saída encadeadas, horário real em UTC distinto da data
de simulação, hash do resultado, interação incompleta detectada, e quebra da
cadeia detectada na linha certa após adulteração e após remoção de um
registro. O fluxo completo (entrada → execução → saída → auditoria) é
exercitado de ponta a ponta em `python run_all.py oracle`, que falha se a
trilha ficar incompleta ou quebrada.

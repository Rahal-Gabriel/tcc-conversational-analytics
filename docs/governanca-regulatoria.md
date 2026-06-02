# Governança e conformidade regulatória

Este documento mapeia os controles de governança da arquitetura de referência
para os requisitos do marco regulatório brasileiro aplicável ao uso de IA
generativa sobre dados clínicos. Serve de base para a seção de Resultados
Preliminares do TCC e como rastreabilidade entre projeto e implementação.

> **Aviso.** Trata-se de um mapeamento referencial, de natureza técnica, entre
> controles de engenharia e princípios regulatórios. Não constitui parecer
> jurídico. Os números de artigos e resoluções devem ser conferidos na fonte
> oficial antes do depósito final.

## Marco regulatório considerado

- **LGPD** (Lei nº 13.709/2018). Dados de saúde são dados pessoais sensíveis
  (art. 5º, II; art. 11), sujeitos a proteção reforçada. São relevantes os
  princípios do art. 6º (finalidade, adequação, necessidade, segurança,
  prevenção e responsabilização), as medidas de segurança do art. 46 e a
  anonimização do art. 5º, XI, e art. 12.
- **ANVISA**, software como dispositivo médico (SaMD), Resoluções RDC nº
  657/2022, 751/2022 e 830/2023, que tratam de controle, segurança e
  rastreabilidade do software de saúde.
- **ANPD**, Radar Tecnológico sobre Inteligência Artificial Generativa
  (novembro de 2024), que reafirma a aplicação integral da LGPD a sistemas com
  LLMs e destaca os riscos de alucinação e de uso secundário não autorizado de
  dados.

## Premissa de base: dados 100% sintéticos

Toda a pesquisa usa dados sintéticos gerados com `SEED` e `SIM_TODAY` fixos
(ver `src/config.py`). Não há tratamento de dados pessoais reais em nenhuma
etapa, o que elimina na origem o risco de exposição. A PII existe de propósito
apenas na camada Bronze, para que a anonimização na Silver seja real e
demonstrável, e nunca sobrevive à Silver.

## Tabela de requisitos e controles

A coluna **Situação** reflete o estado atual do protótipo: `config` significa
que os parâmetros já estão centralizados em `src/config.py`; `projetado`
significa que o controle está definido no design (GUIA_DESENVOLVIMENTO.md) e a lógica será
implementada no módulo indicado.

| # | Requisito regulatório | Origem | Controle na arquitetura | Camada / módulo | Situação |
|---|---|---|---|---|---|
| 1 | Proteção reforçada de dados sensíveis de saúde e minimização | LGPD art. 11; art. 6º (necessidade) | Anonimização na Silver: remoção de `nome`, `cpf` e `data_nascimento`; derivação de `faixa_etaria` | Silver / `pipeline.py` | projetado |
| 2 | Anonimização e pseudonimização | LGPD art. 5º, XI; art. 12 | Pseudonimização de `id_paciente` por hash; nenhuma coluna de identificação direta sobrevive à Silver | Silver / `pipeline.py` | projetado |
| 3 | Minimização na exposição (só o necessário ao consumo) | LGPD art. 6º (necessidade, adequação) | Apenas a camada Gold, com métricas agregadas, é exposta ao motor de linguagem; Bronze e Silver ficam inacessíveis | Gold / `config.GOLD_TABLES` | config |
| 4 | Controle de acesso por finalidade e perfil | LGPD art. 6º (finalidade); ANVISA RDC (controle de acesso) | Perfis `gestor`, `enfermagem` e `administrativo` autorizam apenas tabelas Gold específicas | Entrada / `config.PERFIS`, `governance.py` | config |
| 5 | Segurança e prevenção de acesso ou comando indevido | LGPD art. 46; art. 6º (segurança, prevenção) | Guardrails de entrada: apenas uma instrução somente leitura (SELECT/WITH); bloqueio de escrita e comandos administrativos; bloqueio de múltiplas instruções; bloqueio de acesso a Bronze/Silver; conexão DuckDB em modo somente leitura (defesa em profundidade) | Entrada / `governance.py` | projetado |
| 6 | Mitigação de alucinação da IA generativa | ANPD, Radar de IA Generativa | Aterramento: toda tabela referenciada na SQL deve existir no schema Gold conhecido, caso contrário a consulta é bloqueada | Saída / `governance.py` | projetado |
| 7 | Prevenção de vazamento de dado sensível na resposta | LGPD art. 11; ANPD (uso secundário) | Filtro de saída: se qualquer coluna do resultado tiver nome de campo sensível (`nome`, `cpf`, `data_nascimento`, `id_paciente_pseudo`), a resposta é bloqueada | Saída / `config.CAMPOS_SENSIVEIS`, `governance.py` | config |
| 8 | Rastreabilidade e prestação de contas | LGPD art. 6º (responsabilização); ANVISA RDC (rastreabilidade) | Auditoria: registro de toda pergunta e resposta com timestamp, usuário, perfil, SQL e evento (correto, incorreto, bloqueado, erro) | Auditoria / `governance.py` | projetado |
| 9 | Prevenção de uso secundário não autorizado | ANPD, Radar de IA Generativa | Escopo restrito por perfil, execução somente leitura e registro integral em log limitam o uso dos dados ao fim declarado | Entrada e Auditoria / `governance.py` | projetado |
| 10 | Reprodutibilidade e integridade do experimento | Boas práticas de pesquisa; suporte à responsabilização | Determinismo por `SEED` e `SIM_TODAY`; dados exclusivamente sintéticos; separação entre motor LLM (gera os números) e motor oráculo (apenas autoteste da tubulação) | Transversal / `config.py`, `nl2sql.py`, CI | config |

## Leitura da tabela para os Resultados Preliminares

A tabela evidencia que a governança não é um apêndice do motor de IA, mas
atravessa as quatro camadas da arquitetura. Já estão consolidados como
resultado parcial o desenho dos controles e a centralização dos parâmetros que
os sustentam em `src/config.py` (perfis de acesso, tabelas Gold autorizadas,
campos sensíveis, semente e data de referência). A etapa seguinte implementa a
lógica correspondente em `pipeline.py` (anonimização) e `governance.py`
(guardrails, aterramento, filtro de saída e auditoria), o que tornará cada
linha da coluna Situação verificável por teste automatizado.

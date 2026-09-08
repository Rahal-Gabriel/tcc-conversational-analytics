# 07. Mapa: o que a literatura diz sobre cada caminho da conclusão

**Última atualização**: 2026-09-08
**Alimenta**: decisão dos experimentos da fase final · Metodologia · Discussão

Para cada caminho proposto para a conclusão do TCC, este mapa registra: o que a
literatura já sabe, o que ainda não sabe (a lacuna que o experimento fecha), o
desenho recomendado à luz das fontes, as métricas a reportar e as referências
a citar. A ideia é que nenhum experimento seja desenhado de novo depois de
escrito o texto.

Resumo da avaliação de cada caminho:

| Caminho | Sustentação na literatura | Lacuna que fecha | Esforço | Custo API |
|---|---|---|---|---|
| 1. Value linking barato | Forte (Liu 2026; Tanković 2025; Maamari 2024) | Erro de Q12; custo em tokens de expor valores | Pequeno | Baixo |
| 2. Schema por perfil sob verificador determinista | Forte e recente (Fei 2026; Klisura 2025; Miyamoto 2026) | Ninguém isolou Full-Schema vs Role-Schema com verificador externo | Pequeno | Baixo |
| 3. Perguntas de terceiros | Forte (Runeson e Höst 2009; Liu 2026 limita-se por isso; Li 2026 usa humanos) | Ameaça de validade de construção declarada | Médio (depende de pessoa externa) | Médio |
| 4. Comparação entre modelos com custo | Forte (Tanković 2025; Li 2026; Silva 2025) | Modelo único | Pequeno | Médio a alto |
| 5. Conjunto adversarial de governança | Forte (Pedro 2025; Klisura e Rios 2025; Lee 2024; Fei 2026) | AVAL-002 mede só bloqueio indevido; falta medir bloqueio devido | Pequeno a médio | Baixo |
| 6. Discussão da métrica e Soft F1 | Forte (Zhong 2020; BIRD; Atil 2025; Brown 2001) | Set match de conteúdo é métrica própria, sem par na literatura | Pequeno, sem API se a SQL gerada foi guardada | Nenhum |

---

## 1. Value linking: expor valores categóricos ao modelo

**O que se sabe.**
- Expor valores enumerados nos metadados elevou a acurácia de consultas com
  dois campos de 32% para 92,5% e de três campos de 10% para 82% (Liu et al.
  2026).
- Amostras de linhas no prompt custam 82% a 150% mais tokens e o ganho é
  inconsistente entre modelos (−2,5% a +26%); um único exemplo pergunta-SQL
  custa 6% a 13% e ajuda de forma consistente (Tanković et al. 2025).
- Com modelos atuais, filtrar o schema perde colunas; dar o schema completo é
  o recomendado quando cabe no contexto (Maamari et al. 2024).
- Erros de resolução de termos (códigos ICD, nomes de valor) são a principal
  causa de falha em SQL médico, não a sintaxe (Tanković et al. 2025), o que
  coincide com Q12 (`'enfermaria'` versus `'Enfermaria'`).

**Lacuna.** Nenhum dos trabalhos mede a forma mais barata de value linking:
listar apenas os **valores distintos de colunas categóricas de baixa
cardinalidade** (tipo, situação, especialidade, faixa etária), sem linhas de
amostra. No protótipo isso custa poucas dezenas de tokens.

**Desenho recomendado.**
- Variável: `VALUE_LINKING` (desligado / ligado) em `nl2sql.descrever_schema_gold`,
  anexando `{valores: ...}` às colunas categóricas com até N valores distintos
  (N em `config.py`, por exemplo 12), obtidos por introspecção da Gold.
- Pré-registro: critério de sucesso é Q12 passar a `correto` **sem** regressão
  nas demais 17; hipótese secundária é que colunas extras (Q04, Q13, Q14) não
  mudam, pois value linking não trata projeção.
- Reportar: execution match estrito, set match de conteúdo, Soft F1 (ver §6),
  tokens de entrada por pergunta (antes e depois), k=3.

**Citar**: Liu et al. (2026); Tanković et al. (2025); Maamari et al. (2024);
Gao et al. (2024) para tratar prompt como variável experimental.

## 2. Schema por perfil (Role-Schema) sob verificador determinista

**O que se sabe.**
- Fei et al. (2026) definem seis desfechos (Correct, Wrong, Proper Refusal,
  Violation Correct, Violation Wrong, Over-Refusal) e as métricas Violation
  Rate, Over-Refusal Rate, AC-F1 e Safe-EX. Os dois bloqueios do protótipo
  (Q01, Q11) são **Violation Correct**.
- Ainda em Fei et al. (2026): restringir o schema visível ao papel reduz o
  vazamento explícito, mas aumenta violações por alucinação de tabelas e
  colunas inexistentes; os modelos raramente recusam sozinhos.
- Política no prompt não garante nada: vazamento de 4,8% a 42,4% (Miyamoto et
  al. 2026); verificação explícita melhora a precisão de recusa (Klisura et al.
  2025).
- O protótipo já é um pipeline gerador-verificador (desenho ii de Klisura et
  al. 2025) com verificador determinista em código.

**Lacuna.** Os benchmarks avaliam o modelo decidindo sozinho ou com verificador
por LLM. Ninguém mediu, sob verificador **determinista** que garante zero
vazamento, se mostrar ao modelo só as tabelas autorizadas reduz o Violation
Correct (SQL correta barrada) sem elevar a alucinação (Violation Wrong / erro).
É uma pergunta pequena, mas nova, e diretamente ligada à pergunta de pesquisa
(custo mensurável da governança).

**Desenho recomendado.**
- Variável: `SCHEMA_POR_PERFIL` (Full-Schema / Role-Schema): no segundo, o
  prompt recebe apenas as tabelas de `config.PERFIS[perfil]`, e uma frase
  informando que só essas existem para o usuário.
- Cruzar com o caminho 1: quatro configurações (base; +value linking;
  +role-schema; ambos), k=3 cada, 18 perguntas (ou o conjunto ampliado).
- Reclassificar todos os casos nos seis desfechos de Fei et al. (2026) e
  reportar Safe-EX, Violation Rate (esperado 0 pelo verificador) e Over-Refusal.
- Atenção: em Role-Schema, o modelo pode inventar uma tabela fora do seu escopo
  (alucinação), que CTRL-VALID-001 barra; contar como Violation Wrong, e não
  como bloqueio de governança "correto".

**Citar**: Fei et al. (2026); Klisura et al. (2025); Miyamoto et al. (2026);
Pedro et al. (2025) para a necessidade de verificação fora do modelo.

## 3. Perguntas escritas por terceiros e ampliação do conjunto

**O que se sabe.**
- A validade de construção deve ser tratada desde o planejamento; perguntas
  feitas pelo mesmo autor do sistema inflam métricas (Runeson e Höst 2009;
  Wohlin et al. 2012).
- Liu et al. (2026) listam como limitação exatamente "questões sintéticas
  geradas por IA, não consultas clínicas reais"; Li et al. (2026) comparam o
  modelo com engenheiros humanos; Waltl (2025) usou 65 perguntas curadas e
  categorizadas por necessidade de informação.
- n=18 produz IC de Wilson amplos (Brown et al. 2001); dobrar o conjunto
  estreita, mas não elimina a incerteza.

**Lacuna.** Perguntas de quem **não** conhece o schema, em linguagem de gestor.

**Desenho recomendado.**
- Pedir a duas ou três pessoas (orientador, colega de MBA, profissional de
  saúde) 8 a 10 perguntas cada sobre ocupação de leitos, a partir de uma
  descrição em linguagem natural das quatro tabelas Gold, **sem** ver colunas.
- O autor escreve as SQL de referência e classifica por tipo e perfil;
  perguntas não respondíveis pelo schema entram no conjunto adversarial
  (caminho 5) como "não respondível", à maneira do EHRSQL 2024.
- Reportar separadamente "conjunto do autor" e "conjunto de terceiros", com IC.

**Citar**: Runeson e Höst (2009); Wohlin et al. (2012); Brown et al. (2001);
Liu et al. (2026); Waltl (2025).

## 4. Comparação entre modelos com custo

**O que se sabe.**
- Tanković et al. (2025): sete modelos, cinco repetições, fronteira de Pareto
  custo × acurácia; Claude 3.5 teve a menor acurácia (43,4%) e o maior custo no
  TREQS, GPT-4o a maior (64,1%), GPT-4o-mini o melhor custo.
- Li et al. (2026): GPT-4.1 zero-shot 78%, few-shot 96%; modelos abertos
  pequenos sem ajuste ≈ 0.
- Silva et al. (2025): entre modelos abertos, 3B é o melhor equilíbrio;
  Al Attrach et al. (2025): modelo aberto de 20B chega a 93% em agente.
- Variação entre repetições em temperatura fixa é pequena em Text-to-SQL (≤
  0,6 ponto em Tanković et al. 2025), mas pode ser grande em outras tarefas
  (Atil et al. 2025).

**Lacuna.** Nenhum desses trabalhos mede modelos **sob governança** nem em
português sobre dados de gestão hospitalar.

**Desenho recomendado.**
- Dois ou três modelos da mesma família (por exemplo, o atual, um menor e um
  maior), mesmo prompt e mesma configuração vencedora dos caminhos 1 e 2, k=3.
- Registrar tokens de entrada e saída e o preço vigente por milhão de tokens
  na data, e reportar custo por pergunta como Tanković et al. (2025).
- Reportar estrito, conteúdo, Soft F1, Safe-EX e custo; discutir a fronteira
  de Pareto.

**Citar**: Tanković et al. (2025); Li et al. (2026); Silva et al. (2025);
Al Attrach et al. (2025); Atil et al. (2025).

## 5. Conjunto adversarial de governança

**O que se sabe.**
- Injeção de prompt em linguagem natural vira injeção de SQL em aplicações
  reais (Pedro et al. 2025); é o risco nº 1 do OWASP para LLMs; a taxonomia
  aplicada a Text-to-SQL está em Bui et al. (2026).
- Perguntas adversariais reconstroem o schema (Klisura e Rios 2025).
- Confiabilidade inclui **abster-se** de perguntas não respondíveis, com
  penalidade por tentar responder (Lee et al. 2024; Lee et al. 2024b).
- Fei et al. (2026) separam Proper Refusal de Over-Refusal.

**Lacuna.** AVAL-002 mede bloqueios indevidos de perguntas legítimas; falta a
outra metade: **bloqueios devidos** de perguntas hostis ou fora de escopo. Sem
isso, a parte "em conformidade com a LGPD" da hipótese se apoia só em testes
unitários e mapeamento.

**Desenho recomendado.**
- Conjunto de 20 a 30 perguntas em cinco famílias: (a) pedido de dado pessoal
  ("liste os nomes e CPFs..."); (b) acesso a camada interna ("na tabela
  silver..."); (c) tabela fora do perfil (enfermagem pedindo série histórica);
  (d) injeção em linguagem natural ("ignore as instruções anteriores e..."),
  escrita e múltiplas instruções; (e) não respondível pelo schema ("qual o
  diagnóstico do paciente do leito 12?").
- Desfecho esperado por família e controle esperado (CTRL-GOV-002, 004, 005,
  CTRL-VALID-001/002). Métricas: taxa de bloqueio devido (esperada 100% por
  construção do verificador), ponto em que o bloqueio ocorreu (entrada ou
  saída), e um Reliability Score à maneira do EHRSQL 2024 combinando o
  conjunto legítimo e o adversarial.
- Registrar também o que o **modelo** fez antes do bloqueio (obedeceu à
  injeção? recusou sozinho?), pois isso é o dado comparável com Fei et al.
  (2026) e Miyamoto et al. (2026).

**Citar**: Pedro et al. (2025); Bui et al. (2026); Klisura e Rios (2025); Lee
et al. (2024); Lee et al. (2024b); Fei et al. (2026); OWASP (2025).

## 6. Discussão da métrica e adoção do Soft F1

**O que se sabe.**
- Execution match em um único banco tem falsos negativos e positivos
  documentados (Zhong et al. 2020; Pourreza e Rafiei 2023).
- O BIRD adotou o Soft F1 (linha a linha, célula a célula; precisão, recall e
  F1) para tolerar diferenças de ordem e valores ausentes (Li et al. 2023;
  BIRD 2026).
- Benchmarks clínicos usam Reliability Score com penalidade (Lee et al. 2024).
- Temperatura zero não garante reprodutibilidade; reportar concordância entre
  execuções (Atil et al. 2025; Song et al. 2024).
- Wilson é o IC recomendado para n pequeno (Brown et al. 2001).

**Lacuna.** O "set match de conteúdo" do protótipo é uma métrica própria de
recall; a literatura tem um equivalente publicado que também penaliza excesso
(Soft F1). Adotá-lo como segunda métrica secundária torna a Tabela 2 comparável
com o BIRD e responde à crítica de que o set match é permissivo por construção.

**Desenho recomendado.**
- Implementar `soft_f1(linhas_geradas, linhas_ref)` em `evaluate.py` seguindo
  a definição do BIRD; manter execution match estrito como primária, set match
  de conteúdo como diagnóstica de recall e Soft F1 como diagnóstica com
  precisão. Reportar TARa@3 (Atil et al. 2025) como nome da estabilidade.
- Se as SQL geradas das execuções anteriores estiverem em `results/auditoria.log`,
  o Soft F1 pode ser recalculado sem nova chamada de API.
- Na Discussão: posicionar 61,1% estrito na faixa zero-shot da literatura
  (43% a 78%), 94,4% de conteúdo na faixa agêntica (83% a 94%), e explicar a
  diferença pelas técnicas que a literatura mostra fecharem essa distância
  (exemplos no prompt, value linking, correção por execução), e não pelo modelo.

**Citar**: Zhong et al. (2020); Pourreza e Rafiei (2023); Li et al. (2023);
BIRD (2026); Lee et al. (2024); Atil et al. (2025); Song et al. (2024); Brown
et al. (2001).

---

## Ordem sugerida para caber até 6 de outubro

1. Caminhos 1, 2 e 6 juntos (uma matriz 2×2 de prompt, k=3, com as três
   métricas): fecham Q12, quantificam o custo da governança com o vocabulário
   de Fei et al. (2026) e alinham a métrica ao BIRD. Uma semana.
2. Caminho 5 (adversarial), sem depender de terceiros. Dois a três dias.
3. Caminho 3 se as perguntas de terceiros chegarem até 15 de setembro;
   caso contrário, registrar como trabalho futuro com a justificativa de
   Runeson e Höst (2009).
4. Caminho 4 com um ou dois modelos adicionais, se houver orçamento, usando a
   configuração vencedora de 1.
5. Redação de Resultados e Discussão, Conclusão e Resumo com as fichas de 01 a
   06 e a lista de 08.

<!--
Fonte da versão final do TCC (Etapa F). Cada seção entra num PR próprio,
na ordem do plano (docs/tcc/etapas/2026-09-21_etapa-F-plano.md). O .docx é
gerado a partir deste arquivo com o template oficial como referência de
estilos. Seções ainda não escritas aparecem como marcador.
-->

# [Título: escrito em 25/09]

[Resumo, palavras-chave: escritos em 25/09]

# Introdução

[Escrita em 25/09]

# Metodologia

A pesquisa caracterizou-se como aplicada, com abordagem quantitativa e
caráter exploratório e descritivo, e adotou o delineamento de estudo de
caso instrumental (Yin, 2015) apoiado no desenvolvimento de um protótipo
funcional, em linha com a pesquisa em ciência do projeto, na qual o
artefato construído é também o instrumento de avaliação (Hevner et al.,
2004). O protótipo materializou uma arquitetura de referência, entendida
como um modelo de solução reutilizável para uma classe de sistemas
(Angelov et al., 2012). Os métodos são descritos na mesma ordem em que os
resultados são apresentados.

## Escopo e levantamento da literatura

A pesquisa delimitou-se a um domínio operacional hospitalar, a ocupação
de leitos, com modelo de dados próprio e quatro tabelas expostas ao
motor de linguagem. A delimitação privilegiou profundidade de governança
sobre amplitude de dados: com um domínio único foi possível medir cada
controle isoladamente, em execução real e com repetição, dentro do prazo
do trabalho. As consequências dessa escolha para a generalização são
discutidas entre as limitações.

O levantamento da literatura foi narrativo, com protocolo registrado: a
busca de 8 de setembro de 2026 usou arXiv, ACL Anthology, Europe PMC e
PubMed, bibliotecas de editoras e da Sociedade Brasileira de Computação e
os portais oficiais da ANPD e da ANVISA, com termos, recorte temporal e
critérios de inclusão e exclusão definidos antes da leitura, seguindo
Prodanov e Freitas (2013). Os itens encontrados e triados não foram
contabilizados por base, razão pela qual o levantamento não é apresentado
como revisão sistemática. Resultaram 73 fichas de leitura agrupadas por
tema, das quais saíram as citações deste trabalho.

## Dados sintéticos e pipeline em camadas

Todos os dados foram gerados de forma determinista com a biblioteca Faker
em localidade pt_BR, controlada por uma semente única (42) e ancorada em
uma data de referência fixa da simulação (31 de maio de 2026). O ambiente
representou um hospital com oito unidades, duzentos leitos, seiscentos
pacientes e cerca de 2.200 internações, com noventa dias de histórico de
ocupação diária. Nenhum dado real foi utilizado em qualquer etapa.

Os dados percorreram um pipeline em três camadas implementado em DuckDB,
no modelo Lakehouse (Armbrust et al., 2021). A camada Bronze recebeu os
dados brutos, com nome, CPF e data de nascimento inseridos de propósito,
para que a proteção aplicada na camada seguinte fosse real e verificável.
A camada Silver removeu esses campos, derivou a faixa etária a partir da
idade completa na data de referência e pseudonimizou o identificador do
paciente com HMAC-SHA256, hash com chave lida do ambiente, técnica
recomendada no lugar do hash simples quando o domínio do identificador é
pequeno (European Data Protection Board [EDPB], 2025; European Union Agency
for Cybersecurity [ENISA], 2022); por isso a Silver foi tratada como
pseudonimizada, e não anonimizada. A camada Gold, única exposta ao modelo
de linguagem, reuniu quatro tabelas: a situação de cada leito na data de
referência, o resumo por unidade, a série diária do hospital e as
internações, estas sem identificador de paciente e reduzidas a tipo de
leito, faixa etária, situação e tempo de permanência. Sobre as
internações foi imposto k-anonimato (Sweeney, 2002) com k mínimo de 5 no
par tipo de leito e faixa etária, limiar adequado a uso interno
controlado (El Emam e Arbuckle, 2013), verificado por teste a cada
construção. A Gold foi exportada para um arquivo próprio, de modo que as
camadas internas não existissem no banco consultado pelo sistema.

## Governança de entrada e de saída

A governança foi concebida como defesa em profundidade, alinhada à gestão
de risco de sistemas de inteligência artificial (National Institute of Standards and Technology [NIST],
2023) e aos riscos
catalogados para aplicações de modelos de linguagem, em especial a injeção
de instruções e o acesso indevido a recursos (OWASP Foundation, 2025). O desenho
seguiu o padrão gerador e verificador: o modelo propôs a consulta e um
verificador determinista, escrito em código, decidiu se ela seria
executada (Klisura et al., 2025).

Antes de qualquer chamada ao modelo, o texto da pergunta foi verificado
contra padrões de CPF, e-mail e telefone; havendo ocorrência, a pergunta
foi recusada e o trecho mascarado, sem chegar ao modelo nem à trilha de
auditoria. A consulta gerada passou por cinco verificações textuais:
instrução única, somente leitura, ausência de comandos de escrita, de
leitura de arquivo e de consulta ao catálogo do banco, ausência de
referência às camadas Bronze e Silver, e restrição às tabelas Gold
autorizadas ao perfil. A execução ocorreu em conexão somente leitura,
restrita ao arquivo da Gold e com o acesso do banco a arquivos externos
desligado, de modo que as garantias principais dependessem do dado e da
conexão, e não apenas do texto da consulta. Na saída, o sistema verificou
que as tabelas citadas existiam na Gold e bloqueou colunas com nome de
campo sensível. Cada pergunta e cada resposta foram registradas numa
trilha de auditoria com horário real, perfil, consulta, controle que
barrou e hash do resultado entregue, em cadeia de hashes que torna
detectável qualquer alteração posterior (Kent e Souppaya, 2006; Schneier e
Kelsey, 1999).

Foram definidos três perfis de acesso, com escopo derivado da finalidade
de cada função, conforme os princípios de finalidade e necessidade da
LGPD (Brasil, 2018). A enfermagem acessou a situação de cada leito e o
resumo por unidade, que servem à operação do turno. O perfil
administrativo acessou o resumo por unidade e a série histórica, que
servem ao planejamento, sem nível de leito nem de internação. O gestor
acessou as quatro tabelas. A matriz seguiu o princípio do menor
privilégio: cada perfil recebeu o escopo mínimo necessário à sua
finalidade, e nenhum acesso foi concedido por conveniência.

## Enquadramento regulatório

Os requisitos da LGPD (Brasil, 2018), das diretrizes da ANPD (Autoridade
Nacional de Proteção de Dados [ANPD], 2024)
e das normas da ANVISA foram mapeados a controles concretos, à camada
responsável e à situação de implementação, distinguindo controle com
código e teste, controle por configuração, controle parcial e controle
apenas projetado. Como os dados são sintéticos, a LGPD não incidiu sobre
o protótipo, e a conformidade foi tratada como propriedade de projeto
("projetada para atender"), e não como aderência demonstrada. O
protótipo realiza análise de ocupação de leitos para apoio à gestão, sem
finalidade diagnóstica ou terapêutica sobre paciente individual, e nesse
escopo não se caracteriza como software como dispositivo médico nos
termos da RDC 657/2022 (Agência Nacional de
Vigilância Sanitária [ANVISA], 2022); as normas da ANVISA foram adotadas
por analogia, como referência de controle, segurança e rastreabilidade de
software em saúde.

## Motores de tradução e desenho do prompt

Três motores intercambiáveis traduziram as perguntas em SQL. O oráculo
devolveu a consulta de referência e serviu apenas para o autoteste do
pipeline, nunca como medida de desempenho. O motor local executou o
modelo aberto Qwen2.5-Coder de 14 bilhões de parâmetros (Hui et al.,
2024), quantizado em 4 bits, pelo servidor Ollama na própria máquina, sem
custo e sem saída de dados. O motor via API usou o modelo
claude-sonnet-4-6, o mesmo dos resultados preliminares. Todas as
chamadas usaram temperatura zero; no motor local, a semente do projeto
também controlou a amostragem, e o relatório registrou a versão do
servidor e o identificador exato dos pesos.

O prompt foi tratado como variável experimental (Gao et al., 2024). Cada
configuração, chamada célula, combinou quatro componentes: a descrição
do schema, simples (só nomes) ou enriquecida com tipos, notas de tabela e
unidades, como recomendado para schemas que cabem no contexto (Maamari
et al., 2024); a lista dos valores distintos das colunas categóricas
(value linking), cujo efeito sobre filtros por valor foi documentado em
dados clínicos (Liu et al., 2026); a restrição do schema às tabelas do
perfil, com aviso explícito ao modelo (Fei et al., 2026); e uma instrução
de recusa, que informou ao modelo que responder "RECUSA" era uma saída
válida quando a pergunta não pudesse ser respondida com o schema ou
pedisse dados de pessoas identificáveis. A Tabela 1 resume as células.

Tabela 1. Células de prompt avaliadas

| Célula | Descrição do schema | Value linking | Schema por perfil | Instrução de recusa | Papel |
|---|---|---|---|---|---|
| C0 | simples | não | não | não | prompt dos resultados preliminares |
| C1 | enriquecida | não | não | não | base da matriz |
| C2 | enriquecida | sim | não | não | efeito do value linking |
| C3 | enriquecida | não | sim | não | efeito do escopo por perfil |
| C4 | enriquecida | sim | sim | não | os dois efeitos |
| E0 | enriquecida | não | sim | não | igual a C3, no conjunto adversarial |
| E1 | enriquecida | não | sim | sim | efeito da instrução de recusa |

Fonte: Dados originais da pesquisa

As células C0 a C4 foram executadas com o motor local; C0 e C3 também com
o motor via API, para cruzar modelo e prompt; E0 e E1, com o motor local.

## Conjuntos de avaliação

O conjunto legítimo reuniu 18 perguntas em português, cada uma com um
perfil e uma consulta de referência sobre a Gold: seis de situação atual,
cinco de métrica por unidade, três de série histórica e quatro sobre
internações, distribuídas entre enfermagem (5), administrativo (6) e
gestor (7). O tipo de cada pergunta foi derivado mecanicamente da consulta
de referência, e toda referência foi conferida contra os controles do
próprio perfil. As referências seguiram uma regra de projeção explícita:
devolver a grandeza pedida; incluir a chave da entidade quando a resposta
tem uma linha por entidade; e, quando a pergunta seleciona entidades por
um valor, devolver a entidade e esse valor. Para reduzir o viés de um
único autor escrever perguntas, referências e sistema, um colega do
autor, sem participação no projeto, indicou às cegas, a partir apenas do
texto das perguntas e de uma descrição dos dados em linguagem comum, que
informações cada resposta deveria conter.

O conjunto adversarial reuniu 25 perguntas que o sistema deveria recusar,
em cinco famílias de cinco: pedido de dado pessoal; acesso às camadas
internas ou ao catálogo do banco; pergunta legítima para outro perfil,
fora do escopo de quem pergunta; injeção de instruções em linguagem
natural, inclusive com instrução dupla (Pedro et al., 2025); e pergunta
sem resposta no schema, como diagnóstico, previsão ou causa. As famílias
seguiram a noção de que abster-se de perguntas não respondíveis é parte
da confiabilidade (Lee et al., 2024a, 2024b). O conjunto
combinado, com 43 perguntas, foi usado nas células E0 e E1. Os valores de
CPF e e-mail das perguntas foram fictícios.

## Métricas e análise

A métrica primária foi o execution match estrito, consolidado no Spider
(Yu et al., 2018), no EHRSQL (Lee et al., 2022) e no BIRD (Li et al.,
2023): as consultas gerada e de referência foram executadas e seus
resultados comparados após normalização (tolerância numérica de duas
casas, datas em formato ISO e linhas ordenadas). Duas métricas
secundárias, diagnósticas, acompanharam a primária: o set match de
conteúdo, que verifica se os valores da referência aparecem no resultado
e é permissivo por construção, e o Soft F1 do BIRD, que também penaliza
colunas e valores em excesso.

Os desfechos de governança seguiram a taxonomia de Fei et al. (2026), com
seis categorias (correto, errado, recusa devida, violação correta,
violação errada e recusa indevida), atribuídas em dois níveis: o do
modelo, que diz o que a consulta gerada faria sem verificador, e o do
sistema, que diz o que o usuário recebeu. A distância entre os níveis
mediu a contribuição do verificador. Para perguntas a recusar, a
taxonomia classifica como violação qualquer consulta entregue; como o
verificador impede que uma consulta fora do escopo seja entregue, o
texto separou a violação de política (linha fora do perfil, de camada
interna ou com campo sensível chegando ao usuário) da resposta indevida
(consulta dentro do escopo a uma pergunta sem resposta). Também foi
registrado o ponto em que o sistema parou cada pergunta. Sobre o
conjunto combinado calculou-se o Reliability Score RS(c) (Lee et al.,
2024a), que soma um ponto por resposta correta ou recusa devida e
subtrai c pontos por resposta errada entregue, com c igual a 0, 10 e ao
tamanho do conjunto.

As proporções foram acompanhadas de intervalo de confiança de 95% pelo
método de Wilson, adequado a amostras pequenas (Brown et al., 2001). As
células foram comparadas pergunta a pergunta, com teste de sinal exato
bilateral sobre ganhos e perdas; com 18 e 25 perguntas, a leitura foi
descritiva, e nenhuma diferença foi apresentada como significativa sem o
teste ao lado. Cada célula foi executada três vezes, e a estabilidade foi
medida pela taxa de concordância total entre execuções, TARa@k (Atil et
al., 2025), sobre o desfecho e o resultado normalizado de cada pergunta.
A célula de melhor desempenho foi repetida em outro dia, com o servidor
do modelo reiniciado.

## Pré-registro, reprodutibilidade e integridade

As células, as hipóteses de cada comparação e o critério de escolha da
configuração vencedora foram escritos e versionados antes da execução
correspondente, e não foram alterados depois dos números. Cada execução
gerou relatórios com a consulta, o desfecho, o resultado normalizado, o
hash e a telemetria de cada pergunta em cada repetição, além da trilha de
auditoria, e esses artefatos foram versionados no repositório com uma
marca (tag) git no commit que os produziu, permitindo recalcular qualquer
métrica sem nova chamada ao modelo. O ambiente foi fixado em versão de
Python, dependências travadas e imagem reprodutível, e a integração
contínua executou, a cada alteração, apenas o motor oráculo.

A execução real revelou três defeitos no próprio instrumento de medição,
todos corrigidos antes de qualquer número ser reportado e registrados: a
referência pré-arredondava médias que a normalização arredondava de novo
(resultados preliminares); a assinatura de estabilidade usava a ordem das
linhas devolvida pelo banco, não determinística em agrupamentos; e a
execução diagnóstica de consultas barradas, usada para medir conteúdo,
executou uma instrução de exportação injetada que o sistema havia
recusado. Nos três casos a correção foi decidida antes de reexecutar, e
a última foi convertida em barreira na própria conexão com o banco.

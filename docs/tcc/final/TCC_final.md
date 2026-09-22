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
camadas internas não existissem no banco consultado pelo sistema. Como o
DuckDB não oferece controle de acesso por usuário, o isolamento foi
materializado como arquivo separado; em um banco com permissões, o mesmo
princípio de menor privilégio seria implementado por um usuário de
leitura restrito às tabelas Gold.

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

# Resultados e Discussão

Os resultados são apresentados na ordem da Metodologia. Todos os números
do modelo de linguagem provêm de execução real, com os artefatos
versionados; os do pipeline provêm de execução determinista.

## Pipeline, minimização e isolamento

A geração produziu, de forma determinista, 8 unidades, 200 leitos, 600
pacientes, 2.012 internações e 18.000 registros diários de ocupação. Na
data de referência, 150 leitos estavam ocupados, 42 livres e 8
bloqueados (taxa de ocupação de 75%), e as 150 internações em andamento
coincidiram com os 150 leitos ocupados. A Silver não conteve nome, CPF
nem data de nascimento, e o pseudônimo por HMAC não teve colisão entre
os 600 pacientes. A faixa etária derivada da idade completa resultou em
108, 143, 127, 129 e 93 pacientes nas cinco faixas, corrigindo a fórmula
por ano-calendário dos resultados preliminares, que classificava 11
pacientes na faixa errada.

A minimização da Gold foi decidida por medição. Com as colunas originais
da tabela de internações (unidade, tipo, faixa etária, sexo e data de
admissão), 1.763 dos 1.883 grupos de quase-identificadores tinham uma
única internação: a tabela, apresentada como agregada, permitia
individualizar cada estadia. Após a redução a tipo de leito, faixa
etária, situação e tempo de permanência, o k mínimo passou a 29 sobre o
par tipo e faixa, acima tanto do limiar de 5 adotado para uso interno
controlado (El Emam e Arbuckle, 2013) quanto do limiar de 11 usado em
regras de supressão de célula (Tabela 2). O custo de utilidade foi
declarado: internações por unidade deixaram de ser respondíveis. Na
análise de sensibilidade que acrescenta a situação (em andamento ou
encerrada) aos quase-identificadores, o k mínimo cai para 3, com 3,2%
das linhas em grupos menores que 11; o controle imposto por teste cobre o
conjunto completo, e não esse subconjunto, o que é retomado nas
limitações.

Tabela 2. Minimização da tabela de internações da Gold

| Medida | Antes | Depois |
|---|---|---|
| Colunas expostas | identificador, unidade, tipo, faixa etária, sexo, data de admissão, permanência, situação | tipo, faixa etária, situação, permanência |
| k mínimo sobre os quase-identificadores | 1 (1.763 grupos com uma internação) | 29 sobre tipo e faixa; 3 incluindo a situação |
| Linhas em grupos com k menor que 11 | 100% | 0% (3,2% incluindo a situação) |
| Verificação | nenhuma | teste exige k de pelo menos 5 a cada construção |

Fonte: Resultados originais da pesquisa

O isolamento das camadas internas também foi corrigido por medição. Na
primeira versão, a garantia de que Bronze e Silver eram inacessíveis
dependia só da inspeção textual da consulta, e três consultas hostis
aprovadas pelos guardrails devolveram dados internos: uma função de
tabela que recebe o nome da tabela como texto, uma consulta ao catálogo
que revelou a coluna de CPF e uma listagem das tabelas internas. A
correção adotou duas barreiras independentes: a Gold passou a ser
exportada para um arquivo próprio, o único que o sistema abre, e as
funções de tabela e de catálogo passaram a ser bloqueadas. O achado
reproduz, no protótipo, o que a literatura recente afirma: restrições
expressas apenas sobre o texto, no prompt ou por inspeção da consulta,
não garantem isolamento, e a garantia precisa ser imposta de forma
determinista fora do texto (Fei et al., 2026; Klisura et al., 2025;
Miyamoto et al., 2026). A conexão de consulta recebeu ainda, na Etapa E,
o bloqueio de acesso a arquivos externos, pelo motivo relatado adiante.

## Matriz de prompt com o modelo local

A Tabela 3 apresenta as cinco células executadas com o modelo local, três
vezes cada, sobre as 18 perguntas legítimas. O desvio entre execuções foi
zero em todas as métricas e a concordância total (TARa@3) foi de 100% em
todas as células: as 90 combinações de pergunta e célula produziram a
mesma consulta nas três chamadas.

Tabela 3. Matriz de prompt com o modelo local (18 perguntas, média de três execuções)

| Célula | Execution match estrito | IC 95% | Set match | Soft F1 | Recusa indevida | Tokens por pergunta |
|---|---|---|---|---|---|---|
| C0 | 22,2% | 9,0% a 45,2% | 38,9% | 70,0% | 22,2% | 288 |
| C1 | 55,6% | 33,7% a 75,4% | 61,1% | 72,5% | 5,6% | 529 |
| C2 | 61,1% | 38,6% a 79,7% | 72,2% | 94,2% | 5,6% | 687 |
| C3 | 72,2% | 49,1% a 87,5% | 72,2% | 84,3% | 0 | 463 |
| C4 | 72,2% | 49,1% a 87,5% | 77,8% | 89,0% | 0 | 586 |

Fonte: Resultados originais da pesquisa

A descrição enriquecida do schema (C1 contra C0) produziu o maior efeito:
seis perguntas passaram a corretas e nenhuma regrediu (teste de sinal,
p = 0,03, a única comparação da matriz abaixo de 0,05). Com nomes de
coluna sem descrição, o modelo supôs que a tabela de resumo por unidade,
uma fotografia do dia, tinha coluna de data, e escreveu literais de texto
para uma coluna booleana; a descrição resolveu ambos, em linha com a
recomendação de fornecer o schema completo e descrito quando ele cabe no
contexto (Maamari et al., 2024). O value linking (C2 contra C1) fechou o
erro de literal que motivou sua adoção, a caixa de "Enfermaria", e mais
duas perguntas, mas fez o modelo regredir em outras duas, uma por
projetar coluna a mais e outra por inventar uma coluna na tabela certa;
o saldo foi de uma pergunta (p = 1,0), com o maior Soft F1 da matriz. O
resultado contraria em parte a expectativa formada a partir de Liu et
al. (2026), para quem expor valores enumerados eleva a acurácia de
filtros; aqui elevou, mas não sem custo.

A restrição do schema ao perfil (C3 contra C1) foi observada na direção
prevista: três perguntas passaram a corretas e nenhuma regrediu
(p = 0,25). Só uma delas é efeito atribuível ao escopo, a pergunta em que
o modelo, vendo o schema completo, buscava uma tabela fora do perfil e
era barrado; as outras duas mudaram por efeito colateral da forma do
prompt. A alucinação de tabelas que Fei et al. (2026) observam quando o
schema é restrito não ocorreu: com o aviso explícito e o verificador, o
modelo não citou tabela inexistente em nenhuma das 54 chamadas de C3. A
recusa indevida, que nos resultados preliminares havia custado 11,1
pontos de execution match, caiu a 5,6 pontos com a descrição enriquecida
e a zero quando o prompt informou o escopo, sem regressão. Esse número
mede a recusa de perguntas legítimas, todas construídas para caber no
perfil de quem pergunta; o custo da governança propriamente dito, sobre
perguntas que o perfil não pode fazer, é medido no conjunto adversarial.

Pelo critério registrado antes da execução, C3 e C4 empataram no
execution match e na ausência de violação, e C3 venceu por consumir
menos tokens. C4 foi melhor nas métricas secundárias, o que fica
declarado; o critério não foi alterado depois dos números. Os cinco erros
residuais de C3 não foram de raciocínio sobre a pergunta: dois de
projeção incompleta (a unidade sem a taxa que a selecionou), um de
dialeto (uma função do MySQL em DuckDB, apesar de o prompt declarar o
dialeto) e dois de literal (um nome de unidade incompleto e uma caixa
errada com um valor de situação inexistente).

## Modelo e prompt cruzados e o veredito da hipótese

Os resultados preliminares haviam medido 61,1% de execution match com o
modelo claude-sonnet-4-6, sobre a Gold anterior à minimização e com o
prompt simples, e as consultas geradas naquela execução não foram
preservadas. Esse número é tratado aqui como observação histórica, sem
servir de base de comparação. Para separar o efeito do modelo do efeito
do prompt, o mesmo modelo via API foi executado nas células C0 e C3 sobre
a Gold e o harness atuais (Tabela 4).

Tabela 4. Execution match estrito por modelo e célula (18 perguntas, média de três execuções)

| Modelo | C0 (prompt simples) | C3 (enriquecido, schema por perfil) | Efeito do prompt |
|---|---|---|---|
| Qwen2.5-Coder 14B, local | 22,2% | 72,2% | 50,0 pontos |
| Claude Sonnet 4.6, via API | 74,1% | 90,7% | 16,6 pontos |
| Efeito do modelo | 51,9 pontos | 18,5 pontos | |

Fonte: Resultados originais da pesquisa

Modelo e prompt importaram, e interagiram. O prompt valeu 50 pontos no
modelo pequeno e 17 no grande; o modelo valeu 52 pontos sob o prompt
simples e 19 sob o prompt com escopo. O que os dados sustentam é que um
prompt bem desenhado reduziu a distância entre o modelo local e o modelo
via API de 52 para 19 pontos, e não que um fator pese mais que o outro.
Em C0, o modelo via API reproduziu o padrão dos resultados preliminares:
as duas perguntas da enfermagem barradas por escopo, duas perguntas com
colunas a mais e a diferença de 61,1% para 74,1% explicada pela Gold
minimizada e pelo harness revisto, não pelo modelo, que foi o mesmo. Em
C3, o modelo via API errou os mesmos dois tipos de coisa que o modelo
local: uma coluna a mais em uma pergunta e a caixa de um literal em outra.

O intervalo de Wilson para C3 no modelo via API foi de 67,2% a 96,9%; no
modelo local, de 49,1% a 87,5%. Com 18 perguntas, nenhum dos intervalos
exclui 80%. A hipótese de acurácia superior a 80% foi, portanto, atingida
na estimativa pontual com o modelo forte sob o prompt com escopo (90,7%),
não foi atingida com o modelo local (72,2%), e em nenhum dos casos o
tamanho do conjunto permite afirmar que o valor verdadeiro está acima ou
abaixo do limiar. A leitura cega do segundo anotador tornou esse veredito
robusto à convenção de projeção das referências: ele concordou com as
referências em 17 das 18 perguntas, inclusive nas duas que a projeção
mínima do modelo havia contrariado, e divergiu em uma, pedindo também a
data da maior taxa de ocupação, que nenhum modelo devolveu. Sob a leitura
do anotador, todas as células perdem 5,6 pontos, e o modelo local fica
abaixo de 80% nas duas leituras, enquanto o modelo via API fica acima nas
duas (90,7% e 85,2%). A referência divergente não foi alterada, para não
ajustar o gabarito depois dos números.

A execução via API trouxe um achado próprio: com temperatura zero, o
modelo mudou a consulta de uma pergunta em cada célula entre chamadas
contíguas (TARa@3 de 94,4%), variação que o modelo local com semente fixa
não apresentou em nenhuma das 270 chamadas da matriz, coerente com o não
determinismo de configurações "deterministas" em serviços hospedados
descrito por Atil et al. (2025).

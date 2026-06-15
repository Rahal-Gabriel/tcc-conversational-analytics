# Rascunho: seção Resultados Preliminares (apoio à redação)

**Status**: rascunho de apoio
**Prioridade**: ALTA
**Última atualização**: 2026-06-15
**Origem**: montado a partir de [01_RESULTADOS_PRELIMINARES.md](01_RESULTADOS_PRELIMINARES.md)
(RES-001 a RES-007), na ordem definida em [02_MAPA_DOC_PARA_TEMPLATE.md](02_MAPA_DOC_PARA_TEMPLATE.md)

---

> Este arquivo não é o documento final do template. É um rascunho da **seção
> Resultados Preliminares** para colar e ajustar no template do MBA USP/Esalq
> (teto de 30 páginas, redação no pretérito impessoal, subtópicos na mesma ordem
> da Metodologia). Antes do depósito, remover este bloco de instrução, conferir a
> formatação das tabelas e numerar figuras e tabelas conforme as normas. Os
> números aqui vêm de execução determinista (`SEED=42`, `SIM_TODAY=2026-05-31`) e
> são reprodutíveis. O 100% do motor oráculo é autoteste da tubulação e não
> representa o desempenho do modelo; a hipótese de acurácia superior a 80% ainda
> não se confirma sob execution match estrito (RNC-002).

## Resultados Preliminares

O protótipo foi implementado nas quatro camadas da arquitetura de referência e
avaliado sobre dados sintéticos no domínio de ocupação de leitos hospitalares.
Apresentam-se a seguir os resultados parciais verificáveis, na mesma ordem dos
métodos: geração do dataset, arquitetura, modelo de governança, conformidade
regulatória, avaliação e reprodutibilidade.

### Geração do dataset sintético

A geração sintética produziu, de forma determinista, o ambiente de dados de um
hospital de grande porte, materializado na camada Bronze: 8 unidades, 200 leitos,
600 pacientes (com dados pessoais propositais, para tornar a anonimização
demonstrável), 2.012 internações e 18.000 registros de ocupação diária (200
leitos ao longo de 90 dias). No dia de referência da simulação (31 de maio de
2026), o hospital apresentava 150 leitos ocupados, 42 livres e 8 bloqueados, o
que corresponde a uma taxa de ocupação de 75,0%. A coerência foi verificada: as
150 internações ativas, sem alta registrada, igualaram exatamente os 150 leitos
ocupados no dia de referência.

A transformação para as camadas Silver e Gold confirmou a anonimização exigida.
A tabela de pacientes da Silver não contém nome, CPF nem data de nascimento; o
identificador do paciente foi substituído por um pseudônimo derivado de função de
hash com salt, sem colisão entre os 600 pacientes, e a data de nascimento deu
lugar à faixa etária. A distribuição por faixa etária foi de 105 pacientes em
0-17, 142 em 18-39, 127 em 40-59, 128 em 60-79 e 98 em 80 ou mais. A camada Gold,
única exposta ao motor de linguagem, consolidou as métricas agregadas; a soma dos
leitos por unidade (200) coincidiu com o total configurado, e as taxas de
ocupação por unidade variaram de 64,0% a 92,0%.

### Arquitetura de referência em quatro camadas

A arquitetura foi documentada e implementada em quatro camadas encadeadas: o
pipeline Lakehouse (Bronze, Silver e Gold), a governança de entrada, o motor
Text-to-SQL e a validação de saída. Apenas a camada Gold, agregada, é exposta ao
modelo de linguagem, enquanto as camadas internas (Bronze e Silver) permanecem
inacessíveis ao motor. O fluxo de uma pergunta percorre as quatro camadas de
forma rastreável, da autenticação por perfil até o registro da resposta na trilha
de auditoria. A documentação modular consolidou essa arquitetura como o principal
artefato de referência do trabalho, com decisões, regras críticas, controles e
requisitos regulatórios identificados e rastreáveis ao código.

### Modelo de governança de entrada e saída

O modelo de governança foi implementado como defesa em profundidade. Na entrada,
seis guardrails verificam que a SQL candidata é uma única instrução somente
leitura, sem comandos administrativos ou de escrita, restrita às tabelas Gold
autorizadas ao perfil do usuário, com uma conexão de banco somente leitura como
barreira final. Na saída, a validação confere o aterramento contra o schema Gold
conhecido (mitigação de alucinação), bloqueia qualquer coluna de resultado com
nome de campo sensível e registra cada pergunta e cada resposta na trilha de
auditoria, com o evento da interação.

A eficácia da governança foi observada na avaliação com o motor de linguagem
real: em duas perguntas, o modelo produziu uma consulta que retornaria o número
correto, porém a partir de uma tabela fora do escopo autorizado ao perfil de
enfermagem. Em ambos os casos, o guardrail de escopo por perfil bloqueou a
execução antes que a consulta tocasse o banco, evidenciando que o controle de
acesso por finalidade opera como projetado.

### Conformidade regulatória

O mapeamento entre requisitos regulatórios e controles da arquitetura foi
concluído, cobrindo a LGPD, as normas da ANVISA aplicáveis a software como
dispositivo médico e as diretrizes da ANPD, em onze requisitos. O mapeamento
demonstrou que a governança atravessa as quatro camadas e não se restringe ao
motor de inteligência artificial, associando cada requisito a um controle
implementado, à camada responsável e à sua situação.

### Avaliação

A tubulação de avaliação foi exercitada de ponta a ponta com o motor oráculo, que
devolve a SQL de referência de cada pergunta. Para as 18 perguntas do conjunto, o
execution match resultou em 100%, a taxa de aprovação na governança em 100% e a
completude do log de auditoria em 100%. Esse resultado é um autoteste da
tubulação (geração, governança, execução e avaliação) e não representa o
desempenho do modelo.

A primeira execução com o motor de linguagem real (modelo Claude Sonnet 4.6)
forneceu os primeiros números de acurácia. Sobre o conjunto inicial de 10
perguntas, o execution match estrito foi de 60,0%. Após a correção de uma
inconsistência interna do harness de medição (o arredondamento da referência) e a
ampliação do conjunto para 18 perguntas, o execution match foi de 61,1%. A
estabilidade do valor com o conjunto quase dobrado indica que a medida não foi
fortuita.

A análise dos resultados não correspondentes mostrou que a maior parte não
decorreu de erro de cálculo do modelo. Das 18 perguntas, apenas uma apresentou
erro genuíno de cálculo, em que o modelo filtrou um valor categórico com a caixa
incorreta e obteve resultado vazio. Duas foram bloqueadas pela governança, por
acessarem tabela fora do escopo do perfil, embora o valor numérico estivesse
correto. As quatro restantes divergiram apenas na forma do resultado, com colunas
adicionais ou formato distinto, apesar de valores corretos, refletindo a
sensibilidade conhecida do execution match estrito à projeção. Mantém-se o
execution match estrito como métrica primária, sem a introdução de métricas
alternativas mais permissivas; a categorização dos erros acompanha o número.

### Reprodutibilidade e integridade

A reprodutibilidade foi assegurada por construção. A combinação de semente fixa e
data de referência fixa reproduz exatamente os mesmos dados e números, inclusive
entre as versões 3.12 e 3.14 do Python. O ambiente foi fixado, as dependências
travadas e a imagem reprodutível, de modo que o experimento roda de forma idêntica
em qualquer máquina e na integração contínua, que executa apenas o motor oráculo,
sem chave e sem custo. A integridade dos resultados foi tratada como princípio: os
números de acurácia provêm somente de execução real do modelo, com a metodologia
de medição decidida antes da reexecução, e os valores bruto e refinado reportados
lado a lado.

## Lacunas e próximos passos

Sob execution match estrito, a hipótese de acurácia superior a 80% ainda não se
confirma. A análise de erros indica que o teto é puxado pela forma do resultado e
pela governança, não pelo raciocínio do modelo. Os próximos passos previstos são
o tratamento de value linking (expor ao motor os valores categóricos do schema ou
comparar texto sem distinção de caixa), a discussão da métrica sensível à forma e
a ampliação e estratificação do conjunto de avaliação por tipo de pergunta e por
perfil.

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType, PageBreak,
} = require("docx");

// ---- constantes de layout (A4, margens ABNT: 3cm esq/topo, 2cm dir/base) ----
const CONTENT = 9071; // 11906 - 1701 - 1134
const border = { style: BorderStyle.SINGLE, size: 1, color: "999999" };
const borders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 60, bottom: 60, left: 100, right: 100 };

// paragrafo de corpo, justificado
function corpo(text) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { line: 360, after: 120 },
    children: [new TextRun(text)],
  });
}
// paragrafo de corpo com runs mistos (para destacar [preencher])
function corpoRuns(runs) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { line: 360, after: 120 },
    children: runs,
  });
}
function ph(text) { return new TextRun({ text, bold: true }); } // placeholder em negrito
function txt(text) { return new TextRun(text); }

function h1(num, title) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 240, after: 160 },
    children: [new TextRun(`${num}. ${title}`)],
  });
}
function h2(num, title) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 160, after: 100 },
    children: [new TextRun(`${num} ${title}`)],
  });
}

// celula
function cell(text, widthDxa, opts = {}) {
  return new TableCell({
    borders, width: { size: widthDxa, type: WidthType.DXA }, margins: cellMargins,
    shading: opts.head ? { fill: "D9E2F3", type: ShadingType.CLEAR } : undefined,
    children: [new Paragraph({
      alignment: opts.align || AlignmentType.LEFT,
      children: [new TextRun({ text, bold: !!opts.head || !!opts.bold })],
    })],
  });
}
function tabela(colWidths, rows) {
  return new Table({
    width: { size: CONTENT, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: rows.map((r, i) =>
      new TableRow({
        children: r.map((c, j) =>
          cell(String(c), colWidths[j], {
            head: i === 0,
            align: j === 0 ? AlignmentType.LEFT : AlignmentType.CENTER,
            bold: i === rows.length - 1 && r[0].toString().startsWith("Hospital"),
          })
        ),
      })
    ),
  });
}
function legenda(text) {
  return new Paragraph({
    spacing: { before: 60, after: 160 },
    children: [new TextRun({ text, size: 20, italics: true })],
  });
}

// ---------------- conteudo ----------------
const children = [];

// Titulo
children.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { after: 240 },
  children: [new TextRun({
    text: "Governança integrada habilita consulta em linguagem natural sobre ocupação de leitos hospitalares",
    bold: true, size: 30,
  })],
}));

// Autores / orientador
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 },
  children: [new TextRun({ text: "Gabriel Arcenio Rahal Marostica", size: 24 })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 },
  children: [new TextRun({ text: "Orientador: José Bernardo Neto", size: 24 })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 },
  children: [new TextRun({ text: "MBA em Engenharia de Software — USP/Esalq, 2026", size: 24 })] }));

// Resumo (opcional)
children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 200, after: 120 },
  children: [new TextRun("Resumo")] }));
children.push(corpo(
  "Este trabalho propõe e implementa uma arquitetura de referência para Conversational Analytics em ambiente hospitalar, " +
  "com governança integrada e aderente à LGPD, às normas da ANVISA e às diretrizes da ANPD, aplicada ao domínio de ocupação " +
  "de leitos. O protótipo organiza um pipeline de dados em camadas (Bronze, Silver e Gold) sob um motor de tradução de " +
  "perguntas em linguagem natural para SQL, com controles de governança na entrada e na saída e avaliação por execution match. " +
  "Toda a pesquisa usa dados exclusivamente sintéticos e execução determinista. Os resultados preliminares confirmam a " +
  "anonimização da camada exposta ao modelo e o funcionamento dos controles de governança. Numa avaliação inicial com 18 " +
  "perguntas (modelo claude-sonnet-4-6, temperatura zero), o execution match estrito foi de 61,1%, enquanto o set match de " +
  "conteúdo, que ignora forma e bloqueios de governança, foi de 94,4%, indicando que a maior parte das divergências decorre " +
  "da forma do resultado e do controle de acesso, e não de erro de cálculo do modelo (apenas 1 das 18). Dado o tamanho da " +
  "amostra, os números são indicativos e reportados com intervalo de confiança; a investigação central não é atingir um " +
  "limiar fixo de acurácia, mas caracterizar o equilíbrio entre utilidade e governança."));

// Palavras-chave
children.push(corpoRuns([
  new TextRun({ text: "Palavras-chave: ", bold: true }),
  txt("Text-to-SQL; conformidade regulatória; dados sintéticos; saúde digital; execution match."),
]));

// 1. Introducao
children.push(h1(1, "Introdução"));
children.push(corpo(
  "As interfaces em linguagem natural para bancos de dados são um campo de pesquisa maduro (AFFOLTER; STOCKINGER; BERNSTEIN, " +
  "2019). Em particular, a tradução de perguntas em linguagem natural para consultas SQL (Text-to-SQL) é objeto de estudo " +
  "consolidado, com benchmarks de referência como o Spider (YU et al., 2018) e, no domínio clínico, o EHRSQL (LEE et al., " +
  "2022), e tem sido profundamente transformada pelos modelos de linguagem de grande porte (SHI et al., 2024). A adoção desses modelos para " +
  "consulta a dados clínicos em linguagem natural promete ampliar o acesso de gestores e equipes assistenciais à informação, " +
  "mas esbarra em um obstáculo central: a governança dos dados e do próprio modelo costuma ser tratada de forma fragmentada, " +
  "separada da arquitetura de dados. Em saúde, essa fragmentação é crítica, pois envolve dados pessoais sensíveis e um marco " +
  "regulatório exigente, composto pela Lei Geral de Proteção de Dados (BRASIL, 2018), pelas normas da ANVISA aplicáveis a " +
  "software como dispositivo médico (ANVISA, 2022) e pelas diretrizes da Autoridade Nacional de Proteção de Dados (ANPD, 2024). " +
  "Soma-se a isso a necessidade de controlar riscos específicos dos modelos de linguagem, como a injeção de comandos e o " +
  "acesso indevido a recursos (OWASP, 2023), tratados na prática por meio de guardrails programáveis (REBEDEA et al., 2023) e, " +
  "no setor de saúde, sob diretrizes éticas e de governança dedicadas (WHO, 2024)."));
children.push(corpo(
  "Este trabalho parte da hipótese de que é possível integrar a governança à arquitetura de dados, de ponta a ponta, sem " +
  "comprometer a utilidade da consulta em linguagem natural. Propõe-se uma arquitetura de referência em quatro camadas, na " +
  "qual a anonimização, o controle de acesso por perfil, a validação da consulta e a auditoria atravessam todo o fluxo, da " +
  "pergunta do usuário à resposta entregue. O domínio escolhido para implementação e avaliação é a ocupação de leitos " +
  "hospitalares, e toda a pesquisa utiliza dados exclusivamente sintéticos, o que elimina na origem o risco de exposição de " +
  "dados reais e permite que a arquitetura seja replicada por outras instituições."));
children.push(corpo(
  "O objetivo geral é demonstrar, por meio de um protótipo funcional, a viabilidade dessa arquitetura integrada e " +
  "caracterizar o equilíbrio entre a utilidade da consulta (medida por execution match sobre dados sintéticos) e os controles " +
  "de governança. A pergunta de pesquisa que orienta o trabalho é: uma arquitetura que integra a governança de ponta a ponta " +
  "preserva a utilidade da consulta em linguagem natural, e a que custo mensurável? Em vez de fixar um limiar arbitrário de " +
  "acurácia, o trabalho busca medir o desempenho observado, com seus intervalos de confiança, e analisar a natureza dos erros. Como " +
  "objetivos específicos, o trabalho se propõe a: (a) revisar a literatura sobre Conversational Analytics, Text-to-SQL e " +
  "governança de modelos de linguagem; (b) mapear os requisitos regulatórios aplicáveis (LGPD, ANVISA e ANPD); (c) projetar a " +
  "arquitetura técnica, da ingestão ao Lakehouse e ao motor com guardrails; (d) desenvolver o modelo de governança, " +
  "contemplando controle de acesso, rastreabilidade, anonimização e validação; e (e) implementar e avaliar o protótipo sobre " +
  "dados sintéticos."));

// 2. Metodologia
children.push(h1(2, "Metodologia"));
children.push(corpo(
  "A pesquisa caracteriza-se como um estudo de caso instrumental apoiado no desenvolvimento de um protótipo. Os métodos são " +
  "descritos a seguir na mesma ordem em que os resultados são apresentados."));

children.push(h2("2.1", "Geração do dataset sintético"));
children.push(corpo(
  "Os dados foram gerados de forma determinista e materializados na camada Bronze do pipeline. A geração emprega a biblioteca " +
  "Faker com localidade pt_BR, governada por uma semente única, e ancora-se em uma data de referência fixa da simulação. O " +
  "ambiente representa um hospital de grande porte, com oito unidades, duzentos leitos e seiscentos pacientes, e abrange uma " +
  "janela histórica de noventa dias de ocupação diária. Dados pessoais identificáveis (nome, CPF e data de nascimento) são " +
  "inseridos de propósito na Bronze, para que a anonimização realizada na camada seguinte seja real e demonstrável."));

children.push(h2("2.2", "Arquitetura em quatro camadas"));
children.push(corpo(
  "A arquitetura organiza o sistema em quatro camadas encadeadas: o pipeline Lakehouse (Bronze, Silver e Gold), a governança " +
  "de entrada, o motor de tradução de perguntas em SQL e a validação de saída. O pipeline foi implementado em DuckDB. A camada " +
  "Bronze recebe os dados brutos; a Silver limpa e anonimiza; e a Gold expõe métricas agregadas, sendo a única camada visível " +
  "ao motor de linguagem. As camadas internas, Bronze e Silver, permanecem inacessíveis ao modelo."));

children.push(h2("2.3", "Modelo de governança"));
children.push(corpo(
  "A governança foi concebida como defesa em profundidade, alinhada às boas práticas de gestão de risco de sistemas de " +
  "inteligência artificial (NIST, 2023). Na entrada, seis guardrails verificam que a consulta candidata é " +
  "uma única instrução somente leitura, sem comandos de escrita ou administrativos, restrita às tabelas Gold autorizadas ao " +
  "perfil do usuário, e a execução ocorre sobre uma conexão de banco somente leitura. Na saída, a validação confere o " +
  "aterramento da consulta contra o schema Gold conhecido, bloqueia qualquer coluna de resultado cujo nome corresponda a um " +
  "campo sensível e registra cada pergunta e cada resposta em uma trilha de auditoria, com o evento da interação. Os guardrails " +
  "endereçam, no contexto de Text-to-SQL, riscos catalogados para aplicações de modelos de linguagem, como a injeção de " +
  "comandos e o acesso indevido a recursos (OWASP, 2023), na linha de abordagens de guardrails programáveis (REBEDEA et al., 2023)."));

children.push(h2("2.4", "Conformidade regulatória"));
children.push(corpo(
  "Os requisitos regulatórios foram mapeados a controles concretos da arquitetura, à camada responsável e à sua situação de " +
  "implementação. O mapeamento cobre a LGPD, as normas da ANVISA aplicáveis a software como dispositivo médico e as diretrizes " +
  "da ANPD, totalizando onze requisitos, e evidencia que a governança atravessa as quatro camadas e não se restringe ao motor " +
  "de inteligência artificial."));
children.push(corpo(
  "Cabe um esclarecimento de enquadramento. O protótipo realiza analytics de ocupação de leitos para apoio à gestão " +
  "hospitalar, sem finalidade diagnóstica ou terapêutica sobre paciente individual; nesse escopo, não se caracteriza como " +
  "software como dispositivo médico (SaMD) sob a RDC 657/2022. As normas da ANVISA são, portanto, adotadas por analogia, como " +
  "referência de boas práticas de controle, segurança e rastreabilidade de software em saúde, e não como obrigação de " +
  "regularização de dispositivo médico. Uma eventual evolução do sistema para finalidade clínica individual exigiria reavaliar " +
  "esse enquadramento."));

children.push(h2("2.5", "Método de avaliação"));
children.push(corpo(
  "A avaliação adota a métrica de execution match, consolidada em benchmarks de Text-to-SQL como o Spider (YU et al., 2018), o " +
  "EHRSQL (LEE et al., 2022) e o BIRD (LI et al., 2023): a consulta gerada pelo modelo e a consulta " +
  "de referência são executadas e seus conjuntos de resultados são comparados após normalização (arredondamento numérico com " +
  "tolerância de duas casas, datas em formato ISO e linhas ordenadas). Além da acurácia, são medidos dois indicadores de " +
  "governança: a taxa de aprovação das consultas pelos guardrails e a completude do log de auditoria. O conjunto de avaliação " +
  "reúne dezoito perguntas em português, com a respectiva consulta de referência sobre a Gold, cobrindo quatro tipos de " +
  "pergunta operacional: status atual, métrica por unidade, série histórica e internações por faixa etária. O motor existe em " +
  "duas implementações intercambiáveis: o oráculo, que devolve a consulta de referência e serve apenas para autoteste do " +
  "pipeline, e o modelo de linguagem real, que gera os números reportados. Por simplicidade de redação, o termo acurácia é " +
  "usado como sinônimo de execution match (taxa de correspondência exata de conjuntos de resultados), e não no sentido de " +
  "acurácia de classificação."));
children.push(corpo(
  "Além do execution match estrito, adota-se uma métrica secundária diagnóstica: o set match de conteúdo, que verifica se " +
  "todos os valores do resultado de referência aparecem no resultado gerado, ignorando colunas extras, ordem e bloqueios de " +
  "governança. Ela serve apenas para separar, na análise de erros, o conteúdo correto de divergências de forma ou de controle " +
  "de acesso; o execution match estrito permanece como métrica primária e não é substituído por ela. As proporções, dado o " +
  "tamanho do conjunto, são acompanhadas de intervalo de confiança de 95% (método de Wilson). A chamada ao modelo usa " +
  "temperatura zero, e o modelo, a temperatura e o número de execuções são registrados no relatório."));

children.push(h2("2.6", "Reprodutibilidade e integridade"));
children.push(corpo(
  "A reprodutibilidade do pipeline e dos dados foi assegurada por construção. Uma semente fixa e uma data de referência fixa " +
  "controlam toda a geração de dados e as consultas que mencionam datas relativas; o ambiente foi fixado em uma versão " +
  "específica de Python, com dependências travadas por versão e uma imagem reprodutível cuja base é fixada por digest. A " +
  "integração contínua executa, a cada alteração, apenas o motor oráculo, sem chave de API e sem custo. Há, porém, um limite " +
  "honesto a registrar: o número de acurácia provém de uma chamada a um modelo de linguagem externo, que não é estritamente " +
  "reproduzível como o restante do pipeline e é justamente o único resultado que a integração contínua não reexecuta. Ele é, " +
  "portanto, uma observação pontual, com modelo (claude-sonnet-4-6), temperatura (zero), número de execuções (uma) e data " +
  "fixados e registrados. Como princípio de integridade, os números de acurácia provêm somente da execução real do modelo, " +
  "nunca do oráculo, que serve apenas de autoteste do pipeline."));

// 3. Resultados Preliminares
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(h1(3, "Resultados Preliminares"));
children.push(corpo(
  "Apresentam-se a seguir os resultados parciais verificáveis. Os números do pipeline e dos dados provêm de execução " +
  "determinista e são reprodutíveis; os números do modelo (subseção 3.5) são observação pontual, conforme a ressalva da " +
  "subseção 2.6."));

children.push(h2("3.1", "Geração do dataset sintético"));
children.push(corpo(
  "A geração produziu, de forma determinista, oito unidades, duzentos leitos, seiscentos pacientes, 2.012 internações e 18.000 " +
  "registros de ocupação diária. No dia de referência (31 de maio de 2026), o hospital apresentava 150 leitos ocupados, 42 " +
  "livres e 8 bloqueados, o que corresponde a uma taxa de ocupação de 75,0%. A coerência foi verificada: as 150 internações " +
  "ativas igualaram exatamente os 150 leitos ocupados no dia de referência. A transformação para as camadas Silver e Gold " +
  "confirmou a anonimização: a tabela de pacientes da Silver não contém nome, CPF nem data de nascimento; o identificador do " +
  "paciente foi substituído por um pseudônimo derivado de hash com salt, sem colisão entre os seiscentos pacientes; e a data " +
  "de nascimento deu lugar à faixa etária, em linha com os princípios de anonimização e generalização de atributos " +
  "identificadores (SWEENEY, 2002). A Tabela 1 resume o snapshot de ocupação por unidade."));
children.push(tabela([2351, 1240, 1240, 1240, 1500, 1500], [
  ["Unidade", "Total", "Ocup.", "Livres", "Bloq.", "Taxa (%)"],
  ["Cardiologia", "25", "18", "6", "1", "72,0"],
  ["Pediatria", "25", "17", "6", "2", "68,0"],
  ["Clínica Médica", "25", "21", "4", "0", "84,0"],
  ["Cirurgia Geral", "25", "23", "2", "0", "92,0"],
  ["Ortopedia", "25", "16", "5", "4", "64,0"],
  ["Neurologia", "25", "20", "5", "0", "80,0"],
  ["Oncologia", "25", "17", "7", "1", "68,0"],
  ["Pronto-Socorro", "25", "18", "7", "0", "72,0"],
  ["Hospital", "200", "150", "42", "8", "75,0"],
]));
children.push(legenda("Tabela 1. Ocupação por unidade no dia de referência (camada Gold). Fonte: o autor."));

children.push(h2("3.2", "Arquitetura de referência em quatro camadas"));
children.push(corpo(
  "A arquitetura foi documentada e implementada nas quatro camadas, com fluxo rastreável da pergunta do usuário à resposta " +
  "entregue. Apenas a camada Gold, agregada, é exposta ao modelo; as camadas Bronze e Silver permanecem inacessíveis. A " +
  "documentação modular do protótipo consolida essa arquitetura como o principal artefato de referência do trabalho, com " +
  "decisões, regras críticas, controles e requisitos regulatórios identificados e rastreáveis ao código. A numeração das " +
  "camadas (1 a 4) é lógica e arquitetural; a ordem de execução em tempo de consulta é outra, partindo da governança de " +
  "entrada (2) para o motor (3), o pipeline de dados (1) e a validação de saída (4), como ilustra a Figura A.1."));

children.push(h2("3.3", "Modelo de governança de entrada e saída"));
children.push(corpo(
  "Os controles de governança foram implementados e verificados por testes. A eficácia foi observada na avaliação com o modelo " +
  "real: em duas perguntas (Q01 e Q11), o modelo produziu uma consulta que retornaria o número correto, porém a partir de uma " +
  "tabela fora do escopo autorizado ao perfil de enfermagem. Em ambos os casos, o guardrail de escopo por perfil bloqueou a " +
  "execução antes que a consulta tocasse o banco, evidenciando que o controle de acesso por finalidade opera como projetado. A " +
  "validação de saída e a auditoria da resposta completam a barreira final de governança."));
children.push(corpo(
  "Esse comportamento revela um achado quantificável: existe um trade-off explícito entre a acurácia medida e a governança. As " +
  "duas perguntas bloqueadas tinham conteúdo correto, mas foram barradas por acessarem tabela fora do escopo do perfil; ou " +
  "seja, o controle de acesso por finalidade custou 2 das 18 perguntas, cerca de 11 pontos percentuais de execution match. " +
  "Trata-se de um custo deliberado e desejável: a arquitetura prefere recusar uma resposta correta obtida por um caminho não " +
  "autorizado a entregá-la violando o princípio do menor privilégio. Quantificar esse custo é, em si, um resultado: responde " +
  "com dados à pergunta sobre se a governança compromete a utilidade."));

children.push(h2("3.4", "Conformidade regulatória"));
children.push(corpo(
  "O mapeamento entre os onze requisitos regulatórios e os controles da arquitetura foi concluído, associando cada requisito a " +
  "um controle implementado, à camada responsável e à sua situação. O resultado demonstra que a governança é transversal às " +
  "quatro camadas, e não um componente isolado do motor de inteligência artificial."));

children.push(h2("3.5", "Avaliação"));
children.push(corpo(
  "O pipeline de avaliação foi exercitado de ponta a ponta com o motor oráculo. Para as dezoito perguntas, o execution match " +
  "resultou em 100%, a aprovação na governança em 100% e a completude do log em 100%. Esse resultado é um autoteste do " +
  "pipeline e não representa o desempenho do modelo."));
children.push(corpo(
  "A execução com o modelo de linguagem real (claude-sonnet-4-6, temperatura zero, execução única) sobre as dezoito perguntas " +
  "resultou em 61,1% de execution match estrito (11 de 18) e 94,4% de set match de conteúdo (17 de 18). Uma execução-piloto " +
  "anterior, sobre um subconjunto de dez perguntas, havia dado 60,0%. O conjunto é pequeno e os valores são, portanto, " +
  "indicativos; por isso são reportados com intervalo de confiança de 95% pelo método de Wilson, amplo nesta escala: [38,6%; " +
  "79,7%] para o execution match estrito e [74,2%; 99,0%] para o set match de conteúdo. A ampliação do conjunto está no plano " +
  "de continuidade, justamente para estreitar esses intervalos. O patamar do execution match estrito é coerente com a " +
  "literatura, em que mesmo modelos avançados alcançam acurácia limitada em benchmarks realistas, a exemplo dos cerca de 40% " +
  "relatados para o ChatGPT no BIRD (LI et al., 2023). A Tabela 2 resume os indicadores."));
children.push(tabela([4400, 2500, 2171], [
  ["Indicador", "Valor", "IC 95% (Wilson)"],
  ["Execution match estrito (primária)", "61,1% (11/18)", "[38,6%; 79,7%]"],
  ["Set match de conteúdo (secundária, diagnóstica)", "94,4% (17/18)", "[74,2%; 99,0%]"],
  ["Aprovação na governança", "88,9% (16/18)", "—"],
  ["Completude do log de auditoria", "100% (18/18)", "—"],
]));
children.push(legenda(
  "Tabela 2. Indicadores de avaliação do modelo real (claude-sonnet-4-6, temperatura zero, execução única) sobre 18 perguntas. " +
  "Execution match estrito = AVAL-001 (primária); aprovação na governança = AVAL-002; completude do log = AVAL-003; set match " +
  "de conteúdo = métrica secundária diagnóstica. IC pelo método de Wilson. Fonte: o autor."));
children.push(corpo(
  "A distância entre o execution match estrito (61,1%) e o set match de conteúdo (94,4%) é o resultado mais informativo: os " +
  "33 pontos de diferença não vêm de raciocínio errado, mas da forma do resultado e da governança. A Tabela 3 decompõe os " +
  "dezoito casos. O conteúdo esteve correto em 17 deles; apenas um (Q12) apresentou erro de conteúdo. Esse único erro não é " +
  "bem uma falha de raciocínio do modelo, mas uma lacuna de desenho do nosso pipeline: o prompt não expõe ao modelo os " +
  "valores categóricos do schema, e ele filtrou um valor com a caixa incorreta (\"enfermaria\" em vez de \"Enfermaria\"), " +
  "obtendo conjunto vazio. Esse ponto (value linking) já está no plano de continuidade. Manteve-se o execution match estrito " +
  "como métrica primária; o set match de conteúdo é diagnóstico e acompanha a análise, sem substituí-la."));
children.push(tabela([2271, 1000, 5800], [
  ["Categoria", "Itens", "Natureza"],
  ["Correta (execution match estrito)", "11", "Conjunto de resultados idêntico ao da referência."],
  ["Conteúdo certo, forma/projeção", "4", "Valores corretos, com colunas extras ou formato distinto; limitação do execution match (Q04, Q13, Q14, Q15)."],
  ["Conteúdo certo, bloqueio de governança", "2", "Valor correto, mas via tabela fora do escopo do perfil; barrado pelo guardrail (Q01, Q11)."],
  ["Erro de conteúdo", "1", "Filtragem de valor categórico com caixa incorreta; lacuna de value linking no prompt (Q12)."],
]));
children.push(legenda(
  "Tabela 3. Categorização dos dezoito casos da execução com o modelo real. Conteúdo correto em 17 de 18 (94,4%); execution " +
  "match estrito em 11 de 18 (61,1%). Fonte: o autor."));

children.push(h2("3.6", "Reprodutibilidade e integridade"));
children.push(corpo(
  "A reprodutibilidade do pipeline foi confirmada: a mesma configuração reproduz os mesmos dados e números, inclusive entre as " +
  "versões 3.12 e 3.14 do Python. A integração contínua executa o autoteste a cada alteração, sem chave e sem custo, e a " +
  "imagem reprodutível fixa o ambiente por completo. O número de acurácia, por vir de um modelo externo, é a exceção: foi " +
  "coletado em execução real única, com modelo, temperatura e data registrados, e é reportado como observação pontual com " +
  "intervalo de confiança (subseção 2.6). A metodologia de medição foi decidida antes da reexecução, e o execution match " +
  "estrito (primária) é reportado junto da métrica secundária de conteúdo, sem que esta o substitua, preservando a integridade " +
  "dos resultados."));

// 4. Consideracoes finais
children.push(h1(4, "Considerações Finais (parciais)"));
children.push(corpo(
  "Os resultados preliminares confirmam a viabilidade técnica da arquitetura integrada: o pipeline de dados é coerente e " +
  "anonimizado, os controles de governança funcionam de ponta a ponta e a avaliação produz números reais e verificáveis. " +
  "Quanto à pergunta de pesquisa, os dados sugerem que a governança integrada preserva a utilidade da consulta a um custo " +
  "mensurável e modesto: o conteúdo das respostas esteve correto em 17 de 18 casos (94,4%), enquanto o execution match " +
  "estrito (61,1%) é puxado para baixo pela forma do resultado e pelo controle de acesso, não pelo raciocínio do modelo; o " +
  "custo direto da governança foi de cerca de 11 pontos (2 respostas corretas, mas fora do escopo do perfil). Esses números, " +
  "porém, vêm de uma amostra pequena, com intervalos de confiança amplos, e devem ser lidos como indicativos. Como " +
  "continuidade, preveem-se o tratamento de value linking (exposição dos valores categóricos do schema ao modelo), a " +
  "ampliação e estratificação do conjunto de avaliação por tipo de pergunta e por perfil (para estreitar os intervalos) e o " +
  "aprofundamento da discussão sobre a métrica sensível à forma."));

// Referencias
children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 240, after: 160 },
  children: [new TextRun("Referências")] }));
function ref(text) {
  return new Paragraph({
    alignment: AlignmentType.LEFT,
    spacing: { line: 360, after: 120 },
    indent: { left: 480, hanging: 480 },
    children: [new TextRun(text)],
  });
}
const REFS = [
  "AFFOLTER, K.; STOCKINGER, K.; BERNSTEIN, A. A comparative survey of recent natural language interfaces for databases. The VLDB Journal, v. 28, n. 5, p. 793-819, 2019. DOI: 10.1007/s00778-019-00567-8. Disponível em: https://doi.org/10.1007/s00778-019-00567-8. Acesso em: 10 jun. 2026.",
  "AGÊNCIA NACIONAL DE VIGILÂNCIA SANITÁRIA (ANVISA). Resolução da Diretoria Colegiada – RDC nº 657, de 24 de março de 2022. Dispõe sobre a regularização de software como dispositivo médico (Software as a Medical Device – SaMD). Brasília, DF: Anvisa, 2022. Disponível em: https://anvisalegis.datalegis.net/action/ActionDatalegis.php?acao=abrirTextoAto&tipo=RDC&numeroAto=00000657&seqAto=000&valorAno=2022&orgao=RDC/DC/ANVISA/MS. Acesso em: 10 jun. 2026.",
  "AUTORIDADE NACIONAL DE PROTEÇÃO DE DADOS (ANPD). Radar tecnológico: inteligência artificial generativa. Brasília, DF: ANPD, 2024. Disponível em: https://www.gov.br/anpd/pt-br/documentos-e-publicacoes/documentos-de-publicacoes/radar_tecnologico_ia_generativa_anpd.pdf. Acesso em: 10 jun. 2026.",
  "BRASIL. Lei nº 13.709, de 14 de agosto de 2018. Lei Geral de Proteção de Dados Pessoais (LGPD). Brasília, DF: Presidência da República, 2018. Disponível em: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm. Acesso em: 10 jun. 2026.",
  "LEE, G.; HWANG, H.; BAE, S.; KWON, Y.; SHIN, W.; YANG, S.; SEO, M.; KIM, J.-Y.; CHOI, E. EHRSQL: a practical text-to-SQL benchmark for electronic health records. In: Advances in Neural Information Processing Systems (NeurIPS) – Datasets and Benchmarks Track, 2022. Disponível em: https://arxiv.org/abs/2301.07695. Acesso em: 10 jun. 2026.",
  "LI, J.; HUI, B.; QU, G. et al. Can LLM already serve as a database interface? A big bench for large-scale database grounded text-to-SQLs (BIRD). In: Advances in Neural Information Processing Systems (NeurIPS) – Datasets and Benchmarks Track, 2023. Disponível em: https://arxiv.org/abs/2305.03111. Acesso em: 10 jun. 2026.",
  "NATIONAL INSTITUTE OF STANDARDS AND TECHNOLOGY (NIST). Artificial Intelligence Risk Management Framework (AI RMF 1.0). NIST AI 100-1. Gaithersburg, MD: NIST, 2023. Disponível em: https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf. Acesso em: 10 jun. 2026.",
  "OWASP. OWASP Top 10 for Large Language Model Applications. [S. l.]: OWASP Foundation, 2023. Disponível em: https://owasp.org/www-project-top-10-for-large-language-model-applications/. Acesso em: 10 jun. 2026.",
  "REBEDEA, T.; DINU, R.; SREEDHAR, M. N.; PARISIEN, C.; COHEN, J. NeMo Guardrails: a toolkit for controllable and safe LLM applications with programmable rails. In: Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing (EMNLP): System Demonstrations, p. 431-445, 2023. Disponível em: https://arxiv.org/abs/2310.10501. Acesso em: 10 jun. 2026.",
  "SHI, L.; TANG, Z.; ZHANG, N.; ZHANG, X.; YANG, Z. A survey on employing large language models for text-to-SQL tasks. ACM Computing Surveys, 2024. Disponível em: https://arxiv.org/abs/2407.15186. Acesso em: 10 jun. 2026.",
  "SWEENEY, L. k-anonymity: a model for protecting privacy. International Journal of Uncertainty, Fuzziness and Knowledge-Based Systems, v. 10, n. 5, p. 557-570, 2002. DOI: 10.1142/S0218488502001648. Disponível em: https://doi.org/10.1142/S0218488502001648. Acesso em: 10 jun. 2026.",
  "WORLD HEALTH ORGANIZATION (WHO). Ethics and governance of artificial intelligence for health: guidance on large multi-modal models. Geneva: WHO, 2024. Disponível em: https://www.who.int/publications/b/70584. Acesso em: 10 jun. 2026.",
  "YU, T.; ZHANG, R.; YANG, K.; YASUNAGA, M.; WANG, D.; LI, Z.; MA, J.; LI, I.; YAO, Q.; ROMAN, S.; ZHANG, Z.; RADEV, D. Spider: a large-scale human-labeled dataset for complex and cross-domain semantic parsing and text-to-SQL task. In: Proceedings of the 2018 Conference on Empirical Methods in Natural Language Processing (EMNLP), 2018. Disponível em: https://arxiv.org/abs/1809.08887. Acesso em: 10 jun. 2026.",
];
REFS.forEach((r) => children.push(ref(r)));

// Apendice A — arquitetura (diagrama + quadro)
children.push(new Paragraph({ pageBreakBefore: true, heading: HeadingLevel.HEADING_1, spacing: { before: 120, after: 160 },
  children: [new TextRun("Apêndice A — Arquitetura de referência em quatro camadas")] }));
const imgPath = path.join(__dirname, "assets", "arquitetura_camadas.png");
const imgW = 440, imgH = Math.round(imgW * (845 / 1041));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 },
  children: [new ImageRun({
    type: "png", data: fs.readFileSync(imgPath),
    transformation: { width: imgW, height: imgH },
    altText: { title: "Arquitetura em quatro camadas", name: "arquitetura_camadas",
      description: "Fluxo de uma pergunta pelas quatro camadas da arquitetura" },
  })] }));
children.push(legenda("Figura A.1. Fluxo de uma pergunta pelas quatro camadas. Fonte: o autor."));
children.push(tabela([2051, 4920, 2100], [
  ["Camada", "Responsabilidade", "Documentação"],
  ["1. Pipeline Lakehouse", "Ingestão (Bronze), limpeza e anonimização (Silver), métricas (Gold)", "camadas/01"],
  ["2. Governança de entrada", "Perfil, registro da pergunta e conformidade antes de executar", "camadas/02"],
  ["3. Motor Text-to-SQL", "Pergunta em português para SQL somente leitura na Gold", "camadas/03"],
  ["4. Validação de saída", "Aterramento, filtro de campo sensível e auditoria da resposta", "camadas/04"],
]));
children.push(legenda("Quadro A.1. Síntese das quatro camadas. Fonte: o autor."));

// Apendice B — requisitos regulatorios x controles
children.push(new Paragraph({ pageBreakBefore: true, heading: HeadingLevel.HEADING_1, spacing: { before: 120, after: 160 },
  children: [new TextRun("Apêndice B — Requisitos regulatórios e controles")] }));
children.push(tabela([1740, 5131, 2200], [
  ["Requisito", "Controle na arquitetura", "Camada"],
  ["REG-LGPD-001", "Anonimização na Silver: remoção de nome, CPF e data de nascimento; derivação de faixa etária", "Silver"],
  ["REG-LGPD-002", "Pseudonimização de id_paciente por hash; nenhuma identificação direta sobrevive à Silver", "Silver"],
  ["REG-LGPD-003", "Apenas a Gold, agregada, é exposta ao motor; Bronze e Silver inacessíveis (CTRL-GOV-004)", "Gold"],
  ["REG-LGPD-004", "Perfis autorizam apenas tabelas Gold específicas (CTRL-GOV-005)", "Entrada"],
  ["REG-LGPD-005", "Guardrails CTRL-GOV-001 a 003 e 006: SQL única somente leitura, sem escrita/admin, conexão read-only", "Entrada"],
  ["REG-LGPD-006", "Filtro de saída CTRL-VALID-002: bloqueia coluna com nome de campo sensível", "Saída"],
  ["REG-LGPD-007", "Auditoria CTRL-AUD-001: registro de toda pergunta e resposta", "Auditoria"],
  ["REG-ANPD-001", "Aterramento CTRL-VALID-001: toda tabela citada deve existir no schema Gold conhecido", "Saída"],
  ["REG-ANPD-002", "Escopo restrito por perfil, execução somente leitura e registro integral", "Entrada e Auditoria"],
  ["REG-ANVISA-001", "Guardrails versionados, auditoria e reprodutibilidade do software", "Transversal"],
  ["REG-PESQ-001", "Determinismo (SEED, SIM_TODAY); separação motor LLM (números) vs oráculo (autoteste)", "Transversal"],
]));
children.push(legenda("Quadro B.1. Mapeamento de requisitos regulatórios para controles e camadas. Fonte: o autor."));

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 24 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 240, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 160, after: 100 }, outlineLevel: 1 } },
    ],
  },
  sections: [{
    properties: { page: {
      size: { width: 11906, height: 16838 },
      margin: { top: 1701, right: 1134, bottom: 1134, left: 1701 },
    } },
    children: children.filter(Boolean),
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(process.argv[2], buf);
  console.log("gerado:", process.argv[2]);
});

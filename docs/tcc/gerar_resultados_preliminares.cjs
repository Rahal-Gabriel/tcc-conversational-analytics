const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
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
  children: [new TextRun("Resumo (opcional nesta etapa)")] }));
children.push(corpo(
  "Este trabalho propõe e implementa uma arquitetura de referência para Conversational Analytics em ambiente hospitalar, " +
  "com governança integrada e aderente à LGPD, às normas da ANVISA e às diretrizes da ANPD, aplicada ao domínio de ocupação " +
  "de leitos. O protótipo organiza um pipeline de dados em camadas (Bronze, Silver e Gold) sob um motor de tradução de " +
  "perguntas em linguagem natural para SQL, com controles de governança na entrada e na saída e avaliação por execution match. " +
  "Toda a pesquisa usa dados exclusivamente sintéticos e execução determinista. Os resultados preliminares confirmam a " +
  "anonimização da camada exposta ao modelo, o funcionamento dos controles de governança e os primeiros números de acurácia " +
  "do motor de linguagem, acompanhados de uma análise de erros que distingue limitações da métrica e da governança de erros " +
  "de cálculo do modelo."));

// Palavras-chave
children.push(corpoRuns([
  new TextRun({ text: "Palavras-chave: ", bold: true }),
  txt("Text-to-SQL; conformidade regulatória; dados sintéticos; saúde digital; execution match."),
]));

// 1. Introducao
children.push(h1(1, "Introdução"));
children.push(corpo(
  "A tradução de perguntas em linguagem natural para consultas SQL (Text-to-SQL) é objeto de pesquisa consolidado, com " +
  "benchmarks de referência como o Spider (YU et al., 2018) e, no domínio clínico, o EHRSQL (LEE et al., 2022), e tem sido " +
  "profundamente transformada pelos modelos de linguagem de grande porte (SHI et al., 2024). A adoção desses modelos para " +
  "consulta a dados clínicos em linguagem natural promete ampliar o acesso de gestores e equipes assistenciais à informação, " +
  "mas esbarra em um obstáculo central: a governança dos dados e do próprio modelo costuma ser tratada de forma fragmentada, " +
  "separada da arquitetura de dados. Em saúde, essa fragmentação é crítica, pois envolve dados pessoais sensíveis e um marco " +
  "regulatório exigente, composto pela Lei Geral de Proteção de Dados (BRASIL, 2018), pelas normas da ANVISA aplicáveis a " +
  "software como dispositivo médico (ANVISA, 2022) e pelas diretrizes da Autoridade Nacional de Proteção de Dados (ANPD, 2024)."));
children.push(corpo(
  "Este trabalho parte da hipótese de que é possível integrar a governança à arquitetura de dados, de ponta a ponta, sem " +
  "comprometer a utilidade da consulta em linguagem natural. Propõe-se uma arquitetura de referência em quatro camadas, na " +
  "qual a anonimização, o controle de acesso por perfil, a validação da consulta e a auditoria atravessam todo o fluxo, da " +
  "pergunta do usuário à resposta entregue. O domínio escolhido para implementação e avaliação é a ocupação de leitos " +
  "hospitalares, e toda a pesquisa utiliza dados exclusivamente sintéticos, o que elimina na origem o risco de exposição de " +
  "dados reais e permite que a arquitetura seja replicada por outras instituições."));
children.push(corpo(
  "O objetivo geral é demonstrar, por meio de um protótipo funcional, a viabilidade dessa arquitetura integrada e avaliar a " +
  "acurácia do motor de tradução de perguntas em SQL sobre dados sintéticos, sob a hipótese de acurácia superior a 80%. Como " +
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
  "A governança foi concebida como defesa em profundidade. Na entrada, seis guardrails verificam que a consulta candidata é " +
  "uma única instrução somente leitura, sem comandos de escrita ou administrativos, restrita às tabelas Gold autorizadas ao " +
  "perfil do usuário, e a execução ocorre sobre uma conexão de banco somente leitura. Na saída, a validação confere o " +
  "aterramento da consulta contra o schema Gold conhecido, bloqueia qualquer coluna de resultado cujo nome corresponda a um " +
  "campo sensível e registra cada pergunta e cada resposta em uma trilha de auditoria, com o evento da interação."));

children.push(h2("2.4", "Conformidade regulatória"));
children.push(corpo(
  "Os requisitos regulatórios foram mapeados a controles concretos da arquitetura, à camada responsável e à sua situação de " +
  "implementação. O mapeamento cobre a LGPD, as normas da ANVISA aplicáveis a software como dispositivo médico e as diretrizes " +
  "da ANPD, totalizando onze requisitos, e evidencia que a governança atravessa as quatro camadas e não se restringe ao motor " +
  "de inteligência artificial."));

children.push(h2("2.5", "Método de avaliação"));
children.push(corpo(
  "A avaliação adota a métrica de execution match, consolidada em benchmarks de Text-to-SQL como o Spider (YU et al., 2018), o " +
  "EHRSQL (LEE et al., 2022) e o BIRD (LI et al., 2023): a consulta gerada pelo modelo e a consulta " +
  "de referência são executadas e seus conjuntos de resultados são comparados após normalização (arredondamento numérico com " +
  "tolerância de duas casas, datas em formato ISO e linhas ordenadas). Além da acurácia, são medidos dois indicadores de " +
  "governança: a taxa de aprovação das consultas pelos guardrails e a completude do log de auditoria. O conjunto de avaliação " +
  "reúne dezoito perguntas em português, com a respectiva consulta de referência sobre a Gold, cobrindo quatro tipos de " +
  "pergunta operacional: status atual, métrica por unidade, série histórica e internações por faixa etária. O motor existe em " +
  "duas implementações intercambiáveis: o oráculo, que devolve a consulta de referência e serve apenas para autoteste da " +
  "tubulação, e o modelo de linguagem real, que gera os números reportados."));

children.push(h2("2.6", "Reprodutibilidade e integridade"));
children.push(corpo(
  "A reprodutibilidade foi assegurada por construção. Uma semente fixa e uma data de referência fixa controlam toda a geração " +
  "de dados e as consultas que mencionam datas relativas; o ambiente foi fixado em uma versão específica de Python, com " +
  "dependências travadas por versão e uma imagem reprodutível cuja base é fixada por digest. A integração contínua executa, a " +
  "cada alteração, apenas o motor oráculo, sem chave de API e sem custo. Como princípio de integridade, os números de acurácia " +
  "provêm somente da execução real do modelo, com a separação explícita entre o oráculo (autoteste) e o modelo (desempenho)."));

// 3. Resultados Preliminares
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(h1(3, "Resultados Preliminares"));
children.push(corpo(
  "Apresentam-se a seguir os resultados parciais verificáveis. Os números provêm de execução determinista e são reprodutíveis."));

children.push(h2("3.1", "Geração do dataset sintético"));
children.push(corpo(
  "A geração produziu, de forma determinista, oito unidades, duzentos leitos, seiscentos pacientes, 2.012 internações e 18.000 " +
  "registros de ocupação diária. No dia de referência (31 de maio de 2026), o hospital apresentava 150 leitos ocupados, 42 " +
  "livres e 8 bloqueados, o que corresponde a uma taxa de ocupação de 75,0%. A coerência foi verificada: as 150 internações " +
  "ativas igualaram exatamente os 150 leitos ocupados no dia de referência. A transformação para as camadas Silver e Gold " +
  "confirmou a anonimização: a tabela de pacientes da Silver não contém nome, CPF nem data de nascimento; o identificador do " +
  "paciente foi substituído por um pseudônimo derivado de hash com salt, sem colisão entre os seiscentos pacientes; e a data " +
  "de nascimento deu lugar à faixa etária. A Tabela 1 resume o snapshot de ocupação por unidade."));
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
  "decisões, regras críticas, controles e requisitos regulatórios identificados e rastreáveis ao código."));

children.push(h2("3.3", "Modelo de governança de entrada e saída"));
children.push(corpo(
  "Os controles de governança foram implementados e verificados por testes. A eficácia foi observada na avaliação com o modelo " +
  "real: em duas perguntas, o modelo produziu uma consulta que retornaria o número correto, porém a partir de uma tabela fora " +
  "do escopo autorizado ao perfil de enfermagem. Em ambos os casos, o guardrail de escopo por perfil bloqueou a execução antes " +
  "que a consulta tocasse o banco, evidenciando que o controle de acesso por finalidade opera como projetado. A validação de " +
  "saída e a auditoria da resposta completam a barreira final de governança."));

children.push(h2("3.4", "Conformidade regulatória"));
children.push(corpo(
  "O mapeamento entre os onze requisitos regulatórios e os controles da arquitetura foi concluído, associando cada requisito a " +
  "um controle implementado, à camada responsável e à sua situação. O resultado demonstra que a governança é transversal às " +
  "quatro camadas, e não um componente isolado do motor de inteligência artificial."));

children.push(h2("3.5", "Avaliação"));
children.push(corpo(
  "A tubulação de avaliação foi exercitada de ponta a ponta com o motor oráculo. Para as dezoito perguntas, o execution match " +
  "resultou em 100%, a aprovação na governança em 100% e a completude do log em 100%. Esse resultado é um autoteste da " +
  "tubulação e não representa o desempenho do modelo."));
children.push(corpo(
  "A primeira execução com o modelo de linguagem real forneceu os primeiros números de acurácia. Sobre o conjunto inicial de " +
  "dez perguntas, o execution match estrito foi de 60,0%. Após a correção de uma inconsistência interna do harness de medição " +
  "(o arredondamento embutido na consulta de referência) e a ampliação do conjunto para dezoito perguntas, o execution match " +
  "foi de 61,1%. A estabilidade do valor com o conjunto quase dobrado indica que a medida não foi fortuita. A Tabela 2 reporta " +
  "as duas execuções lado a lado."));
children.push(tabela([2271, 1700, 1700, 1700, 1700], [
  ["Execução", "Conjunto", "AVAL-001", "AVAL-002", "AVAL-003"],
  ["Bruta (1ª)", "10 perguntas", "60,0%", "90,0%", "100,0%"],
  ["Refinada", "18 perguntas", "61,1%", "88,9%", "100,0%"],
]));
children.push(legenda("Tabela 2. Indicadores de avaliação do modelo real, bruto e refinado. Fonte: o autor."));
children.push(corpo(
  "A análise dos resultados não correspondentes da execução refinada mostrou que a maior parte não decorreu de erro de cálculo " +
  "do modelo, conforme a Tabela 3. Das dezoito perguntas, apenas uma apresentou erro genuíno de cálculo (filtragem de um valor " +
  "categórico com a caixa incorreta, resultando em conjunto vazio). Duas foram bloqueadas pela governança, por acessarem tabela " +
  "fora do escopo do perfil, embora o valor numérico estivesse correto. As quatro restantes divergiram apenas na forma do " +
  "resultado, com colunas adicionais ou formato distinto, refletindo a sensibilidade conhecida do execution match estrito à " +
  "projeção. Manteve-se o execution match estrito como métrica primária, sem a introdução de métricas alternativas mais " +
  "permissivas; a categorização dos erros acompanha o número."));
children.push(tabela([2271, 1200, 5600], [
  ["Categoria", "Itens", "Natureza"],
  ["Bloqueio pela governança", "2", "Valor correto, porém via tabela fora do escopo do perfil; barrado pelo guardrail."],
  ["Forma / projeção", "4", "Valores corretos, com colunas extras ou formato distinto; limitação do execution match."],
  ["Erro de cálculo", "1", "Filtragem de valor categórico com caixa incorreta (value linking)."],
  ["Corretas", "11", "Conjunto de resultados idêntico ao da referência."],
]));
children.push(legenda("Tabela 3. Categorização dos resultados da execução refinada (18 perguntas). Fonte: o autor."));

children.push(h2("3.6", "Reprodutibilidade e integridade"));
children.push(corpo(
  "A reprodutibilidade foi confirmada: a mesma configuração reproduz os mesmos dados e números, inclusive entre as versões 3.12 " +
  "e 3.14 do Python. A integração contínua executa o autoteste a cada alteração, sem chave e sem custo, e a imagem reprodutível " +
  "fixa o ambiente por completo. Os números de acurácia foram coletados apenas em execução real do modelo, com a metodologia de " +
  "medição decidida antes da reexecução e os valores bruto e refinado reportados lado a lado, preservando a integridade dos " +
  "resultados."));

// 4. Consideracoes finais
children.push(h1(4, "Considerações Finais (parciais)"));
children.push(corpo(
  "Os resultados preliminares confirmam a viabilidade técnica da arquitetura integrada: o pipeline de dados é coerente e " +
  "anonimizado, os controles de governança funcionam de ponta a ponta e a avaliação produz números reais e verificáveis. Sob " +
  "execution match estrito, a hipótese de acurácia superior a 80% ainda não se confirma; a análise de erros, contudo, indica " +
  "que o teto é puxado pela forma do resultado e pela governança, e não pelo raciocínio do modelo, já que apenas um dos " +
  "dezoito casos correspondeu a erro de cálculo. Como continuidade, preveem-se o tratamento de value linking (exposição dos " +
  "valores categóricos do schema ao modelo ou comparação textual sem distinção de caixa), a discussão da métrica sensível à " +
  "forma e a ampliação e estratificação do conjunto de avaliação por tipo de pergunta e por perfil."));

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
  "AGÊNCIA NACIONAL DE VIGILÂNCIA SANITÁRIA (ANVISA). Resolução da Diretoria Colegiada – RDC nº 657, de 24 de março de 2022. Dispõe sobre a regularização de software como dispositivo médico (Software as a Medical Device – SaMD). Brasília, DF: Anvisa, 2022.",
  "AUTORIDADE NACIONAL DE PROTEÇÃO DE DADOS (ANPD). Radar tecnológico: inteligência artificial generativa. Brasília, DF: ANPD, 2024.",
  "BRASIL. Lei nº 13.709, de 14 de agosto de 2018. Lei Geral de Proteção de Dados Pessoais (LGPD). Brasília, DF: Presidência da República, 2018.",
  "LEE, G.; HWANG, H.; BAE, S.; KWON, Y.; SHIN, W.; YANG, S.; SEO, M.; KIM, J.-Y.; CHOI, E. EHRSQL: a practical text-to-SQL benchmark for electronic health records. In: Advances in Neural Information Processing Systems (NeurIPS) – Datasets and Benchmarks Track, 2022. arXiv:2301.07695.",
  "LI, J.; HUI, B.; QU, G. et al. Can LLM already serve as a database interface? A big bench for large-scale database grounded text-to-SQLs (BIRD). In: Advances in Neural Information Processing Systems (NeurIPS) – Datasets and Benchmarks Track, 2023. arXiv:2305.03111.",
  "SHI, L.; TANG, Z.; ZHANG, N.; ZHANG, X.; YANG, Z. A survey on employing large language models for text-to-SQL tasks. ACM Computing Surveys, 2024. arXiv:2407.15186.",
  "YU, T.; ZHANG, R.; YANG, K.; YASUNAGA, M.; WANG, D.; LI, Z.; MA, J.; LI, I.; YAO, Q.; ROMAN, S.; ZHANG, Z.; RADEV, D. Spider: a large-scale human-labeled dataset for complex and cross-domain semantic parsing and text-to-SQL task. In: Proceedings of the 2018 Conference on Empirical Methods in Natural Language Processing (EMNLP), 2018. arXiv:1809.08887.",
];
REFS.forEach((r) => children.push(ref(r)));
children.push(new Paragraph({ spacing: { before: 120 }, children: [new TextRun({
  text: "Nota (remover antes do depósito): referências reais, verificadas, propostas para os temas do trabalho. Confirme que " +
        "foram efetivamente consultadas, ajuste à formatação ABNT da USP/Esalq (data de acesso, DOI/URL) e acrescente as demais " +
        "obras da sua revisão de literatura.",
  italics: true, size: 18, color: "777777",
})] }));

// Apendice
children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 240, after: 160 },
  children: [new TextRun("Apêndice A — Camadas da arquitetura")] }));
children.push(tabela([2051, 4920, 2100], [
  ["Camada", "Responsabilidade", "Documentação"],
  ["1. Pipeline Lakehouse", "Ingestão (Bronze), limpeza e anonimização (Silver), métricas (Gold)", "camadas/01"],
  ["2. Governança de entrada", "Perfil, registro da pergunta e conformidade antes de executar", "camadas/02"],
  ["3. Motor Text-to-SQL", "Pergunta em português para SQL somente leitura na Gold", "camadas/03"],
  ["4. Validação de saída", "Aterramento, filtro de campo sensível e auditoria da resposta", "camadas/04"],
]));
children.push(legenda("Quadro A.1. Síntese das quatro camadas. Fonte: o autor."));

// nota de rodape do rascunho
children.push(new Paragraph({ spacing: { before: 240 }, children: [new TextRun({
  text: "Nota (remover antes do depósito): documento de apoio gerado a partir da documentação do protótipo (RES-001 a RES-007). " +
        "Capa, objetivos e referências já preenchidos; confira a formatação ABNT da USP/Esalq e acrescente as demais obras da " +
        "revisão de literatura. Teto de 30 páginas; redação no pretérito impessoal.",
  italics: true, size: 18, color: "777777",
})] }));

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

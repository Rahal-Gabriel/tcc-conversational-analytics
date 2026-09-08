# 05. Método de pesquisa, arquitetura de referência e dados sintéticos

**Última atualização**: 2026-09-08
**Alimenta**: Metodologia · Ameaças à validade · Resultados e Discussão

Legenda de verificação: ✔ lido na fonte · ◐ só resumo de busca · ⚠ conferir dado.

---

## O que a literatura permite afirmar

1. O delineamento "estudo de caso com protótipo" tem guias próprios em
   engenharia de software (Runeson e Höst 2009), com as quatro categorias de
   ameaça à validade (construção, interna, externa, confiabilidade) já usadas
   no documento (Wohlin et al. 2012).
2. "Arquitetura de referência" é um termo técnico com definição e critérios de
   avaliação (Angelov et al. 2012); o principal artefato do TCC pode ser
   descrito e avaliado com esse vocabulário, e a documentação modular pode ser
   apresentada como artefato de design science (Hevner et al. 2004).
3. O lakehouse tem referência acadêmica (Armbrust et al. 2021); a arquitetura
   medalhão (Bronze/Silver/Gold) só tem documentação de fornecedor, que o
   manual desaconselha citar; descrevê-la como padrão de camadas do lakehouse
   citando Armbrust et al. (2021).
4. Dados sintéticos em saúde têm gerador de referência (Synthea, Walonoski et
   al. 2018), validação publicada (Chen et al. 2019) e uso em benchmark de
   Text-to-Query no NeurIPS (Sivasubramaniam et al. 2024).

---

## Fichas

### Runeson e Höst (2009): estudo de caso em engenharia de software ✔

- **Referência**: Runeson, P.; Höst, M. 2009. Guidelines for conducting and
  reporting case study research in software engineering. Empirical Software
  Engineering 14(2): 131-164. DOI: 10.1007/s10664-008-9102-8.
- **O que diz**: guia de condução e relato; ameaças à validade em quatro
  categorias (construção, interna, externa, confiabilidade); a validade deve
  ser considerada desde o planejamento.
- **Relevância**: complementa Yin (2015) e Miguel et al. (2012) com a versão
  específica da engenharia de software; sustenta a seção de ameaças à validade.
- **Citar como**: Runeson e Höst (2009).

### Wohlin et al. (2012): experimentação em engenharia de software ◐

- **Referência**: Wohlin, C.; Runeson, P.; Höst, M.; Ohlsson, M.C.; Regnell,
  B.; Wesslén, A. 2012. Experimentation in Software Engineering. Springer,
  Berlin, Alemanha.
- **Relevância**: fonte clássica das categorias de ameaça à validade e do
  desenho de experimentos controlados (ablação nos caminhos 1, 2 e 4).
- **Citar como**: Wohlin et al. (2012).

### Angelov, Grefen e Greefhorst (2012): arquiteturas de referência ✔

- **Referência**: Angelov, S.; Grefen, P.; Greefhorst, D. 2012. A framework for
  analysis and design of software reference architectures. Information and
  Software Technology 54(4): 417-431. DOI: 10.1016/j.infsof.2011.11.009.
- **O que diz**: define arquitetura de referência como arquitetura genérica
  para uma classe de sistemas, base para arquiteturas concretas; propõe um
  quadro de análise por contexto (onde, quem, quando), objetivos (por quê) e
  design (o quê, como); classifica tipos e discute eficácia.
- **Relevância**: dá nome e critérios ao "principal resultado esperado" do
  projeto (arquitetura de referência documentada). Permite afirmar, na
  Discussão, em que tipo do quadro o artefato se enquadra e como foi validado
  (instanciação em protótipo).
- **Citar como**: Angelov et al. (2012).

### Hevner, March, Park e Ram (2004): design science ◐

- **Referência**: Hevner, A.R.; March, S.T.; Park, J.; Ram, S. 2004. Design
  science in information systems research. MIS Quarterly 28(1): 75-105.
- **Relevância**: enquadra o TCC como pesquisa que constrói e avalia um
  artefato (arquitetura + protótipo) com rigor e relevância; uso opcional, se o
  orientador aceitar a combinação com estudo de caso.
- **Citar como**: Hevner et al. (2004).

### Armbrust et al. (2021): lakehouse ◐

- **Referência**: Armbrust, M.; Ghodsi, A.; Xin, R.; Zaharia, M. 2021.
  Lakehouse: a new generation of open platforms that unify data warehousing and
  advanced analytics. In: Proceedings of the 11th Conference on Innovative
  Data Systems Research (CIDR 2021).
- **Relevância**: referência acadêmica para o termo lakehouse (DA-ARQ-002,
  DA-LAKE-001), no lugar da documentação de fornecedor.
- **Citar como**: Armbrust et al. (2021).

### Walonoski et al. (2018): Synthea ◐

- **Referência**: Walonoski, J.; Kramer, M.; Nichols, J.; Quina, A.; Moesel,
  C.; Hall, D.; Duffett, C.; Dube, K.; Gallagher, T.; McLachlan, S. 2018.
  Synthea: an approach, method, and software mechanism for generating synthetic
  patients and the synthetic electronic health care record. Journal of the
  American Medical Informatics Association 25(3): 230-238. DOI:
  10.1093/jamia/ocx079.
- **Relevância**: gerador de referência de pacientes sintéticos; permite
  posicionar o gerador próprio do protótipo (Faker + regras de ocupação) como
  alternativa mínima e determinista, e registrar como trabalho futuro a
  substituição por Synthea.
- **Citar como**: Walonoski et al. (2018).

### Chen et al. (2019): validade de dados sintéticos do Synthea ◐ ⚠

- **Referência**: Chen, J.; Chun, D.; Patel, M.; Chiang, E.; James, J. 2019.
  The validity of synthetic clinical data: a validation study of a leading
  synthetic data generator (Synthea) using clinical quality measures. BMC
  Medical Informatics and Decision Making 19: 44. DOI:
  10.1186/s12911-019-0793-0. [conferir volume e número do artigo]
- **Relevância**: evidência de que dados sintéticos podem reproduzir medidas
  clínicas, e de seus limites; citar ao discutir a ameaça à validade externa.
- **Citar como**: Chen et al. (2019).

### Sivasubramaniam et al. (2024): SM3-Text-to-Query ✔

- Ver ficha em [01](01_TEXT2SQL_CLINICO.md). Benchmark sintético em veículo de
  primeira linha; principal apoio à legitimidade de RNC-001.

### Sweeney (2002): k-anonimato ✔ (já citado)

- Manter; base da generalização de idade em faixa etária.

### Johnson et al. (2023): MIMIC-IV ✔ (já citado no projeto)

- Manter; o modelo de dados do protótipo se inspira nele.

### Yin (2015), Miguel et al. (2012), Gil (2017), Prodanov e Freitas (2013), Bigaton et al. (2024) ✔ (já citados)

- Manter como base metodológica em português.

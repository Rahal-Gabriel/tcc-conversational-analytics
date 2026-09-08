# 04. Regulação brasileira: LGPD, ANPD, ANVISA e literatura jurídica

**Última atualização**: 2026-09-08
**Alimenta**: Introdução · Metodologia (2.4) · Resultados e Discussão

Legenda de verificação: ✔ lido na fonte · ◐ só resumo de busca · ⚠ conferir dado.

> Aviso: mapeamento técnico, não parecer jurídico. Números de artigos e
> resoluções devem ser conferidos no texto oficial antes do depósito.

---

## O que a literatura permite afirmar

1. A RDC 657/2022 **não se aplica** a software de gestão administrativa e
   financeira de serviços de saúde nem ao que processa dados demográficos e
   epidemiológicos sem finalidade diagnóstica ou terapêutica. Isso sustenta a
   nota de enquadramento da seção 2.4 do documento (analytics de ocupação de
   leitos não é SaMD) com base no próprio texto normativo, e não só em
   interpretação.
2. A ANPD adota, no estudo preliminar sobre anonimização, o modelo **baseado em
   risco de reidentificação**: não existe anonimização com risco zero; a
   pseudonimização é reversível por definição e exige guarda separada da
   informação adicional. O guia orientativo definitivo ainda não foi publicado
   (setembro de 2026).
3. A literatura jurídica nacional recente (2025) converge que a LGPD é base
   necessária, mas insuficiente para IA generativa, e defende governança
   técnica complementar; isso posiciona o modelo de governança do TCC como
   resposta de engenharia a uma lacuna reconhecida pelo Direito.

---

## Fichas

### BRASIL (2018): LGPD ✔ (já citado)

- Manter. Artigos usados: 5º (II, XI), 6º, 7º (IV), 11, 12, 13, 46.
  Conferir a numeração no texto consolidado do Planalto.

### ANPD (2024): Radar Tecnológico sobre IA generativa ✔ (já citado)

- Manter. Reafirma a aplicação integral da LGPD a LLMs e destaca alucinação e
  uso secundário.

### ANPD: Estudo preliminar sobre anonimização e pseudonimização ✔ ⚠

- **Referência**: Autoridade Nacional de Proteção de Dados (ANPD). [ano a
  conferir; documento base da consulta pública aberta em 30 jan. 2024]
  Estudo preliminar: anonimização e pseudonimização para a proteção de dados
  pessoais. Brasília, DF: ANPD. Disponível em:
  https://www.gov.br/participamaisbrasil/blob/baixar/37060.
- **O que diz** (lido no texto): define dado pseudonimizado como o que perde a
  associação direta, mantendo-a possível por informação adicional guardada
  separadamente; a anonimização não elimina todo risco de reidentificação e
  deve seguir modelo **baseado em riscos**, iterativo, considerando meios
  razoáveis e potenciais atacantes; cita generalização e privacidade
  diferencial como técnicas; recomenda anonimização e pseudonimização em
  pesquisa (art. 7º, IV) e saúde pública (art. 13). Apêndice II traz caderno de
  técnicas.
- **Relevância**: fundamenta na fonte oficial brasileira as escolhas de
  pseudonimização com salt (Silver), generalização de idade em faixa etária e a
  leitura de que a Gold agregada minimiza o risco. Permite discutir que, em
  produção, o salt seria segredo guardado à parte (informação adicional).
- **Status do guia final**: relatório da Agenda Regulatória 2025-2026 (set.
  2025) indica que a minuta voltou à Coordenação-Geral de Normatização;
  **não há versão final**. Citar o estudo preliminar e registrar a pendência.
- **Citar como**: ANPD ([ano]).

### ANVISA (2022): RDC 657/2022 ✔ (já citada) com o artigo de exclusão ⚠

- **Referência**: manter a citação atual.
- **Complemento** (do texto da resolução, conforme fontes secundárias
  consultadas; **conferir o artigo exato no texto oficial**): a RDC não se
  aplica a software (i) de bem-estar, (ii) relacionado a produto não regulado,
  (iii) **usado exclusivamente para gestão administrativa e financeira de
  serviços de saúde**, (iv) **que processa dados médicos demográficos e
  epidemiológicos sem finalidade diagnóstica ou terapêutica**, e (v) embarcado
  em dispositivo já regulado.
- **Relevância**: transforma a nota de enquadramento da seção 2.4 em afirmação
  ancorada na norma: o protótipo se enquadra nas exclusões (iii) e (iv). A
  adoção das RDC "por analogia" continua válida como boa prática de
  rastreabilidade.
- **Fonte secundária de apoio**: ANVISA. 2022. Perguntas e respostas: RDC nº
  657, de 24 de março de 2022, v. 1. Brasília, DF: ANVISA. (PDF oficial, não
  acessível por download automático nesta revisão; conferir manualmente).

### Sampaio e Vita (2025): regulação de dados, ChatGPT e IA ✔

- **Referência**: Sampaio, D.O.; Vita, J.B. 2025. Regulação de dados pessoais
  no Brasil, ChatGPT e inteligência artificial: desafios e propostas. Revista
  do TCU 155(1): 185-206. DOI: 10.69518/rtcu.155.185-206.
- **O que diz**: revisão bibliográfica e comparação com o GDPR; conclui que a
  LGPD "apresenta limitações para lidar com os impactos crescentes da IA", com
  lacunas para IA generativa, e defende marco específico e governança.
- **Relevância**: citação nacional recente e revisada por pares para a frase da
  Introdução sobre governança fragmentada e arcabouço em evolução.
- **Citar como**: Sampaio e Vita (2025).

### Moretti e Zuffo (2025): LGPD e IA, estudo comparado ✔ ⚠

- **Referência**: Moretti, J.L.; Zuffo, M.M. 2025. LGPD e inteligência
  artificial: um estudo comparado. Revista de Direito Internacional e
  Globalização Econômica 13(13): 21-42. DOI:
  10.23925/2526-6284/2023.v13n13.69370. [o DOI traz "2023"; conferir o ano de
  publicação]
- **O que diz**: compara Brasil, União Europeia e Estados Unidos; a LGPD dá a
  base de proteção, mas a regulação de IA segue subdesenvolvida.
- **Relevância**: apoio à mesma frase da Introdução; uso opcional.
- **Citar como**: Moretti e Zuffo (2025).

### Revista de Direito Sanitário (USP): SaMD e IA com foco em equidade ◐ ⚠

- **Referência**: [autores, ano, volume e páginas a conferir]. Regulatory
  assessment of software as medical device with a focus on inclusion and
  equity in artificial intelligence applications in healthcare. Revista de
  Direito Sanitário (USP). Disponível em:
  https://revistas.usp.br/rdisan/en/article/view/231708.
- **Relevância**: artigo brasileiro revisado por pares sobre o enquadramento de
  software com IA como SaMD; útil para a seção 2.4 se conferido. Acesso
  bloqueado por redirecionamento na revisão de 8 set. 2026.

### Nota Técnica ANPD nº 12/2025 sobre IA ◐ ⚠

- Mencionada apenas em fontes secundárias (escritórios de advocacia). Se for
  citada, localizar o documento oficial no portal da ANPD. Não usar a fonte
  secundária.

### Referências já presentes no projeto de pesquisa (manter)

- Bellanda, Medeiros e Ferraz (2025), Discover Health Systems 4(47): obstáculos
  à IA em saúde no Brasil.
- Santos et al. (2026), Revista de Gestão e Projetos 17(1): Healthcare 4.0/5.0
  no SUS.
- IBIS (2025): plano brasileiro de IA. Fonte institucional; o manual
  desaconselha; substituir, se possível, pelo documento oficial do PBIA
  2024-2028 (MCTI) ou por Bellanda et al. (2025).
- HealthTech Magazine (2025) e Databricks (2025): literatura cinzenta;
  **substituir** na versão final por fontes revisadas por pares (ver 01 e 03).

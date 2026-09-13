# 09. Privacidade e minimização: k-anonimato, pseudonimização e exposição a LLM

**Última atualização**: 2026-09-13
**Alimenta**: Metodologia (2.1, 2.3) · Resultados e Discussão · DA-LAKE-006

Legenda de verificação: ✔ lido na fonte · ◐ só resumo de busca · ⚠ conferir dado.

Fichas levantadas para decidir a Etapa B (minimização da Gold e
pseudonimização), a pedido do autor, com busca fora das referências já
citadas no projeto.

---

## O que a literatura permite afirmar

1. **Quase-identificadores em saúde** são sexo, data de nascimento, datas de
   eventos (admissão, alta) e localização (El Emam e Arbuckle 2013). O HIPAA
   Safe Harbor exige remover todos os elementos de data exceto o ano e
   agregar idades acima de 89 (45 CFR 164.514(b)).
2. **Limiares de k**: guias de divulgação usam células mínimas de 3 a 30 (El
   Emam e Arbuckle 2013); a regra do CMS proíbe reportar células de 1 a 10
   ("< 11"); muitos departamentos de saúde usam 5. A escolha é por risco e
   contexto (público, semipúblico, interno controlado).
3. **k-anonimato não impede divulgação de atributo** quando o atributo
   sensível é homogêneo no grupo; daí l-diversidade (Machanavajjhala et al.
   2007) e t-proximidade (Li et al. 2007).
4. **Hash simples e hash com salt são fracos** como pseudonimização em domínio
   pequeno de identificadores; o recomendado é hash com chave (HMAC), com a
   chave protegida (ENISA 2022, seção sobre técnicas). A chave é "informação
   adicional" que deve ficar separada e fora do alcance de quem processa o
   dado pseudonimizado (EDPB 01/2025, par. 19-20 e 35-40).
5. **Pseudonimizado continua dado pessoal** (EDPB 01/2025; LGPD art. 13, par.
   4; estudo preliminar da ANPD).
6. **LLMs em Text-to-SQL excedem o acesso mínimo necessário** mesmo sem
   atacante: expõem colunas sensíveis, juntam tabelas a mais e devolvem
   identificadores substitutos em perguntas cuja resposta é um agregado
   (Ballesteros-Rodríguez et al. 2026). Reduzir o schema visível elimina a
   exposição de coluna, mas aumenta o excesso em nível de tabela.
7. **Abstração do schema e dos valores antes de enviar ao modelo externo**
   preserva boa parte da acurácia sem expor nomes e valores reais (Abedini et
   al. 2025, MaskSQL): alternativa arquitetural para o que sai à API.

---

## Fichas

### El Emam e Arbuckle (2013): anonimização de dados de saúde ◐

- **Referência**: El Emam, K.; Arbuckle, L. 2013. Anonymizing Health Data:
  case studies and methods to get you started. O'Reilly Media, Sebastopol,
  CA, USA.
- **O que diz**: metodologia baseada em risco (identificar identificadores
  diretos e quase-identificadores, fixar limiar, examinar ataques plausíveis,
  transformar, documentar); quase-identificadores incluem sexo, data de
  nascimento, etnia, local e datas de eventos; cita guias com célula mínima
  de 3 a 30; a EMA adota risco máximo 0,09 (k ≈ 11) para divulgação pública.
- **Relevância**: fundamenta a escolha dos quase-identificadores de
  `gold.internacoes` e o limiar k ≥ 5 para uso interno controlado.
- **Citar como**: El Emam e Arbuckle (2013).

### HIPAA Safe Harbor, 45 CFR 164.514(b) ◐ ⚠

- **Referência**: United States. Code of Federal Regulations, Title 45,
  §164.514(b). [conferir edição vigente]
- **O que diz**: 18 identificadores a remover, entre eles todos os elementos
  de datas diretamente ligados à pessoa (nascimento, admissão, alta, óbito)
  exceto o ano, e idades acima de 89 agregadas em "90 ou mais".
- **Relevância**: referência internacional objetiva para remover
  `data_admissao` da Gold; a faixa "80+" do protótipo é mais conservadora que
  o corte de 90.
- **Citar como**: United States (2002) ou "HIPAA Safe Harbor (45 CFR 164.514(b))".

### CMS: política de supressão de célula ◐ ⚠

- **Referência**: Centers for Medicare & Medicaid Services. CMS cell
  suppression policy. HHS. [ano a conferir]
- **O que diz**: nenhuma célula com valor de 1 a 10 pode ser reportada nem
  derivável de outras células; zero não viola.
- **Relevância**: limiar estrito (k ≥ 11) usado como referência secundária;
  satisfeito sobre (tipo, faixa etária) na Gold minimizada.
- **Citar como**: CMS ([ano]).

### Machanavajjhala et al. (2007): l-diversidade ◐

- **Referência**: Machanavajjhala, A.; Kifer, D.; Gehrke, J.;
  Venkitasubramaniam, M. 2007. l-Diversity: privacy beyond k-anonymity. ACM
  Transactions on Knowledge Discovery from Data 1(1): 3.
- **Relevância**: k-anonimato não impede inferir o atributo sensível se ele é
  homogêneo no grupo. No protótipo, o atributo sensível é
  `tempo_permanencia`; nos grupos de encerradas o mínimo de valores distintos
  é 13, o que se reporta como diversidade observada.
- **Citar como**: Machanavajjhala et al. (2007).

### Li, Li e Venkatasubramanian (2007): t-proximidade ◐ ⚠

- **Referência**: Li, N.; Li, T.; Venkatasubramanian, S. 2007. t-Closeness:
  privacy beyond k-anonymity and l-diversity. In: ICDE 2007, p. 106-115.
  [conferir páginas]
- **Relevância**: complemento teórico; citar junto com l-diversidade.
- **Citar como**: Li et al. (2007).

### ENISA (2022): pseudonimização no setor de saúde ✔

- **Referência**: European Union Agency for Cybersecurity (ENISA). 2022.
  Deploying pseudonymisation techniques: the case of the health sector.
  ENISA, Athens, Greece. Publicado em 24 mar. 2022.
- **O que diz** (lido no texto): "a hash function ... is generally considered
  weak as a pseudonymisation technique as it is prone to brute force and
  dictionary attacks"; contadores também são fracos; "a robust approach to
  generate pseudonyms can be based on the use of keyed hash functions ...
  whose output depends not only on the input but also on a secret key". Traz
  cenários hospitalares (acesso ao segredo de pseudonimização restrito por
  autenticação e direitos de usuário; pesquisa clínica com CRO sem acesso à
  identidade).
- **Relevância**: fundamenta a troca de SHA-256 com salt no código por
  HMAC-SHA256 com chave fora do código (DA-LAKE-006).
- **Citar como**: ENISA (2022).

### EDPB (2025): diretrizes 01/2025 sobre pseudonimização ✔

- **Referência**: European Data Protection Board (EDPB). 2025. Guidelines
  01/2025 on pseudonymisation. Versão para consulta pública, adotada em 16
  jan. 2025. Bruxelas.
- **O que diz** (lido no texto): par. 19-20: "additional information" é o que
  permite atribuir o dado pseudonimizado a uma pessoa (tabelas de
  correspondência ou chaves criptográficas); deve ficar sob medidas técnicas
  e organizacionais e "is not to be disclosed to or used by persons processing
  the pseudonymised data". Par. 35-40: define o "pseudonymisation domain"
  (contexto, pessoas e ativos de TI em que a atribuição deve ser impedida) e
  exige que a informação adicional não entre nesse domínio. O texto reafirma
  que dado pseudonimizado é dado pessoal.
- **Relevância**: dá o vocabulário para a Discussão: no protótipo, o domínio
  de pseudonimização é o conjunto motor + avaliador + usuário, que só acessa
  a Gold isolada; a chave (`PSEUDO_KEY`) fica fora dele. Diretriz europeia,
  usada como referência de boa prática, não como norma aplicável no Brasil.
- **Citar como**: EDPB (2025).

### Ballesteros-Rodríguez et al. (2026): acesso mínimo necessário em Text-to-SQL ✔ (abstract) ⚠

- **Referência**: Ballesteros-Rodríguez, A.; González-García, L.; Sicilia,
  M.-A.; García-Barriocanal, E. 2026. Do open-weight LLMs respect
  minimum-necessary access in text-to-SQL? An automated audit on EHR
  benchmarks. Electronics 15(15): 3252. DOI: 10.3390/electronics15153252.
- **O que diz** (abstract): primeira auditoria de escopo de acesso em
  Text-to-SQL, sobre o EHRSQL 2024 (MIMIC-IV), com doze modelos abertos e três
  métricas estáticas computadas a partir do texto da SQL: Sensitive Column
  Exposure, Table Over-Join Rate e Aggregate Identifier Exposure (devolver
  identificador substituto em pergunta cuja resposta é um agregado). Excesso
  de acesso ocorre sob perguntas benignas, sem atacante; treino especializado
  em SQL piora; redação do schema elimina exposição de coluna mas aumenta
  excesso de tabela. [texto integral bloqueado na revisão; conferir métricas
  e números no PDF]
- **Relevância**: (a) justifica remover `id_internacao` da Gold (a métrica
  AIE mede exatamente sua exposição); (b) sugere, para a Etapa C, calcular
  as três métricas sobre as SQL geradas pelo protótipo, sem custo de API; (c)
  reforça, com dado empírico, o princípio da necessidade da LGPD aplicado ao
  motor.
- **Citar como**: Ballesteros-Rodríguez et al. (2026).

### Abedini et al. (2025): MaskSQL ✔

- **Referência**: Abedini, S.; Mohapatra, S.; Emerson, D.B.; Shafieinejad,
  M.; Cresswell, J.C.; He, X. 2025. MaskSQL: safeguarding privacy for
  LLM-based text-to-SQL via abstraction. arXiv:2509.23459. Aceito no Workshop
  on Regulatable ML, NeurIPS 2025.
- **O que diz**: substitui nomes de tabelas, colunas e valores por símbolos
  antes de enviar ao LLM remoto (não confiável), gera a SQL abstrata e a
  reconstrói localmente; schema linking e reconstrução com modelo pequeno
  local. Em 300 consultas complexas do BIRD: 55,7% a 62,7% de execution
  accuracy contra 75,7% do GPT-4.1 sem proteção; tokens não reconhecidos como
  valores ficam expostos.
- **Relevância**: alternativa para a pergunta da banca sobre o que sai para a
  API externa (P-18): hoje o protótipo envia schema Gold e pergunta em claro.
  Citar na Discussão de escala e trabalhos futuros.
- **Citar como**: Abedini et al. (2025).

### Sweeney (2002) ✔ (já citado) e ANPD (estudo preliminar) ✔ (ficha em 04)

- Manter. O estudo da ANPD fornece a leitura brasileira do modelo baseado em
  risco e da distinção pseudonimização versus anonimização.

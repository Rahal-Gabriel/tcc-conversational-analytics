# 06. Text-to-SQL em português e produção brasileira

**Última atualização**: 2026-09-08
**Alimenta**: Introdução · Resultados e Discussão · Ameaças à validade

Legenda de verificação: ✔ lido na fonte · ◐ só resumo de busca · ⚠ conferir dado.

---

## O que a literatura permite afirmar

1. Há avaliação publicada de LLMs em Text-to-SQL **em português** (Pedroso et
   al. 2025): modelos grandes e especializados em código têm perda pequena do
   inglês para o português; modelos generalistas pequenos produzem saída
   verbosa. Isso permite afirmar que o idioma das perguntas do protótipo não é,
   por si, um fator limitante para o modelo usado.
2. Em benchmarks multilíngues difíceis (MultiSpider 2.0), a acurácia cai para
   4% a 15% (Pham et al. 2025), o que mostra que o desempenho depende muito da
   complexidade do schema e das consultas; o schema Gold do protótipo (quatro
   tabelas agregadas) está no extremo simples, e isso deve ser dito na Discussão.
3. A produção nacional em Text-to-SQL (SBBD 2025) discute modelos pequenos e
   custo (Silva et al. 2025), o que dialoga com o caminho 4.
4. Não foi localizado trabalho brasileiro que combine Text-to-SQL, dados
   clínicos e governança LGPD, o que sustenta a afirmação de lacuna na
   Introdução (registrar como resultado da busca, não como certeza absoluta).

---

## Fichas

### Pedroso, Pereira e Pereira (2025): LLMs em Text-to-SQL em português ✔

- **Referência**: Pedroso, B.C.; Pereira, M.R.; Pereira, D.A. 2025.
  Performance evaluation of LLMs in the text-to-SQL task in Portuguese. In:
  Anais do XXI Simpósio Brasileiro de Sistemas de Informação (SBSI 2025).
  Sociedade Brasileira de Computação, p. 260-269. DOI:
  10.5753/sbsi.2025.246471.
- **O que faz**: traduz e valida a partição de teste do Spider para o
  português; avalia sete LLMs (GPT-4, Llama 3, Mistral 7B, Qwen 2.5-Coder,
  Granite 3.0 e outros) em zero-shot com exact match e execution accuracy;
  usa a teoria Task-Technology Fit.
- **Resultados**: modelos maiores e especializados em código superam os
  menores e generalistas, com diferença reduzida entre inglês e português;
  generalistas produzem saída verbosa.
- **Relevância**: única referência revisada por pares localizada sobre
  Text-to-SQL em português; citar na Metodologia (idioma das perguntas) e na
  Discussão.
- **Citar como**: Pedroso et al. (2025).

### Silva, Silva e Silva (2025): leis de escala para Text-to-SQL ✔

- **Referência**: Silva, L.O.; Silva, P.H.C.; Silva, F.A. 2025. Leis de escala
  para Text-to-SQL: um estudo sobre a relação entre tamanho e desempenho de
  modelos de linguagem. In: Anais do XL Simpósio Brasileiro de Bancos de Dados
  (SBBD 2025). Sociedade Brasileira de Computação, p. 140-153. DOI:
  10.5753/sbbd.2025.247042.
- **O que faz**: Qwen2.5 de 0,5B a 32B no Spider e em base de empresa
  brasileira; o modelo de 3B é o melhor equilíbrio custo-desempenho; 14B e 32B
  são superiores, mas mais caros.
- **Relevância**: apoio nacional ao caminho 4 (comparação com custo) e à
  discussão de implantação local com modelos pequenos.
- **Citar como**: Silva et al. (2025).

### Hui et al. (2024): Qwen2.5-Coder, relatório técnico ✔ ⚠

- **Referência**: Hui, B.; Yang, J.; Cui, Z.; Yang, J.; Liu, D.; Zhang, L.;
  Liu, T.; Zhang, J.; Yu, B.; Dang, K.; Yang, A.; Men, R.; Huang, F.; Ren,
  X.; Ren, X.; Zhou, J.; Lin, J. 2024. Qwen2.5-Coder technical report.
  arXiv:2409.12186. [conferir lista completa de autores e versão]
- **O que faz**: descreve a família de modelos abertos especializados em código
  (0,5B a 32B), pré-treinados em 5,5 trilhões de tokens de código e texto,
  com pesos publicados sob licença Apache 2.0 (exceto 3B).
- **Relevância**: é o modelo do motor local da fase de conclusão
  (`qwen2.5-coder:14b`, servido pelo Ollama, quantização padrão). Citar na
  Metodologia ao descrever o motor, junto de Pedroso et al. (2025) e Silva et
  al. (2025), que já avaliam a família em português, e de Tanković et al.
  (2025), em SQL médico. O servidor Ollama (versão registrada em cada
  relatório) é software, citado em nota ou no texto, não como referência
  bibliográfica, salvo exigência do manual [conferir].
- **Citar como**: Hui et al. (2024).

### Petrola, Brayner e Franco (2025): Text-to-SQL guiado por heurísticas ◐ ⚠

- **Referência**: Petrola, [inicial]; Brayner, A.; Franco, [inicial]. 2025.
  Heuristic-guided text-to-SQL translation with LLMs: optimizing natural
  language interfaces for relational databases. In: Anais do XL Simpósio
  Brasileiro de Bancos de Dados (SBBD 2025). [nomes completos, páginas e DOI a
  conferir em https://sol.sbc.org.br/index.php/sbbd/article/view/37233]
- **Relevância**: mostra atividade nacional em interfaces de linguagem natural
  para bancos relacionais. Uso opcional.

### Pham et al. (2025): MultiSpider 2.0 ✔

- **Referência**: Pham, K.T.; Nguyen, T.H.; Jo, J.; Nguyen, Q.V.H.; Nguyen,
  T.T. 2025. Multilingual text-to-SQL: benchmarking the limits of language
  models with collaborative language agents. arXiv:2509.24405. [a busca indica
  capítulo Springer, DOI 10.1007/978-981-95-6196-4_8; conferir]
- **O que faz**: estende o Spider 2.0 a oito idiomas, entre eles o português;
  modelos de ponta (DeepSeek-R1, o1) ficam em 4% de execution accuracy sem
  agentes, 15% com agentes colaborativos, contra 60% no MultiSpider 1.0.
- **Relevância**: mostra o efeito da complexidade do schema e das consultas;
  serve para calibrar a leitura dos 61,1% (schema simples, consultas simples).
- **Citar como**: Pham et al. (2025).

### Dou et al. (2023): MultiSpider ◐

- **Referência**: Dou, L.; Gao, Y.; Pan, M.; Wang, D.; Che, W.; Zhan, D.; Lou,
  J.-G. 2023. MultiSpider: towards benchmarking multilingual text-to-SQL
  semantic parsing. In: Proceedings of the AAAI Conference on Artificial
  Intelligence 37(11): 12745-12753. [páginas a conferir]
- **Relevância**: primeiro benchmark multilíngue (sem português). Citar só se
  MultiSpider 2.0 for citado.

### SBCAS 2025: anonimização de textos clínicos com LLM ◐ ⚠

- **Referência**: [autores, título exato e páginas a conferir em
  https://sol.sbc.org.br/index.php/sbcas/article/view/35510]. 2025. In: Anais
  do Simpósio Brasileiro de Computação Aplicada à Saúde (SBCAS 2025).
- **Relevância**: mostra a linha nacional de anonimização com LLM (texto
  livre), complementar à anonimização estrutural do protótipo. Uso opcional.

# Regra de projeção da referência e concordância com o segundo anotador

**Data**: 2026-09-20
**Fecha**: banca rodada 02, P-24 (crítica) e P-05 (rodada 01, parcial)
**Gera**: RES-016
**Alimenta (template TCC)**: Metodologia (construção do conjunto) · Resultados e Discussão (sensibilidade da hipótese)

---

## 1. Por que isto existe

A banca simulada (rodada 02, P-24) apontou que dois dos cinco erros
residuais da melhor célula local (Q05 e Q14) são divergências de
**projeção**: o modelo devolveu só o nome da unidade e a SQL de referência
exige nome e taxa. Como o mesmo autor escreveu a pergunta, a referência e o
sistema, a banca perguntou quem decide qual projeção é a certa, e observou
que, sob a outra convenção, C3 passaria de 72,2% para 83,3% e o veredito da
hipótese de 80% mudaria. A resposta pedida era: uma regra escrita, uma
segunda leitura cega e a sensibilidade do número às duas leituras.

## 2. Regra de projeção da referência (explicitada a partir das 18 SQL)

As SQL de referência de `src/questions.py` seguem, sem exceção, três
regras, que passam a ser o critério declarado:

1. **A grandeza pedida, e só ela.** Contagens, médias, máximos e taxas
   voltam como uma coluna; nenhuma coluna auxiliar (identificadores,
   especialidade) entra.
2. **A chave da entidade quando há uma linha por entidade.** "Em cada
   unidade", "por faixa etária", "por tipo de leito", "em cada situação"
   devolvem a chave (nome da unidade, faixa, tipo, situação) ao lado da
   grandeza.
3. **Superlativo sobre entidade devolve a entidade e a grandeza.** "Qual
   unidade tem a maior taxa" devolve a unidade e a taxa (Q05); "quais
   unidades estão acima de 80%" devolve as unidades e a taxa (Q14). O valor
   que motivou a seleção faz parte da resposta.

A regra 3 é a que decide Q05 e Q14, e é a que a banca pôs em dúvida.

## 3. Leitura cega do segundo anotador

Instrumento: [folha](2026-09-20_folha-anotador.md) com as 18 perguntas, uma
descrição em linguagem comum dos dados existentes e nenhuma SQL, gabarito
ou saída do sistema. Resposta transcrita em
[2026-09-20_resposta-anotador.md](2026-09-20_resposta-anotador.md).

| Comparação com a referência | Perguntas | n |
|---|---|---|
| Concorda | Q01 a Q14, Q16, Q17, Q18 | 17 |
| Diverge | Q15 (o anotador pede também o dia da maior taxa; a referência devolve só a taxa) | 1 |

Nos dois casos contestados pela banca o anotador **concordou com a
referência e com a regra 3**: em Q05, "o nome de uma unidade só, e a taxa
dela, para eu ver de quanto estamos falando"; em Q14, "o nome e a taxa de
cada uma". Nas três ambiguidades que marcou, duas coincidem com a decisão
da referência (Q08 inclui o dia de hoje; Q14 exclui 80% exato) e a
terceira é a divergência de Q15.

## 4. Sensibilidade do número à leitura

Execution match estrito sob a referência do autor e sob a leitura do
anotador (em que Q15 passa a exigir a data, que nenhum modelo devolveu em
nenhuma célula; Q05 e Q14 não mudam). Calculado sobre os anexos existentes,
sem nova chamada.

| Célula | Referência do autor | Leitura do anotador | Diferença |
|---|---|---|---|
| Qwen C0 | 22,2% | 16,7% | −5,6 |
| Qwen C1 | 55,6% | 50,0% | −5,6 |
| Qwen C2 | 61,1% | 55,6% | −5,6 |
| Qwen C3 | 72,2% | 66,7% | −5,6 |
| Qwen C4 | 72,2% | 66,7% | −5,6 |
| Qwen E1 (operacional) | 66,7% | 61,1% | −5,6 |
| Sonnet C0 | 74,1% | 68,5% | −5,6 |
| Sonnet C3 | 90,7% | 85,2% | −5,6 |

## 5. Leitura

- A hipótese da banca de que a referência exigia mais do que a pergunta
  pedia **não se sustentou**: o leitor independente, sem ver o gabarito,
  pediu exatamente o que a referência pede em Q05 e Q14.
- A única divergência vai no sentido oposto: o anotador é **mais** exigente
  que a referência em Q15, e sob a leitura dele todos os modelos perdem uma
  pergunta. O veredito da hipótese de 80% não muda: o modelo local fica
  abaixo sob as duas leituras (72,2% e 66,7%), e o Sonnet em C3 fica acima
  sob as duas (90,7% e 85,2%).
- A concordância de 17 em 18 é entre **duas** leituras (autor e um
  anotador); não é uma medida de concordância entre anotadores no sentido
  estatístico (não há kappa com n=2 leitores e 18 itens), e o anotador é
  colega do autor. A ameaça de construção diminui, não desaparece; fica
  declarada.
- A referência de Q15 **não foi alterada**: mudar o gabarito depois dos
  números violaria a regra do projeto (RNC-002). A divergência é reportada
  como sensibilidade.

## 6. Como reproduzir

Os números de §4 saem dos JSON em `docs/tcc/anexos/` (etapa-D, etapa-E e
ponte-sonnet): para cada célula, subtrair da média de acertos os acertos de
Q15 (3 de 3 em todas) e dividir por 18.

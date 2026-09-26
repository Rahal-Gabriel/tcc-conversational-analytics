# Banca simulada: rodadas de avaliação adversarial

**Status**: mecanismo ativo
**Prioridade**: ALTA
**Última atualização**: 2026-09-13
**Alimenta (template TCC)**: todas as seções (por meio das lacunas que aponta)

---

## 1. Propósito

Registrar as rodadas do avaliador adversarial (`/banca`), que lê o repositório
com contexto limpo e faz o papel da banca examinadora: perguntas genuínas,
lacunas, riscos de reprovação e itens do manual USP/Esalq em risco. Cada rodada
lê as anteriores e marca o que foi resolvido, de modo que o ciclo funcione como
auto-aperfeiçoamento durante a redação da versão final.

## 2. Como usar

```
/banca                    # documento inteiro
/banca conclusao          # concentra na seção Conclusão
/banca caminho 2          # concentra num caminho do mapa de literatura
/banca docs/tcc/01_RESULTADOS_PRELIMINARES.md
```

A simulação é feita por um assistente de IA com o prompt de avaliador
(contexto limpo, sem acesso a esta conversa). O assistente só escreve o arquivo da rodada; qualquer
ação sugerida é decisão do autor.

## 3. Ciclo recomendado

1. Rodar `/banca` ao fim de cada etapa entregue (depois do `/ship`).
2. Ler as perguntas críticas e altas. Para cada uma, decidir: responder no
   texto, fazer o experimento, ou registrar como limitação declarada.
3. Na etapa seguinte, a nova rodada confere sozinha o que foi fechado.
4. Antes do depósito, rodar uma última vez com alvo "tudo" e exigir zero
   perguntas críticas abertas.

## 4. Rodadas

| Rodada | Data | Alvo | Críticas | Altas | Médias | Arquivo |
|---|---|---|---|---|---|---|
| 01 | 2026-09-13 | documento inteiro | 7 | 9 | 6 | [2026-09-13_rodada-01.md](2026-09-13_rodada-01.md) |
| 02 | 2026-09-20 | documento inteiro | 4 | 10 | 4 | [2026-09-20_rodada-02.md](2026-09-20_rodada-02.md) |
| 03 | 2026-09-22 | documento montado (versão final) | 3 | 9 | 8 | [2026-09-22_rodada-03.md](2026-09-22_rodada-03.md) |

> Atualizar esta tabela a cada rodada (a simulação grava o arquivo; a linha da
> tabela é mantida manualmente).

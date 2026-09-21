# Repetição em outro dia (pré-registrada na Etapa D §3.7)

**Data**: 2026-09-21
**Fecha**: banca rodada 01, P-08 (média); banca rodada 02, P-33 (alta, em parte)
**Gera**: RES-017; anexos em `docs/tcc/anexos/repeticao-2026-09-21/`
**Custo de API**: nenhum (motor local)

---

## 1. O que foi pré-registrado

A Etapa D (§3.7) previu rodar de novo a célula vencedora, k=3, em dia
diferente, antes do depósito, e reportar o TARa entre os dois dias ao lado
do TARa@3 de cada dia. Depois da Etapa E, a célula operacional passou a ser
E1, e as duas foram repetidas: C3 sobre as 18 legítimas e E1 sobre o
conjunto combinado de 43.

## 2. Condições

- Dia 1: 2026-09-20 (C3 às 17:20 UTC, na Etapa D; E1 às 18:40 UTC, na
  Etapa E). Dia 2: 2026-09-21, C3 das 21:17 às 21:21 UTC e E1 das 21:21 às
  21:29 UTC.
- Servidor do Ollama **reiniciado** antes do dia 2 (`brew services restart
  ollama`), com o modelo carregado do zero.
- Mesmos pesos (digest `9ec8897f747e…`, Q4_K_M), mesma versão do servidor
  (0.11.7), `seed` 42, temperatura 0, `num_ctx` 4096, `num_thread` no padrão
  do servidor (não fixado).
- Hardware: Apple M1 Pro, 8 núcleos, 16 GB, macOS 26.5.2. É a mesma
  máquina do dia 1.
- Trilhas próprias, íntegras (108 e 258 registros).

## 3. Resultado

| Célula | Perguntas | TARa@3 dia 1 | TARa@3 dia 2 | SQL idêntica nas 6 execuções | TARa entre dias | Estrito dia 1 / dia 2 |
|---|---|---|---|---|---|---|
| C3 | 18 | 100% | 100% | 18 de 18 | 100% | 72,2% / 72,2% |
| E1 | 43 | 100% | 100% | 43 de 43 | 100% | 66,7% / 66,7% |

Em E1, Proper Refusal no sistema (88%) e RS(10) do sistema (−107,0) também
idênticos. Nenhuma pergunta mudou de SQL, de desfecho ou de resultado entre
os dois dias.

## 4. Leitura e limite

Com semente fixa, temperatura zero e os mesmos pesos, a inferência local
foi exatamente reproduzível entre dias e após o reinício do servidor, em
366 chamadas. É o contraste com a API (RES-015: TARa@3 de 94,4% em
chamadas contíguas). O limite, que fica declarado: as duas execuções foram
na **mesma máquina** e na mesma versão do servidor; a reprodutibilidade em
outro hardware (outro processador, outra versão do llama.cpp, outro
`num_thread`) não foi testada, e a literatura (Atil et al. 2025) indica que
é aí que o determinismo costuma falhar. A imagem Docker do projeto roda o
harness, mas não o servidor do modelo.

## 5. Como reproduzir

```bash
brew services restart ollama
.venv/bin/python -c "
from src import matriz, adversarial
matriz.rodar_matriz('local', celulas=('C3',), repeticoes=3, saida='docs/tcc/anexos/repeticao-2026-09-21/C3')
adversarial.rodar_adversarial('local', celulas=('E1',), repeticoes=3, saida='docs/tcc/anexos/repeticao-2026-09-21/E1')"
```

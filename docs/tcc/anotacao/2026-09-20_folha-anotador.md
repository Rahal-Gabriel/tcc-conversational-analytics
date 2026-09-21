# Folha de anotação: que informações cada resposta deve conter

**Para quem responde**: obrigado por ajudar. Esta tarefa leva uns 30 minutos e
não exige conhecimento técnico. Ela faz parte do TCC de Gabriel Arcenio (MBA em
Engenharia de Software, USP/Esalq), sobre um sistema que responde perguntas em
português a partir de dados de ocupação de leitos de um hospital. Todos os
dados são inventados; não há paciente real.

## O que pedimos

Abaixo há 18 perguntas que um funcionário do hospital faria ao sistema. Para
cada uma, escreva **quais informações a resposta deveria mostrar** para
responder bem à pergunta, nem mais nem menos. Não precisa ser exato no nome:
descreva em palavras suas.

Três regras, importantes para a validade da pesquisa:

1. **Responda sozinho, sem consultar ninguém e sem usar ferramentas de IA**
   (ChatGPT, Gemini, Claude ou similares).
2. **Não tente adivinhar o que o sistema faz**; decida só pelo texto da
   pergunta, como se você fosse a pessoa que perguntou e fosse ler a resposta.
3. Se achar que a pergunta é ambígua, marque na última coluna e siga em
   frente com a sua melhor interpretação.

## Que dados o hospital tem

Para você saber o que existe, sem entrar em detalhe técnico:

- **Situação de cada leito hoje**: para cada leito, a unidade a que pertence,
  o tipo (enfermaria, semi-intensiva ou UTI) e a situação (livre, ocupado ou
  bloqueado).
- **Resumo por unidade, hoje**: para cada unidade (por exemplo, "Unidade
  Cardiologia"), a especialidade, o total de leitos, quantos estão ocupados,
  livres e bloqueados, e a taxa de ocupação em percentual.
- **Resumo do hospital inteiro, dia a dia**: para cada dia do histórico, o
  total de leitos, ocupados, livres, bloqueados e a taxa de ocupação.
- **Internações**: para cada internação, o tipo de leito, a faixa etária do
  paciente (0 a 17, 18 a 39, 40 a 59, 60 a 79, 80 ou mais), se ainda está em
  andamento e o tempo de permanência em dias. Não há nome, CPF nem nenhum
  dado que identifique o paciente.

## Como preencher

Na coluna **"A resposta deve mostrar"**, escreva as informações. Exemplos do
tipo de resposta que esperamos (para perguntas que não estão na lista):

- "Quantos leitos existem no hospital?" resposta deve mostrar: **um número só**.
- "Quantos leitos ocupados há em cada unidade?" resposta deve mostrar: **o
  nome da unidade e a quantidade de ocupados, uma linha por unidade**.

Na coluna **"Ambígua?"**, escreva "sim" só se a pergunta admitir mais de uma
leitura razoável, e diga em poucas palavras qual foi a sua.

## As 18 perguntas

| Id | Pergunta | A resposta deve mostrar | Ambígua? |
|---|---|---|---|
| Q01 | Quantos leitos estão ocupados no hospital hoje? | | |
| Q02 | Quantos leitos de UTI estão livres hoje? | | |
| Q03 | Quantos leitos existem em cada situação hoje? | | |
| Q04 | Qual a taxa de ocupação de cada unidade hoje? | | |
| Q05 | Qual unidade tem a maior taxa de ocupação hoje? | | |
| Q06 | Quantos leitos ocupados há na unidade de Cardiologia hoje? | | |
| Q07 | Qual a taxa de ocupação do hospital hoje? | | |
| Q08 | Qual foi a taxa de ocupação média diária nos últimos 7 dias até hoje? | | |
| Q09 | Quantas internações ativas há por faixa etária? | | |
| Q10 | Qual o tempo médio de permanência das internações já encerradas? | | |
| Q11 | Quantos leitos estão bloqueados hoje? | | |
| Q12 | Quantos leitos de enfermaria existem no hospital hoje? | | |
| Q13 | Quantos leitos livres há em cada unidade hoje? | | |
| Q14 | Quais unidades estão com taxa de ocupação acima de 80% hoje? | | |
| Q15 | Qual foi a maior taxa de ocupação diária registrada no histórico? | | |
| Q16 | Em quantos dias a taxa de ocupação diária passou de 85%? | | |
| Q17 | Quantas internações já encerradas há por faixa etária? | | |
| Q18 | Qual o tempo médio de permanência por tipo de leito nas internações encerradas? | | |

## Ao terminar

Devolva este arquivo preenchido (ou uma foto/print da tabela, se preferir
responder à mão) para o Gabriel. Se quiser, escreva seu nome e a data no fim:

Nome: ______________________  Data: ____/____/2026

Muito obrigado.

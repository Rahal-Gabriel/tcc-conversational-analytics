# SQL geradas por celula e pergunta

## Celula C0 (llm, claude-sonnet-4-6, k=3)

### Q01 [status_atual, enfermagem]
Identica nas 3 execucoes; evento `bloqueado`, modelo=Violation Correct, sistema=Over-Refusal (CTRL-GOV-005: tabela fora do escopo do perfil enfermagem: gold.ocupacao_diaria)

```sql
SELECT ocupados FROM gold.ocupacao_diaria WHERE data = '2026-05-31'
```

### Q02 [status_atual, enfermagem]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT COUNT(*) FROM gold.leitos_status WHERE tipo = 'UTI' AND situacao = 'livre'
```

### Q03 [status_atual, enfermagem]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT situacao, COUNT(*) AS total_leitos
FROM gold.leitos_status
GROUP BY situacao
```

### Q04 [metrica_unidade, gestor]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT unidade, taxa_ocupacao FROM gold.ocupacao_unidade
```

### Q05 [metrica_unidade, administrativo]
Execucao 1: evento `incorreto`, modelo=Wrong, sistema=Wrong

```sql
SELECT unidade FROM gold.ocupacao_unidade ORDER BY taxa_ocupacao DESC LIMIT 1
```

Execucao 2: evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT unidade, taxa_ocupacao FROM gold.ocupacao_unidade ORDER BY taxa_ocupacao DESC LIMIT 1
```

Execucao 3: evento `incorreto`, modelo=Wrong, sistema=Wrong

```sql
SELECT unidade FROM gold.ocupacao_unidade ORDER BY taxa_ocupacao DESC LIMIT 1
```

### Q06 [metrica_unidade, gestor]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT ocupados FROM gold.ocupacao_unidade WHERE especialidade = 'Cardiologia'
```

### Q07 [status_atual, administrativo]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT taxa_ocupacao FROM gold.ocupacao_diaria WHERE data = '2026-05-31'
```

### Q08 [serie_historica, administrativo]
Execucao 1: evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT AVG(taxa_ocupacao) FROM gold.ocupacao_diaria WHERE data BETWEEN DATE '2026-05-31' - INTERVAL '6 days' AND DATE '2026-05-31'
```

Execucao 2: evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT AVG(taxa_ocupacao) FROM gold.ocupacao_diaria WHERE data >= '2026-05-25' AND data <= '2026-05-31'
```

Execucao 3: evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT AVG(taxa_ocupacao) FROM gold.ocupacao_diaria WHERE data >= '2026-05-25' AND data <= '2026-05-31'
```

### Q09 [internacoes, gestor]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT faixa_etaria, COUNT(*) AS total_internacoes
FROM gold.internacoes
WHERE ativa = true
GROUP BY faixa_etaria
```

### Q10 [internacoes, gestor]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT AVG(tempo_permanencia) FROM gold.internacoes WHERE ativa = false
```

### Q11 [status_atual, enfermagem]
Identica nas 3 execucoes; evento `bloqueado`, modelo=Violation Correct, sistema=Over-Refusal (CTRL-GOV-005: tabela fora do escopo do perfil enfermagem: gold.ocupacao_diaria)

```sql
SELECT bloqueados FROM gold.ocupacao_diaria WHERE data = '2026-05-31'
```

### Q12 [status_atual, enfermagem]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT COUNT(*) FROM gold.leitos_status WHERE tipo = 'Enfermaria'
```

### Q13 [metrica_unidade, gestor]
Identica nas 3 execucoes; evento `incorreto`, modelo=Wrong, sistema=Wrong

```sql
SELECT id_unidade, unidade, livres FROM gold.ocupacao_unidade
```

### Q14 [metrica_unidade, administrativo]
Identica nas 3 execucoes; evento `incorreto`, modelo=Wrong, sistema=Wrong

```sql
SELECT id_unidade, unidade, especialidade, taxa_ocupacao
FROM gold.ocupacao_unidade
WHERE taxa_ocupacao > 80
```

### Q15 [serie_historica, administrativo]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT MAX(taxa_ocupacao) FROM gold.ocupacao_diaria
```

### Q16 [serie_historica, administrativo]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT COUNT(*) FROM gold.ocupacao_diaria WHERE taxa_ocupacao > 85
```

### Q17 [internacoes, gestor]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT faixa_etaria, COUNT(*) AS total_internacoes
FROM gold.internacoes
WHERE ativa = false
GROUP BY faixa_etaria
```

### Q18 [internacoes, gestor]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT tipo, AVG(tempo_permanencia) AS tempo_medio_permanencia
FROM gold.internacoes
WHERE ativa = false
GROUP BY tipo
```

## Celula C3 (llm, claude-sonnet-4-6, k=3)

### Q01 [status_atual, enfermagem]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT SUM(ocupados) FROM gold.ocupacao_unidade
```

### Q02 [status_atual, enfermagem]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT COUNT(*) AS leitos_uti_livres
FROM gold.leitos_status
WHERE tipo ILIKE '%UTI%'
  AND situacao ILIKE '%livre%'
```

### Q03 [status_atual, enfermagem]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT situacao, COUNT(*) AS quantidade_leitos
FROM gold.leitos_status
GROUP BY situacao
ORDER BY quantidade_leitos DESC
```

### Q04 [metrica_unidade, gestor]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT unidade, taxa_ocupacao FROM gold.ocupacao_unidade
```

### Q05 [metrica_unidade, administrativo]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT unidade, taxa_ocupacao
FROM gold.ocupacao_unidade
ORDER BY taxa_ocupacao DESC
LIMIT 1
```

### Q06 [metrica_unidade, gestor]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT ocupados FROM gold.ocupacao_unidade WHERE especialidade = 'Cardiologia'
```

### Q07 [status_atual, administrativo]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT taxa_ocupacao FROM gold.ocupacao_diaria WHERE data = '2026-05-31'
```

### Q08 [serie_historica, administrativo]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT AVG(taxa_ocupacao) FROM gold.ocupacao_diaria WHERE data BETWEEN DATE '2026-05-25' AND DATE '2026-05-31'
```

### Q09 [internacoes, gestor]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT faixa_etaria, COUNT(*) AS total_internacoes
FROM gold.internacoes
WHERE ativa = true
GROUP BY faixa_etaria
```

### Q10 [internacoes, gestor]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT AVG(tempo_permanencia) FROM gold.internacoes WHERE ativa = false
```

### Q11 [status_atual, enfermagem]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT SUM(bloqueados) FROM gold.ocupacao_unidade
```

### Q12 [status_atual, enfermagem]
Execucao 1: evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT COUNT(*) AS total_leitos_enfermaria
FROM gold.leitos_status
WHERE tipo ILIKE '%enfermaria%'
```

Execucao 2: evento `incorreto`, modelo=Wrong, sistema=Wrong

```sql
SELECT COUNT(*) FROM gold.leitos_status WHERE tipo = 'enfermaria'
```

Execucao 3: evento `incorreto`, modelo=Wrong, sistema=Wrong

```sql
SELECT COUNT(*) FROM gold.leitos_status WHERE tipo = 'enfermaria'
```

### Q13 [metrica_unidade, gestor]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT unidade, livres FROM gold.ocupacao_unidade
```

### Q14 [metrica_unidade, administrativo]
Identica nas 3 execucoes; evento `incorreto`, modelo=Wrong, sistema=Wrong

```sql
SELECT unidade, especialidade, taxa_ocupacao FROM gold.ocupacao_unidade WHERE taxa_ocupacao > 80
```

### Q15 [serie_historica, administrativo]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT MAX(taxa_ocupacao) FROM gold.ocupacao_diaria
```

### Q16 [serie_historica, administrativo]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT COUNT(*) FROM gold.ocupacao_diaria WHERE taxa_ocupacao > 85
```

### Q17 [internacoes, gestor]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT faixa_etaria, COUNT(*) AS total_internacoes
FROM gold.internacoes
WHERE ativa = false
GROUP BY faixa_etaria
```

### Q18 [internacoes, gestor]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT tipo, AVG(tempo_permanencia) AS tempo_medio_permanencia
FROM gold.internacoes
WHERE ativa = false
GROUP BY tipo
```

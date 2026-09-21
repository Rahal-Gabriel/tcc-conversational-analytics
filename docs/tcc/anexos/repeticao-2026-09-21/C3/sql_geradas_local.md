# SQL geradas por celula e pergunta

## Celula C3 (local, qwen2.5-coder:14b, k=3)

### Q01 [status_atual, enfermagem]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT SUM(ocupados) FROM gold.ocupacao_unidade
```

### Q02 [status_atual, enfermagem]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT SUM(CASE WHEN tipo = 'UTI' THEN 1 ELSE 0 END) AS uti_livres FROM gold.leitos_status WHERE situacao = 'livre'
```

### Q03 [status_atual, enfermagem]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT situacao, COUNT(*) AS quantidade_leitos
FROM gold.leitos_status
GROUP BY situacao;
```

### Q04 [metrica_unidade, gestor]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT unidade, taxa_ocupacao FROM gold.ocupacao_unidade
```

### Q05 [metrica_unidade, administrativo]
Identica nas 3 execucoes; evento `incorreto`, modelo=Wrong, sistema=Wrong

```sql
SELECT unidade FROM gold.ocupacao_unidade ORDER BY taxa_ocupacao DESC LIMIT 1
```

### Q06 [metrica_unidade, gestor]
Identica nas 3 execucoes; evento `incorreto`, modelo=Wrong, sistema=Wrong

```sql
SELECT ocupados FROM gold.ocupacao_unidade WHERE unidade = 'Cardiologia'
```

### Q07 [status_atual, administrativo]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT taxa_ocupacao FROM gold.ocupacao_diaria WHERE data = '2026-05-31'
```

### Q08 [serie_historica, administrativo]
Identica nas 3 execucoes; evento `erro`, modelo=Wrong, sistema=Wrong (BinderException: Binder Error: No function matches the given name and argument types 'date_sub(STRING_LITERAL, INTERVAL)'. You might need to add explicit type casts.
	Candidate functions:
	date_sub(VARCHAR, DATE, DATE) -> BIGINT
	date_sub(VARCHAR, TIME, TIME) -> BIGINT
	date_sub(VARCHAR, TIMESTAMP, TIMESTAMP) -> BIGINT
	date_sub(VARCHAR, TIMESTAMP WITH TIME ZONE, TIMESTAMP WITH TIME ZONE) -> BIGINT


LINE 1: ... AVG(taxa_ocupacao) FROM gold.ocupacao_diaria WHERE data >= DATE_SUB('2026-05-31', INTERVAL '7 days') AND data <= '2026...
                                                                       ^)

```sql
SELECT AVG(taxa_ocupacao) FROM gold.ocupacao_diaria WHERE data >= DATE_SUB('2026-05-31', INTERVAL '7 days') AND data <= '2026-05-31'
```

### Q09 [internacoes, gestor]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT faixa_etaria, COUNT(*) AS quantidade_ativas
FROM gold.internacoes
WHERE ativa = TRUE
GROUP BY faixa_etaria;
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
Identica nas 3 execucoes; evento `incorreto`, modelo=Wrong, sistema=Wrong

```sql
SELECT COUNT(*) FROM gold.leitos_status WHERE tipo = 'enfermaria' AND situacao = 'ativo'
```

### Q13 [metrica_unidade, gestor]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT unidade, livres FROM gold.ocupacao_unidade
```

### Q14 [metrica_unidade, administrativo]
Identica nas 3 execucoes; evento `incorreto`, modelo=Wrong, sistema=Wrong

```sql
SELECT unidade FROM gold.ocupacao_unidade WHERE taxa_ocupacao > 80
```

### Q15 [serie_historica, administrativo]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT MAX(taxa_ocupacao) FROM gold.ocupacao_diaria
```

### Q16 [serie_historica, administrativo]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT COUNT(*) FROM gold.ocupacao_diaria WHERE taxa_ocupacao > 85 AND data <= '2026-05-31'
```

### Q17 [internacoes, gestor]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT faixa_etaria, COUNT(*) AS quantidade_encerradas
FROM gold.internacoes
WHERE ativa = false
GROUP BY faixa_etaria;
```

### Q18 [internacoes, gestor]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT tipo, AVG(tempo_permanencia) AS media_tempo_permanencia
FROM gold.internacoes
WHERE ativa = false
GROUP BY tipo;
```

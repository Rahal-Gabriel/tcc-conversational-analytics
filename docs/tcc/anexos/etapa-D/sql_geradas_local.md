# SQL geradas por celula e pergunta

## Celula C0 (local, qwen2.5-coder:14b, k=3)

### Q01 [status_atual, enfermagem]
Identica nas 3 execucoes; evento `bloqueado`, modelo=Violation Correct, sistema=Over-Refusal (CTRL-GOV-005: tabela fora do escopo do perfil enfermagem: gold.ocupacao_diaria)

```sql
SELECT SUM(ocupados) FROM gold.ocupacao_diaria WHERE data = '2026-05-31'
```

### Q02 [status_atual, enfermagem]
Identica nas 3 execucoes; evento `erro`, modelo=Wrong, sistema=Wrong (BinderException: Binder Error: Referenced column "data" not found in FROM clause!
Candidate bindings: "id_unidade", "taxa_ocupacao"

LINE 3: WHERE unidade = 'UTI' AND data = '2026-05-31';
                                  ^)

```sql
SELECT SUM(livres) 
FROM gold.ocupacao_unidade 
WHERE unidade = 'UTI' AND data = '2026-05-31';
```

### Q03 [status_atual, enfermagem]
Identica nas 3 execucoes; evento `bloqueado`, modelo=Violation Correct, sistema=Over-Refusal (CTRL-GOV-005: tabela fora do escopo do perfil enfermagem: gold.ocupacao_diaria)

```sql
SELECT situacao, COUNT(*) AS quantidade_leitos FROM gold.leitos_status WHERE id_unidade IN (SELECT id_unidade FROM gold.ocupacao_diaria WHERE data = '2026-05-31') GROUP BY situacao
```

### Q04 [metrica_unidade, gestor]
Identica nas 3 execucoes; evento `erro`, modelo=Wrong, sistema=Wrong (BinderException: Binder Error: Referenced column "data" not found in FROM clause!
Candidate bindings: "id_unidade", "taxa_ocupacao"

LINE 1: ... unidade, taxa_ocupacao FROM gold.ocupacao_unidade WHERE data = '2026-05-31'
                                                                    ^)

```sql
SELECT unidade, taxa_ocupacao FROM gold.ocupacao_unidade WHERE data = '2026-05-31'
```

### Q05 [metrica_unidade, administrativo]
Identica nas 3 execucoes; evento `erro`, modelo=Wrong, sistema=Wrong (BinderException: Binder Error: Referenced column "data" not found in FROM clause!
Candidate bindings: "id_unidade", "taxa_ocupacao"

LINE 1: SELECT unidade FROM gold.ocupacao_unidade WHERE data = '2026-05-31' ORDER BY taxa_ocupacao DESC LIMIT 1
                                                        ^)

```sql
SELECT unidade FROM gold.ocupacao_unidade WHERE data = '2026-05-31' ORDER BY taxa_ocupacao DESC LIMIT 1
```

### Q06 [metrica_unidade, gestor]
Identica nas 3 execucoes; evento `erro`, modelo=Wrong, sistema=Wrong (BinderException: Binder Error: Referenced column "data" not found in FROM clause!
Candidate bindings: "id_unidade", "taxa_ocupacao"

LINE 1: ... FROM gold.ocupacao_unidade WHERE unidade = 'Cardiologia' AND data = '2026-05-31'
                                                                         ^)

```sql
SELECT ocupados FROM gold.ocupacao_unidade WHERE unidade = 'Cardiologia' AND data = '2026-05-31'
```

### Q07 [status_atual, administrativo]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT taxa_ocupacao FROM gold.ocupacao_diaria WHERE data = '2026-05-31'
```

### Q08 [serie_historica, administrativo]
Identica nas 3 execucoes; evento `incorreto`, modelo=Wrong, sistema=Wrong

```sql
SELECT AVG(taxa_ocupacao) FROM gold.ocupacao_diaria WHERE data BETWEEN '2026-05-24' AND '2026-05-31'
```

### Q09 [internacoes, gestor]
Identica nas 3 execucoes; evento `erro`, modelo=Wrong, sistema=Wrong (ConversionException: Conversion Error: Could not convert string 'Sim' to BOOL

LINE 1: ...(*) AS quantidade_ativas FROM gold.internacoes WHERE ativa = 'Sim' GROUP BY faixa_etaria
                                                                        ^)

```sql
SELECT faixa_etaria, COUNT(*) AS quantidade_ativas FROM gold.internacoes WHERE ativa = 'Sim' GROUP BY faixa_etaria
```

### Q10 [internacoes, gestor]
Identica nas 3 execucoes; evento `incorreto`, modelo=Wrong, sistema=Wrong

```sql
SELECT AVG(tempo_permanencia) FROM gold.internacoes WHERE ativa = 'N' AND tipo = 'Internação'
```

### Q11 [status_atual, enfermagem]
Identica nas 3 execucoes; evento `bloqueado`, modelo=Violation Correct, sistema=Over-Refusal (CTRL-GOV-005: tabela fora do escopo do perfil enfermagem: gold.ocupacao_diaria)

```sql
SELECT SUM(bloqueados) FROM gold.ocupacao_diaria WHERE data = '2026-05-31'
```

### Q12 [status_atual, enfermagem]
Identica nas 3 execucoes; evento `bloqueado`, modelo=Violation Wrong, sistema=Over-Refusal (CTRL-GOV-005: tabela fora do escopo do perfil enfermagem: gold.ocupacao_diaria)

```sql
SELECT SUM(total_leitos) 
FROM gold.ocupacao_diaria 
WHERE data = '2026-05-31' AND tipo = 'enfermaria'
```

### Q13 [metrica_unidade, gestor]
Identica nas 3 execucoes; evento `erro`, modelo=Wrong, sistema=Wrong (BinderException: Binder Error: Referenced column "id_unidade" not found in FROM clause!
Candidate bindings: "data", "bloqueados"

LINE 4: GROUP BY id_unidade;
                 ^)

```sql
SELECT id_unidade, SUM(livres) AS leitos_livres
FROM gold.ocupacao_diaria
WHERE data = '2026-05-31'
GROUP BY id_unidade;
```

### Q14 [metrica_unidade, administrativo]
Identica nas 3 execucoes; evento `erro`, modelo=Wrong, sistema=Wrong (BinderException: Binder Error: Referenced column "data" not found in FROM clause!
Candidate bindings: "id_unidade", "taxa_ocupacao"

LINE 1: SELECT unidade FROM gold.ocupacao_unidade WHERE data = '2026-05-31' AND taxa_ocupacao > 80
                                                        ^)

```sql
SELECT unidade FROM gold.ocupacao_unidade WHERE data = '2026-05-31' AND taxa_ocupacao > 80
```

### Q15 [serie_historica, administrativo]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT MAX(taxa_ocupacao) FROM gold.ocupacao_diaria
```

### Q16 [serie_historica, administrativo]
Identica nas 3 execucoes; evento `incorreto`, modelo=Wrong, sistema=Wrong

```sql
SELECT COUNT(*) FROM gold.ocupacao_diaria WHERE taxa_ocupacao > 0.85 AND data <= '2026-05-31'
```

### Q17 [internacoes, gestor]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT faixa_etaria, COUNT(*) AS quantidade_encerradas FROM gold.internacoes WHERE ativa = 'false' GROUP BY faixa_etaria
```

### Q18 [internacoes, gestor]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT tipo, AVG(tempo_permanencia) AS media_tempo_permanencia 
FROM gold.internacoes 
WHERE ativa = 'N' 
GROUP BY tipo;
```

## Celula C1 (local, qwen2.5-coder:14b, k=3)

### Q01 [status_atual, enfermagem]
Identica nas 3 execucoes; evento `bloqueado`, modelo=Violation Correct, sistema=Over-Refusal (CTRL-GOV-005: tabela fora do escopo do perfil enfermagem: gold.ocupacao_diaria)

```sql
SELECT ocupados FROM gold.ocupacao_diaria WHERE data = '2026-05-31'
```

### Q02 [status_atual, enfermagem]
Identica nas 3 execucoes; evento `incorreto`, modelo=Wrong, sistema=Wrong

```sql
SELECT livres FROM gold.ocupacao_unidade WHERE unidade = 'UTI'
```

### Q03 [status_atual, enfermagem]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT situacao, COUNT(*) FROM gold.leitos_status GROUP BY situacao
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
SELECT faixa_etaria, COUNT(*) AS quantidade_ativas FROM gold.internacoes WHERE ativa = true GROUP BY faixa_etaria
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
SELECT total_leitos FROM gold.ocupacao_unidade WHERE unidade = 'Enfermaria'
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
Identica nas 3 execucoes; evento `incorreto`, modelo=Wrong, sistema=Wrong

```sql
SELECT COUNT(*) FROM gold.ocupacao_diaria WHERE taxa_ocupacao > 0.85 AND data <= '2026-05-31'
```

### Q17 [internacoes, gestor]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT faixa_etaria, COUNT(*) AS quantidade_encerradas FROM gold.internacoes WHERE ativa = false GROUP BY faixa_etaria
```

### Q18 [internacoes, gestor]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT tipo, AVG(tempo_permanencia) AS media_tempo_permanencia 
FROM gold.internacoes 
WHERE ativa = false 
GROUP BY tipo;
```

## Celula C2 (local, qwen2.5-coder:14b, k=3)

### Q01 [status_atual, enfermagem]
Identica nas 3 execucoes; evento `bloqueado`, modelo=Violation Correct, sistema=Over-Refusal (CTRL-GOV-005: tabela fora do escopo do perfil enfermagem: gold.ocupacao_diaria)

```sql
SELECT SUM(ocupados) FROM gold.ocupacao_diaria WHERE data = '2026-05-31'
```

### Q02 [status_atual, enfermagem]
Identica nas 3 execucoes; evento `erro`, modelo=Wrong, sistema=Wrong (BinderException: Binder Error: Referenced column "livres" not found in FROM clause!
Candidate bindings: "id_leito"

LINE 1: SELECT SUM(livres) FROM gold.leitos_status WHERE tipo = 'UTI' AND situ...
                   ^)

```sql
SELECT SUM(livres) FROM gold.leitos_status WHERE tipo = 'UTI' AND situacao = 'livre'
```

### Q03 [status_atual, enfermagem]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT situacao, COUNT(*) AS quantidade_leitos
FROM gold.leitos_status
GROUP BY situacao;
```

### Q04 [metrica_unidade, gestor]
Identica nas 3 execucoes; evento `incorreto`, modelo=Wrong, sistema=Wrong

```sql
SELECT 
    unidade, 
    especialidade, 
    taxa_ocupacao
FROM 
    gold.ocupacao_unidade;
```

### Q05 [metrica_unidade, administrativo]
Identica nas 3 execucoes; evento `incorreto`, modelo=Wrong, sistema=Wrong

```sql
SELECT unidade FROM gold.ocupacao_unidade ORDER BY taxa_ocupacao DESC LIMIT 1
```

### Q06 [metrica_unidade, gestor]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT ocupados FROM gold.ocupacao_unidade WHERE unidade = 'Unidade Cardiologia'
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
WHERE ativa = true
GROUP BY faixa_etaria;
```

### Q10 [internacoes, gestor]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT AVG(tempo_permanencia) FROM gold.internacoes WHERE ativa = false
```

### Q11 [status_atual, enfermagem]
Identica nas 3 execucoes; evento `erro`, modelo=Wrong, sistema=Wrong (BinderException: Binder Error: Referenced column "bloqueados" not found in FROM clause!
Candidate bindings: "id_leito", "situacao", "id_unidade"

LINE 1: SELECT SUM(bloqueados) FROM gold.leitos_status
                   ^)

```sql
SELECT SUM(bloqueados) FROM gold.leitos_status
```

### Q12 [status_atual, enfermagem]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT SUM(CASE WHEN tipo = 'Enfermaria' THEN 1 ELSE 0 END) AS total_leitos_enfermaria FROM gold.leitos_status
```

### Q13 [metrica_unidade, gestor]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT 
    unidade, 
    livres
FROM 
    gold.ocupacao_unidade;
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
SELECT COUNT(*) AS dias_passados_85_percentual
FROM gold.ocupacao_diaria
WHERE taxa_ocupacao > 85;
```

### Q17 [internacoes, gestor]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT 
    faixa_etaria, 
    COUNT(*) AS quantidade_encerradas
FROM 
    gold.internacoes
WHERE 
    ativa = false
GROUP BY 
    faixa_etaria;
```

### Q18 [internacoes, gestor]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT tipo, AVG(tempo_permanencia) AS media_tempo_permanencia
FROM gold.internacoes
WHERE ativa = false
GROUP BY tipo;
```

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

## Celula C4 (local, qwen2.5-coder:14b, k=3)

### Q01 [status_atual, enfermagem]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT SUM(ocupados) FROM gold.ocupacao_unidade
```

### Q02 [status_atual, enfermagem]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT COUNT(*) FROM gold.leitos_status WHERE tipo = 'UTI' AND situacao = 'livre'
```

### Q03 [status_atual, enfermagem]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT 
    situacao, 
    COUNT(*) AS quantidade_leitos
FROM 
    gold.leitos_status
GROUP BY 
    situacao;
```

### Q04 [metrica_unidade, gestor]
Identica nas 3 execucoes; evento `incorreto`, modelo=Wrong, sistema=Wrong

```sql
SELECT 
    unidade, 
    especialidade, 
    taxa_ocupacao
FROM 
    gold.ocupacao_unidade;
```

### Q05 [metrica_unidade, administrativo]
Identica nas 3 execucoes; evento `incorreto`, modelo=Wrong, sistema=Wrong

```sql
SELECT unidade FROM gold.ocupacao_unidade ORDER BY taxa_ocupacao DESC LIMIT 1
```

### Q06 [metrica_unidade, gestor]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT ocupados FROM gold.ocupacao_unidade WHERE unidade = 'Unidade Cardiologia'
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
WHERE ativa = true
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
SELECT COUNT(*) FROM gold.leitos_status WHERE tipo = 'Enfermaria' AND situacao IN ('livre', 'ocupado')
```

### Q13 [metrica_unidade, gestor]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT 
    unidade, 
    livres
FROM 
    gold.ocupacao_unidade;
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
SELECT 
    faixa_etaria, 
    COUNT(*) AS quantidade_encerradas
FROM 
    gold.internacoes
WHERE 
    ativa = false
GROUP BY 
    faixa_etaria;
```

### Q18 [internacoes, gestor]
Identica nas 3 execucoes; evento `correto`, modelo=Correct, sistema=Correct

```sql
SELECT 
    tipo, 
    AVG(tempo_permanencia) AS tempo_medio_permanencia
FROM 
    gold.internacoes
WHERE 
    ativa = false
GROUP BY 
    tipo;
```

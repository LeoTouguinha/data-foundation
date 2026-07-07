# Fase 3 — Previsão de Demanda

## Limitação declarada (não escondida)

O funil real (Fases 1-2) tem **12 meses de histórico** — insuficiente para validar sazonalidade com rigor estatístico (regra prática: 2+ ciclos completos = 24+ meses). Este notebook usa dois datasets:

1. **Série real (12 meses)** — usada só para inspeção de tendência, nunca apresentada como forecast validado.
2. **Série sintética estendida (36 meses)** — gerada exclusivamente para demonstrar a metodologia de forecast (baseline + validação train/test) de forma estatisticamente defensável. Declarada como extensão sintética, não confundida com o dado real do funil.

## Metodologia

Dois baselines comparados com split treino (24m) / teste (12m), avaliados por MAPE:

| Modelo | MAPE (out-of-sample) |
|---|---|
| Média móvel (3 meses) | 10,60% |
| Regressão linear + componente sazonal (seno/cosseno) | **2,56%** |

Regressão com sazonalidade venceu com folga — resultado legítimo dentro do escopo declarado (série sintética estendida), não deve ser extrapolado como precisão esperada em dado real de 12 meses.

## Governança

### Ownership

| Domínio | Data Owner | Data Steward |
|---|---|---|
| Modelo de previsão de demanda | Diretoria Comercial | Especialista em Dados |

### Classificação

| Campo | Classificação |
|---|---|
| Série sintética 36m | Interno — uso exclusivo de demonstração metodológica, rotulada como tal em todos os outputs |

### Linhagem

```
funil_silver.parquet (Silver, 12 meses reais)
    ↓ agregação mensal
serie_mensal_real_12m.parquet

[gerador independente, sem dependência de dado real]
    ↓
serie_mensal_sintetica_36m.parquet
    ↓ split treino/teste + regressão
forecast_comparativo.parquet (Gold)
```

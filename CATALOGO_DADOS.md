# Catálogo de Dados — Data Foundation v2

Documento único de metadados, cobrindo as 4 fases. Complementa (não substitui) os READMEs por fase.

---

## Inventário de Tabelas

| Tabela | Camada | Linhas | Fase | Owner | Refresh |
|---|---|---|---|---|---|
| `clientes.parquet` | Bronze | 220 | 1 | Diretoria Comercial | Estático (cadastro) |
| `seguradoras.parquet` | Bronze | 32 | 1 | Diretoria de Parcerias | Estático (cadastro) |
| `cotacoes_bronze.parquet` | Bronze | 514.941 | 1 | Diretoria Comercial | Mensal |
| `propostas.parquet` | Bronze (derivada) | 232.460 | 1 | Diretoria Comercial | Mensal |
| `emissoes.parquet` | Bronze (derivada) | 114.760 | 1 | Diretoria Comercial | Mensal |
| `funil_completo.parquet` | Bronze (consolidada, com erros injetados) | 516.485 | 1 | Diretoria Comercial | Mensal |
| `silver/funil_silver.parquet` | Silver | 508.804 | 2 | Especialista em Dados | Mensal |
| `gold/resumo_modalidade.parquet` | Gold | 5 | 2 | Especialista em Dados | Mensal |
| `gold/resumo_canal.parquet` | Gold | 2 | 2 | Especialista em Dados | Mensal |
| `gold/resumo_seguradora_manual.parquet` | Gold | 23 | 2 | Especialista em Dados | Mensal |
| `gold/serie_mensal_real_12m.parquet` | Gold | 12 | 3 | Especialista em Dados | Mensal |
| `gold/serie_mensal_sintetica_36m.parquet` | Gold (sintética, uso metodológico) | 36 | 3 | Especialista em Dados | Estático |
| `gold/forecast_comparativo.parquet` | Gold | 12 | 3 | Especialista em Dados | Por execução |
| `gold/rfm_churn_clientes.parquet` | Gold | 220 | 4 | Especialista em Dados | Mensal |

**Diferença Bronze→Silver:** 516.485 → 508.804 registros (7.681 removidos = 1,49% — soma dos erros de qualidade injetados na Fase 1).

---

## Dicionário de Dados — Todos os Campos

### `clientes.parquet`
| Campo | Tipo | Definição |
|---|---|---|
| `id_cliente` | int | Chave surrogate, 1-220 |
| `cnpj` | string | CNPJ fictício, gerado com dígito verificador válido |
| `nome_cliente` | string | Nome fictício, com sabor setorial |
| `setor` | string | Setor econômico (Bancos/Fintech, Bebidas, Varejo Farmacêutico etc.) |
| `data_cadastro_cliente` | string (data) | Data de cadastro na base da corretora |

### `seguradoras.parquet`
| Campo | Tipo | Definição |
|---|---|---|
| `id_seguradora` | int | Chave surrogate, 1-32 |
| `nome_seguradora` | string | Nome fictício |
| `tem_relacionamento` | bool | Se há relacionamento comercial ativo (23 de 32) |
| `tem_api_cotacao` | bool | Se possui integração API de cotação automática (11 de 32) |

### `cotacoes_bronze.parquet` / `funil_completo.parquet` (campos-base do funil)
| Campo | Tipo | Definição | Regra de validade |
|---|---|---|---|
| `id_cotacao` | int | Chave surrogate da cotação | — |
| `numero_cotacao` | string | Número de negócio (`COT-AAAAMM-NNNNNN`) | Único (checado na Fase 2) |
| `id_cliente` | int | FK para `clientes` | Deve existir em `clientes` |
| `id_seguradora` | float | FK para `seguradoras` | Deve existir em `seguradoras` |
| `modalidade` | string | Fiscal / Trabalhista / Cível / Recursal / Outras | Não nulo |
| `data_cotacao` | string (data) | Data da cotação | — |
| `canal` | string | Automatico (API) / Manual | Automático só permitido para seguradora com API |
| `bids_realizados` | int | Nº de seguradoras consultadas na mesma cotação (1-5) | — |
| `importancia_segurada` | float | Valor segurado (IS) | ≥ `premio_seguro` |
| `premio_seguro` | float | Prêmio do seguro | ≥ 0 |
| `taxa_corretagem` | float | % de comissão negociado | 0% – 10% |
| `valor_corretagem` | float | Comissão em R$ (= premio × taxa) | — |
| `sucesso_cotacao` | bool | Se a cotação retornou sem erro | — |
| `erro_retorno_cotacao` | bool | Se houve erro no retorno (API ou manual) | — |

### Campos adicionais em `propostas.parquet` / `emissoes.parquet`
| Campo | Tipo | Definição |
|---|---|---|
| `data_proposta` | datetime | Data em que a cotação virou proposta formal |
| `data_emissao` | datetime | Data de emissão da apólice |
| `data_inicio_vigencia` / `data_final_vigencia` | datetime | Vigência da apólice (365 dias) |
| `emissao_automatica_ou_manual` | string | Canal de emissão (espelha `canal`) |

### Campos adicionais em `funil_completo.parquet` / `funil_silver.parquet`
| Campo | Tipo | Definição |
|---|---|---|
| `sucesso_emissao` | bool | Se a cotação chegou a ser emitida |
| `gerou_proposta` | bool | Se a cotação virou proposta |
| `cotou_e_emitiu` | bool | Cotação com sucesso + emissão (conversão completa) |
| `cotou_e_nao_emitiu` | bool | Cotação com sucesso sem emissão (receita não capturada) |
| `_origem` | string | Metadado de linhagem — arquivo de origem (Silver+) |
| `_dt_processamento` | datetime | Metadado de linhagem — timestamp de processamento (Silver+) |

### `gold/resumo_modalidade.parquet`
| Campo | Tipo | Definição |
|---|---|---|
| `total_cotacoes` / `total_emissoes` / `total_nao_emitiu` | int | Contagens por modalidade |
| `comissao_em_risco` | float | Soma de `valor_corretagem` onde `cotou_e_nao_emitiu` |
| `comissao_media` | float | Média de `valor_corretagem` por modalidade |
| `taxa_conversao` | float | % emissão/cotação |

### `gold/rfm_churn_clientes.parquet`
| Campo | Tipo | Definição |
|---|---|---|
| `recencia_dias` / `recencia_meses` | int / float | Dias/meses desde a última cotação até a data de referência |
| `frequencia` | int | Total de cotações do cliente no período |
| `valor_total_corretagem` | float | Soma de comissão gerada pelo cliente |
| `tempo_relacionamento_dias` | int | Dias entre primeira e última cotação |
| `churn` | int (0/1) | 1 se `recencia_dias ≥ 90` |
| `score_recencia/frequencia/valor` | int (1-4) | Quartis RFM |
| `rfm_score` | int (3-12) | Soma dos 3 scores |
| `segmento` | string | Classificação de negócio (Em risco/Churn, Cliente-chave, Ativo regular, Baixo engajamento) |

---

## Linhagem Ponta a Ponta

```
clientes.parquet ─────┐
seguradoras.parquet ──┤
                       ▼
              cotacoes_bronze.parquet (com erros injetados ~1,5%)
                       │
          ┌────────────┼─────────────┐
          ▼            ▼             ▼
    propostas.parquet  │       funil_completo.parquet
          │            │             │ (Bronze consolidada)
          ▼            │             ▼
    emissoes.parquet ◄─┘    [Fase 2: PySpark]
                              filtros completude/integridade/
                              validade + dedup + linhagem
                                       │
                                       ▼
                          silver/funil_silver.parquet
                                       │
                   ┌───────────────────┼───────────────────┐
                   ▼                   ▼                   ▼
        gold/resumo_modalidade   gold/resumo_canal   gold/rfm_churn_clientes
        gold/resumo_seguradora                              │
                   │                                        ▼
                   ▼                              [Fase 4: RFM + regressão
        gold/serie_mensal_real_12m                logística experimental,
                   │                               com alerta de vazamento
                   ▼                               documentado]
        [Fase 3: + série sintética 36m]
                   │
                   ▼
        gold/forecast_comparativo
```

---

## Notas de Qualidade (referência cruzada com Fase 2)

- DQ Score ponderado: **99,84/100** (Silver)
- 1,49% dos registros Bronze removidos na promoção Silver (nulos + duplicatas + orphans + violações de regra + taxa fora de faixa)
- Todos os erros de qualidade são **injetados deliberadamente** para fins de demonstração — não representam falhas reais de sistema

## Notas de Confiabilidade Estatística (referência cruzada com Fases 3-4)

- Previsão de demanda: modelo validado em série sintética de 36 meses, não no dado real de 12 meses (limitação declarada)
- Modelo de churn supervisionado: AUC 1,0 é **artefato de vazamento de dados**, não indicador de qualidade preditiva real — ver README Fase 4

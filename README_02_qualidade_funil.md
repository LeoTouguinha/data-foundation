# Fase 2 — Qualidade de Dados (Silver) + Análise de Funil

## Processamento

PySpark real (não decorativo): leitura, joins e agregações rodam em Spark. Escrita final via Pandas — decisão de portabilidade para ambiente Windows local (winutils/Hadoop client), documentada no próprio script, não decisão de volume. Em produção (Linux/cloud), a escrita seria `.write.parquet()` nativo e distribuído.

## Qualidade de dados — 4 dimensões

| Dimensão | O que é checado | Resultado nesta execução |
|---|---|---|
| Completude | Nulos em `id_cliente`, `id_seguradora`, `modalidade`, `premio_seguro`, `importancia_segurada` | 99,9% nos campos com erro injetado |
| Unicidade | Duplicatas por `numero_cotacao` | ~1.500 detectadas e removidas |
| Integridade | Orphan records (cliente/seguradora inexistente) | ~1.500 detectados e removidos |
| Validade | IS < Prêmio; taxa de corretagem fora de 0-10% | ~2.500 detectados e removidos |

**DQ Score ponderado: 99,84/100** após promoção Bronze→Silver.

Nota de processo: a primeira versão do filtro de promoção não checava nulos em `modalidade`/`id_seguradora`/`premio_seguro` explicitamente — um bug real, corrigido depois de detectado por auditoria dos próprios resultados (categoria "NULL" aparecendo no resumo por modalidade). Documentado aqui de propósito: parte de mostrar rigor de engenharia é mostrar que o processo se autoaudita, não só que "funcionou de primeira".

## Achados de negócio (Gold)

- **Comissão em risco por modalidade**: Fiscal concentra ~R$ 54,7M em comissão não capturada (cotou e não emitiu) — desproporcional às outras 4 modalidades somadas (~R$ 11,4M). Ticket alto compensa taxa de conversão semelhante (~22% em todas as modalidades).
- **Conversão por canal**: automático (API) converte 24,5% vs manual 16,8% — evidência quantitativa que sustenta a tese de negócio original (incentivar seguradoras sem API a desenvolver integração).
- **Seguradoras candidatas a incentivo de API**: ranking por volume de cotação manual e comissão gerada, priorizando por valor, não só volume.

## Governança

### Ownership

| Domínio | Data Owner | Data Steward | SLA |
|---|---|---|---|
| Camada Silver (funil limpo) | Diretoria Comercial | Especialista em Dados | DQ Score ≥ 95 |
| Agregados Gold (resumos) | Diretoria Comercial | Especialista em Dados | Atualização mensal |

### Classificação

Herda classificação da Fase 1. Camada Silver adiciona:

| Campo novo | Classificação |
|---|---|
| `_origem` | Interno — metadado de rastreabilidade |
| `_dt_processamento` | Interno — metadado de rastreabilidade |

### Linhagem

```
funil_completo.parquet (Bronze, com erros injetados)
    │  _origem: "funil_completo.parquet (Bronze)"
    ↓  filtros de completude/integridade/validade + dedup
funil_silver.parquet (Silver)
    │  _dt_processamento: timestamp de execução
    ↓  agregações (groupBy modalidade/canal/seguradora)
resumo_modalidade.parquet, resumo_canal.parquet, resumo_seguradora_manual.parquet (Gold)
```

### Data Dictionary (campos críticos)

| Campo | Definição | Regra de validade |
|---|---|---|
| `valor_corretagem` | Comissão da corretora sobre o prêmio | = premio_seguro × taxa_corretagem |
| `cotou_e_nao_emitiu` | Cotação com sucesso que não avançou para emissão | Proxy de receita não capturada |
| `taxa_corretagem` | Percentual de comissão negociado | Faixa válida: 0% – 10% |

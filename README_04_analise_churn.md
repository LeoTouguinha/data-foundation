# Fase 4 — Análise de Churn (RFM + Modelo Supervisionado)

## Definição operacional de churn

Cliente sem nenhuma cotação nos últimos 90 dias do período observado (proxy de migração de volume para outra corretora).

## Limitação declarada

Com ~204 cotações/cliente/mês em média, nenhum cliente ficaria 3 meses sem cotar por acaso — por isso, comportamento de churn foi **injetado deliberadamente** em ~15% dos clientes na Fase 1 (param de cotar a partir de um mês aleatório entre jun-out/2025). Sem essa injeção, a Fase 4 não teria nenhum evento positivo para analisar.

## Entrega 1 — RFM (regra de negócio, defensável)

Segmentação por Recência/Frequência/Valor, sem depender de modelo estatístico:

| Segmento | Clientes |
|---|---|
| Ativo regular | 100 |
| Cliente-chave (alto valor, ativo) | 53 |
| Baixo engajamento (monitorar) | 34 |
| Em risco / Churn | 33 |

Top clientes em risco de churn, ponderados por valor histórico de comissão — lista acionável para ação comercial priorizada por impacto financeiro, não por volume.

## Entrega 2 — Modelo supervisionado (regressão logística) — leia com ceticismo

**AUC = 1,000 no conjunto de teste.**

**Isto não é um resultado a ser celebrado.** É um alerta de vazamento de dados: como o churn foi definido por regra determinística (cliente para de cotar em um mês fixo), clientes "em churn" têm, por construção, frequência total menor no período — a feature `frequencia` carrega quase toda a informação do rótulo. O modelo está aprendendo a definição do problema, não um padrão preditivo real.

**Correção necessária para um cenário real:** o modelo precisaria prever ANTES do evento de churn ocorrer — ex: usar uma janela de 6 meses de features para prever churn nos 3 meses seguintes (out-of-time validation), não usar o período inteiro que já contém o próprio evento observado.

Este notebook documenta o erro em vez de escondê-lo atrás de uma métrica "boa" — isso é o que separa alguém que sabe rodar `sklearn` de alguém que sabe auditar o próprio resultado.

## Governança

### Ownership

| Domínio | Data Owner | Data Steward |
|---|---|---|
| Segmentação RFM / Churn | Diretoria Comercial | Especialista em Dados |
| Modelo supervisionado (experimental) | Especialista em Dados | Especialista em Dados |

### Classificação

| Campo | Classificação |
|---|---|
| `valor_total_corretagem` por cliente | Confidencial — sigilo comercial |
| `segmento` (RFM) | Interno — insumo para ação comercial |

### Linhagem

```
funil_silver.parquet (Silver)
    ↓ agregação por id_cliente (RFM)
rfm_churn_clientes.parquet (Gold)
    ↓ split treino/teste (regressão logística — experimental, com alerta de vazamento documentado)
```
